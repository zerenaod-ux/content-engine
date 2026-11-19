import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from studio_lib import narration_timing as timing
from studio_lib import solar,pump,wind
from studio_lib.director import pose,verify_overview,verify_component
from studio_lib.topic_scope import scope_error
from unittest.mock import patch
from test_components import plan_fixture,timeline

class NarrationTimingTests(unittest.TestCase):
    def bind_fixture(self,folder):
        voice=Path(folder)/'voice.wav';voice.write_bytes(b'fixture only, never production audio')
        plan={'mechanism':'bascule_bridge','beats':[{'action':'balance','say':'The bridge rises while its heavy counterweight descends.','motion_cue':'bridge rises'}]}
        tl={'beats':[dict(plan['beats'][0],start=10.,end=16.,voice=str(voice),voice_duration=5.)]}
        words=[{'text':s,'start':a,'end':b} for s,a,b in [('The',0.,.2),('bridge',1.,1.4),('rises',1.4,2.),('while',2.,2.3)]]
        return plan,tl,Mock(return_value=words)

    def test_uses_measured_phrase_not_guessed_word_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            plan,tl,recognize=self.bind_fixture(folder);result=timing.bind(plan,tl,folder,recognize)
            self.assertAlmostEqual(result['beats'][0]['motion_window'][0],10.73)
            report=json.loads((Path(folder)/'spoken-action-timing.json').read_text())
            self.assertAlmostEqual(report['cues'][0]['spoken_start'],11.08)
            self.assertEqual(result['motion_policy'],timing.VERSION)

    def test_missing_or_repeated_exact_phrase_holds(self):
        with tempfile.TemporaryDirectory() as folder:
            plan,tl,recognize=self.bind_fixture(folder)
            recognize.return_value=[]
            with self.assertRaisesRegex(ValueError,'uniquely'):timing.bind(plan,tl,folder,recognize)
            plan['beats'][0]['say']='bridge rises then bridge rises'
            self.assertTrue(timing.cue_errors(plan))

    def test_cue_function_word_repair_preserves_every_spoken_word(self):
        original={'beats':[{'say':'The span seats, barriers lift, and the car crosses.','motion_cue':'span seats and barriers lift'}]}
        fixed=timing.normalize_cues(original)
        self.assertEqual(fixed['beats'][0]['say'],original['beats'][0]['say'])
        self.assertEqual(fixed['beats'][0]['motion_cue'],'span seats, barriers lift')
        self.assertEqual(original['beats'][0]['motion_cue'],'span seats and barriers lift')
        original['beats'][0]['motion_cue']='span does not seat'
        self.assertEqual(timing.normalize_cues(original),original)

    def test_unshown_bearing_friction_topic_is_rejected_before_media(self):
        self.assertTrue(scope_error('How the trunnion bearing reduces friction during a bascule bridge lift','bascule_bridge'))
        self.assertFalse(scope_error('How a bascule bridge counterweight balances the moving road','bascule_bridge'))

    def test_passage_cue_names_the_moving_vessel_not_the_static_road(self):
        original={'mechanism':'bascule_bridge','beats':[{'action':'pass','say':'The road stays fully raised as the vessel glides through the channel.','motion_cue':'road stays fully raised'}]}
        fixed=timing.normalize_cues(original)
        self.assertEqual(fixed['beats'][0]['say'],original['beats'][0]['say'])
        self.assertIn('vessel glides',fixed['beats'][0]['motion_cue'])

    def test_resume_reuses_only_matching_audio_and_phrase(self):
        with tempfile.TemporaryDirectory() as folder:
            plan,tl,recognize=self.bind_fixture(folder);timing.bind(plan,tl,folder,recognize)
            timing.bind(plan,tl,folder,recognize);self.assertEqual(recognize.call_count,1)
            Path(tl['beats'][0]['voice']).write_bytes(b'changed audio')
            timing.bind(plan,tl,folder,recognize);self.assertEqual(recognize.call_count,2)

    def test_gate_rejects_changed_action_window_or_voice(self):
        with tempfile.TemporaryDirectory() as folder:
            plan,tl,recognize=self.bind_fixture(folder);plan['motion_policy']=timing.VERSION
            timing.bind(plan,tl,folder,recognize);timing.require_bound(plan,tl,folder,verify_audio=True)
            saved=tl['beats'][0]['motion_window'];tl['beats'][0]['motion_window']=[10,16]
            with self.assertRaisesRegex(ValueError,'does not use'):timing.require_bound(plan,tl,folder)
            tl['beats'][0]['motion_window']=saved;Path(tl['beats'][0]['voice']).write_bytes(b'different audio')
            with self.assertRaisesRegex(ValueError,'Voice changed'):timing.require_bound(plan,tl,folder,verify_audio=True)

    def test_bad_word_time_and_mismatched_saved_speech_hold(self):
        with tempfile.TemporaryDirectory() as folder:
            plan,tl,recognize=self.bind_fixture(folder)
            recognize.return_value=[{'text':'bridge','start':float('nan'),'end':2}]
            with self.assertRaisesRegex(ValueError,'invalid'):timing.bind(plan,tl,folder,recognize)
            tl['beats'][0]['say']='different accepted words'
            with self.assertRaisesRegex(ValueError,'does not match'):timing.bind(plan,tl,folder,recognize)

    def test_bridge_holds_until_spoken_action_but_camera_keeps_its_clock(self):
        tl=timeline();b=tl['beats'][3];b['motion_window']=[b['start']+2,b['end']-.2]
        self.assertEqual(pose(b['start']+1,tl)['angle'],0)
        self.assertGreater(pose(b['start']+3,tl)['angle'],0)
        self.assertNotEqual(pose(b['start']+.1,tl)['zoom'],pose(b['start']+1,tl)['zoom'])

    def test_switch_waits_for_its_cue(self):
        tl=timeline();b=tl['beats'][5];b['motion_window']=[b['start']+2,b['end']]
        self.assertFalse(solar.pose(b['start']+1,tl)['current'])
        self.assertTrue(solar.pose(b['start']+3,tl)['current'])

    def test_continuous_rotor_is_not_paused_by_switch_cue(self):
        tl=timeline();b=tl['beats'][6];b['motion_window']=[b['start']+2,b['end']]
        a=wind.pose(b['start']+.2,tl);z=wind.pose(b['start']+1,tl)
        self.assertFalse(z['closed']);self.assertNotEqual(a['angle'],z['angle'])
        self.assertEqual(z['angle'],z['shaft_angle']);self.assertEqual(z['angle'],z['magnet_angle'])
        self.assertTrue(wind.pose(b['start']+3,tl)['closed'])

    def test_pump_withdrawal_waits_and_valves_stay_coupled(self):
        tl=timeline();b=tl['beats'][2];b['motion_window']=[b['start']+2,b['end']]
        before=pump.phase(b['start']+1,tl);after=pump.phase(b['start']+3,tl)
        self.assertAlmostEqual(before['piston_x'],.1);self.assertFalse(before['intake'])
        self.assertLess(after['piston_x'],before['piston_x']);self.assertTrue(after['intake']);self.assertFalse(after['delivery'])

    def test_whole_object_overviews_fit_before_internal_closeups(self):
        for mechanism in ('photovoltaic_cell','piston_pump','wind_turbine'):
            with self.subTest(mechanism=mechanism),tempfile.TemporaryDirectory() as folder:
                tl=timeline();tl['motion_policy']=timing.VERSION
                self.assertEqual(verify_overview({'mechanism':mechanism},tl,Path(folder)),[])

    def test_cropped_overview_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder,patch('studio_lib.solar.shot',return_value=((0,0,2),8,.3)):
            self.assertTrue(verify_overview({'mechanism':'photovoltaic_cell'},timeline(),Path(folder)))

    def test_component_audit_uses_delayed_stroke_cues(self):
        from test_library import fixture,timeline as component_timeline
        plan=fixture('piston_pump');tl=component_timeline('piston_pump');tl['motion_policy']=timing.VERSION
        for i in (1,2,4,7):
            beat=tl['beats'][i];beat['motion_window']=[beat['start']+1.5,beat['end']-.2]
        with tempfile.TemporaryDirectory() as folder:verify_component(plan,tl,Path(folder))

if __name__=='__main__':unittest.main()
