"""Component correctness and checkpoint recovery; not fresh AI-video evidence."""
import io,json,math,tempfile,unittest,urllib.error,os
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio_lib.director import ACTIONS,validate,pose,verify
from studio_lib.checkpoints import Checkpoint
from studio_lib.providers import call,_UNAVAILABLE
def plan_fixture():
    return {'mechanism':'bascule_bridge','title':'Why This Bascule Bridge Lifts for Ships','hook':'A road makes room for a ship','beats':[{'action':a,'say':'This is an authored engineering fixture for checking the component rather than automatic narration quality at each independently checked stage.','camera':'mechanism' if i in (2,3,4) else 'wide'} for i,a in enumerate(ACTIONS)]}
def timeline():return {'beats':[dict(b,start=i*6,end=(i+1)*6) for i,b in enumerate(plan_fixture()['beats'])],'duration':48}
class ComponentTests(unittest.TestCase):
    def test_unsupported_topic_cannot_be_substituted(self):
        s=plan_fixture();s['mechanism']='solar';self.assertTrue(validate(s))
    def test_pump_rejects_vertical_motion_and_steady_flow_claims(self):
        from studio_lib.registry import REGISTRY
        s=plan_fixture();s['mechanism']='piston_pump'
        for b,a in zip(s['beats'],REGISTRY['piston_pump']['actions']):b['action']=a
        s['beats'][0]['say']='The piston rod pulls upward, expanding the cylinder chamber and creating low pressure ready to draw water.'
        s['beats'][7]['say']='Because each check valve only permits flow one way, backflow is prevented and the pump delivers steady water.'
        errors=validate(s)
        self.assertTrue(any('moves horizontally' in e for e in errors))
        self.assertTrue(any('pulsating' in e for e in errors))
        s['beats'][0]['say']='The piston rod moves horizontally, expanding the cylinder chamber and lowering pressure to draw source water inward.'
        s['beats'][7]['say']='The pump transfers water in pulses, while the check valves keep net flow toward the receiving reservoir.'
        self.assertFalse(any('moves horizontally' in e or 'pulsating' in e for e in validate(s)))
    def test_safety_action_order_cannot_change(self):
        s=plan_fixture();s['beats'][1]['action']='pass';self.assertTrue(validate(s))
    def test_narration_cannot_announce_motion_during_static_pivot(self):
        s=plan_fixture();s['beats'][2]['say']='The span begins to pivot while the camera shows the fixed trunnion in close detail.'
        errors=validate(s);self.assertTrue(any('static close-up' in e for e in errors));self.assertTrue(any('production or camera' in e for e in errors))
    def test_bridge_only_closes_after_ship_clears(self):
        tl=timeline();self.assertTrue(all(abs(pose(t,tl)['angle']-math.radians(72))<1e-6 for t in np.linspace(30,35.99,40)))
        self.assertGreater(pose(36,tl)['shipy']-1.6,1.0)
    def test_component_checks_and_ship_visibility(self):
        with tempfile.TemporaryDirectory() as d:verify(plan_fixture(),timeline(),Path(d))
    def test_checkpoint_rejects_corrupted_content(self):
        with tempfile.TemporaryDirectory() as d:
            c=Checkpoint('bridge',d,validator=validate,namespace='test');c.save('checked_scene',plan_fixture());self.assertIsNotNone(c.load())
            envelope=json.loads(c.path.read_text());envelope['data']['scene']['hook']='tampered';c.path.write_text(json.dumps(envelope));self.assertIsNone(c.load())
    def test_invalid_plan_cannot_be_cached_as_valid(self):
        with tempfile.TemporaryDirectory() as d:
            c=Checkpoint('bridge',d,validator=validate,namespace='test')
            with self.assertRaises(ValueError):c.save('checked_scene',{'mechanism':'unsupported'})
    def test_checkpoint_survives_provider_change(self):
        with tempfile.TemporaryDirectory() as d:
            first=Checkpoint('bridge',d,validator=validate,namespace='test');first.save('checked_scene',plan_fixture(),timeline=timeline())
            second=Checkpoint('bridge',d,validator=validate,namespace='test');self.assertEqual(second.load()['scene'],plan_fixture())
    def test_unavailable_model_is_skipped(self):
        error=urllib.error.HTTPError('https://example.invalid',404,'not found',{},io.BytesIO(b'{"error":{"message":"model not found"}}'))
        answer={'choices':[{'message':{'content':'{"ok":true}'}}]}
        _UNAVAILABLE.clear()
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test-private-key','CE_METRICS_PATH':'/nonexistent/test'},clear=True),patch('studio_lib.providers.llm._models',return_value=['models/old-flash','models/new-flash']),patch('studio_lib.providers.llm._req',side_effect=[error,answer]) as request:
            self.assertEqual(call('system','prompt'),{'ok':True});self.assertEqual(request.call_args.args[2]['model'],'gemini-flash-latest')
        _UNAVAILABLE.clear()
    def test_json_validation_refusal_retries_without_server_json_mode(self):
        error=urllib.error.HTTPError('https://example.invalid',400,'invalid JSON',{},io.BytesIO(b'{"error":{"message":"Failed to validate JSON"}}'))
        answer={'choices':[{'message':{'content':'{"errors":[]}'}}]}
        with patch.dict(os.environ,{'GROQ_API_KEY':'test-private-key','CE_METRICS_PATH':'/nonexistent/test'},clear=True),patch('studio_lib.providers.llm._models',return_value=['example']),patch('studio_lib.providers.llm._req',side_effect=[error,answer]) as request:
            self.assertEqual(call('system','prompt'),{'errors':[]});self.assertNotIn('response_format',request.call_args.args[2])
if __name__=='__main__':unittest.main()
