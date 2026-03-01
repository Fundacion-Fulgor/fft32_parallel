import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_signed(val, bits):
    if val >= (1 << (bits - 1)):
        val -= (1 << bits)
    return val


async def reset_dut(dut):
    dut.i_rst_n.value    = 0
    dut.i_clk_en.value   = 0
    dut.i_valid.value    = 0
    dut.i_tx_ready.value = 0
    for k in range(8):
        getattr(dut, f"i_data{k}_re").value = 0
        getattr(dut, f"i_data{k}_im").value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)
    dut.i_rst_n.value  = 1
    dut.i_clk_en.value = 1
    await RisingEdge(dut.i_clk)


async def feed_batch(dut, batch):
    """Drive one valid pulse with 8 complex samples."""
    for k in range(8):
        getattr(dut, f"i_data{k}_re").value = batch[k][0] & 0xFF
        getattr(dut, f"i_data{k}_im").value = batch[k][1] & 0xFF
    dut.i_valid.value = 1
    await RisingEdge(dut.i_clk)
    dut.i_valid.value = 0


async def collect_outputs(dut, n_samples, busy_cycles, timeout=2000):
    """
    Collect n_samples from the serial output.

    Protocol per sample:
      1. Assert i_tx_ready=1 and hold it until o_valid goes high.
      2. Capture o_data_re / o_data_im on the cycle o_valid is seen.
      3. Deassert i_tx_ready=0 for busy_cycles (simulates receiver busy).

    Returns list of (re, im) signed tuples.
    """
    NB_DATA = 8
    results = []
    cycles  = 0

    while len(results) < n_samples and cycles < timeout:

        # --- Phase 1: hold ready until o_valid ---
        dut.i_tx_ready.value = 1
        while cycles < timeout:
            await RisingEdge(dut.i_clk)
            cycles += 1
            if dut.o_valid.value == 1:
                re = to_signed(int(dut.o_data_re.value), NB_DATA)
                im = to_signed(int(dut.o_data_im.value), NB_DATA)
                results.append((re, im))
                break

        # --- Phase 2: deassert ready for busy_cycles ---
        dut.i_tx_ready.value = 0
        for _ in range(busy_cycles):
            await RisingEdge(dut.i_clk)
            cycles += 1

    dut.i_tx_ready.value = 0
    return results


# ---------------------------------------------------------------------------
# Test 1: Basic ordering — fast handshake (busy = 1 cycle)
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_basic_ordering(dut):
    """
    Feed 2 batches of 8, collect 16 outputs with fast handshake (busy=1).
    Verify flat ordering: batch0[0..7] followed by batch1[0..7].
    """
    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    batch0   = [(i,     -i    ) for i in range(8)]
    batch1   = [(i + 8, -(i+8)) for i in range(8)]
    expected = batch0 + batch1

    cocotb.log.info("--- test_basic_ordering ---")

    await feed_batch(dut, batch0)
    await feed_batch(dut, batch1)

    results = await collect_outputs(dut, 16, busy_cycles=1)

    assert len(results) == 16, f"Expected 16 samples, got {len(results)}"
    for idx, (got, exp) in enumerate(zip(results, expected)):
        assert got == exp, f"Mismatch at index {idx}: got {got}, expected {exp}"
        cocotb.log.info(f"[{idx:2d}] re={got[0]:+4d} im={got[1]:+4d}  OK")

    cocotb.log.info("test_basic_ordering PASSED.")


# ---------------------------------------------------------------------------
# Test 2: Backpressure — slow receiver (busy = 5 cycles)
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_backpressure(dut):
    """
    Same data but receiver stays busy for 5 cycles after each item.
    Verifies FSM waits in S_WAIT_BSY without dropping data.
    """
    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    batch0   = [(i * 3,      i * 2     ) for i in range(8)]
    batch1   = [(i * 3 + 24, i * 2 + 16) for i in range(8)]
    expected = batch0 + batch1

    cocotb.log.info("--- test_backpressure ---")

    await feed_batch(dut, batch0)
    await feed_batch(dut, batch1)

    results = await collect_outputs(dut, 16, busy_cycles=5)

    assert len(results) == 16, f"Expected 16 samples, got {len(results)}"
    for idx, (got, exp) in enumerate(zip(results, expected)):
        assert got == exp, f"Mismatch at index {idx}: got {got}, expected {exp}"
        cocotb.log.info(f"[{idx:2d}] re={got[0]:+4d} im={got[1]:+4d}  OK")

    cocotb.log.info("test_backpressure PASSED.")


# ---------------------------------------------------------------------------
# Test 3: Delayed ready — receiver not ready when loading finishes
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_delayed_ready(dut):
    """
    Feed both batches, wait 20 cycles before starting collection.
    Verifies S_WAIT_RDY holds correctly with no data loss.
    """
    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    batch0   = [( 10 + i,  -(10 + i)) for i in range(8)]
    batch1   = [(-10 - i,   (10 + i)) for i in range(8)]
    expected = batch0 + batch1

    cocotb.log.info("--- test_delayed_ready ---")

    await feed_batch(dut, batch0)
    await feed_batch(dut, batch1)

    # Simulate receiver not ready yet
    dut.i_tx_ready.value = 0
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    results = await collect_outputs(dut, 16, busy_cycles=2)

    assert len(results) == 16, f"Expected 16 samples, got {len(results)}"
    for idx, (got, exp) in enumerate(zip(results, expected)):
        assert got == exp, f"Mismatch at index {got}, expected {exp}"
        cocotb.log.info(f"[{idx:2d}] re={got[0]:+4d} im={got[1]:+4d}  OK")

    cocotb.log.info("test_delayed_ready PASSED.")


# ---------------------------------------------------------------------------
# Test 4: Random data, random backpressure
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_random(dut):
    """
    Random signed 8-bit values, random busy duration (1..8 cycles).
    Verifies ordering is preserved end-to-end.
    """
    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)

    NB_DATA = 8
    MIN_VAL = -(1 << (NB_DATA - 1))
    MAX_VAL =  (1 << (NB_DATA - 1)) - 1

    random.seed(42)

    batch0   = [(random.randint(MIN_VAL, MAX_VAL),
                 random.randint(MIN_VAL, MAX_VAL)) for _ in range(8)]
    batch1   = [(random.randint(MIN_VAL, MAX_VAL),
                 random.randint(MIN_VAL, MAX_VAL)) for _ in range(8)]
    expected = batch0 + batch1

    cocotb.log.info("--- test_random ---")

    await feed_batch(dut, batch0)
    await feed_batch(dut, batch1)

    busy     = random.randint(1, 8)
    results  = await collect_outputs(dut, 16, busy_cycles=busy)

    assert len(results) == 16, f"Expected 16 samples, got {len(results)}"
    for idx, (got, exp) in enumerate(zip(results, expected)):
        assert got == exp, f"Mismatch at index {idx}: got {got}, expected {exp}"
        cocotb.log.info(f"[{idx:2d}] re={got[0]:+4d} im={got[1]:+4d}  OK")

    cocotb.log.info("test_random PASSED.")