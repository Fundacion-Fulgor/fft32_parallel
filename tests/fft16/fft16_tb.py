import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from fft16 import FFT16

# =====================================================
# Helpers
# =====================================================


def float_to_int(val, frac_bits):
    return int(round(val * (2**frac_bits)))


def int_to_float(val, frac_bits):
    return val / (2**frac_bits)


# =====================================================
# DUT reset
# =====================================================


async def full_reset(dut, inverse_val):
    """Assert reset for 8 cycles to flush all pipeline state."""
    dut.i_clk_en.value = 0
    dut.i_rst_n.value = 0
    dut.i_inverse.value = inverse_val
    dut.i_valid.value = 0
    dut.i_tx_ready.value = 1
    dut.i_data_re.value = 0
    dut.i_data_im.value = 0
    for _ in range(8):
        await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)
    dut.i_clk_en.value = 1
    await RisingEdge(dut.i_clk)


# =====================================================
# Capture coroutines
# =====================================================


async def capture_stage1(dut, N, NBF_STAGE1, results, timeout=5000):
    cycles = 0
    while len(results) < N and cycles < timeout:
        await RisingEdge(dut.i_clk)
        cycles += 1
        if dut.fft4_valid.value == 1:
            re_ports = [
                dut.fft4_data0_re,
                dut.fft4_data1_re,
                dut.fft4_data2_re,
                dut.fft4_data3_re,
            ]
            im_ports = [
                dut.fft4_data0_im,
                dut.fft4_data1_im,
                dut.fft4_data2_im,
                dut.fft4_data3_im,
            ]
            for p_re, p_im in zip(re_ports, im_ports):
                results.append(
                    complex(
                        int_to_float(p_re.value.to_signed(), NBF_STAGE1),
                        int_to_float(p_im.value.to_signed(), NBF_STAGE1),
                    )
                )
    assert len(results) == N, f"Stage 1 capture timeout: got {len(results)} of {N}."


async def capture_mdc(
    dut, N, NBF_STAGE1, NBF_STAGE2, mdc_results, stage2_results, inverse, timeout=5000
):
    """
    Captures both the raw MDC butterfly output and the final clip_round output.
    For FFT  (inverse=0) reads rnd_mdc*  (NBF_OUT = NB_DATA-5 = 3).
    For IFFT (inverse=1) reads rnd_ifft* (NBF_OUT = NB_DATA-2 = 6).
    """
    cycles = 0
    while len(mdc_results) < N and cycles < timeout:
        await RisingEdge(dut.i_clk)
        cycles += 1
        if dut.mdc_ffx_valid.value == 1:
            re_mdc = [
                dut.mdc_ff0_data0_re,
                dut.mdc_ff0_data1_re,
                dut.mdc_ff1_data0_re,
                dut.mdc_ff1_data1_re,
                dut.mdc_ff2_data0_re,
                dut.mdc_ff2_data1_re,
                dut.mdc_ff3_data0_re,
                dut.mdc_ff3_data1_re,
            ]
            im_mdc = [
                dut.mdc_ff0_data0_im,
                dut.mdc_ff0_data1_im,
                dut.mdc_ff1_data0_im,
                dut.mdc_ff1_data1_im,
                dut.mdc_ff2_data0_im,
                dut.mdc_ff2_data1_im,
                dut.mdc_ff3_data0_im,
                dut.mdc_ff3_data1_im,
            ]
            if inverse == 0:
                re_out = [
                    dut.rnd_mdc0_d0_re,
                    dut.rnd_mdc0_d1_re,
                    dut.rnd_mdc1_d0_re,
                    dut.rnd_mdc1_d1_re,
                    dut.rnd_mdc2_d0_re,
                    dut.rnd_mdc2_d1_re,
                    dut.rnd_mdc3_d0_re,
                    dut.rnd_mdc3_d1_re,
                ]
                im_out = [
                    dut.rnd_mdc0_d0_im,
                    dut.rnd_mdc0_d1_im,
                    dut.rnd_mdc1_d0_im,
                    dut.rnd_mdc1_d1_im,
                    dut.rnd_mdc2_d0_im,
                    dut.rnd_mdc2_d1_im,
                    dut.rnd_mdc3_d0_im,
                    dut.rnd_mdc3_d1_im,
                ]
            else:
                re_out = [
                    dut.rnd_ifft0_d0_re,
                    dut.rnd_ifft0_d1_re,
                    dut.rnd_ifft1_d0_re,
                    dut.rnd_ifft1_d1_re,
                    dut.rnd_ifft2_d0_re,
                    dut.rnd_ifft2_d1_re,
                    dut.rnd_ifft3_d0_re,
                    dut.rnd_ifft3_d1_re,
                ]
                im_out = [
                    dut.rnd_ifft0_d0_im,
                    dut.rnd_ifft0_d1_im,
                    dut.rnd_ifft1_d0_im,
                    dut.rnd_ifft1_d1_im,
                    dut.rnd_ifft2_d0_im,
                    dut.rnd_ifft2_d1_im,
                    dut.rnd_ifft3_d0_im,
                    dut.rnd_ifft3_d1_im,
                ]
            for i in range(8):
                mdc_results.append(
                    complex(
                        int_to_float(re_mdc[i].value.to_signed(), NBF_STAGE1),
                        int_to_float(im_mdc[i].value.to_signed(), NBF_STAGE1),
                    )
                )
                stage2_results.append(
                    complex(
                        int_to_float(re_out[i].value.to_signed(), NBF_STAGE2),
                        int_to_float(im_out[i].value.to_signed(), NBF_STAGE2),
                    )
                )
    assert len(mdc_results) == N, f"MDC capture timeout: got {len(mdc_results)} of {N}."


