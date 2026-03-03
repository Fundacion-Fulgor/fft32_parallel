import numpy as np
from fxpmath import Fxp

class ROUND:
    def __init__(self, rounding='floor'):
        """
        rounding: 'floor', 'around'
        """
    def rnd(self, val, signed, n_word, n_frac, rouding):
        fxp_val = Fxp(val, 
                      signed=signed, 
                      n_word=n_word, 
                      n_frac=n_frac, 
                      rounding=rouding, 
                      overflow='saturate')
        return fxp_val.get_val()

    def crnd(self, val, signed, n_word, n_frac, rounding):
        q_r = self.rnd(val.real, signed, n_word, n_frac, rounding)
        q_i = self.rnd(val.imag, signed, n_word, n_frac, rounding)
        return complex(q_r, q_i)
    
    def crnd_vec(self, val_vec, signed, n_word, n_frac, rounding):
        result_list = [self.crnd(v, signed, n_word, n_frac, rounding) for v in val_vec]
        return result_list    

class FFT16:
    def __init__(self, N=16, fxp=0, NB_INPUT=8, NBF_INPUT=6, fft_mode=1):
        self.fxp      = fxp
        self.N        = N
        self.round    = ROUND()
        self.fft_mode = fft_mode
        self.tw_sign  = -1 if fft_mode == 1 else +1

        self.nb_i    = NB_INPUT
        self.nbf_i   = NBF_INPUT
        self.nb_tw   = 10
        self.nbf_tw  =  9
        self.nb_st1  = self.nb_i+2
        self.nbf_st1 = self.nbf_i
        self.nb_st2  = self.nb_st1
        self.nbf_st2 = self.nbf_st1
        self.nb_out  = NB_INPUT
        self.nbf_out = NBF_INPUT-3 if fft_mode == 1 else NBF_INPUT+3

        tw_float = np.exp(self.tw_sign * 1j * 2 * np.pi * np.arange(self.N) / self.N)
        tw_fxp = self.round.crnd_vec(val_vec = tw_float, signed=True,  n_word=self.nb_tw, n_frac=self.nbf_tw, rounding='around')
        self.TW16 = tw_fxp
            
    def fft4_radix4_buttefly(self, x):
        s0, s1, s2, s3 = x[0], x[1], x[2], x[3]
        
        y0_real = s0.real + s1.real + s2.real + s3.real
        y0_imag = s0.imag + s1.imag + s2.imag + s3.imag
        y0 = complex(y0_real, y0_imag)

        y2_real = s0.real - s1.real + s2.real - s3.real
        y2_imag = s0.imag - s1.imag + s2.imag - s3.imag
        y2 = complex(y2_real, y2_imag)

        if self.fft_mode == 1:
            y1_real = s0.real + s1.imag - s2.real - s3.imag
            y1_imag = s0.imag - s1.real - s2.imag + s3.real
            y1 = complex(y1_real, y1_imag)

            y3_real = s0.real - s1.imag - s2.real + s3.imag
            y3_imag = s0.imag + s1.real - s2.imag - s3.real
            y3 = complex(y3_real, y3_imag)
        else:
            y1_real = s0.real - s1.imag - s2.real + s3.imag
            y1_imag = s0.imag + s1.real - s2.imag - s3.real
            y1 = complex(y1_real, y1_imag)

            y3_real = s0.real + s1.imag - s2.real - s3.imag
            y3_imag = s0.imag - s1.real - s2.imag + s3.real
            y3 = complex(y3_real, y3_imag)

        y0 = self.round.crnd(val=y0, signed=True, n_word=self.nb_st1, n_frac=self.nbf_st1, rounding='floor')
        y1 = self.round.crnd(val=y1, signed=True, n_word=self.nb_st1, n_frac=self.nbf_st1, rounding='floor')
        y2 = self.round.crnd(val=y2, signed=True, n_word=self.nb_st1, n_frac=self.nbf_st1, rounding='floor')
        y3 = self.round.crnd(val=y3, signed=True, n_word=self.nb_st1, n_frac=self.nbf_st1, rounding='floor')
        result = [y0, y1, y2, y3]
        return result

    def fft4_radix4(self, x):
        """FFT4-Radix-4"""
        h_result = [0.0 + 1j*0.0] * self.N

        for m in range(int(self.N/4)):
            input_select = [x[m], x[m+4], x[m+8], x[m+12]]
            result_butterfly = self.fft4_radix4_buttefly(input_select)
            for k in range(int(self.N/4)):
                idx = (m * 4) + k
                value = result_butterfly[k] * self.TW16[m * k]
                h_result[idx] = self.round.crnd(val=value, signed=True, n_word=self.nb_st2, n_frac=self.nbf_st2, rounding='around')
        return h_result


    def fft4_radix2(self, x):
        """FFT4-Radix-2"""
        b0, b1, b2, b3 = x[0], x[1], x[2], x[3]

        # Stage 1
        v0_real = b0.real + b2.real
        v0_imag = b0.imag + b2.imag
        v0 = complex(v0_real, v0_imag)

        v1_real = b0.real - b2.real
        v1_imag = b0.imag - b2.imag
        v1 = complex(v1_real, v1_imag)

        v2_real = b1.real + b3.real
        v2_imag = b1.imag + b3.imag
        v2 = complex(v2_real, v2_imag)

        v3_real = b1.real - b3.real
        v3_imag = b1.imag - b3.imag
        v3 = complex(v3_real, v3_imag)        
        
        # Twiddle factor correction
        if self.fft_mode == 1:
            v3_fix_real = +v3.imag
            v3_fix_imag = -v3.real
        else:
            v3_fix_real = -v3.imag
            v3_fix_imag = +v3.real
        v3 = complex(v3_fix_real, v3_fix_imag)
        
        # Stage 2
        y0 = v0 + v2
        y1 = v1 + v3
        y2 = v0 - v2
        y3 = v1 - v3
        
        result = [y0, y1, y2, y3]

        return result

    def process(self, x):
        if len(x) != self.N:
            raise ValueError(f"Input size is different to {self.N}.")

        fft4_result = self.fft4_radix4(x)

        # FFT4 (Radix-2)
        X_out      = [0] * self.N
        FFT4_rdx2  = [0] * self.N
        FFT4_shift = [0] * 4
        FFT4_rnd   = [0] * 4
        
        for k in range(4):
            stage2_input = [fft4_result[k], fft4_result[4+k], fft4_result[8+k], fft4_result[12+k]]
            
            stage2_output = self.fft4_radix2(stage2_input)

            FFT4_rdx2[k]      = stage2_output[0]
            FFT4_rdx2[k + 4]  = stage2_output[1]
            FFT4_rdx2[k + 8]  = stage2_output[2]
            FFT4_rdx2[k + 12] = stage2_output[3]

            if self.fft_mode == 1:
                FFT4_shift[0] = stage2_output[0]
                FFT4_shift[1] = stage2_output[1]
                FFT4_shift[2] = stage2_output[2]
                FFT4_shift[3] = stage2_output[3]
            else:
                FFT4_shift[0] = stage2_output[0] / self.N
                FFT4_shift[1] = stage2_output[1] / self.N
                FFT4_shift[2] = stage2_output[2] / self.N
                FFT4_shift[3] = stage2_output[3] / self.N

            FFT4_rnd[0] = self.round.crnd(val=FFT4_shift[0], signed=True, n_word=self.nb_out, n_frac=self.nbf_out, rounding='floor')
            FFT4_rnd[1] = self.round.crnd(val=FFT4_shift[1], signed=True, n_word=self.nb_out, n_frac=self.nbf_out, rounding='floor')
            FFT4_rnd[2] = self.round.crnd(val=FFT4_shift[2], signed=True, n_word=self.nb_out, n_frac=self.nbf_out, rounding='floor')
            FFT4_rnd[3] = self.round.crnd(val=FFT4_shift[3], signed=True, n_word=self.nb_out, n_frac=self.nbf_out, rounding='floor') 

            X_out[k]      = FFT4_rnd[0]
            X_out[k + 4]  = FFT4_rnd[1]
            X_out[k + 8]  = FFT4_rnd[2]
            X_out[k + 12] = FFT4_rnd[3]

        return fft4_result, FFT4_rdx2, X_out