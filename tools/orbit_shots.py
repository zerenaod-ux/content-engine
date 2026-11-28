"""Give a hand-built machine a moving camera: different side (azimuth) and tighter close-ups in the middle beats.
Usage: python3 tools/orbit_shots.py <key> [--apply]   (rewrites the SHOTS= line; beats 0,1,7 keep their tested framing)"""
import sys,importlib,re,pathlib
sys.path.insert(0,'.')
AZ=[None,None,-.45,.8,.2,-.7,.5,None]
ZM=[1,1,1.15,1.2,1.2,1.15,1.1,1]
def new_shots(mod):
 out=[]
 for i,(t,z,a) in enumerate(mod.SHOTS):
  out.append((tuple(t),round(min(3.0,z*ZM[i]),2),AZ[i] if AZ[i] is not None else a))
 return out
if __name__=='__main__':
 key=sys.argv[1];mod=importlib.import_module('studio_lib.'+key);s=new_shots(mod)
 print(s)
 if '--apply' in sys.argv:
  p=pathlib.Path('studio_lib/%s.py'%key);t=p.read_text()
  t2=re.sub(r'^SHOTS=.*$','SHOTS='+repr(s),t,count=1,flags=re.M)
  assert t2!=t;p.write_text(t2);print('applied')
