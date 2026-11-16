"""Offline behavior tests, not automatic-generation or editorial evidence."""
import copy,tempfile,unittest,json,os,time,urllib.error
from unittest.mock import patch
from pathlib import Path
import numpy as np
from studio_lib.schema import check
from studio_lib.render import transforms,frame
from studio_lib.check import provisional,inspect
from studio_lib.providers import call
def fixture():
    # Authored engineering fixture only. Never read by the topic generation path.
    words='You can follow this moving component as it carries the load across the mechanism and returns to its starting position.'
    return {'title':'How This Test Mechanism Moves Safely','hook':'A motion test','principle':'This fixture tests rendering and validation rather than explaining a factual topic.','setting':'studio','objects':[
        {'id':'body','position':[0,0,1], 'meshes':[{'type':'box','at':[0,0,0],'size':[4,1,.5],'color':[70,100,120]}]},
        {'id':'shaft','position':[0,-1,2],'meshes':[{'type':'gear','at':[0,0,0],'radius':.8,'teeth':20,'color':[230,165,75]}],'motion':{'angle':[[0,0],[5,540]]}},
        {'id':'marker','parent':'shaft','position':[.5,0,0],'meshes':[{'type':'box','at':[0,0,0],'size':[.2,.2,.2],'color':[250,100,40]}]}
        ],'beats':[{'say':words,'seconds':9,'focus':['body','shaft'],'evidence':['shaft'],'demonstration':'The shaft rotates and carries the attached marker.'} for _ in range(5)]}
class StudioTests(unittest.TestCase):
    def test_fixture_schema(self):self.assertEqual(check(fixture()),[])
    def test_cycle_rejected(self):
        s=fixture();s['objects'][1]['parent']='marker';self.assertTrue(any('cyclic' in x for x in check(s)))
    def test_nan_rejected(self):
        s=fixture();s['objects'][0]['position'][0]=float('nan');self.assertTrue(check(s))
    def test_unsupported_motion_rejected(self):
        s=fixture();s['objects'][1]['motion']['python']='arbitrary code';self.assertTrue(check(s))
    def test_child_follows_rigid_parent(self):
        s=fixture();s['objects'][1]['motion']['angle']=[[0,0],[1,90],[5,90]]
        matrices,_=transforms(s,1);self.assertTrue(np.allclose(matrices['marker'][:3,3],[0,-1,2.5]))
    def test_removed_parent_removes_child(self):
        s=fixture();tl=provisional(s);self.assertFalse(np.array_equal(np.asarray(frame(s,5,tl)),np.asarray(frame(s,5,tl,hidden=('shaft',)))))
    def test_static_scene_fails_motion_gate(self):
        s=fixture();s['objects'][1]['motion']={}
        with tempfile.TemporaryDirectory() as folder:
            errors=inspect(s,provisional(s),Path(folder));self.assertTrue(any('no visible object motion' in x for x in errors))
    def test_occluded_or_invisible_evidence_rejected(self):
        s=fixture();s['objects'][1]['motion']['visible']=[[0,0],[5,0]]
        with tempfile.TemporaryDirectory() as folder:
            errors=inspect(s,provisional(s),Path(folder));self.assertTrue(any('visible pixels' in x for x in errors))
    def test_provider_waits_for_known_reset_before_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger=Path(folder)/'metrics.json';ledger.write_text(json.dumps({'rate_limits':{'api.groq.com':{'retry_at':time.time()+10}}}))
            with patch.dict(os.environ,{'GROQ_API_KEY':'test-not-a-real-key','CE_METRICS_PATH':str(ledger)},clear=True),patch('studio_lib.providers.llm._models',return_value=['example']),patch('studio_lib.providers.llm._req',return_value={'choices':[{'message':{'content':'{"ok":true}'}}]}) as request,patch('studio_lib.providers.time.sleep') as sleep:
                self.assertEqual(call('system','prompt'),{'ok':True});self.assertEqual(request.call_count,1);self.assertGreater(sleep.call_args[0][0],9)
    def test_empty_provider_answer_is_not_success(self):
        with patch.dict(os.environ,{'GROQ_API_KEY':'test-not-a-real-key','CE_METRICS_PATH':'/nonexistent/test'},clear=True),patch('studio_lib.providers.llm._models',return_value=['example']),patch('studio_lib.providers.llm._req',return_value={'choices':[{'message':{'content':''}}]}):
            with self.assertRaisesRegex(ValueError,'empty answer'):call('system','prompt')
if __name__=='__main__':unittest.main()
