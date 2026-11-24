import copy,json,tempfile,unittest
from pathlib import Path
from studio_lib import machine_spec as ms,action_contracts,narration_timing
from studio_lib.registry import REGISTRY
from studio_lib.director import verify_component,COMPONENTS
from studio_lib.topic_scope import scope_error

SPECS=sorted(ms.SPEC_DIR.glob('*.json'))

class MachineSpecs(unittest.TestCase):
 def spec(self):return json.loads((ms.SPEC_DIR/'ratchet_wrench.json').read_text())
 def test_every_spec_file_installs_cleanly(self):
  self.assertTrue(SPECS)
  ms.load_all(COMPONENTS)
  self.assertEqual(ms._STATE.get('problems'),{})
  for f in SPECS:
   key=f.stem;self.assertIn(key,REGISTRY);self.assertIn(key,COMPONENTS);self.assertIn(key,action_contracts.CONTRACTS);self.assertIn(key,narration_timing.TRANSITIONS)
 def test_each_spec_machine_passes_real_motion_and_visibility_preflight(self):
  for f in SPECS:
   key=f.stem
   with self.subTest(key=key),tempfile.TemporaryDirectory() as folder:
    tl={'beats':[{'start':i*6,'end':(i+1)*6,'action':a,'camera':'wide','say':'Engineering test fixture only'} for i,a in enumerate(REGISTRY[key]['actions'])],'duration':48,'motion_policy':'fixture'}
    verify_component({'mechanism':key,'beats':tl['beats'],'hook':'Engineering check'},tl,Path(folder))
 def test_bad_specs_are_refused_with_a_plain_reason(self):
  good=self.spec();ms.validate(good)
  cases={
   'missing field':lambda s:s.pop('facts'),
   'bad regex':lambda s:s.update(detect='(unclosed'),
   'wrong action count':lambda s:s.update(actions=s['actions'][:7]),
   'fact for unknown action':lambda s:s['facts'].update(extra='x'*40),
   'transition not an action':lambda s:s.update(transitions=['nonsense']),
   'move and hold same channel':lambda s:s['contract']['holds'].update({'2':['handle']}),
   'http source':lambda s:s.update(source='http://example.com'),
   'anchors mismatch':lambda s:s['anchors'].pop('cutaway'),
  }
  for name,mutate in cases.items():
   with self.subTest(name):
    bad=copy.deepcopy(good);mutate(bad)
    with self.assertRaises(ms.SpecError):ms.validate(bad)
 def test_family_already_taken_is_refused_and_nothing_is_registered(self):
  bad=self.spec();bad.update(key='ratchet_twin');bad['family']='pendulum_escapement'
  with self.assertRaises(ms.SpecError):ms.install(bad)
  self.assertNotIn('ratchet_twin',REGISTRY)
 def test_spec_narration_rules_and_cue_bans_are_enforced(self):
  plan={'mechanism':'ratchet_wrench','beats':[{'say':'The wrench handle'}]*8}
  plan['beats']=[dict(b) for b in plan['beats']];plan['beats'][3]['say']='The handle swings back and the bolt turns again with it'
  self.assertTrue(any('bolt holds still' in e for e in action_contracts.narration_errors(plan)))
  cue={'mechanism':'ratchet_wrench','beats':[{'action':'cutaway','say':'The pawl is shown in cutaway now','motion_cue':'the pawl is'}]+[{'action':'x','say':''}]*7}
  self.assertTrue(any('pawl' in e for e in narration_timing.cue_errors(cue)))
 def test_spec_topic_limits_and_detection(self):
  self.assertEqual(scope_error('How does a ratchet wrench turn a bolt one way?'),'')
  self.assertTrue(scope_error('How does a cordless ratchet wrench work?'))
 def test_spec_caption_label_is_registered(self):
  self.assertIn('ratchet_wrench',ms.LABELS)
if __name__=='__main__':unittest.main()

class Scaffold(unittest.TestCase):
 def test_new_machine_scaffold_is_refused_until_finished_then_installs_and_passes_preflight(self):
  import sys,importlib,re
  from tools import new_machine
  key='scaffold_demo_machine'
  mod=new_machine.ROOT/'studio_lib'/(key+'.py');draft=new_machine.ROOT/'machines'/'_drafts'/(key+'.json')
  try:
   new_machine.main([key,'Scaffold demo','--family','scaffold_demo_family'])
   spec=json.loads(draft.read_text())
   with self.assertRaises(ms.SpecError):ms.validate(spec)
   def finish(v,name=''):
    if isinstance(v,dict):return {k:finish(i,k) for k,i in v.items()}
    if isinstance(v,list):return [finish(i,name) for i in v]
    if isinstance(v,str) and 'TODO' in v:
     return {'pattern':r'\bscaffoldgizmo\b','detect':'scaffoldgizmo','block':'motorised','source':'https://example.org/gizmo'}.get(name,'A plain sentence about gizmo, gear and spring parts and what stays hidden.' if len(v)>20 else 'gizmo|gear|spring')
    return v
   done=finish(spec);done['anchors']['payoff']='gizmo|gear';text=json.dumps(done)
   self.assertNotIn('TODO',text)
   key_in=ms.install(done);self.assertEqual(key_in,key)
   COMPONENTS[key]=importlib.import_module('studio_lib.'+key)
   with tempfile.TemporaryDirectory() as folder:
    tl={'beats':[{'start':i*6,'end':(i+1)*6,'action':a,'camera':'wide','say':'Engineering test fixture only'} for i,a in enumerate(done['actions'])],'duration':48,'motion_policy':'fixture'}
    verify_component({'mechanism':key,'beats':tl['beats'],'hook':'Engineering check'},tl,Path(folder))
  finally:
   for p in (mod,draft):
    if p.exists():p.unlink()
   from studio_lib import novelty,topic_scope
   for d in (REGISTRY,action_contracts.CONTRACTS,narration_timing.TRANSITIONS,narration_timing.ANCHORS,novelty.FAMILIES,novelty.PATTERNS,topic_scope.SPEC_DETECT,topic_scope.SPEC_BLOCK,ms.SPECS,COMPONENTS):d.pop(key,None)
   sys.modules.pop('studio_lib.'+key,None)
