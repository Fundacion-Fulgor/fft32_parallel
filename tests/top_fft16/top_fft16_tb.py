import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import numpy as np

CLK_NS      = 20
SPI_HALF_NS = 50
NB_DATA     = 8
N           = 16
TIMEOUT     = 2000

SPI_RW_WRITE = 0
SPI_RW_READ  = 1

ADDR_STATUS_FLAGS = 0x00
ADDR_ERROR_FLAGS  = 0x01
ADDR_CNT_INPUTS   = 0x02
ADDR_CNT_OUTPUTS  = 0x03
ADDR_LAST_OUT_RE  = 0x04
ADDR_LAST_OUT_IM  = 0x05
ADDR_MID_DATA_RE  = 0x06
ADDR_SYS_CONFIG   = 0x10

CFG_DISABLE = 0b000
CFG_ENABLE  = 0b001
CFG_SRESET  = 0b100

# Cycles to wait after enabling clk_en before injecting real data.
# This drains any residual valid signals left in shift_r4 / shift_r2
# that survive hardware reset because those modules have no reset port.
PIPELINE_DRAIN_CYCLES = 64


def to_signed_8(val):
    val = val & 0xFF
    return val - 256 if val > 127 else val


# ─────────────────────────────────────────────────────────────────
# Infrastructure helpers
# ─────────────────────────────────────────────────────────────────

async def reset_dut(dut):
    """
    Hardware reset only.  Does NOT touch SPI config — leaves sys_config = 0
    (fft_enable = 0, soft_reset = 0) after rst_n rises.
    """
    dut.i_rst_n.value    = 0
    dut.i_data.value     = 0
    dut.i_spi_ss_n.value = 1
    dut.i_spi_sclk.value = 0
    dut.i_spi_mosi.value = 0
    for _ in range(4):
        await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)


async def full_reset(dut):
    """
    Hardware reset followed by a SPI soft-reset pulse, then FFT disabled.
    Leaves the DUT in a clean, disabled state ready for each test.
    Call this at the top of every test.
    """
    await reset_dut(dut)
    # SPI soft-reset: drives rst_n low inside the chip for a few cycles
    await spi_write(dut, ADDR_SYS_CONFIG, CFG_SRESET)
    for _ in range(8):
        await RisingEdge(dut.i_clk)
    await spi_write(dut, ADDR_SYS_CONFIG, CFG_DISABLE)
    for _ in range(4):
        await RisingEdge(dut.i_clk)


async def enable_fft_and_drain(dut):
    """
    Enable the FFT clock gate and wait PIPELINE_DRAIN_CYCLES before injecting
    real data.  This is the fix for the stale-state bug:
    fft16_shift_r4 and fft16_shift_r2 have no reset port — they are only gated
    by i_clk_en.  During reset (clk_en = 0) they retain stale values from the
    previous test.  Once clk_en rises, any residual valid pulses drain through
    the pipeline in at most a few dozen cycles.  Waiting here ensures they
    complete before we start capturing.
    """
    await spi_write(dut, ADDR_SYS_CONFIG, CFG_ENABLE)
    for _ in range(PIPELINE_DRAIN_CYCLES):
        await RisingEdge(dut.i_clk)


async def soft_reset_between_blocks(dut):
    """
    fft4_radix4 internal state machine does not auto-reload for a second block
    without a reset.  Use this between consecutive blocks when the test needs
    to process more than one batch.
    """
    await spi_write(dut, ADDR_SYS_CONFIG, CFG_SRESET)
    for _ in range(8):
        await RisingEdge(dut.i_clk)
    await spi_write(dut, ADDR_SYS_CONFIG, CFG_ENABLE)
    for _ in range(PIPELINE_DRAIN_CYCLES):
        await RisingEdge(dut.i_clk)


async def spi_transfer(dut, rw, addr, wdata=0x00):
    frame = ((rw & 1) << 15) | ((addr & 0x7F) << 8) | (wdata & 0xFF)
    dut.i_spi_ss_n.value = 0
    dut.i_spi_sclk.value = 0
    dut.i_spi_mosi.value = 0
    await Timer(SPI_HALF_NS, unit="ns")
    miso_byte = 0
    for i in range(16):
        dut.i_spi_mosi.value = (frame >> (15 - i)) & 1
        await Timer(SPI_HALF_NS, unit="ns")
        dut.i_spi_sclk.value = 1
        await Timer(SPI_HALF_NS, unit="ns")
        dut.i_spi_sclk.value = 0
        await Timer(SPI_HALF_NS, unit="ns")
        if 7 <= i <= 14:
            miso_byte = (miso_byte << 1) | int(dut.o_spi_miso.value)
    dut.i_spi_ss_n.value = 1
    await Timer(SPI_HALF_NS, unit="ns")
    for _ in range(8):
        await RisingEdge(dut.i_clk)
    return miso_byte


