import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import numpy as np
from model_fft4 import FFT4_Reference

def get_complex_fxp(r_sig, i_sig, n_frac=6):
    try:
        r = r_sig.value.to_signed() / (2 ** n_frac)
        i = i_sig.value.to_signed() / (2 ** n_frac)
        return complex(r, i)
    except:
        return 0j

async def drive_input_negotiated(dut, input_seq, n_frac=6):
    scale = 2 ** n_frac
    
    dut.i_valid.value = 1
    dut.i_data1_r.value = int(np.round(input_seq[0].real * scale))
    dut.i_data1_i.value = int(np.round(input_seq[0].imag * scale))
    dut.i_data2_r.value = int(np.round(input_seq[2].real * scale))
    dut.i_data2_i.value = int(np.round(input_seq[2].imag * scale))
    await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0
    dut.i_data1_r.value = 0
    dut.i_data1_i.value = 0
    dut.i_data2_r.value = 0
    dut.i_data2_i.value = 0
    for _ in range(7):
        await RisingEdge(dut.i_clk)

    dut.i_valid.value = 1
    dut.i_data1_r.value = int(np.round(input_seq[1].real * scale))
    dut.i_data1_i.value = int(np.round(input_seq[1].imag * scale))
    dut.i_data2_r.value = int(np.round(input_seq[3].real * scale))
    dut.i_data2_i.value = int(np.round(input_seq[3].imag * scale))
    await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0
    dut.i_data1_r.value = 0
    dut.i_data1_i.value = 0
    dut.i_data2_r.value = 0
    dut.i_data2_i.value = 0
    for _ in range(7):
        await RisingEdge(dut.i_clk)

async def monitor_mdc_logic(dut, vld_signal, r1, i1, r2, i2, n_samples=4):
    captured = []
    while len(captured) < n_samples:
        await RisingEdge(dut.i_clk)
        if vld_signal.value == 1:
            val_a = get_complex_fxp(r1, i1)
            val_b = get_complex_fxp(r2, i2)
            captured.append(val_a)
            captured.append(val_b)
    return captured

@cocotb.test()
async def test_fft4_mdc_debug(dut):
    NB_INPUT = 8
    NBF_INPUT = 6
    model_fft  = FFT4_Reference(NB_INPUT=NB_INPUT, NBF_INPUT=NBF_INPUT, inverse=False)
    model_ifft = FFT4_Reference(NB_INPUT=NB_INPUT, NBF_INPUT=NBF_INPUT, inverse=True)
    
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    dut.i_rst_n.value = 0
    dut.i_inverse.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    
    dut._log.info("====================================================")
    dut._log.info("Starting FFT4 MDC verification (FFT/IFFT alternating)")
    dut._log.info("====================================================")

    num_tests = 1
    for k in range(num_tests):
        
        is_inverse = (k % 2 != 0)
        dut.i_inverse.value = 1 if is_inverse else 0
        model = model_ifft if is_inverse else model_fft
        mode_str = "IFFT" if is_inverse else "FFT "

        input_float = 2 * np.random.uniform(-1, 1, 4) + 2j * np.random.uniform(-1, 1, 4)
        input_q = [model.round.crnd(x, True, NB_INPUT, NBF_INPUT, 'around') for x in input_float]
        mod_stg1, mod_stg2 = model.process(input_q)

        task_stg1 = cocotb.start_soon(monitor_mdc_logic(dut, 
                    dut.u_fft4_mdc_stage1.o_valid, 
                    dut.w_out_stg1_1r, dut.w_out_stg1_1i, 
                    dut.w_out_stg1_2r, dut.w_out_stg1_2i))

        task_stg2 = cocotb.start_soon(monitor_mdc_logic(dut, 
                    dut.o_valid, 
                    dut.o_data1_r, dut.o_data1_i, 
                    dut.o_data2_r, dut.o_data2_i))

        dut.i_rst_n.value = 0
        dut.i_inverse.value = 0
        await RisingEdge(dut.i_clk)
        await RisingEdge(dut.i_clk)
        dut.i_rst_n.value = 1

        await drive_input_negotiated(dut, input_q)

        rtl_stg1 = await task_stg1
        rtl_stg2 = await task_stg2

        stg1_rtl = [rtl_stg1[0], rtl_stg1[2], rtl_stg1[1], rtl_stg1[3]]
        stg2_rtl = [rtl_stg2[0], rtl_stg2[2], rtl_stg2[1], rtl_stg2[3]]

        dut._log.info("========== RESULT DEBUG ==========")
        for i in range(4):
            dut._log.info(f"Bin {i} | STG1 RTL: {stg1_rtl[i]:.4f} | STG1 MOD: {mod_stg1[i]:.4f}")

        dut._log.info("--------------------------------------")
        for i in range(4):
            dut._log.info(f"Bin {i} | STG2 RTL: {stg2_rtl[i]:.4f} | STG2 MOD: {mod_stg2[i]:.4f}")

    
        tolerancia = (1 / (2**6)) + 1e-9 

        dut._log.info(f"Test {k:02d} | Mode: {mode_str}")
        for i in range(4):
            err_stg1_r = abs(stg1_rtl[i].real - mod_stg1[i].real)
            err_stg1_i = abs(stg1_rtl[i].imag - mod_stg1[i].imag)

            err_stg2_r = abs(stg2_rtl[i].real - mod_stg2[i].real)
            err_stg2_i = abs(stg2_rtl[i].imag - mod_stg2[i].imag)

            assert err_stg1_r <= tolerancia, f"STG1 Real mismatch: Bin {i} Real: RTL={stg1_rtl[i].real}, MOD={mod_stg1[i].real}"
            assert err_stg1_i <= tolerancia, f"STG1 Imag mismatch: {i} Imag: RTL={stg1_rtl[i].imag}, MOD={mod_stg1[i].imag}"

            assert err_stg2_r <= tolerancia, f"STG2 Real mismatch: Bin {i} Real: RTL={stg2_rtl[i].real}, MOD={mod_stg2[i].real}"
            assert err_stg2_i <= tolerancia, f"STG2 Imag mismatch: Bin {i} Imag: RTL={stg2_rtl[i].imag}, MOD={mod_stg2[i].imag}"

        dut._log.info(f"✅ TEST {k} PASSED: Todo coincide dentro de la tolerancia {tolerancia:.6f}")

    dut._log.info("====================================================")
    dut._log.info(f"ALL {num_tests} TESTS PASSED")
    dut._log.info("====================================================")