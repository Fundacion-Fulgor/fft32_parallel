import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random

CLK_SYS_NS = 20
CLK_SPI_NS = 100

ADDR_STATUS_FLAGS = 0x00
ADDR_ERROR_FLAGS  = 0x01
ADDR_CNT_INPUTS   = 0x02
ADDR_CNT_OUTPUTS  = 0x03
ADDR_LAST_OUT_RE  = 0x04
ADDR_LAST_OUT_IM  = 0x05
ADDR_MID_DATA_RE  = 0x06
ADDR_SYS_CONFIG   = 0x10


async def reset_dut(dut):
    dut.rst_n.value        = 0
    dut.spi_addr.value     = 0
    dut.spi_wdata.value    = 0
    dut.spi_rw.value       = 1   # default READ
    dut.spi_ss_n.value     = 1
    dut.status_flags.value = 0
    dut.error_flags.value  = 0
    dut.cnt_inputs.value   = 0
    dut.cnt_outputs.value  = 0
    dut.last_out_re.value  = 0
    dut.last_out_im.value  = 0
    dut.mid_data_re.value  = 0
    for _ in range(4):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def trigger_snapshot(dut):
    """
    Pulls ss_n low asynchronously to freeze probe inputs via cdc_snapshot,
    then releases it. rw_rw stays 1 (READ) so no write is committed.
    """
    await Timer(CLK_SPI_NS, unit="ns")
    dut.spi_ss_n.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
    dut.spi_ss_n.value = 1
    for _ in range(6):
        await RisingEdge(dut.clk)


async def spi_write(dut, addr, data):
    """
    Simulates a complete SPI write transaction using rw_bit (0=WRITE).
    rw_bit is stable from the 8th sclk cycle — here we set it before
    ss_n falls to replicate that the master has already decided to write.
    ss_n falls  -> snapshot_pulse (status frozen)
    data settles in SPI domain
    ss_n rises  -> commit_pulse captures addr/wdata/rw_snap
    commit_pulse_q -> sys_config written
    """
    dut.spi_rw.value    = 0   # WRITE
    dut.spi_addr.value  = addr
    dut.spi_wdata.value = data
    await Timer(CLK_SPI_NS, unit="ns")
    dut.spi_ss_n.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(CLK_SPI_NS, unit="ns")
    dut.spi_ss_n.value = 1
    for _ in range(6):
        await RisingEdge(dut.clk)
    dut.spi_rw.value = 1   # back to READ


async def spi_read(dut, addr):
    """
    Reads spi_rdata combinationally via spi_addr directly.
    No transaction needed — frozen snapshot values remain stable.
    """
    dut.spi_addr.value = addr
    await RisingEdge(dut.clk)
    return int(dut.spi_rdata.value)


@cocotb.test()
async def test_sys_config_write(dut):
    """
    Writes different values to sys_config via full SPI write transactions.
    Uses spi_rw=0 (WRITE) stable before ss_n falls, mimicking real
    spi_slave_mode0 behavior where rw_bit is latched at the 8th sclk cycle.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_sys_config_write ---")

    for val in [0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111]:
        await spi_write(dut, ADDR_SYS_CONFIG, val)
        got = int(dut.sys_config.value)
        assert got == val, \
            f"sys_config mismatch: wrote {val:#05b}, got {got:#05b}"
        cocotb.log.info(f"  sys_config = {val:#05b}  OK")

    cocotb.log.info("test_sys_config_write PASSED.")


@cocotb.test()
async def test_sys_config_readback(dut):
    """
    Writes sys_config and reads it back via spi_rdata.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_sys_config_readback ---")

    for val in [0b001, 0b011, 0b111]:
        await spi_write(dut, ADDR_SYS_CONFIG, val)
        got = await spi_read(dut, ADDR_SYS_CONFIG)
        assert got == val, \
            f"sys_config readback mismatch: expected {val:#05b}, got {got:#05b}"
        cocotb.log.info(f"  readback sys_config = {val:#05b}  OK")

    cocotb.log.info("test_sys_config_readback PASSED.")