async def spi_write(dut, addr, data):
    await spi_transfer(dut, SPI_RW_WRITE, addr, data)


async def spi_read(dut, addr):
    return await spi_transfer(dut, SPI_RW_READ, addr)


async def drive_stream(dut, pairs):
    """
    Sends a full batch of N samples to the rx_serializer.
    One idle cycle + start bit, then all N*16 bits continuously.
    """
    dut.i_data.value = 0
    await RisingEdge(dut.i_clk)
    dut.i_data.value = 1
    await RisingEdge(dut.i_clk)
    for re_val, im_val in pairs:
        word = ((re_val & 0xFF) << 8) | (im_val & 0xFF)
        for i in range(16):
            dut.i_data.value = (word >> (15 - i)) & 1
            await RisingEdge(dut.i_clk)
    dut.i_data.value = 0


async def capture_block(dut, n_samples):
    """
    Captures n_samples from the tx_serializer serial output.
    First sample: wait for start bit (first HIGH), then capture 16 bits.
    Subsequent samples: 2 extra awaits for the TX pipeline gap.
    """
    results = []
    for idx in range(n_samples):
        if idx == 0:
            cycles = 0
            while cycles < TIMEOUT:
                await RisingEdge(dut.i_clk)
                cycles += 1
                if int(dut.o_data.value) == 1:
                    break
            else:
                assert False, "Timeout: start bit never detected on o_data"
        else:
            await RisingEdge(dut.i_clk)
            await RisingEdge(dut.i_clk)

        word = 0
        for _ in range(16):
            await RisingEdge(dut.i_clk)
            word = (word << 1) | int(dut.o_data.value)

        results.append((to_signed_8(word >> 8), to_signed_8(word & 0xFF)))

    return results


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_fft_disabled_no_output(dut):
    """
    After reset sys_config=0b000 so fft_enable=0.
    rx_serializer still receives and cnt_inputs counts.
    fft16 with i_clk_en=0 does not process: o_data stays 0, cnt_outputs=0.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await full_reset(dut)
    cocotb.log.info("--- test_fft_disabled_no_output ---")

    samples = [(i * 3, i * 2) for i in range(N)]
    await drive_stream(dut, samples)

    for _ in range(200):
        await RisingEdge(dut.i_clk)
        assert int(dut.o_data.value) == 0, \
            "o_data must remain 0 when FFT is disabled"

    cocotb.log.info("  o_data stayed 0 with FFT disabled  OK")

    for _ in range(10):
        await RisingEdge(dut.i_clk)

    cnt_in  = await spi_read(dut, ADDR_CNT_INPUTS)
    cnt_out = await spi_read(dut, ADDR_CNT_OUTPUTS)
    assert cnt_in == N,  f"cnt_inputs: expected {N}, got {cnt_in}"
    assert cnt_out == 0, f"cnt_outputs: expected 0, got {cnt_out}"
    cocotb.log.info(f"  cnt_inputs={cnt_in}  cnt_outputs={cnt_out}  OK")
    cocotb.log.info("test_fft_disabled_no_output PASSED.")


@cocotb.test()
async def test_enable_counters_and_status(dut):
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await full_reset(dut)
    cocotb.log.info("--- test_enable_counters_and_status ---")

    await enable_fft_and_drain(dut)
    cocotb.log.info("  FFT enabled via SPI  OK")

    samples   = [(10 * (i % 4 + 1), -5 * (i % 4 + 1)) for i in range(N)]
    send_task = cocotb.start_soon(drive_stream(dut, samples))
    received  = await capture_block(dut, N)
    await send_task

    cocotb.log.info(f"  Captured {len(received)} output samples")

    non_zero = [(re, im) for re, im in received if re != 0 or im != 0]
    assert len(non_zero) > 0, \
        "All output samples are (0,0) — FFT output not reaching serial output"
    cocotb.log.info(f"  {len(non_zero)}/{N} non-zero output samples  OK")

    for _ in range(20):
        await RisingEdge(dut.i_clk)

    cnt_in  = await spi_read(dut, ADDR_CNT_INPUTS)
    cnt_out = await spi_read(dut, ADDR_CNT_OUTPUTS)
    assert cnt_in == N,  f"cnt_inputs: expected {N}, got {cnt_in}"
    assert cnt_out == N, f"cnt_outputs: expected {N}, got {cnt_out}"
    cocotb.log.info(f"  cnt_inputs={cnt_in}  cnt_outputs={cnt_out}  OK")

    status = await spi_read(dut, ADDR_STATUS_FLAGS)
    assert (status >> 2) & 1 == 1, \
        f"tx_ready should be 1 when idle, status=0x{status:02X}"
    assert (status >> 3) & 1 == 0, \
        f"fft_inverse should be 0, status=0x{status:02X}"
    cocotb.log.info(f"  status_flags=0x{status:02X}  OK")

    # last_out_re/im is registered when fft_out_valid pulses (combinational
    # with the FFT output, before tx_serializer).  received[-1] is the last
    # word to come out of the tx_serializer — same data, different path.
    # Compare to received[-1] only if the tx_serializer output order equals
    # the fft_out order (no re-buffering).
    last_re_raw = await spi_read(dut, ADDR_LAST_OUT_RE)
    last_im_raw = await spi_read(dut, ADDR_LAST_OUT_IM)
    last_re = to_signed_8(last_re_raw)
    last_im = to_signed_8(last_im_raw)
    exp_re, exp_im = received[-1]
    assert last_re == exp_re, f"last_out_re: expected {exp_re}, got {last_re}"
    assert last_im == exp_im, f"last_out_im: expected {exp_im}, got {last_im}"
    cocotb.log.info(f"  last_out: re={last_re} im={last_im}  OK")
    cocotb.log.info("test_enable_counters_and_status PASSED.")


@cocotb.test()
async def test_zero_input(dut):
    """FFT of all-zero input is all-zero. Verifies no clipping flagged."""
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    # full_reset + enable_fft_and_drain is the fix:
    # without the drain, residual valid signals from shift_r4/shift_r2
    # (which have no reset port) produce a spurious output block that
    # capture_block mistakes for the zero-input result.
    await full_reset(dut)
    cocotb.log.info("--- test_zero_input ---")

    await enable_fft_and_drain(dut)

    send_task = cocotb.start_soon(drive_stream(dut, [(0, 0)] * N))
    received  = await capture_block(dut, N)
    await send_task

    for i, (re, im) in enumerate(received):
        assert re == 0 and im == 0, \
            f"Sample {i}: expected (0,0), got ({re},{im})"
    cocotb.log.info(f"  All {N} output samples are (0,0)  OK")

    for _ in range(10):
        await RisingEdge(dut.i_clk)
    err = await spi_read(dut, ADDR_ERROR_FLAGS)
    assert (err & 0x01) == 0, \
        f"error_flags[0] should be 0 for zero input, got 0x{err:02X}"
    cocotb.log.info(f"  error_flags=0x{err:02X} (no clipping)  OK")
    cocotb.log.info("test_zero_input PASSED.")


@cocotb.test()
async def test_soft_reset(dut):
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await full_reset(dut)
    cocotb.log.info("--- test_soft_reset ---")

    await enable_fft_and_drain(dut)

    send_task = cocotb.start_soon(drive_stream(dut, [(i+1, -(i+1)) for i in range(N)]))
    await capture_block(dut, N)
    await send_task

    for _ in range(10):
        await RisingEdge(dut.i_clk)

    cnt_in  = await spi_read(dut, ADDR_CNT_INPUTS)
    cnt_out = await spi_read(dut, ADDR_CNT_OUTPUTS)
    assert cnt_in == N,  f"Pre-reset cnt_inputs: expected {N}, got {cnt_in}"
    assert cnt_out == N, f"Pre-reset cnt_outputs: expected {N}, got {cnt_out}"
    cocotb.log.info(f"  Pre-reset: cnt_inputs={cnt_in} cnt_outputs={cnt_out}  OK")

    await spi_write(dut, ADDR_SYS_CONFIG, CFG_SRESET)
    for _ in range(10):
        await RisingEdge(dut.i_clk)
    await spi_write(dut, ADDR_SYS_CONFIG, CFG_ENABLE)
    for _ in range(PIPELINE_DRAIN_CYCLES):
        await RisingEdge(dut.i_clk)

    cnt_in  = await spi_read(dut, ADDR_CNT_INPUTS)
    cnt_out = await spi_read(dut, ADDR_CNT_OUTPUTS)
    assert cnt_in == 0,  f"Post-reset cnt_inputs: expected 0, got {cnt_in}"
    assert cnt_out == 0, f"Post-reset cnt_outputs: expected 0, got {cnt_out}"
    cocotb.log.info(f"  Post-reset: cnt_inputs={cnt_in} cnt_outputs={cnt_out}  OK")

    send_task = cocotb.start_soon(drive_stream(dut, [(0, 0)] * N))
    received  = await capture_block(dut, N)
    await send_task
    assert len(received) == N, \
        f"Post-reset block: expected {N} samples, got {len(received)}"
    cocotb.log.info(f"  Post-reset block: {N} outputs received  OK")
    cocotb.log.info("test_soft_reset PASSED.")


@cocotb.test()
async def test_spi_last_out_tracking(dut):
    """
    Tracks last_out across two blocks.
    NOTE: fft4_radix4 does not auto-reload between blocks — it requires a
    soft reset.  soft_reset_between_blocks() handles this and also drains
    residual pipeline state before the second block is injected.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await full_reset(dut)
    cocotb.log.info("--- test_spi_last_out_tracking ---")

    await enable_fft_and_drain(dut)

    expected_cnt = 0

    for block_idx in range(2):
        samples = [
            ((block_idx + 1) * (i % 8 + 1), -(block_idx + 1) * (i % 8 + 1))
            for i in range(N)
        ]
        send_task = cocotb.start_soon(drive_stream(dut, samples))
        received  = await capture_block(dut, N)
        await send_task

        expected_cnt += N

        for _ in range(20):
            await RisingEdge(dut.i_clk)

        non_zero = [(re, im) for re, im in received if re != 0 or im != 0]
        assert len(non_zero) > 0, f"Block {block_idx}: all outputs are (0,0)"
        cocotb.log.info(f"  Block {block_idx}: {len(non_zero)}/{N} non-zero samples  OK")

        last_re_raw = await spi_read(dut, ADDR_LAST_OUT_RE)
        last_im_raw = await spi_read(dut, ADDR_LAST_OUT_IM)
        last_re = to_signed_8(last_re_raw)
        last_im = to_signed_8(last_im_raw)
        exp_re, exp_im = received[-1]
        assert last_re == exp_re, \
            f"Block {block_idx} last_out_re: expected {exp_re}, got {last_re}"
        assert last_im == exp_im, \
            f"Block {block_idx} last_out_im: expected {exp_im}, got {last_im}"
        cocotb.log.info(f"  Block {block_idx} last_out: re={last_re} im={last_im}  OK")

        # Soft reset between blocks: required because fft4_radix4 state machine
        # does not reload automatically after completing a block.
        if block_idx < 1:
            await soft_reset_between_blocks(dut)

    cnt_in  = await spi_read(dut, ADDR_CNT_INPUTS)
    cnt_out = await spi_read(dut, ADDR_CNT_OUTPUTS)
    # Counters reset during soft_reset_between_blocks, so only the last block
    # is reflected in the post-loop read.
    assert cnt_in  == N, f"cnt_inputs after last block: expected {N}, got {cnt_in}"
    assert cnt_out == N, f"cnt_outputs after last block: expected {N}, got {cnt_out}"
    cocotb.log.info(f"  Final counters: cnt_inputs={cnt_in} cnt_outputs={cnt_out}  OK")
    cocotb.log.info("test_spi_last_out_tracking PASSED.")


