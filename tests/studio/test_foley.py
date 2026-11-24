import unittest
import numpy as np
from studio_lib import foley

class M:
    @staticmethod
    def state(t,tl):
        b=min(7,next((i for i,x in enumerate(tl['beats']) if t<x['end']),7))
        return {'beat':b,'turn':(t-tl['beats'][2]['start'])*6 if b==2 else (6*5 if b>2 else 0.),'still':1.0}
TL={'duration':20,'beats':[{'start':i*2.5,'end':i*2.5+2.5} for i in range(8)]}

class FoleyTests(unittest.TestCase):
 def test_ticks_only_while_the_part_moves(self):
     ev=foley.events(M,TL);ticks=[e for e in ev if e[1]=='tick']
     self.assertTrue(ticks and all(5.0<=e[0]<=7.6 for e in ticks))           # beat 2 only
     self.assertTrue({e[1] for e in ev}>={'clunk','clack','tick'})

 def test_render_and_mix_stay_in_range_and_duck_under_voice(self):
     f=foley.render(M,TL,'x');self.assertTrue(f.shape[0]>=20*foley.SR and abs(f).max()<=1.0001)
     v=np.zeros(len(f));v[6*foley.SR:7*foley.SR]=.7*np.sin(np.arange(foley.SR)/10)
     m=foley.mix(v,f);self.assertLess(abs(m).max(),1.2)
     quiet=np.zeros(len(f));self.assertGreater(np.abs(foley.mix(quiet,f)).max(),np.abs(foley.mix(v,f)-v)[6*foley.SR:7*foley.SR].max())   # ducked while speaking

if __name__=='__main__':unittest.main()
