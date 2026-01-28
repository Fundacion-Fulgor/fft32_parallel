import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import numpy as np
from fxpmath import Fxp

# Configuration
NB_IO = 8
NBF_IO = 7

def get_fxp(value):
    return Fxp(value, signed=True, n_word=NB_IO, n_frac=NBF_IO)

async def reset_dut(dut):
    dut.i_rst_n.value = 0
    dut.i_enable.value = 0
    dut.i_valid.value = 0
    dut.i_inverse.value = 0
    for i in range(4):
        getattr(dut, f"i_data{i}_re").value = 0
        getattr(dut, f"i_data{i}_im").value = 0
    await Timer(20, unit="ns")
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

@cocotb.test()
async def test_fft4(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    # -----------------------------------------------------------
    # TEST 1: Forward FFT
    # -----------------------------------------------------------
    print("--- STARTING FFT TEST ---")
    
    # 1. Generate Float Input
    n = np.arange(4)
    input_float = 0.2 * np.cos(2 * np.pi * n / 4) + 0j
    
    # 2. Quantize Input
    # We use these integers for BOTH the DUT and the Reference
    input_int_re = [int(get_fxp(x.real).val) for x in input_float]
    input_int_im = [int(get_fxp(x.imag).val) for x in input_float]

    # Drive Inputs
    dut.i_enable.value = 1
    dut.i_valid.value = 1
    dut.i_inverse.value = 0 

    for i in range(4):
        getattr(dut, f"i_data{i}_re").value = input_int_re[i]
        getattr(dut, f"i_data{i}_im").value = input_int_im[i]

    await RisingEdge(dut.i_clk)
    dut.i_valid.value = 0
    
    # Wait for Valid Output
    timeout = 20
    while dut.o_valid.value == 0:
        await RisingEdge(dut.i_clk)
        timeout -= 1
        if timeout == 0:
            assert False, "Timeout: o_valid never asserted!"

    # 3. Calculate Reference using QUANTIZED inputs
    input_complex_int = [complex(r, i) for r, i in zip(input_int_re, input_int_im)]
    ref_fft = np.fft.fft(input_complex_int)
    
    # 4. Verification
    for i in range(4):
        # DUT Output
        out_re = dut.o_data0_re.value.to_signed() if i==0 else \
                 dut.o_data1_re.value.to_signed() if i==1 else \
                 dut.o_data2_re.value.to_signed() if i==2 else \
                 dut.o_data3_re.value.to_signed()
                 
        out_im = dut.o_data0_im.value.to_signed() if i==0 else \
                 dut.o_data1_im.value.to_signed() if i==1 else \
                 dut.o_data2_im.value.to_signed() if i==2 else \
                 dut.o_data3_im.value.to_signed()
        
        # Reference (Expected integer result)
        # Since hardware only saturates MSBs (no fractional truncation), 
        # exact match is expected for low amplitudes.
        ref_re = int(ref_fft[i].real)
        ref_im = int(ref_fft[i].imag)

        assert out_re == ref_re, f"FFT Bin {i} Real mismatch. DUT: {out_re}, REF: {ref_re}"
        assert out_im == ref_im, f"FFT Bin {i} Imag mismatch. DUT: {out_im}, REF: {ref_im}"

    await RisingEdge(dut.i_clk)

    # -----------------------------------------------------------
    # TEST 2: Inverse FFT
    # -----------------------------------------------------------
    print("--- STARTING IFFT TEST ---")

    dut.i_valid.value = 1
    dut.i_inverse.value = 1 

    # Input: DC Constant (Using clean integers directly)
    # 25 is approx 0.2 in Q1.7
    input_inv_int = [complex(25, 0), complex(0,0), complex(0,0), complex(0,0)]
    
    for i in range(4):
        getattr(dut, f"i_data{i}_re").value = int(input_inv_int[i].real)
        getattr(dut, f"i_data{i}_im").value = int(input_inv_int[i].imag)

    await RisingEdge(dut.i_clk)
    dut.i_valid.value = 0

    # Wait for Valid Output
    timeout = 20
    while dut.o_valid.value == 0:
        await RisingEdge(dut.i_clk)
        timeout -= 1
        if timeout == 0:
            assert False, "Timeout: o_valid never asserted (IFFT)!"

    # Verification
    # Hardware IFFT is unscaled sum. Numpy IFFT needs * N to match.
    ref_ifft = np.fft.ifft(input_inv_int)

    for i in range(4):
        out_re = getattr(dut, f"o_data{i}_re").value.to_signed()
        out_im = getattr(dut, f"o_data{i}_im").value.to_signed()
        
        ref_re = int(ref_ifft[i].real)
        ref_im = int(ref_ifft[i].imag)

        assert out_re == ref_re, f"IFFT Bin {i} Real mismatch. DUT: {out_re}, REF: {ref_re}"
        assert out_im == ref_im, f"IFFT Bin {i} Imag mismatch. DUT: {out_im}, REF: {ref_im}"

    print("TEST PASSED")