@cocotb.test()
async def test_dc_input_energy(dut):
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await full_reset(dut)
    cocotb.log.info("--- test_dc_input_energy ---")

    await enable_fft_and_drain(dut)

    A = 4
    send_task = cocotb.start_soon(drive_stream(dut, [(A, 0)] * N))
    received  = await capture_block(dut, N)
    await send_task

    non_zero = [(i, re, im) for i, (re, im) in enumerate(received)
                if re != 0 or im != 0]
    cocotb.log.info(f"  Non-zero outputs: {non_zero}")

    assert len(non_zero) == 1, \
        f"DC input should produce exactly 1 non-zero bin, got {len(non_zero)}: {non_zero}"

    bin0_phys, bin0_re, bin0_im = non_zero[0]
    cocotb.log.info(f"  Bin 0 at physical index {bin0_phys}: re={bin0_re} im={bin0_im}  OK")

    for _ in range(10):
        await RisingEdge(dut.i_clk)
    err = await spi_read(dut, ADDR_ERROR_FLAGS)
    assert (err & 0x01) == 0, \
        f"No clipping expected for DC A={A}, error_flags=0x{err:02X}"
    cocotb.log.info(f"  error_flags=0x{err:02X} (no clipping)  OK")
    cocotb.log.info("test_dc_input_energy PASSED.")


