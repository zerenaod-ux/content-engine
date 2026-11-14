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
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_CACHE_DIR':str(Path(d)/'cache'),'CE_METRICS_PATH':str(Path(d)/'metrics.json'),'CE_REPAIR_CONTEXT':''}):
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

    def test_demonstration_can_focus_on_light_instead_of_forced_object_hook(self):
        from scene_lib.validate import check
        s=json.loads(Path('tests/fixtures/rainbow-rejected.json').read_text())
        s['steps'][0]['shows']='ray'
        self.assertFalse(any('main object of the video must' in e for e in check(s)))

    def test_declarations_compile_into_real_animation_and_reject_conflicts(self):
        from scene_lib.evidence import compile_animation
        original=contract(); original['parts'][0]['progress']=0
        original['parts'][0]['color']='#ffffff'
        compiled=compile_animation(original)
        self.assertEqual(0,original['parts'][0]['progress'])
        self.assertEqual(.5,value_at(compiled['parts'][0]['progress'],2.5))
        self.assertEqual('#ffffff',compiled['parts'][0]['color'])
        self.assertEqual([],check_contract(compiled))
        original['parts'][0]['progress']=[[0,0],[5,1],[6,0]]
        self.assertEqual([6,0],compile_animation(original)['parts'][0]['progress'][-1])
        conflicting=copy.deepcopy(original['steps'][0])
        conflicting['evidence'][0]['values']=[1,0]
        original['steps'].append(conflicting)
        with self.assertRaises(ValueError): compile_animation(original)

    def test_duration_fit_preserves_variable_pacing_without_another_call(self):
        from scene_lib.writer import normalize_plan
        source={'steps':[{'seconds':s} for s in [2,4,3,2,1,3]]}
        fixed=normalize_plan(source)
        self.assertEqual(2,source['steps'][0]['seconds'])
        self.assertEqual(45,round(timeline(fixed)[-1][1]+.3,2))
        self.assertAlmostEqual(2,fixed['steps'][1]['seconds']/fixed['steps'][0]['seconds'],places=2)
        long={'steps':[{'seconds':15} for _ in range(8)]}
        self.assertEqual(65,round(timeline(normalize_plan(long))[-1][1]+.3,2))

    def test_static_contrast_members_are_all_render_requirements(self):
        from scene_lib.evidence import render_requirements
        s=contract()
        s['parts'][0]['color']='#ff0000'
        s['parts'].append({'type':'line','id':'comparison','pts':[[0,20],[100,20]],'color':'#0000ff'})
        s['steps'][0]['contrasts']=[{'parts':['ray','comparison'],'fields':['color','pts']}]
        self.assertEqual([],check_contract(s))
        requirements=render_requirements(s)
        self.assertEqual(['ray','comparison'],[e['part'] for e in requirements])
        self.assertEqual('contrast',requirements[1]['field'])
        self.assertEqual([0,5],requirements[1]['at'])

    def test_simple_plan_does_not_need_filler_cast_or_causal_links(self):
        p={'principle':'Light changes direction when it crosses between different transparent materials.',
           'style':'icons','setting':{'preset':'lab','ground':'none'},
           'basis':{'status':'model_knowledge_unverified','limitations':'Schematic'},
           'chain':['Light reaches the boundary','Its direction changes'],
           'cast':[{'id':'object','x0':-100,'x1':100,'y0':0,'y1':200}],
           'steps':[{'label':'Boundary','say':'The light changes direction at this boundary.',
                     'shows':'object','seconds':8,'demonstration':'A visible ray changes direction.'} for _ in range(6)]}
        self.assertEqual([],check_plan(p))

    def test_rate_limit_stops_wasting_calls_on_same_provider(self):
        import llm, urllib.error
        from email.message import Message
        headers=Message();headers['Retry-After']='120'
        failure=urllib.error.HTTPError('https://example.invalid/models',429,'limited',headers,None)
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_METRICS_PATH':str(Path(d)/'metrics.json'),'CE_MAX_REQUESTS':'16'}):
            with patch('urllib.request.urlopen',side_effect=failure) as network:
                with self.assertRaises(urllib.error.HTTPError): llm._req('https://example.invalid/models','unused')
                with self.assertRaises(llm.ProviderCoolingDown): llm._req('https://example.invalid/chat/completions','unused')
                self.assertEqual(1,network.call_count)
                ledger=json.loads((Path(d)/'metrics.json').read_text())
                self.assertEqual(1,ledger['requests'])
                self.assertEqual(1,ledger['http_statuses']['429'])
                self.assertGreater(ledger['rate_limits']['example.invalid']['retry_at'],ledger['started_at'])

    def test_budget_stops_before_network(self):
        import llm
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_METRICS_PATH':str(Path(d)/'metrics.json'),'CE_MAX_REQUESTS':'0'}):
            with patch('urllib.request.urlopen') as network:
                with self.assertRaises(llm.BudgetExceeded): llm._req('https://example.invalid','unused')
                network.assert_not_called()

    def test_request_ledger_spans_calls_and_records_usage(self):
        import llm
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return b'{"usage":{"total_tokens":17}}'
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CE_METRICS_PATH':str(Path(d)/'metrics.json'),'CE_MAX_REQUESTS':'1'}):
            with patch('urllib.request.urlopen',return_value=Response()) as network:
                llm._req('https://example.invalid','unused')
                with self.assertRaises(llm.BudgetExceeded): llm._req('https://example.invalid','unused')
                self.assertEqual(1,network.call_count)
                ledger=json.loads((Path(d)/'metrics.json').read_text())
                self.assertEqual(17,ledger['usage']['total_tokens'])
                self.assertEqual(1,ledger['responses'])
                # A new call reads the persisted ledger rather than resetting it.
                ledger['requests']=0;ledger['started_at']=0
                (Path(d)/'metrics.json').write_text(json.dumps(ledger))
                with self.assertRaises(llm.BudgetExceeded): llm._req('https://example.invalid','unused')
                self.assertEqual(1,network.call_count)

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
