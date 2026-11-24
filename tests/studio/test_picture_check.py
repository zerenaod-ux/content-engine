import json,tempfile,unittest
from pathlib import Path
from PIL import Image
from studio_lib.mesh import Scene
from studio_lib import parts_rich as P,picture_check as pc

BG=Image.new('RGB',(1080,1920),(30,44,56))
TL={'beats':[{'start':i*6,'end':(i+1)*6,'action':'a'} for i in range(8)],'duration':48}
CONTRACT={'moves':{1:{'cut':1},2:{'wheel':1}},'holds':{},'visible':[]}

def rich(t,zoom=1.0,turn=None):
 s=Scene(t,3.0*zoom,(0,0,2.4),.3,elevation=6,lighting=True,raster_scale=1)
 P.gear(s,(-.4,0,2.6),1.2,16,(t*.5 if turn is None else turn),.4,(186,198,206))
 P.gear(s,(1.5,0,1.7),.7,10,-t*.8 if turn is None else -turn,.4,(222,176,84))
 P.spring(s,(-1.8,-.1,1.0),(1.5,-.1,1.0),8,.2,.04,(190,200,190))
 im=BG.copy().resize((720,1280));s.paint(im);return im.resize((1080,1920)),s.faces

def plain(t,zoom=1.0):
 s=Scene(t,.55*zoom,(0,0,2.4),.3,elevation=6,lighting=True)
 s.box((0,0,2.4),(1,1,1),(120,120,120));s.box((.8,0,2.4),(.5,.5,.5),(120,120,120))
 im=BG.copy().resize((720,1280));s.paint(im);return im.resize((1080,1920)),s.faces

class PictureCheck(unittest.TestCase):
 def test_rich_machine_passes_and_plain_boxes_fail(self):
  good=pc.evaluate(lambda t:rich(t),TL,moving_beats=(2,))
  self.assertEqual(good['errors'],[]);self.assertGreater(good['score'],6)
  bad=pc.evaluate(lambda t:plain(t),TL)
  self.assertTrue(any('too few facets' in e for e in bad['errors']))
  self.assertTrue(any('flat shading' in e or 'too little visible detail' in e or 'fills only' in e for e in bad['errors']))
 def test_still_machine_fails_the_motion_check(self):
  rep=pc.evaluate(lambda t:rich(t,turn=.7),TL,moving_beats=(2,))
  self.assertTrue(any('almost nothing moves' in e for e in rep['errors']))
 def test_adjustments_zoom_in_for_small_and_flag_builder_work_for_flat(self):
  self.assertGreater(pc.adjustments({'errors':['beat 2 at 1s: machine fills only 3% of the stage; zoom in']},1.0)['zoom'],1.0)
  adj=pc.adjustments({'errors':['beat 2: flat shading (3 tones); parts look like plain boxes']},1.0)
  self.assertTrue(adj['needs_builder']);self.assertEqual(adj['zoom'],1.0)
 def test_run_redoes_a_small_picture_with_a_bigger_view_and_records_it(self):
  def pic(t,z):return rich(t,zoom=z*.62)
  with tempfile.TemporaryDirectory() as d:
   plan={'mechanism':'x'};v=pc.run(pic,TL,plan,CONTRACT,d)
   self.assertTrue(v['pass']);self.assertGreater(plan['picture_zoom'],1.0);self.assertGreaterEqual(len(v['attempts']),2)
   data=json.loads((Path(d)/'picture-check.json').read_text());self.assertTrue(data['verdict']['pass']);self.assertTrue((Path(d)/'picture-contact.jpg').is_file())
 def test_run_stops_before_rendering_when_it_cannot_be_fixed(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError) as c:pc.run(lambda t,z:plain(t,z),TL,{'mechanism':'x'},CONTRACT,d)
   self.assertIn('nothing was rendered',str(c.exception));self.assertTrue((Path(d)/'picture-check.json').is_file())
 def test_vision_is_advisory_and_only_blocks_when_it_answers(self):
  with tempfile.TemporaryDirectory() as d:
   sheet=Path(d)/'s.jpg';Image.new('RGB',(10,10)).save(sheet)
   self.assertIsNone(pc.vision_critique(sheet,lambda p,b:(_ for _ in ()).throw(RuntimeError('down'))))
   self.assertIsNone(pc.vision_critique(sheet,lambda p,b:{'nonsense':1}))
   low=pc.vision_critique(sheet,lambda p,b:{'score':3,'problems':['looks like plain boxes']})
  base={'errors':[],'score':9.}
  self.assertTrue(pc.decide(base,None)['pass']);self.assertTrue(pc.decide(base,{'score':8,'problems':[]})['pass'])
  v=pc.decide(base,low);self.assertFalse(v['pass']);self.assertIn('plain boxes',' '.join(v['errors']))
 def test_sample_times_use_the_measured_motion_window(self):
  tl={'beats':[{'start':0,'end':6,'motion_window':[2,4]}]}
  a,b=[t for _,t in pc.sample_times(tl)];self.assertAlmostEqual(a,2.3);self.assertAlmostEqual(b,3.7)
 def test_moving_beats_ignore_cover_only_motion(self):
  self.assertEqual(pc.moving_beats_for(CONTRACT),[2])
if __name__=='__main__':unittest.main()