@cocotb.test()
async def test_fft_mathematical_roundtrip(dut):
    """
    Full end-to-end verification against the FFT16 Python model.
    Input:  Q(8,6), sent as int8 via serial.
    Output: Q(8,3), captured from serial and compared against model.
    MDC_MAP maps physical serial output index to frequency bin.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await full_reset(dut)
    cocotb.log.info("--- test_fft_mathematical_roundtrip ---")

    from fft16 import FFT16

    NBF_DATA = 6
    NBF_OUT  = 3
    TOL      = 1e-9

    MDC_MAP = [0, 8, 1, 9, 2, 10, 3, 11, 4, 12, 5, 13, 6, 14, 7, 15]

    fft_model = FFT16(N=N, fxp=1, NB_INPUT=NB_DATA, NBF_INPUT=NBF_DATA, fft_mode=1)

    np.random.seed(42)
    input_float = 2 * np.random.uniform(-1, 1, N) + \
                  2j * np.random.uniform(-1, 1, N)

    input_q = [
        fft_model.round.crnd(x, True, NB_DATA, NBF_DATA, 'around')
        for x in input_float
    ]

    _, _, expected_out = fft_model.process(input_q)

    def fxp_to_int8(c, nbf):
        re = max(-128, min(127, int(round(c.real * (2 ** nbf)))))
        im = max(-128, min(127, int(round(c.imag * (2 ** nbf)))))
        return re, im

    def int8_to_float(val, nbf):
        return val / (2 ** nbf)

    samples_int = [fxp_to_int8(x, NBF_DATA) for x in input_q]

    await enable_fft_and_drain(dut)

    send_task = cocotb.start_soon(drive_stream(dut, samples_int))
    received  = await capture_block(dut, N)
    await send_task

    cocotb.log.info(f"  Captured {len(received)} output samples")
    cocotb.log.info("\n" + "=" * 90)
    cocotb.log.info("FFT16 ROUNDTRIP RESULTS")
    cocotb.log.info("=" * 90)
    cocotb.log.info(
        f"{'Phys':<6} {'Bin':<5} | "
        f"{'RTL Re':>10} {'RTL Im':>10} | "
        f"{'Exp Re':>10} {'Exp Im':>10} | "
        f"{'Delta Re':>10} {'Delta Im':>10}"
    )
    cocotb.log.info("-" * 90)

    all_ok = True
    for phys_idx in range(N):
        bin_idx           = MDC_MAP[phys_idx]
        got_re_int, got_im_int = received[phys_idx]
        got_re = int8_to_float(got_re_int, NBF_OUT)
        got_im = int8_to_float(got_im_int, NBF_OUT)
        exp_re = float(expected_out[bin_idx].real)
        exp_im = float(expected_out[bin_idx].imag)
        diff_re = abs(got_re - exp_re)
        diff_im = abs(got_im - exp_im)
        match   = diff_re < TOL and diff_im < TOL
        if not match:
            all_ok = False
        cocotb.log.info(
            f"  [{phys_idx:<3}] bin={bin_idx:<3} | "
            f"{got_re:+.5f} {got_im:+.5f}j | "
            f"{exp_re:+.5f} {exp_im:+.5f}j | "
            f"{diff_re:.2e} {diff_im:.2e} "
            f"{'OK' if match else 'MISMATCH'}"
        )

    assert all_ok, "One or more output samples do not match the FFT16 model"
    cocotb.log.info("=" * 90)
    cocotb.log.info("test_fft_mathematical_roundtrip PASSED.")