"""Finish a HAND-BUILT machine: studio_lib/<key>.py (real geometry) + machines/_drafts/<key>.meta.json (words, facts, subjects, cues).
Measures the motion contract and part visibility from the module, builds and validates the spec, runs the picture check, saves a contact sheet,
and with --write installs machines/<key>.json (no code inside: the spec points at the module file).
Usage: python3 tools/finish_machine.py <key> [--write]"""
import importlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
def main(argv):
 key=argv[0];write='--write' in argv
 from studio_lib import machine_writer as mw,machine_spec,director,action_contracts,picture_check
 meta=json.loads((ROOT/'machines'/'_drafts'/(key+'.meta.json')).read_text())
 module=importlib.import_module('studio_lib.'+key)
 moves,holds=mw.derive_contract(module)
 visible=mw.prove_visible(key,module,[str(p) for p in meta['parts']])
 draft=dict(meta);draft['code']=''
 spec=mw.assemble(draft,key,moves,holds,visible)
 for k in ('code','writer'):spec.pop(k,None)
 spec['block']=meta.get('block',mw.NEVER);spec['narration_rules']=meta.get('narration_rules',[]);spec['cue_bans']=meta.get('cue_bans',[])
 spec['family']=meta.get('family',key)
 if meta.get('label'):spec['label']=meta['label']
 machine_spec.validate(spec)
 print('moves',moves);print('holds',holds);print('visible',visible)
 machine_spec.install(spec,director.COMPONENTS)
 tl=mw.fixture_tl();plan={'mechanism':key,'hook':'How it works','picture_zoom':1.0}
 def picture(x,z):
  r=director.component_picture(x,tl,plan,want_scene=True,zoom_scale=z/float(plan.get('picture_zoom',1.0)));return r[0],r[1].faces
 os.environ['CE_VISION_CHECK']='off';out=Path('/tmp/mach')/key;out.mkdir(parents=True,exist_ok=True)
 try:verdict=picture_check.run(picture,tl,plan,action_contracts.CONTRACTS[key],str(out))
 except ValueError as e:print('PICTURE CHECK FAILED:',e);print('sheet',out/'picture-contact.jpg');return
 print('score',verdict['score'],'zoom',verdict['zoom'],'faces',verdict['measures']['faces'],'colours',verdict['measures']['colours'])
 print('errors',verdict.get('errors') or verdict.get('blocking') or 'none');print('sheet',out/'picture-contact.jpg')
 if write:
  (ROOT/'machines'/(key+'.json')).write_text(json.dumps(spec,indent=1)+'\n');print('WROTE machines/%s.json'%key)
if __name__=='__main__':main(sys.argv[1:])
