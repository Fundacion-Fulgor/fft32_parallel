import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Configuration
NB_DATA = 8

def force_signed_8bit(val):
    """
    Convert Python integer to 8-bit signed representation.
    E.g., 170 (0xAA) -> -86
    """
    val = val & 0xFF 
    if val > 127:
        val -= 256
    return val

async def reset_dut(dut):
    dut.i_rst_n.value = 0
    dut.i_data.value = 0
    await Timer(20, unit="ns")
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

@cocotb.test()
async def test_rx_serializer(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    print("--- STARTING RX SERIALIZER TEST ---")

    test_vectors = [
        (0, 0),
        (127, -128),
        (-1, 1),
        (85, 170),
        (-50, 50)
    ]

    for re_val, im_val in test_vectors:
        
        # Normalize expectation to 8-bit signed
        exp_re = force_signed_8bit(re_val)
        exp_im = force_signed_8bit(im_val)

        # Prepare 16-bit word (MSB=Real, LSB=Imag)
        raw_re = re_val & 0xFF
        raw_im = im_val & 0xFF
        full_word = (raw_re << 8) | raw_im
        
        print(f"Sending: Re={re_val}, Im={im_val} (Word: 0x{full_word:04X})")

        # 1. Ensure IDLE
        dut.i_data.value = 0
        await RisingEdge(dut.i_clk)

        # 2. Generate START BIT (Rising Edge 0->1)
        dut.i_data.value = 1
        await RisingEdge(dut.i_clk) 
        
        # 3. Stream Data Bits (16 bits, MSB first)
        for i in range(16):
            bit_idx = 15 - i
            bit = (full_word >> bit_idx) & 1
            
            dut.i_data.value = bit
            await RisingEdge(dut.i_clk)

        # 4. Wait for VALID output
        dut.i_data.value = 0 # Return to IDLE
        
        timeout = 10
        while dut.o_valid.value == 0:
            await RisingEdge(dut.i_clk)
            timeout -= 1
            if timeout == 0:
                assert False, "Timeout: o_valid never asserted!"

        # 5. Check Outputs
        out_re = dut.o_data_re.value.to_signed()
        out_im = dut.o_data_im.value.to_signed()
        
        print(f"Received: Re={out_re}, Im={out_im}")

        assert out_re == exp_re, f"Real Mismatch! Exp: {exp_re}, Got: {out_re}"
        assert out_im == exp_im, f"Imag Mismatch! Exp: {exp_im}, Got: {out_im}"

        # Wait for FSM to return to IDLE
        await RisingEdge(dut.i_clk)

    print("TEST PASSED")