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

def bit_reverse(n, bits=3):
    result = 0
    for i in range(bits):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result

async def reset_dut(dut):
    dut.i_rst_n.value = 0
    dut.i_valid.value = 0
    dut.i_inverse.value = 0
    dut.i_data1_r.value = 0
    dut.i_data1_i.value = 0
    dut.i_data2_r.value = 0
    dut.i_data2_i.value = 0
    await Timer(20, unit="ns")
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

@cocotb.test()
async def test_fft8(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    # -----------------------------------------------------------
    # TEST 1: Forward FFT (Bit-Perfect)
    # -----------------------------------------------------------
    print("--- STARTING FFT 8-POINT TEST ---")
    
    # 1. Generate Input (Amplitude 0.12 to allow growth x8)
    N = 8
    n_idx = np.arange(N)
    input_float = 0.12 * np.cos(2 * np.pi * n_idx / N) + 0.05j 
    
    # 2. Quantize Input
    input_int_re = [int(get_fxp(x.real).val) for x in input_float]
    input_int_im = [int(get_fxp(x.imag).val) for x in input_float]

    # 3. Drive Inputs (Simulating shift_r2 alignment)
    dut.i_valid.value = 1
    dut.i_inverse.value = 0 

    for k in range(N // 2):
        idx_1 = k          
        idx_2 = k + (N//2) 
        
        dut.i_data1_r.value = input_int_re[idx_1]
        dut.i_data1_i.value = input_int_im[idx_1]
        dut.i_data2_r.value = input_int_re[idx_2]
        dut.i_data2_i.value = input_int_im[idx_2]
        
        await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0
    
    # 4. Wait for Valid Output
    timeout = 100
    while dut.o_valid.value == 0:
        await RisingEdge(dut.i_clk)
        timeout -= 1
        if timeout == 0:
            assert False, "Timeout: o_valid never asserted!"

    # 5. Capture Output
    dut_outputs = []
    for _ in range(N // 2):
        if dut.o_valid.value != 1:
             assert False, "o_valid dropped prematurely!"
        
        r1 = dut.o_data1_r.value.to_signed()
        i1 = dut.o_data1_i.value.to_signed()
        r2 = dut.o_data2_r.value.to_signed()
        i2 = dut.o_data2_i.value.to_signed()
        
        dut_outputs.append(complex(r1, i1))
        dut_outputs.append(complex(r2, i2))
        
        await RisingEdge(dut.i_clk)

    # 6. Reference Calculation
    input_cplx_quant = [complex(r, i) for r, i in zip(input_int_re, input_int_im)]
    ref_fft = np.fft.fft(input_cplx_quant)

    # 7. Verification (Bit-Reversed Order check)
    print("Checking outputs...")
    
    for k in range(N):
        br_idx = bit_reverse(k, 3)
        
        dut_val = dut_outputs[k]
        ref_val = ref_fft[br_idx] 
        
        dut_re = int(dut_val.real)
        dut_im = int(dut_val.imag)
        ref_re = int(ref_val.real)
        ref_im = int(ref_val.imag)

        assert abs(dut_re - ref_re) <= 1, f"Bin {br_idx} Real mismatch. DUT: {dut_re}, REF: {ref_re}"
        assert abs(dut_im - ref_im) <= 1, f"Bin {br_idx} Imag mismatch. DUT: {dut_im}, REF: {ref_im}"

    await RisingEdge(dut.i_clk)

    # -----------------------------------------------------------
    # TEST 2: Inverse FFT 8-POINT
    # -----------------------------------------------------------
    print("--- STARTING IFFT 8-POINT TEST ---")
    
    dut.i_valid.value = 1
    dut.i_inverse.value = 1 
    
    # Input: DC Impulse 
    input_inv_re = [16, 0, 0, 0, 0, 0, 0, 0]
    input_inv_im = [0] * 8

    # Feed pairs
    for k in range(N // 2):
        idx_1 = k
        idx_2 = k + (N//2)
        dut.i_data1_r.value = input_inv_re[idx_1]
        dut.i_data1_i.value = input_inv_im[idx_1]
        dut.i_data2_r.value = input_inv_re[idx_2]
        dut.i_data2_i.value = input_inv_im[idx_2]
        await RisingEdge(dut.i_clk)

    dut.i_valid.value = 0

    while dut.o_valid.value == 0:
        await RisingEdge(dut.i_clk)

    dut_outputs_inv = []
    for _ in range(N // 2):
        r1 = dut.o_data1_r.value.to_signed()
        i1 = dut.o_data1_i.value.to_signed()
        r2 = dut.o_data2_r.value.to_signed()
        i2 = dut.o_data2_i.value.to_signed()
        dut_outputs_inv.append(complex(r1, i1))
        dut_outputs_inv.append(complex(r2, i2))
        await RisingEdge(dut.i_clk)

    # Ref IFFT (Unscaled HW -> Needs x8)
    input_cplx_inv = [complex(r, i) for r, i in zip(input_inv_re, input_inv_im)]
    ref_ifft = np.fft.ifft(input_cplx_inv)

    for k in range(N):
        br_idx = bit_reverse(k, 3)
        dut_val = dut_outputs_inv[k]
        ref_val = ref_ifft[br_idx]
        
        dut_re = int(dut_val.real)
        dut_im = int(dut_val.imag)
        ref_re = int(ref_val.real)
        ref_im = int(ref_val.imag)

        assert abs(dut_re - ref_re) <= 1, f"IFFT Bin {br_idx} Real mismatch."
        assert abs(dut_im - ref_im) <= 1, f"IFFT Bin {br_idx} Imag mismatch."

    print("TEST PASSED")