import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Event
import numpy as np
from fft16 import FFT16


def float_to_int(val, frac_bits):
    return int(round(val * (2**frac_bits)))

def int_to_float(val, frac_bits):
    return val / (2**frac_bits)


# =====================================================
# Concurrent capture coroutines
# =====================================================

async def capture_stage1(dut, N, NBF_STAGE1, results, timeout=5000):
    """
    Waits for fft4_valid pulses and captures 4 samples per pulse.
    Must be started BEFORE input injection so no pulses are missed.
    """
    cycles = 0
    while len(results) < N and cycles < timeout:
        await RisingEdge(dut.i_clk)
        cycles += 1
        if dut.fft4_valid.value == 1:
            re_ports = [dut.fft4_data0_re, dut.fft4_data1_re,
                        dut.fft4_data2_re, dut.fft4_data3_re]
            im_ports = [dut.fft4_data0_im, dut.fft4_data1_im,
                        dut.fft4_data2_im, dut.fft4_data3_im]
            for p_re, p_im in zip(re_ports, im_ports):
                results.append(complex(
                    int_to_float(p_re.value.to_signed(), NBF_STAGE1),
                    int_to_float(p_im.value.to_signed(), NBF_STAGE1)
                ))

    assert len(results) == N, \
        f"Stage 1 capture timeout: got {len(results)} of {N} samples."


async def capture_mdc(dut, N, NBF_STAGE1, NBF_STAGE2, mdc_results, stage2_results, timeout=5000):
    """
    Waits for mdc_ffx_valid pulses and captures 8 samples per pulse.
    Must be started BEFORE input injection so no pulses are missed.
    """
    cycles = 0
    while len(mdc_results) < N and cycles < timeout:
        await RisingEdge(dut.i_clk)
        cycles += 1
        if dut.mdc_ffx_valid.value == 1:
            re_mdc = [
                dut.mdc_ff0_data0_re, dut.mdc_ff0_data1_re,
                dut.mdc_ff1_data0_re, dut.mdc_ff1_data1_re,
                dut.mdc_ff2_data0_re, dut.mdc_ff2_data1_re,
                dut.mdc_ff3_data0_re, dut.mdc_ff3_data1_re,
            ]
            im_mdc = [
                dut.mdc_ff0_data0_im, dut.mdc_ff0_data1_im,
                dut.mdc_ff1_data0_im, dut.mdc_ff1_data1_im,
                dut.mdc_ff2_data0_im, dut.mdc_ff2_data1_im,
                dut.mdc_ff3_data0_im, dut.mdc_ff3_data1_im,
            ]
            re_out = [
                dut.rnd_mdc0_d0_re, dut.rnd_mdc0_d1_re,
                dut.rnd_mdc1_d0_re, dut.rnd_mdc1_d1_re,
                dut.rnd_mdc2_d0_re, dut.rnd_mdc2_d1_re,
                dut.rnd_mdc3_d0_re, dut.rnd_mdc3_d1_re,
            ]
            im_out = [
                dut.rnd_mdc0_d0_im, dut.rnd_mdc0_d1_im,
                dut.rnd_mdc1_d0_im, dut.rnd_mdc1_d1_im,
                dut.rnd_mdc2_d0_im, dut.rnd_mdc2_d1_im,
                dut.rnd_mdc3_d0_im, dut.rnd_mdc3_d1_im,
            ]
            for i in range(8):
                mdc_results.append(complex(
                    int_to_float(re_mdc[i].value.to_signed(), NBF_STAGE1),
                    int_to_float(im_mdc[i].value.to_signed(), NBF_STAGE1)
                ))
                stage2_results.append(complex(
                    int_to_float(re_out[i].value.to_signed(), NBF_STAGE2),
                    int_to_float(im_out[i].value.to_signed(), NBF_STAGE2)
                ))

    assert len(mdc_results) == N, \
        f"MDC capture timeout: got {len(mdc_results)} of {N} samples."


async def tx_serializer_model(dut, NB_DATA, collected, expected_count, timeout=50000):
    """
    Emulates tx_serializer handshake:
    - When o_valid=1 and i_tx_ready=1, capture the sample and pull i_tx_ready low
      for 1 + 2*NB_DATA cycles (start bit + data bits), then raise it again.
    """
    BUSY_CYCLES = 1 + 2 * NB_DATA
    dut.i_tx_ready.value = 1

    cycles = 0
    while len(collected) < expected_count and cycles < timeout:
        await RisingEdge(dut.i_clk)
        cycles += 1
        if dut.o_valid.value == 1 and dut.i_tx_ready.value == 1:
            re = int_to_float(dut.o_data_re.value.to_signed(), 3)
            im = int_to_float(dut.o_data_im.value.to_signed(), 3)
            collected.append(complex(re, im))
            dut.i_tx_ready.value = 0
            for _ in range(BUSY_CYCLES):
                await RisingEdge(dut.i_clk)
            dut.i_tx_ready.value = 1

    assert len(collected) == expected_count, \
        f"Buffer capture timeout: got {len(collected)} of {expected_count} samples."


# =====================================================
# Reorder helper
# =====================================================

MDC_MAP = [0, 8, 1, 9, 2, 10, 3, 11,
           4, 12, 5, 13, 6, 14, 7, 15]