@cocotb.test()
async def test_status_snapshot(dut):
    """
    Sets known values on all probe inputs, triggers a snapshot explicitly,
    then reads each register and verifies the frozen value.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_status_snapshot ---")

    dut.status_flags.value = 0xAB
    dut.error_flags.value  = 0x01
    dut.cnt_inputs.value   = 0x42
    dut.cnt_outputs.value  = 0x10
    dut.last_out_re.value  = 0x7F
    dut.last_out_im.value  = 0x3C
    dut.mid_data_re.value  = 0x55

    for _ in range(3):
        await RisingEdge(dut.clk)

    await trigger_snapshot(dut)

    checks = [
        (ADDR_STATUS_FLAGS, 0xAB, "status_flags"),
        (ADDR_ERROR_FLAGS,  0x01, "error_flags"),
        (ADDR_CNT_INPUTS,   0x42, "cnt_inputs"),
        (ADDR_CNT_OUTPUTS,  0x10, "cnt_outputs"),
        (ADDR_LAST_OUT_RE,  0x7F, "last_out_re"),
        (ADDR_LAST_OUT_IM,  0x3C, "last_out_im"),
        (ADDR_MID_DATA_RE,  0x55, "mid_data_re"),
    ]

    for addr, expected, name in checks:
        got = await spi_read(dut, addr)
        assert got == expected, \
            f"{name} snapshot mismatch: expected {expected:#04x}, got {got:#04x}"
        cocotb.log.info(f"  {name} @ {addr:#04x} = {got:#04x}  OK")

    cocotb.log.info("test_status_snapshot PASSED.")


@cocotb.test()
async def test_cdc_snapshot_freeze(dut):
    """
    Verifies that changes to probe inputs after ss_n falls do not modify
    the frozen snapshot. The snapshot captures what was present at the
    falling edge of ss_n.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_cdc_snapshot_freeze ---")

    dut.cnt_inputs.value  = 0x11
    dut.cnt_outputs.value = 0x22
    dut.last_out_re.value = 0x33
    dut.last_out_im.value = 0x44

    for _ in range(3):
        await RisingEdge(dut.clk)

    await Timer(CLK_SPI_NS, unit="ns")
    dut.spi_ss_n.value = 0
    for _ in range(5):
        await RisingEdge(dut.clk)

    # Change inputs while ss_n is still low — must not affect frozen snapshot
    dut.cnt_inputs.value  = 0xFF
    dut.cnt_outputs.value = 0xEE
    dut.last_out_re.value = 0xDD
    dut.last_out_im.value = 0xCC

    for _ in range(5):
        await RisingEdge(dut.clk)
    dut.spi_ss_n.value = 1
    for _ in range(6):
        await RisingEdge(dut.clk)

    checks = [
        (ADDR_CNT_INPUTS,  0x11, "cnt_inputs"),
        (ADDR_CNT_OUTPUTS, 0x22, "cnt_outputs"),
        (ADDR_LAST_OUT_RE, 0x33, "last_out_re"),
        (ADDR_LAST_OUT_IM, 0x44, "last_out_im"),
    ]

    for addr, expected, name in checks:
        got = await spi_read(dut, addr)
        assert got == expected, \
            f"{name} freeze failed: expected {expected:#04x}, got {got:#04x}"
        cocotb.log.info(f"  {name} frozen @ {expected:#04x}  OK")

    cocotb.log.info("test_cdc_snapshot_freeze PASSED.")


