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
    
    sample_idx = 0
    input_history = []
    for cycle in range(150):
        if sample_idx < 16 and (cycle % 8) == 0:
            dut.i_valid.value = 1
            dut.i_data_re.value = sample_idx
            dut.i_data_im.value = sample_idx
            in_val = sample_idx
            input_history.append(sample_idx)
            sample_idx += 1
        else:
            dut.i_valid.value = 0
            dut.i_data_re.value = 0
            dut.i_data_im.value = 0
            in_val = 0

        await RisingEdge(dut.i_clk)

        v_out = dut.o_valid.value
        d0 = get_signed(dut.o_data0_re)
        d1 = get_signed(dut.o_data1_re)
        d2 = get_signed(dut.o_data2_re)
        d3 = get_signed(dut.o_data3_re)

        dut._log.info(f"{cycle:^5} | {in_val:^2} | {v_out!s:^5} | {d0:^15} | {d1:^14} | {d2:^14} | {d3:^14}")

        if v_out == 1:
        
            valid_count = len(input_history)

            def get_expected(delay):
                idx = valid_count - delay
                if 0 <= idx < len(input_history):
                    return input_history[idx]
                return 0

            exp_d0 = get_expected(13)
            exp_d1 = get_expected(9)
            exp_d2 = get_expected(5)
            exp_d3 = get_expected(1)

            assert d0 == exp_d0, f"d0 error: expected {exp_d0}, got {d0}"
            assert d1 == exp_d1, f"d1 error: expected {exp_d1}, got {d1}"
            assert d2 == exp_d2, f"d2 error: expected {exp_d2}, got {d2}"
            assert d3 == exp_d3, f"d3 error: expected {exp_d3}, got {d3}"

    dut._log.info("--- TEST PASSED ---")