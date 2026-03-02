import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random

CLK_NS  = 20
NB_DATA = 8
N_DATA  = 16

def to_signed_8(val):
    val = val & 0xFF
    return val - 256 if val > 127 else val

async def reset_dut(dut):
    dut.i_rst_n.value   = 0
    dut.i_valid.value   = 0
    dut.i_data_re.value = 0
    dut.i_data_im.value = 0
    for _ in range(4):
        await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

async def drive_samples(dut, pairs, gap=0):
    for re_val, im_val in pairs:
        dut.i_valid.value   = 1
        dut.i_data_re.value = re_val & 0xFF
        dut.i_data_im.value = im_val & 0xFF
        await RisingEdge(dut.i_clk)
        
        dut.i_valid.value = 0
        for _ in range(gap):
            await RisingEdge(dut.i_clk)

async def monitor_burst(dut, expected_count):
    results = []
    
    while dut.o_valid.value == 0:
        await RisingEdge(dut.i_clk)
        
    for _ in range(expected_count):
        assert dut.o_valid.value == 1, "o_valid dropped during burst"
        re = to_signed_8(int(dut.o_data_re.value))
        im = to_signed_8(int(dut.o_data_im.value))
        results.append((re, im))
        await RisingEdge(dut.i_clk)
        
    assert dut.o_valid.value == 0, "o_valid did not drop after burst"
    return results

@cocotb.test()
async def test_continuous_input(dut):
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    
    pairs = [(i, -i) for i in range(N_DATA)]
    
    cocotb.start_soon(drive_samples(dut, pairs, gap=0))
    results = await monitor_burst(dut, N_DATA)
    
    assert len(results) == N_DATA
    for idx, (exp, got) in enumerate(zip(pairs, results)):
        assert exp == got, f"[{idx}] Expected {exp}, got {got}"
        
    cocotb.log.info("test_continuous_input PASSED")

@cocotb.test()
async def test_gapped_input(dut):
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    
    pairs = [(random.randint(-128, 127), random.randint(-128, 127)) for _ in range(N_DATA)]
    
    cocotb.start_soon(drive_samples(dut, pairs, gap=15))
    results = await monitor_burst(dut, N_DATA)
    
    assert len(results) == N_DATA
    for idx, (exp, got) in enumerate(zip(pairs, results)):
        assert exp == got, f"[{idx}] Expected {exp}, got {got}"
        
    cocotb.log.info("test_gapped_input PASSED")

@cocotb.test()
async def test_consecutive_batches(dut):
    cocotb.start_soon(Clock(dut.i_clk, CLK_NS, unit="ns").start())
    await reset_dut(dut)
    
    for batch in range(3):
        pairs = [(batch * 10 + i, -(batch * 10 + i)) for i in range(N_DATA)]
        
        cocotb.start_soon(drive_samples(dut, pairs, gap=5))
        results = await monitor_burst(dut, N_DATA)
        
        assert len(results) == N_DATA
        for idx, (exp, got) in enumerate(zip(pairs, results)):
            assert exp == got, f"Batch {batch} [{idx}] Expected {exp}, got {got}"
            
    cocotb.log.info("test_consecutive_batches PASSED")