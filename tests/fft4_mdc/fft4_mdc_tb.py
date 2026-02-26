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
    except ValueError:
        return 0j

async def drive_input(dut, input_seq, n_frac=6):

    dut.i_valid.value = 1
    scale = 2 ** n_frac
    
    dut.i_data1_r.value = int(np.round(input_seq[0].real * scale))
    dut.i_data1_i.value = int(np.round(input_seq[0].imag * scale))
    dut.i_data2_r.value = int(np.round(input_seq[2].real * scale))
    dut.i_data2_i.value = int(np.round(input_seq[2].imag * scale))
    await RisingEdge(dut.i_clk)

    dut.i_data1_r.value = int(np.round(input_seq[1].real * scale))
    dut.i_data1_i.value = int(np.round(input_seq[1].imag * scale))
    dut.i_data2_r.value = int(np.round(input_seq[3].real * scale))
    dut.i_data2_i.value = int(np.round(input_seq[3].imag * scale))
    await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0

async def monitor_stage1(dut):
    while dut.w_out_stg1_valid.value == 0:
        await RisingEdge(dut.i_clk)
    
    v0 = get_complex_fxp(dut.w_out_stg1_1r, dut.w_out_stg1_1i, n_frac=6)
    v2 = get_complex_fxp(dut.w_out_stg1_2r, dut.w_out_stg1_2i, n_frac=6)
    await RisingEdge(dut.i_clk)
    
    if dut.w_out_stg1_valid.value == 1:
        v1 = get_complex_fxp(dut.w_out_stg1_1r, dut.w_out_stg1_1i, n_frac=6)
        v3 = get_complex_fxp(dut.w_out_stg1_2r, dut.w_out_stg1_2i, n_frac=6)
    else:
        v2, v3 = 0j, 0j
        
    return [v0, v1, v2, v3]

async def monitor_stage2(dut):
    while dut.o_valid.value == 0:
        await RisingEdge(dut.i_clk)
    
    y0 = get_complex_fxp(dut.o_data1_r, dut.o_data1_i, n_frac=6)
    y2 = get_complex_fxp(dut.o_data2_r, dut.o_data2_i, n_frac=6)
    await RisingEdge(dut.i_clk)
    
    if dut.o_valid.value == 1:
        y1 = get_complex_fxp(dut.o_data1_r, dut.o_data1_i, n_frac=6)
        y3 = get_complex_fxp(dut.o_data2_r, dut.o_data2_i, n_frac=6)
    else:
        y1, y3 = 0j, 0j
        
    return [y0, y1, y2, y3]

@cocotb.test()
async def test_fft4_mdc_debug(dut):
    NB_INPUT = 8
    NBF_INPUT = 6
    
    # 1. Instanciar DOS modelos de referencia (Directo e Inverso)
    model_fft  = FFT4_Reference(NB_INPUT=NB_INPUT, NBF_INPUT=NBF_INPUT, inverse=False)
    model_ifft = FFT4_Reference(NB_INPUT=NB_INPUT, NBF_INPUT=NBF_INPUT, inverse=True)
    
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    dut.i_rst_n.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    
    dut._log.info("--- INICIANDO TEST DEBUG POR ETAPAS (FFT e IFFT) ---")

    num_tests = 100
    for k in range(num_tests):
        
        # --- ALTERNAR MODO: Pares = FFT, Impares = IFFT ---
        is_inverse = (k % 2 != 0)
        dut.i_inverse.value = 1 if is_inverse else 0
        model = model_ifft if is_inverse else model_fft
        mode_str = "IFFT" if is_inverse else "FFT "
        
        input_float = 2 * np.random.uniform(-1, 1, 4) + 2j * np.random.uniform(-1, 1, 4)
        input_q = [model.round.crnd(x, True, NB_INPUT, NBF_INPUT, 'around') for x in input_float]
        
        mod_stg1, mod_stg2 = model.process(input_q)

        dut._log.info(f"========== TEST {k} [{mode_str}] ==========")
        
        task_stg1 = cocotb.start_soon(monitor_stage1(dut))
        task_stg2 = cocotb.start_soon(monitor_stage2(dut))
        
        await drive_input(dut, input_q)
        
        rtl_stg1 = await task_stg1
        rtl_stg2 = await task_stg2
        
        dut._log.info("--- STAGE 1 RESULTS ---")
        for i in range(4):
            dut._log.info(f" STG1_Bin {i} | RTL: {rtl_stg1[i]:.4f} | Model: {mod_stg1[i]:.4f}")
            
        dut._log.info("--- STAGE 2 RESULTS (FINAL) ---")
        for i in range(4):
            dut._log.info(f" STG2_Bin {i} | RTL: {rtl_stg2[i]:.4f} | Model: {mod_stg2[i]:.4f}")
            
        dut._log.info("==============================\n")
        
        # --- ASERCIONES ---
        tolerancia = (1 / (2**6)) + 1e-6 
        
        for i in range(4):
            assert abs(rtl_stg1[i].real - mod_stg1[i].real) <= tolerancia, f"Mismatch STG1 Real Bin {i} [{mode_str}]. RTL: {rtl_stg1[i].real}, Mod: {mod_stg1[i].real}"
            assert abs(rtl_stg1[i].imag - mod_stg1[i].imag) <= tolerancia, f"Mismatch STG1 Imag Bin {i} [{mode_str}]. RTL: {rtl_stg1[i].imag}, Mod: {mod_stg1[i].imag}"
            
            assert abs(rtl_stg2[i].real - mod_stg2[i].real) <= tolerancia, f"Mismatch STG2 Real Bin {i} [{mode_str}]. RTL: {rtl_stg2[i].real}, Mod: {mod_stg2[i].real}"
            assert abs(rtl_stg2[i].imag - mod_stg2[i].imag) <= tolerancia, f"Mismatch STG2 Imag Bin {i} [{mode_str}]. RTL: {rtl_stg2[i].imag}, Mod: {mod_stg2[i].imag}"

        await RisingEdge(dut.i_clk)
        await RisingEdge(dut.i_clk)