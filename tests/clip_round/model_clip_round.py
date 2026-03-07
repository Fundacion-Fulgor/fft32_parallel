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