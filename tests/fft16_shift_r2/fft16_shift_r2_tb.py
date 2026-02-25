import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

def get_signed(signal):
    try:
        return signal.value.to_signed()
    except ValueError:
        return 'X'

async def reset_dut(dut):
    dut.i_clk_en.value = 0
    dut.i_valid.value = 0
    dut.i_data_re.value = 0
    dut.i_data_im.value = 0
    await RisingEdge(dut.i_clk)
    dut.i_clk_en.value = 1

@cocotb.test()
async def test_fft16_shift_r2(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    dut._log.info("--- TEST INIT ---")
    dut._log.info("Cycle | In | Valid | d0 | d1")
    dut._log.info("-" * 65)

    for cycle in range(25): 
        if cycle < 16:
            dut.i_valid.value = 1
            dut.i_data_re.value = cycle
            dut.i_data_im.value = cycle
        else:
            dut.i_valid.value = 0
            dut.i_data_re.value = 0
            dut.i_data_im.value = 0

        await RisingEdge(dut.i_clk)

        v_out = dut.o_valid.value
        d0 = get_signed(dut.o_data0_re)
        d1 = get_signed(dut.o_data1_re)

        in_val = cycle if cycle < 16 else "-"
        dut._log.info(f"{cycle:^5} | {in_val:^2} | {v_out!s:^5} | {d0:^14} | {d1:^14}")

        if v_out == 1: 
            exp_d0 = cycle - 3 if (cycle - 3) < 16 else 0
            exp_d1 = cycle - 1 if (cycle - 1) < 16 else 0
            
            assert d0 == exp_d0, f"Error in d0: expected {exp_d0}, received {d0}"
            assert d1 == exp_d1, f"Error in d1: expected {exp_d1}, received {d1}"

    dut._log.info("--- TEST PASSED ---")