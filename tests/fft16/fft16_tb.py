import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random
import numpy as np
from fft16 import FFT16


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def float_to_int(val, frac_bits):
    return int(round(val * (2**frac_bits)))

def int_to_float(val, frac_bits):
    return val / (2**frac_bits)


# ---------------------------------------------------------
# Test: Stage-by-stage verification
# ---------------------------------------------------------

@cocotb.test()
async def test_fft16_stage1(dut):
    """
    Isolated verification of:
      - Stage 1 (FFT4 Radix-4)
      - MDC stage (FFT4 Radix-2)
      - Final clipped/rounded output
    """

    # -----------------------------------------------------
    # Parameters
    # -----------------------------------------------------

    NB_DATA       = 8
    NBF_DATA      = 6
    N             = 16
    NBF_STAGE1    = 6
    NBF_STAGE2    = 3

    fft_model = FFT16(
        N=N,
        fxp=1,
        NB_INPUT=NB_DATA,
        NBF_INPUT=NBF_DATA,
        fft_mode=1
    )

    # -----------------------------------------------------
    # Clock & Reset
    # -----------------------------------------------------

    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.i_clk_en.value   = 0
    dut.i_rst_n.value    = 0
    dut.i_inverse.value  = 0
    dut.i_valid.value    = 0
    dut.i_tx_ready.value = 1
    dut.i_data_re.value  = 0
    dut.i_data_im.value  = 0

    await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)
    dut.i_clk_en.value = 1

    cocotb.log.info("--- Starting FFT16 Stage-by-Stage Verification ---")

    # -----------------------------------------------------
    # Input generation
    # -----------------------------------------------------

    input_float = 2 * np.random.uniform(-1, 1, N) + \
                  2j * np.random.uniform(-1, 1, N)

    input_q = [
        fft_model.round.crnd(x, True, NB_DATA, NBF_DATA, 'around')
        for x in input_float
    ]

    expected_fft4rdx4, expected_fft4rdx2, expected_out = \
        fft_model.process(input_q)

    # -----------------------------------------------------
    # Feed 16 samples into RTL
    # -----------------------------------------------------

    for i in range(N):
        dut.i_valid.value   = 1
        dut.i_data_re.value = float_to_int(input_q[i].real, NBF_DATA)
        dut.i_data_im.value = float_to_int(input_q[i].imag, NBF_DATA)
        await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0

    # =====================================================
    # Stage 1: FFT4 Radix-4
    # =====================================================

    timeout = 100
    cycles_wait = 0

    while dut.fft4_valid.value == 0 and cycles_wait < timeout:
        await RisingEdge(dut.i_clk)
        cycles_wait += 1

    assert cycles_wait < timeout, "TIMEOUT: fft4_valid never asserted."

    rtl_stage1 = []
    capture_cycles = 0

    while len(rtl_stage1) < N and capture_cycles < 20:
        if dut.fft4_valid.value == 1:

            re_ports = [
                dut.fft4_data0_re,
                dut.fft4_data1_re,
                dut.fft4_data2_re,
                dut.fft4_data3_re
            ]

            im_ports = [
                dut.fft4_data0_im,
                dut.fft4_data1_im,
                dut.fft4_data2_im,
                dut.fft4_data3_im
            ]

            for p_re, p_im in zip(re_ports, im_ports):
                val_re = int_to_float(p_re.value.to_signed(), NBF_STAGE1)
                val_im = int_to_float(p_im.value.to_signed(), NBF_STAGE1)
                rtl_stage1.append(complex(val_re, val_im))

        await RisingEdge(dut.i_clk)
        capture_cycles += 1

    assert len(rtl_stage1) == N, \
        f"Stage 1 capture error: {len(rtl_stage1)} of {N} samples."

    # =====================================================
    # Unified Capture: MDC Stage + Final Output
    # =====================================================

    while dut.mdc_ffx_valid.value == 0:
        await RisingEdge(dut.i_clk)

    rtl_mdc     = []
    rtl_stage2  = []
    capture_cycles = 0

    while len(rtl_mdc) < N and capture_cycles < 10:

        if dut.mdc_ffx_valid.value == 1:

            # MDC stage ports (raw)
            re_mdc = [
                dut.mdc_ff0_data0_re, dut.mdc_ff0_data1_re,
                dut.mdc_ff1_data0_re, dut.mdc_ff1_data1_re,
                dut.mdc_ff2_data0_re, dut.mdc_ff2_data1_re,
                dut.mdc_ff3_data0_re, dut.mdc_ff3_data1_re
            ]

            im_mdc = [
                dut.mdc_ff0_data0_im, dut.mdc_ff0_data1_im,
                dut.mdc_ff1_data0_im, dut.mdc_ff1_data1_im,
                dut.mdc_ff2_data0_im, dut.mdc_ff2_data1_im,
                dut.mdc_ff3_data0_im, dut.mdc_ff3_data1_im
            ]

            # Rounded / clipped output ports
            re_out = [
                dut.rnd_mdc0_d0_re, dut.rnd_mdc0_d1_re,
                dut.rnd_mdc1_d0_re, dut.rnd_mdc1_d1_re,
                dut.rnd_mdc2_d0_re, dut.rnd_mdc2_d1_re,
                dut.rnd_mdc3_d0_re, dut.rnd_mdc3_d1_re
            ]

            im_out = [
                dut.rnd_mdc0_d0_im, dut.rnd_mdc0_d1_im,
                dut.rnd_mdc1_d0_im, dut.rnd_mdc1_d1_im,
                dut.rnd_mdc2_d0_im, dut.rnd_mdc2_d1_im,
                dut.rnd_mdc3_d0_im, dut.rnd_mdc3_d1_im
            ]

            for i in range(8):

                val_mdc = complex(
                    int_to_float(re_mdc[i].value.to_signed(), NBF_STAGE1),
                    int_to_float(im_mdc[i].value.to_signed(), NBF_STAGE1)
                )

                val_out = complex(
                    int_to_float(re_out[i].value.to_signed(), NBF_STAGE2),
                    int_to_float(im_out[i].value.to_signed(), NBF_STAGE2)
                )

                rtl_mdc.append(val_mdc)
                rtl_stage2.append(val_out)

        await RisingEdge(dut.i_clk)
        capture_cycles += 1

    # -----------------------------------------------------
    # Reordering
    # -----------------------------------------------------

    rtl_mdc_ord     = [0j] * N
    rtl_output_ord  = [0j] * N

    mdc_map = [0, 8, 1, 9, 2, 10, 3, 11,
               4, 12, 5, 13, 6, 14, 7, 15]

    for i in range(N):
        rtl_mdc_ord[mdc_map[i]]    = rtl_mdc[i]
        rtl_output_ord[mdc_map[i]] = rtl_stage2[i]

    # =====================================================
    # Comparison
    # =====================================================

    tol = 1e-9

    # -----------------------------------------------------
    # Stage 1
    # -----------------------------------------------------

    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info("STAGE 1 RESULTS (FFT4 Radix-4)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<28} | {'Python':<28} | {'Δ':<15}")
    cocotb.log.info("-" * 80)

    for idx in range(N):

        rtl_val = rtl_stage1[idx]
        py_val  = expected_fft4rdx4[idx]

        diff_re = abs(rtl_val.real - py_val.real)
        diff_im = abs(rtl_val.imag - py_val.imag)

        cocotb.log.info(
            f"{idx:<5} | "
            f"{rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )

        assert diff_re < tol and diff_im < tol, \
            f"Stage 1 mismatch at index {idx}"

    cocotb.log.info("Stage 1 PASSED.")

    # -----------------------------------------------------
    # MDC Stage
    # -----------------------------------------------------

    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info("MDC STAGE RESULTS (FFT4 Radix-2)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<28} | {'Python':<28} | {'Δ':<15}")
    cocotb.log.info("-" * 80)

    for idx in range(N):

        rtl_val = rtl_mdc_ord[idx]
        py_val  = expected_fft4rdx2[idx]

        diff_re = abs(rtl_val.real - py_val.real)
        diff_im = abs(rtl_val.imag - py_val.imag)

        cocotb.log.info(
            f"{idx:<5} | "
            f"{rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )

        assert diff_re < tol and diff_im < tol, \
            f"MDC stage mismatch at index {idx}"

    cocotb.log.info("MDC Stage PASSED.")

    # -----------------------------------------------------
    # Final Output
    # -----------------------------------------------------

    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info("FINAL OUTPUT RESULTS (Clipped / Rounded)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<28} | {'Python':<28} | {'Δ':<15}")
    cocotb.log.info("-" * 80)

    for idx in range(N):

        rtl_val = rtl_output_ord[idx]
        py_val  = expected_out[idx]

        diff_re = abs(rtl_val.real - py_val.real)
        diff_im = abs(rtl_val.imag - py_val.imag)

        cocotb.log.info(
            f"{idx:<5} | "
            f"{rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )

        assert diff_re < tol and diff_im < tol, \
            f"Final output mismatch at index {idx}"

    cocotb.log.info("Final Output PASSED.")
    cocotb.log.info("=" * 80)