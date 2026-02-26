import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from model_fft4 import FFT4_Reference
import numpy as np
import random
import sys
import os

def float_to_int(val, frac_bits):
    """Convierte un flotante a un entero (representación de punto fijo)."""
    return int(round(val * (2**frac_bits)))

def int_to_float(val, int_bits, frac_bits):
    """Convierte un entero (representación complemento a 2) a flotante."""
    total_bits = int_bits + frac_bits + 1
    if val >= 2**(total_bits - 1):
        val -= 2**total_bits
    return val / (2**frac_bits)


@cocotb.test()
async def test_fft4_radix4(dut):
    
    NB_INPUT = 8
    NBF_INPUT = 6
    N = 16
    

    fft_model = FFT4_Reference(NB_INPUT=NB_INPUT, NBF_INPUT=NBF_INPUT, inverse=0)

    clock = Clock(dut.i_clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.i_rst_n.value = 0
    dut.i_enable.value = 0
    dut.i_valid.value = 0
    dut.i_inverse.value = 0
    
    dut.i_data0_re.value = 0; dut.i_data0_im.value = 0
    dut.i_data1_re.value = 0; dut.i_data1_im.value = 0
    dut.i_data2_re.value = 0; dut.i_data2_im.value = 0
    dut.i_data3_re.value = 0; dut.i_data3_im.value = 0

    await RisingEdge(dut.i_clk)
    dut.i_rst_n.value = 1
    await RisingEdge(dut.i_clk)

    dut.i_enable.value = 1
    
    num_tests = 100
    for k in range(num_tests):
        cocotb.log.info(f"--- Test {k} ---")
        
        input_float = 2 * np.random.uniform(-1, 1, N) + 2j * np.random.uniform(-1, 1, N)
        input_q = [fft_model.round.crnd(x, True, NB_INPUT, NBF_INPUT, 'around') for x in input_float]

        expected_output = fft_model.process(input_q)
        
        for m in range(4):
            d0 = input_q[m]
            d1 = input_q[m+4]
            d2 = input_q[m+8]
            d3 = input_q[m+12]
            
            dut.i_data0_re.value = float_to_int(d0.real, NBF_INPUT)
            dut.i_data0_im.value = float_to_int(d0.imag, NBF_INPUT)
            dut.i_data1_re.value = float_to_int(d1.real, NBF_INPUT)
            dut.i_data1_im.value = float_to_int(d1.imag, NBF_INPUT)
            dut.i_data2_re.value = float_to_int(d2.real, NBF_INPUT)
            dut.i_data2_im.value = float_to_int(d2.imag, NBF_INPUT)
            dut.i_data3_re.value = float_to_int(d3.real, NBF_INPUT)
            dut.i_data3_im.value = float_to_int(d3.imag, NBF_INPUT)
            
            dut.i_valid.value = 1
            await RisingEdge(dut.i_clk)
            
        dut.i_valid.value = 0
        
        output_rtl = [complex(0,0)] * N
        m_out = 0
        
        timeout_cnt = 0
        while dut.o_valid.value != 1:
            await RisingEdge(dut.i_clk)
            timeout_cnt += 1
            if timeout_cnt > 20:
                assert False, "Timeout waiting for o_valid"
                

        while dut.o_valid.value == 1 and m_out < 4:
            nbf_out_rtl = NB_INPUT - 2 
            int_bits_out = (NB_INPUT+2) - nbf_out_rtl - 1
            
            o0_re = int_to_float(dut.o_data0_re.value.to_signed(), int_bits_out, nbf_out_rtl)
            o0_im = int_to_float(dut.o_data0_im.value.to_signed(), int_bits_out, nbf_out_rtl)
            o1_re = int_to_float(dut.o_data1_re.value.to_signed(), int_bits_out, nbf_out_rtl)
            o1_im = int_to_float(dut.o_data1_im.value.to_signed(), int_bits_out, nbf_out_rtl)
            o2_re = int_to_float(dut.o_data2_re.value.to_signed(), int_bits_out, nbf_out_rtl)
            o2_im = int_to_float(dut.o_data2_im.value.to_signed(), int_bits_out, nbf_out_rtl)
            o3_re = int_to_float(dut.o_data3_re.value.to_signed(), int_bits_out, nbf_out_rtl)
            o3_im = int_to_float(dut.o_data3_im.value.to_signed(), int_bits_out, nbf_out_rtl)

            output_rtl[m_out * 4 + 0] = complex(o0_re, o0_im)
            output_rtl[m_out * 4 + 1] = complex(o1_re, o1_im)
            output_rtl[m_out * 4 + 2] = complex(o2_re, o2_im)
            output_rtl[m_out * 4 + 3] = complex(o3_re, o3_im)
            
            m_out += 1
            await RisingEdge(dut.i_clk)

        for k in range(N):
            exp_val = expected_output[k]
            rtl_val = output_rtl[k]
            
            tol = 2**(-nbf_out_rtl) * 2 
            
            re_match = abs(exp_val.real - rtl_val.real) <= tol
            im_match = abs(exp_val.imag - rtl_val.imag) <= tol
            
            if not (re_match and im_match):
                 cocotb.log.error(f"Mismatch at index {k}! Exp: {exp_val}, RTL: {rtl_val}")
            
            assert re_match and im_match, f"Verification failed at index {k}"
            
    cocotb.log.info(f"--- Test Vector PASSED ---")
    await RisingEdge(dut.i_clk)