async def tx_serializer_model(
    dut, NB_DATA, collected, expected_count, timeout=50000, nbf=3
):
    BUSY_CYCLES = 1 + 2 * NB_DATA
    dut.i_tx_ready.value = 1
    cycles = 0
    while len(collected) < expected_count and cycles < timeout:
        await RisingEdge(dut.i_clk)
        cycles += 1
        if dut.o_valid.value == 1 and dut.i_tx_ready.value == 1:
            re = int_to_float(dut.o_data_re.value.to_signed(), nbf)
            im = int_to_float(dut.o_data_im.value.to_signed(), nbf)
            collected.append(complex(re, im))
            dut.i_tx_ready.value = 0
            for _ in range(BUSY_CYCLES):
                await RisingEdge(dut.i_clk)
            dut.i_tx_ready.value = 1
    assert len(collected) == expected_count, (
        f"Buffer capture timeout: got {len(collected)} of {expected_count}."
    )


# =====================================================
# Reorder helper
# =====================================================

MDC_MAP = [0, 8, 1, 9, 2, 10, 3, 11, 4, 12, 5, 13, 6, 14, 7, 15]


def reorder(seq, n, mapping):
    out = [0j] * n
    for i, v in enumerate(seq):
        out[mapping[i]] = v
    return out


# =====================================================
# Core test logic (shared by both tests)
# =====================================================


