import cocotb
from cocotb.triggers import Timer
import random
import sys
from model_clip_round import ROUND

def to_signed(val, bits):
    """Convierte un entero sin signo (leído del RTL) a entero con signo (complemento a 2)."""
    v = int(val)
    if v & (1 << (bits - 1)):
        v -= (1 << bits)
    return v

def float_to_int(val, frac_bits):
    return int(round(val * (2**frac_bits)))

def int_to_float(val, frac_bits):
    return val / (2**frac_bits)


@cocotb.test()
async def test_clip_round(dut):
    
    NB_INP  = int(dut.NB_INP.value)
    NBF_INP = int(dut.NBF_INP.value)
    NB_OUT  = int(dut.NB_OUT.value)
    NBF_OUT = int(dut.NBF_OUT.value)
    RND_MD  = int(dut.RND_MD.value)

    round_mode_str = 'around' if RND_MD == 1 else 'floor'
    round_model = ROUND()
    
    cocotb.log.info(f"Parameters DUT: INP={NB_INP}.{NBF_INP}, OUT={NB_OUT}.{NBF_OUT}, MODE={round_mode_str}")

    test_cases_int = []
    
    for _ in range(100):
        val_re = random.randint(-2**(NB_INP-1), 2**(NB_INP-1)-1)
        val_im = random.randint(-2**(NB_INP-1), 2**(NB_INP-1)-1)
        test_cases_int.append((val_re, val_im))

    test_cases_int.append((0, 0))
    test_cases_int.append((2**(NB_INP-1)-1, 2**(NB_INP-1)-1))
    test_cases_int.append((-2**(NB_INP-1), -2**(NB_INP-1)))

    for i, (re_int, im_int) in enumerate(test_cases_int):
        

        re_float = int_to_float(re_int, NBF_INP)
        im_float = int_to_float(im_int, NBF_INP)
        val_complex = complex(re_float, im_float)
        
        expected_cplx = round_model.crnd(
            val=val_complex, 
            signed=True, 
            n_word=NB_OUT, 
            n_frac=NBF_OUT, 
            rounding=round_mode_str
        )
        
        dut.i_data_re.value = re_int
        dut.i_data_im.value = im_int
        
        await Timer(1, unit="ns")
        
        out_re_int = to_signed(dut.o_data_re.value, NB_OUT)
        out_im_int = to_signed(dut.o_data_im.value, NB_OUT)
        
        out_re_float = int_to_float(out_re_int, NBF_OUT)
        out_im_float = int_to_float(out_im_int, NBF_OUT)
        rtl_cplx = complex(out_re_float, out_im_float)
        
        tol = 1e-9
        re_match = abs(expected_cplx.real - rtl_cplx.real) < tol
        im_match = abs(expected_cplx.imag - rtl_cplx.imag) < tol
        
        if not (re_match and im_match):
            cocotb.log.error(f"Mismatch in Test {i}!")
            cocotb.log.error(f"Input (float) : {val_complex}")
            cocotb.log.error(f"Python Expected : {expected_cplx}")
            cocotb.log.error(f"Verilog RTL     : {rtl_cplx}")
            
        assert re_match and im_match, f"Test {i} failed."
        
    cocotb.log.info(f"All {len(test_cases_int)} tests passed successfully!")