def reorder(seq, n, mapping):
    out = [0j] * n
    for i, v in enumerate(seq):
        out[mapping[i]] = v
    return out


# =====================================================
# Test
# =====================================================

@cocotb.test()
async def test_fft16_stage1(dut):

    NB_DATA    = 8
    NBF_DATA   = 6
    N          = 16
    NBF_STAGE1 = 6
    NBF_STAGE2 = 3

    fft_model = FFT16(
        N=N,
        fxp=1,
        NB_INPUT=NB_DATA,
        NBF_INPUT=NBF_DATA,
        fft_mode=1
    )

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

    input_float = 2 * np.random.uniform(-1, 1, N) + \
                  2j * np.random.uniform(-1, 1, N)

    input_q = [
        fft_model.round.crnd(x, True, NB_DATA, NBF_DATA, 'around')
        for x in input_float
    ]

    expected_fft4rdx4, expected_fft4rdx2, expected_out = \
        fft_model.process(input_q)

    # =====================================================
    # Launch all capture coroutines BEFORE injecting inputs.
    # This is the key fix: the pipeline produces output
    # concurrently with injection, so captures must be live
    # from the very first clock cycle.
    # =====================================================

    rtl_stage1   = []
    rtl_mdc      = []
    rtl_stage2   = []
    collected_buffer = []

    task_stage1 = cocotb.start_soon(
        capture_stage1(dut, N, NBF_STAGE1, rtl_stage1))

    task_mdc = cocotb.start_soon(
        capture_mdc(dut, N, NBF_STAGE1, NBF_STAGE2, rtl_mdc, rtl_stage2))

    task_buffer = cocotb.start_soon(
        tx_serializer_model(dut, NB_DATA, collected_buffer, N))

    # =====================================================
    # Gapped injection: 1 valid cycle, 15 idle cycles
    # =====================================================

    for i in range(N):
        dut.i_valid.value   = 1
        dut.i_data_re.value = float_to_int(input_q[i].real, NBF_DATA)
        dut.i_data_im.value = float_to_int(input_q[i].imag, NBF_DATA)
        await RisingEdge(dut.i_clk)

        dut.i_valid.value = 0
        if i < N - 1:
            for _ in range(15):
                await RisingEdge(dut.i_clk)

    # =====================================================
    # Wait for all captures to finish (they assert internally
    # if they timeout, so just awaiting is enough)
    # =====================================================

    await task_stage1
    await task_mdc
    await task_buffer

    # =====================================================
    # Reordering
    # =====================================================

    rtl_stage1_ord = reorder(rtl_stage1,   N, MDC_MAP)   # stage1 ordering matches MDC map
    rtl_mdc_ord    = reorder(rtl_mdc,      N, MDC_MAP)
    rtl_output_ord = reorder(rtl_stage2,   N, MDC_MAP)
    buffer_ord     = reorder(collected_buffer, N, MDC_MAP)

    # =====================================================
    # Comparisons
    # =====================================================

    tol = 1e-9

    # --- Stage 1 ---
    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info("STAGE 1 RESULTS (FFT4 Radix-4)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<28} | {'Python':<28} | {'Δ':<15}")
    cocotb.log.info("-" * 80)

    for idx in range(N):
        rtl_val = rtl_stage1[idx]          # raw order, no reorder needed for stage1
        py_val  = expected_fft4rdx4[idx]
        diff_re = abs(rtl_val.real - py_val.real)
        diff_im = abs(rtl_val.imag - py_val.imag)
        cocotb.log.info(
            f"{idx:<5} | {rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )
        assert diff_re < tol and diff_im < tol, \
            f"Stage 1 mismatch at index {idx}: RTL={rtl_val} vs Py={py_val}"

    cocotb.log.info("Stage 1 PASSED.")

    # --- MDC Stage ---
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
            f"{idx:<5} | {rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )
        assert diff_re < tol and diff_im < tol, \
            f"MDC stage mismatch at index {idx}: RTL={rtl_val} vs Py={py_val}"

    cocotb.log.info("MDC Stage PASSED.")

    # --- Final Output ---
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
            f"{idx:<5} | {rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )
        assert diff_re < tol and diff_im < tol, \
            f"Final output mismatch at index {idx}: RTL={rtl_val} vs Py={py_val}"

    cocotb.log.info("Final Output PASSED.")

    # --- Buffer Output ---
    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info("BUFFER OUTPUT RESULTS")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'Buffer':<28} | {'Python':<28} | {'Δ':<15}")
    cocotb.log.info("-" * 80)

    for idx in range(N):
        rtl_val = buffer_ord[idx]
        py_val  = expected_out[idx]
        diff_re = abs(rtl_val.real - py_val.real)
        diff_im = abs(rtl_val.imag - py_val.imag)
        cocotb.log.info(
            f"{idx:<5} | {rtl_val.real:+.5f} {rtl_val.imag:+.5f}j | "
            f"{py_val.real:+.5f} {py_val.imag:+.5f}j | "
            f"{diff_re:.2e} / {diff_im:.2e}"
        )
        assert diff_re < tol and diff_im < tol, \
            f"Buffer output mismatch at index {idx}: RTL={rtl_val} vs Py={py_val}"

    cocotb.log.info("Buffer Output PASSED.")
    cocotb.log.info("=" * 80)