async def run_fft_test(dut, inverse):
    """
    Runs a full stage-by-stage test in either FFT or IFFT mode.
      inverse=0 -> FFT:  input Q(8,6), output Q(8,3)
      inverse=1 -> IFFT: input Q(8,3), output Q(8,6)
    """
    NB_DATA = 8
    N = 16

    if inverse == 0:
        NBF_DATA = 6
        NBF_STAGE1 = 6
        NBF_STAGE2 = 3
        fft_mode = 1
        mode_str = "FFT"
    else:
        NBF_DATA = 3
        NBF_STAGE1 = 3
        NBF_STAGE2 = 6
        fft_mode = 0
        mode_str = "IFFT"

    fft_model = FFT16(
        N=N, fxp=1, NB_INPUT=NB_DATA, NBF_INPUT=NBF_DATA, fft_mode=fft_mode
    )

    # Reset DUT cleanly before each test
    await full_reset(dut, inverse)

    cocotb.log.info("=" * 80)
    cocotb.log.info(f"Starting FFT16 {mode_str} Stage-by-Stage Verification")
    cocotb.log.info("=" * 80)

    # Build quantised input vector
    input_float = 2 * np.random.uniform(-1, 1, N) + 2j * np.random.uniform(-1, 1, N)
    input_q = [
        fft_model.round.crnd(x, True, NB_DATA, NBF_DATA, "around") for x in input_float
    ]
    expected_fft4rdx4, expected_fft4rdx2, expected_out = fft_model.process(input_q)

    # Launch captures BEFORE injection
    rtl_stage1 = []
    rtl_mdc = []
    rtl_stage2 = []
    collected_buffer = []

    task_stage1 = cocotb.start_soon(capture_stage1(dut, N, NBF_STAGE1, rtl_stage1))

    task_mdc = cocotb.start_soon(
        capture_mdc(dut, N, NBF_STAGE1, NBF_STAGE2, rtl_mdc, rtl_stage2, inverse)
    )

    task_buffer = cocotb.start_soon(
        tx_serializer_model(dut, NB_DATA, collected_buffer, N, nbf=NBF_STAGE2)
    )

    # Gapped injection: 1 valid + 15 idle per sample
    for i in range(N):
        dut.i_valid.value = 1
        dut.i_data_re.value = float_to_int(input_q[i].real, NBF_DATA)
        dut.i_data_im.value = float_to_int(input_q[i].imag, NBF_DATA)
        await RisingEdge(dut.i_clk)
        dut.i_valid.value = 0
        if i < N - 1:
            for _ in range(15):
                await RisingEdge(dut.i_clk)

    await task_stage1
    await task_mdc
    await task_buffer

    # Reorder
    rtl_mdc_ord = reorder(rtl_mdc, N, MDC_MAP)
    rtl_output_ord = reorder(rtl_stage2, N, MDC_MAP)
    buffer_ord = reorder(collected_buffer, N, MDC_MAP)

    tol = 1e-9

    # --- Stage 1 ---
    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info(f"{mode_str} STAGE 1 (Radix-4 Butterfly)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<32} | {'Python':<32} | Δre / Δim")
    cocotb.log.info("-" * 80)
    for idx in range(N):
        rv = rtl_stage1[idx]
        pv = expected_fft4rdx4[idx]
        dre, dim = abs(rv.real - pv.real), abs(rv.imag - pv.imag)
        cocotb.log.info(
            f"{idx:<5} | {rv.real:+.6f} {rv.imag:+.6f}j | "
            f"{pv.real:+.6f} {pv.imag:+.6f}j | {dre:.2e} / {dim:.2e}"
        )
        assert dre < tol and dim < tol, (
            f"[Stage1] mismatch idx={idx}: RTL={rv}  Py={pv}"
        )
    cocotb.log.info("Stage 1 PASSED.")

    # --- MDC Stage ---
    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info(f"{mode_str} MDC STAGE (Radix-2 pre-clip)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<32} | {'Python':<32} | Δre / Δim")
    cocotb.log.info("-" * 80)
    for idx in range(N):
        rv = rtl_mdc_ord[idx]
        pv = expected_fft4rdx2[idx]
        dre, dim = abs(rv.real - pv.real), abs(rv.imag - pv.imag)
        cocotb.log.info(
            f"{idx:<5} | {rv.real:+.6f} {rv.imag:+.6f}j | "
            f"{pv.real:+.6f} {pv.imag:+.6f}j | {dre:.2e} / {dim:.2e}"
        )
        assert dre < tol and dim < tol, f"[MDC] mismatch idx={idx}: RTL={rv}  Py={pv}"
    cocotb.log.info("MDC Stage PASSED.")

    # --- Final Output (clip_round) ---
    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info(
        f"{mode_str} FINAL OUTPUT (clip_round, {'rnd_mdc*' if inverse == 0 else 'rnd_ifft*'})"
    )
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'RTL':<32} | {'Python':<32} | Δre / Δim")
    cocotb.log.info("-" * 80)
    for idx in range(N):
        rv = rtl_output_ord[idx]
        pv = expected_out[idx]
        dre, dim = abs(rv.real - pv.real), abs(rv.imag - pv.imag)
        cocotb.log.info(
            f"{idx:<5} | {rv.real:+.6f} {rv.imag:+.6f}j | "
            f"{pv.real:+.6f} {pv.imag:+.6f}j | {dre:.2e} / {dim:.2e}"
        )
        assert dre < tol and dim < tol, f"[Final] mismatch idx={idx}: RTL={rv}  Py={pv}"
    cocotb.log.info("Final Output PASSED.")

    # --- Buffer Output (tx_serializer) ---
    cocotb.log.info("\n" + "=" * 80)
    cocotb.log.info(f"{mode_str} BUFFER OUTPUT (tx_serializer)")
    cocotb.log.info("=" * 80)
    cocotb.log.info(f"{'Idx':<5} | {'Buffer':<32} | {'Python':<32} | Δre / Δim")
    cocotb.log.info("-" * 80)
    for idx in range(N):
        rv = buffer_ord[idx]
        pv = expected_out[idx]
        dre, dim = abs(rv.real - pv.real), abs(rv.imag - pv.imag)
        cocotb.log.info(
            f"{idx:<5} | {rv.real:+.6f} {rv.imag:+.6f}j | "
            f"{pv.real:+.6f} {pv.imag:+.6f}j | {dre:.2e} / {dim:.2e}"
        )
        assert dre < tol and dim < tol, (
            f"[Buffer] mismatch idx={idx}: RTL={rv}  Py={pv}"
        )
    cocotb.log.info("Buffer Output PASSED.")
    cocotb.log.info(f"{'=' * 80}")
    cocotb.log.info(f"ALL {mode_str} STAGES PASSED.")
    cocotb.log.info(f"{'=' * 80}")


# =====================================================
# Individual test entries
# =====================================================


@cocotb.test()
async def test_fft16_fft(dut):
    """Forward FFT: input Q(8,6), output Q(8,3), i_inverse=0."""
    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await run_fft_test(dut, inverse=0)


@cocotb.test()
async def test_fft16_ifft(dut):
    """Inverse FFT: input Q(8,3), output Q(8,6), i_inverse=1.
    The /N=16 normalisation is encoded in clip_round via NBF_INP=7 (=NBF_MDC+4).
    No explicit >>>4 shift is needed or correct in the RTL."""
    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await run_fft_test(dut, inverse=1)
