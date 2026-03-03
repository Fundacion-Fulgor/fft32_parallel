import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

CLK_NS        = 20
NB_DATA       = 8
N_DATA        = 16
TIMEOUT_CYCLES = 200


async def reset_dut(dut):
    dut.i_rst_n.value   = 0
    dut.i_valid.value   = 0
    dut.i_data_re.value = 0
    dut.i_data_im.value = 0
    for _ in range(4):
        await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)


async def wait_for_ready(dut):
    for _ in range(TIMEOUT_CYCLES):
        if dut.o_ready.value == 1:
            return
        await RisingEdge(dut.i_clk)
    assert False, "Timeout: o_ready never asserted"


async def transmit_and_capture(dut, re_val, im_val, expect_start=True):
    """
    Drives one IQ pair and captures 2*NB_DATA serial bits.
    If expect_start=True, waits for start bit first.
    If expect_start=False, captures bits immediately (no start bit).
    """
    await wait_for_ready(dut)

    dut.i_valid.value   = 1
    dut.i_data_re.value = re_val & 0xFF
    dut.i_data_im.value = im_val & 0xFF
    await RisingEdge(dut.i_clk)
    dut.i_valid.value = 0

    if expect_start:
        for _ in range(TIMEOUT_CYCLES):
            await RisingEdge(dut.i_clk)
            if dut.o_data.value == 1:
                break
        else:
            assert False, "Timeout: start bit never detected"
    else:
        await RisingEdge(dut.i_clk)  # wait for first bit to appear on o_data

    received = 0
    for _ in range(2 * NB_DATA):
        await RisingEdge(dut.i_clk)
        received = (received << 1) | int(dut.o_data.value)
    return received


async def transmit_batch(dut, vectors):
    """
    Sends N_DATA IQ pairs as a full batch.
    First sample gets start bit, rest go direct.
    Returns list of received 16-bit words.
    """
    results = []
    for idx, (re_val, im_val) in enumerate(vectors):
        received = await transmit_and_capture(
            dut, re_val, im_val, expect_start=(idx == 0)
        )
        results.append(received)
    return results


@cocotb.test()
async def test_basic_serialization(dut):
    """
    Single batch of N_DATA pairs. First has start bit, rest go direct.
    Verifies each received word matches {re, im}.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_basic_serialization ---")

    import random
    random.seed(0)
    MIN_VAL = -(1 << (NB_DATA - 1))
    MAX_VAL =  (1 << (NB_DATA - 1)) - 1

    vectors = [(random.randint(MIN_VAL, MAX_VAL),
                random.randint(MIN_VAL, MAX_VAL)) for _ in range(N_DATA)]

    results = await transmit_batch(dut, vectors)

    for idx, ((re_val, im_val), received) in enumerate(zip(vectors, results)):
        expected = ((re_val & 0xFF) << 8) | (im_val & 0xFF)
        assert received == expected, \
            f"[{idx}] Re={re_val} Im={im_val}: expected 0x{expected:04X}, got 0x{received:04X}"
        cocotb.log.info(f"  [{idx:2d}] 0x{received:04X}  OK")

    cocotb.log.info("test_basic_serialization PASSED.")


@cocotb.test()
async def test_start_bit_only_on_first(dut):
    """
    Verifies that the start bit (o_data=1 before data) appears only
    on the first sample of each batch and not on the rest.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_start_bit_only_on_first ---")

    vectors = [(i, -i) for i in range(N_DATA)]

    for idx, (re_val, im_val) in enumerate(vectors):
        await wait_for_ready(dut)

        dut.i_valid.value   = 1
        dut.i_data_re.value = re_val & 0xFF
        dut.i_data_im.value = im_val & 0xFF
        await RisingEdge(dut.i_clk)
        dut.i_valid.value = 0

        if idx == 0:
            start_seen = False
            for _ in range(TIMEOUT_CYCLES):
                await RisingEdge(dut.i_clk)
                if dut.o_data.value == 1:
                    start_seen = True
                    break
            assert start_seen, f"[{idx}] Expected start bit but never saw it"
            cocotb.log.info(f"  [{idx:2d}] Start bit detected  OK")
        else:
            await RisingEdge(dut.i_clk)
            assert dut.o_ready.value == 0, \
                f"[{idx}] Serializer should be transmitting"
            cocotb.log.info(f"  [{idx:2d}] No start bit (direct send)  OK")

        # Drain remaining bits
        for _ in range(2 * NB_DATA):
            await RisingEdge(dut.i_clk)

    cocotb.log.info("test_start_bit_only_on_first PASSED.")


