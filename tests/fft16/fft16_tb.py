import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_fft16_sanity(dut):
    """Sanity check to verify fft16 connections."""
    
    clock = Clock(dut.i_clk, 10, unit="ns") 
    cocotb.start_soon(clock.start())

    dut.i_clk_en.value = 0
    dut.i_rst_n.value = 0
    dut.i_inverse.value = 0
    dut.i_valid.value = 0
    dut.i_tx_ready.value = 0
    dut.i_data_re.value = 0
    dut.i_data_im.value = 0

    cocotb.log.info("Applying reset...")
    await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

    dut.i_clk_en.value = 1
    dut.i_tx_ready.value = 1
    
    cocotb.log.info("Injecting test stimuli...")
    for i in range(32):
        dut.i_valid.value = 1
        dut.i_data_re.value = i % 100 
        dut.i_data_im.value = (i * 2) % 100
        await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0
    
    cocotb.log.info("Waiting for data to propagate through the entire pipeline...")
    timeout = 100
    cycles_wait = 0
    
    while cycles_wait < timeout:
        await RisingEdge(dut.i_clk)
        cycles_wait += 1
        
        if dut.o_valid.value == 1:
            try:
                out_re = dut.o_data_re.value.to_signed()
                out_im = dut.o_data_im.value.to_signed()
                cocotb.log.info(f"Cycle {cycles_wait}: WARNING! Undefined (X) signals detected at the output.")
            except ValueError:
                cocotb.log.error(f"Ciclo {cycles_wait}: ¡ALERTA! Señales indefinidas (X) en la salida.")
                
    cocotb.log.info("Sanity check completed.")