@cocotb.test()
async def test_cdc_snapshot_update(dut):
    """
    Two consecutive snapshots with different values. Each must capture
    what was present at its respective ss_n falling edge.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_cdc_snapshot_update ---")

    dut.cnt_inputs.value  = 0xAA
    dut.last_out_re.value = 0xBB
    for _ in range(3):
        await RisingEdge(dut.clk)
    await trigger_snapshot(dut)

    got_inputs = await spi_read(dut, ADDR_CNT_INPUTS)
    got_re     = await spi_read(dut, ADDR_LAST_OUT_RE)
    assert got_inputs == 0xAA, \
        f"First snapshot cnt_inputs: expected 0xAA, got {got_inputs:#04x}"
    assert got_re == 0xBB, \
        f"First snapshot last_out_re: expected 0xBB, got {got_re:#04x}"
    cocotb.log.info(
        f"  First snapshot: cnt_inputs={got_inputs:#04x}  last_out_re={got_re:#04x}  OK"
    )

    dut.cnt_inputs.value  = 0x12
    dut.last_out_re.value = 0x34
    for _ in range(3):
        await RisingEdge(dut.clk)
    await trigger_snapshot(dut)

    got_inputs = await spi_read(dut, ADDR_CNT_INPUTS)
    got_re     = await spi_read(dut, ADDR_LAST_OUT_RE)
    assert got_inputs == 0x12, \
        f"Second snapshot cnt_inputs: expected 0x12, got {got_inputs:#04x}"
    assert got_re == 0x34, \
        f"Second snapshot last_out_re: expected 0x34, got {got_re:#04x}"
    cocotb.log.info(
        f"  Second snapshot: cnt_inputs={got_inputs:#04x}  last_out_re={got_re:#04x}  OK"
    )

    cocotb.log.info("test_cdc_snapshot_update PASSED.")


@cocotb.test()
async def test_default_address(dut):
    """
    Reads from unmapped addresses and verifies spi_rdata returns 0x00.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_default_address ---")

    for addr in [0x07, 0x0F, 0x11, 0x7F]:
        got = await spi_read(dut, addr)
        assert got == 0x00, \
            f"Unmapped address {addr:#04x}: expected 0x00, got {got:#04x}"
        cocotb.log.info(f"  addr {addr:#04x} -> {got:#04x}  OK")

    cocotb.log.info("test_default_address PASSED.")


@cocotb.test()
async def test_random_snapshot(dut):
    """
    Random probe values, random settle time, explicit snapshot trigger,
    then inputs change and frozen values are verified.
    """
    cocotb.start_soon(Clock(dut.clk, CLK_SYS_NS, unit="ns").start())
    await reset_dut(dut)
    cocotb.log.info("--- test_random_snapshot ---")

    random.seed(7)

    for iteration in range(8):
        vals = {
            "status_flags": random.randint(0, 0xFF),
            "error_flags":  random.randint(0, 0xFF),
            "cnt_inputs":   random.randint(0, 0xFF),
            "cnt_outputs":  random.randint(0, 0xFF),
            "last_out_re":  random.randint(0, 0xFF),
            "last_out_im":  random.randint(0, 0xFF),
            "mid_data_re":  random.randint(0, 0xFF),
        }

        for name, val in vals.items():
            getattr(dut, name).value = val

        for _ in range(random.randint(2, 8)):
            await RisingEdge(dut.clk)

        await trigger_snapshot(dut)

        # Change all inputs after snapshot
        for name in vals:
            getattr(dut, name).value = random.randint(0, 0xFF)

        for _ in range(3):
            await RisingEdge(dut.clk)

        checks = [
            (ADDR_STATUS_FLAGS, vals["status_flags"], "status_flags"),
            (ADDR_ERROR_FLAGS,  vals["error_flags"],  "error_flags"),
            (ADDR_CNT_INPUTS,   vals["cnt_inputs"],   "cnt_inputs"),
            (ADDR_CNT_OUTPUTS,  vals["cnt_outputs"],  "cnt_outputs"),
            (ADDR_LAST_OUT_RE,  vals["last_out_re"],  "last_out_re"),
            (ADDR_LAST_OUT_IM,  vals["last_out_im"],  "last_out_im"),
            (ADDR_MID_DATA_RE,  vals["mid_data_re"],  "mid_data_re"),
        ]

        for addr, expected, name in checks:
            got = await spi_read(dut, addr)
            assert got == expected, \
                f"Iter {iteration} - {name}: expected {expected:#04x}, got {got:#04x}"

        cocotb.log.info(f"  Iteration {iteration} PASSED")

    cocotb.log.info("test_random_snapshot PASSED.")