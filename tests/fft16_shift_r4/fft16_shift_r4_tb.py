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
async def test_fft16_shift_r4(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    dut._log.info("--- TEST INIT ---")
    dut._log.info("Cycle | In | Valid | d0 | d1 | d2 | d3 ")
    dut._log.info("-" * 85)

    for cycle in range(30):
        if cycle < 16:
            if cycle == 0:
                dut.i_valid.value = 1
            else:
                dut.i_valid.value = 0
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
        d2 = get_signed(dut.o_data2_re)
        d3 = get_signed(dut.o_data3_re)

        in_val = cycle if cycle < 16 else "-"
        dut._log.info(f"{cycle:^5} | {in_val:^2} | {v_out!s:^5} | {d0:^15} | {d1:^14} | {d2:^14} | {d3:^14}")

        if v_out == 1: 
            exp_d0 = cycle - 13 if (cycle - 13) < 16 else 0
            exp_d1 = cycle - 9  if (cycle - 9)  < 16 else 0
            exp_d2 = cycle - 5  if (cycle - 5)  < 16 else 0
            exp_d3 = cycle - 1  if (cycle - 1)  < 16 else 0
            
            assert d0 == exp_d0, f"Error in d0: expected {exp_d0}, received {d0}"
            assert d1 == exp_d1, f"Error in d1: expected {exp_d1}, received {d1}"
            assert d2 == exp_d2, f"Error in d2: expected {exp_d2}, received {d2}"
            assert d3 == exp_d3, f"Error in d3: expected {exp_d3}, received {d3}"

    dut._log.info("--- TEST PASSED ---")