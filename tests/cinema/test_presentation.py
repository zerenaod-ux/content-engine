import json,math,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
from studio_lib.cinema.presentation import camera_pose,rotor_angle,illustration_labels
from studio_lib.cinema.build import soundtrack,captions,contract

class PresentationTests(unittest.TestCase):
    def test_camera_continuity_at_every_cut_and_settle(self):
        shots=[((0,0,0),(0,-8-i,3+i)) for i in range(8)]
        beats=[{'start':i*4,'end':(i+1)*4} for i in range(8)]
        for mechanism in ('hand_generator','wind_turbine'):
            for i in range(1,8):
                for t in (i*4,i*4+1.2):
                    left=np.array(camera_pose(shots,beats,t-1e-5,mechanism))
                    right=np.array(camera_pose(shots,beats,t+1e-5,mechanism))
                    self.assertLess(np.max(np.abs(right-left)),1e-7)

    def test_realtime_rotation_is_mechanism_specific_and_never_unknown(self):
        self.assertAlmostEqual(rotor_angle('hand_generator',60)/(2*math.pi),45)
        self.assertAlmostEqual(rotor_angle('wind_turbine',60)/(2*math.pi),12)
        with self.assertRaises(ValueError):rotor_angle('invented_machine',1)

    def test_camera_changes_add_no_audio(self):
        with tempfile.TemporaryDirectory() as d:
            tl={'duration':1,'beats':[{'action':'machine','start':0,'voice':'unused'},{'action':'induction','start':.5,'voice':'unused'}]}
            with patch('studio_lib.cinema.build.subprocess.check_output',return_value=np.zeros(1000,dtype=np.float32).tobytes()):
                soundtrack(tl,Path(d))
                baseline=(Path(d)/'mix.wav').read_bytes()
                tl['beats'].insert(1,{'action':'shaft','start':.25,'voice':'unused'})
                soundtrack(tl,Path(d))
            self.assertEqual(baseline,(Path(d)/'mix.wav').read_bytes())
            self.assertEqual(json.loads((Path(d)/'sound-events.json').read_text()),[])

    def test_invisible_effect_labels_follow_only_relevant_beats(self):
        beats=[{'action':a,'start':i,'end':i+1} for i,a in enumerate(('machine','generator','induction','load'))]
        labels=illustration_labels(beats)
        self.assertEqual([x[0] for x in labels],[1,2,3])
        with tempfile.TemporaryDirectory() as d:
            text=captions({'beats':beats,'words':[]},Path(d)).read_text()
        self.assertIn('Magnetic field · illustration',text)
        self.assertIn(r'\an8\fs24\pos(360,90)',text)
        self.assertIn('Current path · illustration',text)
        self.assertIn('schematic',contract('hand-cranked generator')['facts']['induction'])
