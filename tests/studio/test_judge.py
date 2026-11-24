import json,os,tempfile,unittest
from pathlib import Path
from unittest import mock
from studio_lib import judge,picture_check as pc
import test_picture_check as tp

def S(label,f,c,**k):return dict(machine='m',label=label,faces=f,colours=c,**k)

class Judge(unittest.TestCase):
 def test_fit_separates_liked_from_rejected_with_a_margin(self):
  good=[S('good',600,300),S('good',700,260),S('good',1500,80),S('good',350,210)]
  bad=[S('bad',260,100),S('bad',420,140),S('bad',300,110),S('bad',150,50)]
  rule=judge.fit(good+bad);self.assertEqual(rule['accuracy'],1.0)
  for s in good:self.assertTrue(judge.passes(s,rule))
  for s in bad:self.assertFalse(judge.passes(s,rule))
  self.assertIsNone(judge.fit(good[:2]+bad))
 def test_the_seeded_history_is_separated_by_the_fitted_rule(self):
  rule=judge.fit(judge.seed_samples());self.assertEqual(rule['accuracy'],1.0);self.assertEqual(rule['bad_blocked'],'12/12')
 def test_taste_limits_are_clamped_and_missing_file_is_neutral(self):
  with tempfile.TemporaryDirectory() as d,mock.patch.object(judge,'ROOT',Path(d)):
   self.assertEqual(judge.load_taste(),{})
   (Path(d)/'data/scenes').mkdir(parents=True);(Path(d)/judge.TASTE).write_text(json.dumps({'faces_min':99999,'colours_min':1,'faces_alt':900}))
   self.assertEqual(judge.load_taste(),{'faces_min':700,'colours_min':30,'faces_alt':900})
 def test_agreement_and_earned_trust(self):
  live=[S('good',1,1,pixel_pass=True,vision=8) for _ in range(6)]+[S('bad',1,1,pixel_pass=False,vision=2) for _ in range(5)]
  a=judge.agreement(live);self.assertEqual(a['vision'],1.0);self.assertEqual(a['vision_n'],11);self.assertTrue(judge.vision_trusted(live))
  wrong=live[:5]+[S('good',1,1,pixel_pass=True,vision=1) for _ in range(6)]
  self.assertFalse(judge.vision_trusted(wrong));self.assertFalse(judge.vision_trusted(live[:4]))
 def test_live_samples_join_picture_records_with_owner_verdicts(self):
  with tempfile.TemporaryDirectory() as d,mock.patch.object(judge,'ROOT',Path(d)):
   (Path(d)/'data/scenes/review').mkdir(parents=True)
   (Path(d)/'data/scenes/videos.json').write_text(json.dumps([{'tag':'a','mechanism':'zipper','picture_check':{'faces':500,'colours':200,'pass':True,'vision_score':7}},{'tag':'b','mechanism':'x','picture_check':{'faces':100,'colours':50,'pass':False}},{'tag':'c','mechanism':'y'}]))
   (Path(d)/'data/scenes/review/index.json').write_text(json.dumps({'items':[{'tag':'a','folder':'saved'},{'tag':'b','folder':'delete'},{'tag':'c','folder':'saved'}]}))
   rows=judge.live_samples();self.assertEqual([(r['tag'],r['label']) for r in rows],[('a','good'),('b','bad')])
 def test_write_creates_taste_and_report_files(self):
  with tempfile.TemporaryDirectory() as d:
   r=judge.write(d);self.assertTrue((Path(d)/judge.TASTE).is_file());self.assertTrue((Path(d)/judge.REPORT).is_file());self.assertEqual(r['rule']['accuracy'],1.0)

class VisionModes(unittest.TestCase):
 def run_mode(self,mode,score):
  ask=lambda p,b:{'score':score,'problems':['looks flat']}
  with tempfile.TemporaryDirectory() as d,mock.patch.dict(os.environ,{'CE_VISION_CHECK':mode}),mock.patch('studio_lib.judge.vision_trusted',return_value=False):
   plan={'mechanism':'x'}
   try:v=pc.run(lambda t,z:tp.rich(t,zoom=z),tp.TL,plan,tp.CONTRACT,d,ask=ask);return v
   except ValueError as e:return str(e)
 def test_vision_is_recorded_but_does_not_block_until_trusted(self):
  v=self.run_mode('advisory',2);self.assertTrue(v['pass']);self.assertEqual(v['vision']['score'],2.0);self.assertFalse(v['vision_blocks'])
 def test_block_mode_and_earned_trust_let_vision_stop_a_video(self):
  self.assertIn('vision check scored',self.run_mode('block',2))
  with tempfile.TemporaryDirectory() as d,mock.patch('studio_lib.judge.vision_trusted',return_value=True):
   with self.assertRaises(ValueError):pc.run(lambda t,z:tp.rich(t,zoom=z),tp.TL,{'mechanism':'x'},tp.CONTRACT,d,ask=lambda p,b:{'score':1,'problems':['flat']})
 def test_vision_off_skips_the_call(self):
  called=[]
  with tempfile.TemporaryDirectory() as d,mock.patch.dict(os.environ,{'CE_VISION_CHECK':'off','GEMINI_API_KEY':'x'}):
   v=pc.run(lambda t,z:tp.rich(t,zoom=z),tp.TL,{'mechanism':'x'},tp.CONTRACT,d,ask=lambda p,b:called.append(1) or {'score':1,'problems':[]})
  self.assertEqual(called,[]);self.assertIsNone(v['vision'])
if __name__=='__main__':unittest.main()
