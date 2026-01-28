import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Configuration
NB_DATA = 8

async def reset_dut(dut):
    dut.i_rst_n.value = 0
    dut.i_valid.value = 0
    dut.i_data_re.value = 0
    dut.i_data_im.value = 0
    await Timer(20, unit="ns")
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

@cocotb.test()
async def test_tx_serializer(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    print("--- STARTING SERIALIZER TEST ---")

    test_vectors = [
        (0, 0),
        (127, -128),
        (-1, 1),
        (85, 170),
        (-50, 50)
    ]

    for re_val, im_val in test_vectors:
        
        # 1. Wait for Ready
        while dut.o_ready.value == 0:
            await RisingEdge(dut.i_clk)

        # 2. Drive Inputs
        dut.i_valid.value = 1
        dut.i_data_re.value = re_val
        dut.i_data_im.value = im_val
        
        # Calculate Expected Word (MSB=Real, LSB=Imag)
        re_int = re_val & 0xFF
        im_int = im_val & 0xFF
        expected_full_word = (re_int << 8) | im_int
        
        print(f"Driving: Re={re_val}, Im={im_val} (Exp: 0x{expected_full_word:04X})")

        # 3. Wait for FSM to take input
        await RisingEdge(dut.i_clk) 
        dut.i_valid.value = 0       

        # 4. Wait for START BIT (Logic '1')
        # The line stays 0 until the Start bit appears.
        timeout = 20
        while dut.o_data.value == 0:
            await RisingEdge(dut.i_clk)
            timeout -= 1
            if timeout == 0:
                assert False, "Timeout: Start Bit (1) never detected!"
        
        # Start Bit detected. Wait 1 cycle to move to first Data bit
        await RisingEdge(dut.i_clk)

        # 5. Capture Data (16 bits)
        # MSB first
        received_word = 0
        total_bits = 2 * NB_DATA
        
        for b in range(total_bits):
            # Capture current bit
            bit = int(dut.o_data.value)
            received_word = (received_word << 1) | bit
            
            # Move to next bit
            await RisingEdge(dut.i_clk)

        print(f"Received: 0x{received_word:04X}")

        # 6. Verify
        assert received_word == expected_full_word, \
            f"Mismatch! Exp: 0x{expected_full_word:04X}, Got: 0x{received_word:04X}"

        # Allow FSM to return to IDLE
        await RisingEdge(dut.i_clk) 
        
    print("TEST PASSED")