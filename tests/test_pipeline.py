import copy
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scene_lib.evidence import check_contract, value_at
from scene_lib.writer import check_plan, plan_prompt, stage_prompt, tidy, timeline
from scene_lib.pipeline import StageCache
from scene_lib.ideas import too_close


def contract():
    return {'evidence_version': 1, 'basis': {'status':'model_knowledge_unverified','limitations':'Simplified diagram'},
            'parts':[{'id':'ray','type':'line','pts':[[0,0],[100,0]],'progress':[[0,0],[5,1]]}],
            'steps':[{'start':0,'end':5,'demonstration':'A visible ray reaches the surface',
                      'evidence':[{'part':'ray','field':'progress','at':[0,5],'values':[0,1]}]}]}


class PipelineTests(unittest.TestCase):
    def test_contract_catches_missing_and_fake_motion(self):
        s = contract(); self.assertEqual([],check_contract(s))
        s['parts'][0]['progress'] = 0
        self.assertTrue(any('does not match' in e for e in check_contract(s)))
        s = contract(); s['steps'][0]['evidence'][0]['part'] = 'imaginary'
        self.assertTrue(check_contract(s))
        s = contract(); s['steps'][0]['evidence'][0]['at'] = [-1,5]
        self.assertTrue(check_contract(s))
        s = contract(); s['steps'][0]['evidence'] = []
        self.assertTrue(check_contract(s))

    def test_interpolation_and_nan(self):
        self.assertEqual(0.5,value_at([[0,0],[4,1]],2))
        self.assertEqual(0.15625,value_at([[0,0],[4,1]],1))
        self.assertIsNone(value_at([[2,0],[1,1]],2))
        s = contract(); s['steps'][0]['evidence'][0]['values'][0] = float('nan')
        self.assertTrue(check_contract(s))

    def test_variable_timing_and_prompts(self):
        p = {'steps':[{'seconds':x} for x in [4,8,6,7,5,9,10]]}
        self.assertEqual((4.5,12.5),timeline(p)[1])
        self.assertIn('5 to 12 beats',plan_prompt('Why do things happen'))
        self.assertIn('evidence',stage_prompt('Why',p))
        self.assertNotIn('7 sentences',stage_prompt('Why',p))

    def test_natural_narration_legacy_fixture(self):
        from scene_lib.validate import check
        s = json.loads(Path('scenes/hydro-dam.json').read_text())
        for st in s['steps']: st['say'] = st['say'].rstrip('!?') + '.'
        self.assertFalse(any('script is flat' in e for e in check(s)))

    def test_cache_rechecks_and_invalidates(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_CACHE_DIR':d}):
            c = StageCache('one topic'); c.save('plan',{'ok':True})
            self.assertEqual({'ok':True}, c.accepted('plan',lambda s: []))
            self.assertIsNone(c.accepted('plan',lambda s:['rejected']))
            self.assertIsNone(StageCache('different topic').accepted('plan',lambda s:[]))
            with patch('scene_lib.pipeline.fingerprint',return_value='changed source'):
                self.assertIsNone(StageCache('one topic').accepted('plan',lambda s:[]))

    def test_failure_does_not_ban_subject(self):
        idea={'topic':'Why rainbows appear opposite the sun','subject':'rainbow','keywords':['light','rain','observer']}
        self.assertEqual('',too_close(idea,[{**idea,'failed':True}]))
        self.assertTrue(too_close(idea,[idea]))
        other={**idea,'topic':'How polarized glasses reduce reflected glare','keywords':['polarized','glasses','reflection']}
        self.assertEqual('',too_close(other,[idea]))

    def test_camera_uses_measured_svg_geometry(self):
        from scene_lib.validate import _box_at
        p={'type':'path','d':'M 200 200 A 200 200 0 0 1 600 200','x':0,'y':0}
        bounds={p['d']:[200,0,400,200]}
        box=_box_at(p,0,bounds)
        self.assertLessEqual(box[0],200)
        self.assertGreaterEqual(box[1],600)
        self.assertLessEqual(box[2],-200)
        self.assertGreaterEqual(box[3],0)
        self.assertNotEqual(box,_box_at(p,0))

    def test_rainbow_requires_separate_colour_paths(self):
        from scene_lib.validate import check
        s=json.loads(Path('tests/fixtures/rainbow.json').read_text())
        self.assertEqual([],check(s))
        # The reviewed automatic failure: one red line cannot satisfy a spectrum.
        bad=copy.deepcopy(s)
        bad['parts']=[p for p in bad['parts'] if p.get('id') != 'inside1']
        self.assertTrue(check_contract(bad))
        bad=copy.deepcopy(s)
        for p in bad['parts']:
            if p.get('id','').startswith('inside'): p['color']='#ff554e'
        self.assertTrue(any('distinct color' in e for e in check_contract(bad)))

    def test_repair_preserves_untouched_parts_and_timing(self):
        from scene_lib.repair import apply_patch
        s=json.loads(Path('tests/fixtures/rainbow.json').read_text())
        original=copy.deepcopy(s)
        p=copy.deepcopy(next(p for p in s['parts'] if p.get('id')=='inside0'))
        p['w']=2
        changed=apply_patch(s,{'replace_parts':{'inside0':p}})
        self.assertEqual(s,original)
        self.assertEqual(s['steps'],changed['steps'])
        self.assertEqual(s['music'],changed['music'])
        for old,new in zip(s['parts'],changed['parts']):
            if old.get('id') != 'inside0': self.assertEqual(old,new)
        with self.assertRaises(ValueError): apply_patch(s,{'step_updates':[{'index':0,'start':99}]})
        with self.assertRaises(ValueError): apply_patch(s,{'replace_parts':{'missing':p}})

    def test_narration_partial_failure_reuses_completed_lines(self):
        import wave
        from scene_lib import audio as A
        import local_voice
        lines=[(0,1,'First sentence'),(1.2,2.2,'Second sentence')]
        prior=Path.cwd()
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_CACHE_DIR':str(Path(d)/'cache'),'SCENE_VOICE':'test-voice'}):
            os.chdir(d)
            try:
                calls=[]
                def synth(jobs):
                    job=jobs[0];calls.append(job['text'])
                    if len(calls)==2: raise RuntimeError('temporary failure')
                    with wave.open(job['wav'],'wb') as w:
                        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\x01\x00'*4800)
                    Path(job['timing']).write_text(json.dumps({'duration':.2}))
                with patch.object(local_voice,'edge_run',side_effect=synth):
                    with self.assertRaises(RuntimeError): A.speak(lines)
                    calls.clear()
                    # The first line survived the second line's failure.
                    _,log=A.speak(lines)
                    self.assertEqual(['Second sentence'],calls)
                    self.assertIn('1 cached, 1 synthesized',log[0])
                with patch.object(local_voice,'edge_run',side_effect=AssertionError('network must not run')):
                    _,log=A.speak(lines)
                    self.assertIn('2 cached, 0 synthesized',log[0])
            finally: os.chdir(prior)

    def test_finished_cache_reuses_and_rejects_corruption(self):
        import subprocess
        from scene_lib.build import main, result_key, digest
        spec=json.loads(Path('tests/fixtures/rainbow.json').read_text())
        prior=Path.cwd()
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_CACHE_DIR':str(Path(d)/'cache'),'CE_METRICS_PATH':str(Path(d)/'metrics.json')}):
            path=Path(d)/'scene.json';path.write_text(json.dumps(spec))
            cache=Path(d)/'cache/results'/result_key(spec);cache.mkdir(parents=True)
            (cache/'video.mp4').write_bytes(b'cached-result')
            (cache/'scene.json').write_text(json.dumps(spec))
            (cache/'evidence-report.json').write_text(json.dumps({'errors':[],'semantic_verification':False}))
            (cache/'metadata.json').write_text(json.dumps({n:digest(cache/n) for n in ['video.mp4','scene.json','evidence-report.json']}))
            os.chdir(d)
            try:
                with patch('subprocess.run',side_effect=AssertionError('render/network must not run')):
                    main(str(path),'out.mp4')
                self.assertEqual(b'cached-result',Path('out.mp4').read_bytes())
                self.assertTrue(json.loads(Path('metrics.json').read_text())['result_cache_hit'])
                (cache/'video.mp4').write_bytes(b'corrupt')
                with patch('subprocess.run',side_effect=subprocess.CalledProcessError(1,'render')) as run:
                    with self.assertRaises(subprocess.CalledProcessError): main(str(path),'second.mp4')
                    run.assert_called_once()
                self.assertFalse(Path('second.mp4').exists())
            finally: os.chdir(prior)

    def test_wide_view_focuses_legible_evidence_without_rewriting_claim(self):
        from scene_lib.writer import auto_camera
        s=contract(); s['duration']=5.3
        s['parts'].append({'type':'ellipse','id':'endpoint','x':100,'y':0,'rx':10,'ry':20})
        s['steps'][0]['say']='A ray reaches the surface.'
        s['steps'][0]['shows']='endpoint'
        s['parts'][0]['pts']=[[-400,0],[100,0]]
        auto_camera(s)
        self.assertEqual('ray',s['steps'][0]['shows'])
        self.assertEqual('A ray reaches the surface.',s['steps'][0]['say'])

    def test_budget_stops_before_network(self):
        import llm
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_METRICS_PATH':str(Path(d)/'metrics.json'),'CE_MAX_REQUESTS':'0'}):
            with patch('urllib.request.urlopen') as network:
                with self.assertRaises(llm.BudgetExceeded): llm._req('https://example.invalid','unused')
                network.assert_not_called()

    def test_hidden_rendered_evidence_is_rejected(self):
        from PIL import Image
        from scene_lib.check_frames import inspect
        s=contract()
        with tempfile.TemporaryDirectory() as d:
            frames=Path(d); (frames/'evidence').mkdir()
            im=Image.new('RGB',(720,1280),'white')
            im.save(frames/'0075.jpg')
            for k in [0,1]:
                for variant in ['actual','removed']: im.save(frames/('evidence/0-0-%d-%s.jpg'%(k,variant)))
            (frames/'evidence/manifest.json').write_text(json.dumps([{'step':1,'part':'ray','field':'progress','files':['0-0-0','0-0-1']}]))
            report=inspect(s,frames)
            self.assertFalse(report['semantic_verification'])
            self.assertTrue(any('absent' in e for e in report['errors']))

if __name__ == '__main__': unittest.main()
