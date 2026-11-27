"""Find the largest zoom for beats 0 and 7 that still passes the whole-object overview rule; prints it. Usage: fit_overview.py <key>"""
import sys,importlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
def main(key):
 from studio_lib import machine_writer as mw,director,machine_spec
 mod=importlib.import_module('studio_lib.'+key);spec=json.loads((ROOT/'machines'/(key+'.json')).read_text())
 machine_spec.install(spec,director.COMPONENTS)
 tl=mw.fixture_tl();plan={'mechanism':key,'hook':'How it works','picture_zoom':1.0}
 orig=list(mod.SHOTS);best=None
 for z in [x/20 for x in range(60,19,-1)]:
  for i in (0,7):
   t,zm,fl=orig[i];mod.SHOTS[i]=(t,z,fl)
  errs=director.verify_overview(plan,tl,Path('/tmp/mach')/key)
  if not errs:best=z;break
 print(key,'best overview zoom',best)
 if best and '--apply' in sys.argv:
  z=round(best-.05,2);new=list(orig);
  for i in (0,7):new[i]=(orig[i][0],z,orig[i][2])
  f=ROOT/'studio_lib'/(key+'.py');lines=f.read_text().split('\n')
  lines=['SHOTS='+repr(new) if l.startswith('SHOTS=') else l for l in lines];f.write_text('\n'.join(lines));print('applied',z)
if __name__=='__main__':main(sys.argv[1])
