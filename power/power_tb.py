import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from top_fft16_bringup_tb import (
    CLK_NS,
    idle,
    power_on_reset,
    run_verified_block,
    set_config,
)

MODE = os.environ.get("POWER_MODE", "fft").lower()
N_BLOCKS = int(os.environ.get("POWER_BLOCKS", "4"))
SEED = int(os.environ.get("POWER_SEED", "7000"))


@cocotb.test()
async def power_workload(dut):
    if MODE not in ("fft", "ifft"):
        raise ValueError(f"POWER_MODE must be fft or ifft, got {MODE!r}")
    inverse = MODE == "ifft"

    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    dut.i_dump_en.value = 0

    cocotb.log.info("SETUP: reset and configuration, kept outside the VCD window")
    await power_on_reset(dut)
    await set_config(dut, enable=True, inverse=inverse)
    await idle(dut, 8)

    cocotb.log.info(f"MEASURED: {N_BLOCKS} {MODE.upper()} blocks back to back")
    dut.i_dump_en.value = 1
    await RisingEdge(dut.i_clk)

    for idx in range(N_BLOCKS):
        await run_verified_block(
            dut, inverse=inverse, seed=SEED + idx, label=f"{MODE} {idx}: "
        )

    cocotb.log.info(
        f"workload complete: {N_BLOCKS} {MODE.upper()} blocks verified against the "
        f"golden model, VCD covers the streaming window only"
    )