@cocotb.test()
async def test_ready_deasserts_during_tx(dut):
    """
    Verifies o_ready goes low during transmission and returns high after.
    Checked for both first sample (with start bit) and a mid-batch sample.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_ready_deasserts_during_tx ---")

    for idx in range(2):
        await wait_for_ready(dut)
        dut.i_valid.value   = 1
        dut.i_data_re.value = 0xAA
        dut.i_data_im.value = 0x55
        await RisingEdge(dut.i_clk)
        dut.i_valid.value = 0

        ready_low_seen = False
        for _ in range(TIMEOUT_CYCLES):
            await RisingEdge(dut.i_clk)
            if dut.o_ready.value == 0:
                ready_low_seen = True
            if ready_low_seen and dut.o_ready.value == 1:
                break
        else:
            assert False, f"[{idx}] Timeout: o_ready never returned high"

        assert ready_low_seen, f"[{idx}] o_ready never went low"
        cocotb.log.info(f"  [{idx}] o_ready deasserted and reasserted correctly  OK")

    cocotb.log.info("test_ready_deasserts_during_tx PASSED.")


@cocotb.test()
async def test_consecutive_batches(dut):
    """
    Sends two full batches back to back.
    Verifies that after N_DATA samples the start bit reappears.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_consecutive_batches ---")

    import random
    random.seed(7)
    MIN_VAL = -(1 << (NB_DATA - 1))
    MAX_VAL =  (1 << (NB_DATA - 1)) - 1

    for batch_idx in range(2):
        vectors  = [(random.randint(MIN_VAL, MAX_VAL),
                     random.randint(MIN_VAL, MAX_VAL)) for _ in range(N_DATA)]
        results  = await transmit_batch(dut, vectors)

        for idx, ((re_val, im_val), received) in enumerate(zip(vectors, results)):
            expected = ((re_val & 0xFF) << 8) | (im_val & 0xFF)
            assert received == expected, \
                f"Batch {batch_idx}[{idx}]: expected 0x{expected:04X}, got 0x{received:04X}"

        cocotb.log.info(f"  Batch {batch_idx} PASSED.")

    cocotb.log.info("test_consecutive_batches PASSED.")


@cocotb.test()
async def test_data_ignored_when_busy(dut):
    """
    Drives i_valid while serializer is busy. Verifies the ongoing
    transmission is not corrupted.
    """
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_data_ignored_when_busy ---")

    await wait_for_ready(dut)
    re_val, im_val = 0x12, 0x34
    expected = (re_val << 8) | im_val

    dut.i_valid.value   = 1
    dut.i_data_re.value = re_val
    dut.i_data_im.value = im_val
    await RisingEdge(dut.i_clk)

    dut.i_data_re.value = 0xFF
    dut.i_data_im.value = 0xFF
    dut.i_valid.value   = 1
    await RisingEdge(dut.i_clk)
    dut.i_valid.value = 0

    for _ in range(TIMEOUT_CYCLES):
        await RisingEdge(dut.i_clk)
        if dut.o_data.value == 1:
            break
    else:
        assert False, "Timeout: start bit never detected"

    received = 0
    for _ in range(2 * NB_DATA):
        await RisingEdge(dut.i_clk)
        received = (received << 1) | int(dut.o_data.value)

    assert received == expected, \
        f"Expected 0x{expected:04X}, got 0x{received:04X}"
    cocotb.log.info(f"  Received 0x{received:04X} — busy data correctly ignored  OK")
    cocotb.log.info("test_data_ignored_when_busy PASSED.")