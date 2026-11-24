import datetime,json,os,tempfile,unittest
from pathlib import Path
from unittest import mock
from studio_lib import stories,novelty,winners,factory_slots,director
from studio_lib.registry import REGISTRY
from studio_lib.topic_scope import scope_error

DATA=json.loads(stories.PATH.read_text())

class Stories(unittest.TestCase):
 def setUp(self):os.environ.pop('CE_STORY',None)
 tearDown=setUp
 def test_story_data_is_valid_and_only_for_registered_hand_built_machines(self):
  self.assertTrue(stories.validate(DATA,set(REGISTRY)))
  for key in DATA['stories']:self.assertFalse(key.startswith('recipe_'));self.assertNotEqual(key,'bascule_bridge');self.assertGreaterEqual(len(DATA['stories'][key]),3)
  self.assertGreaterEqual(sum(len(v) for v in DATA['stories'].values()),40)
 def test_every_story_question_is_inside_its_machines_scope(self):
  for key,rows in DATA['stories'].items():
   for s in rows:self.assertEqual(scope_error(s['question'],key),'',(key,s['id']))
 def test_bad_story_data_is_refused(self):
  bad=json.loads(json.dumps(DATA));bad['stories']['zipper'][1]['view']=dict(bad['stories']['zipper'][0]['view'])
  with self.assertRaises(ValueError):stories.validate(bad,set(REGISTRY))
  bad=json.loads(json.dumps(DATA));bad['stories']['zipper'][0]['view']['az']=3
  with self.assertRaises(ValueError):stories.validate(bad,set(REGISTRY))
  bad=json.loads(json.dumps(DATA));bad['stories']['nope']=bad['stories']['zipper']
  with self.assertRaises(ValueError):stories.validate(bad,set(REGISTRY))
 def test_story_views_keep_the_whole_machine_in_frame(self):
  for key,rows in DATA['stories'].items():
   for s in rows:
    with self.subTest(key=key,story=s['id']),tempfile.TemporaryDirectory() as d:
     tl={'beats':[{'start':i*6,'end':(i+1)*6,'action':a,'camera':'wide' if i in (0,7) else 'mechanism','say':'x'} for i,a in enumerate(REGISTRY[key]['actions'])],'duration':48,'motion_policy':'fixture'}
     plan={'mechanism':key,'story':s['id'],'story_view':s['view']}
     self.assertEqual(director.verify_overview(plan,tl,Path(d)),[])
 def test_story_family_is_separate_from_the_original_and_from_other_stories(self):
  fam=novelty.FAMILIES['zipper']
  self.assertEqual(novelty.identity('','zipper'),fam)
  self.assertEqual(novelty.identity('','zipper',story='y_channel'),fam+'::y_channel')
  os.environ['CE_STORY']='staggered_teeth';self.assertEqual(novelty.identity('','zipper'),fam+'::staggered_teeth')
  with self.assertRaises(ValueError):novelty.identity('','zipper',story='made_up')
 def test_a_used_original_does_not_spend_stories_and_a_used_story_spends_only_itself(self):
  fam=novelty.FAMILIES['zipper']
  rows=[{'topic':'How a zipper slider seals fabric edges','visual_family':fam,'state':'created'}]
  pairs=novelty.available_pairs({'zipper':REGISTRY['zipper']},rows)
  self.assertNotIn(('zipper',None),pairs);self.assertEqual(len([p for p in pairs if p[1]]),3)
  rows.append({'topic':'How do staggered teeth lock into each other','visual_family':fam+'::staggered_teeth','story':'staggered_teeth','state':'created'})
  pairs=novelty.available_pairs({'zipper':REGISTRY['zipper']},rows)
  self.assertNotIn(('zipper','staggered_teeth'),pairs);self.assertIn(('zipper','y_channel'),pairs);self.assertEqual(len(pairs),2)
  self.assertIn('zipper',{k for k in novelty.unused({'zipper':REGISTRY['zipper']},[])})
 def test_a_story_video_does_not_use_up_the_original_by_its_words(self):
  fam=novelty.FAMILIES['zipper']
  row={'topic':'How do staggered zipper teeth lock','title':'zipper','visual_family':fam+'::staggered_teeth','story':'staggered_teeth'}
  self.assertEqual(novelty.families(row),{fam+'::staggered_teeth'})
  self.assertIn(fam,novelty.families({'topic':'How a zipper slider works'}))
 def test_reason_blocks_the_same_story_twice_but_not_a_new_story(self):
  fam=novelty.FAMILIES['zipper'];rows=[{'topic':'Why do staggered teeth hook together tightly','visual_family':fam+'::staggered_teeth','story':'staggered_teeth','state':'created'}]
  os.environ['CE_STORY']='staggered_teeth'
  self.assertIn('Visual setup already used',novelty.reason('Another angle on interlocking metal chains','zipper',rows))
  os.environ['CE_STORY']='y_channel'
  self.assertEqual(novelty.reason('What shape inside the slider guides each side','zipper',rows),'')
 def test_pick_prefers_least_used_machines_and_winner_weights_break_ties(self):
  pairs=[('zipper',None),('stapler',None),('stapler','legs_fold_in')]
  rows=[{'mechanism':'zipper'},{'mechanism':'zipper'}]
  self.assertEqual(stories.pick(pairs,rows)[0],'stapler')
  self.assertEqual(stories.pick([('a',None),('b',None)],[],{'b':.5})[0],'b')
 def test_story_brief_names_the_hero_and_focus(self):
  b=stories.brief('ratchet_wrench','click_back');self.assertIn('tooth slope',b);self.assertIn('beat 3',b);self.assertEqual(stories.brief('ratchet_wrench','nope'),'')
 def test_disabled_stories_give_nothing(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json';p.write_text(json.dumps({'enabled':False,'stories':DATA['stories']}))
   self.assertEqual(stories.stories_for('zipper',p),[])

class Backlog(unittest.TestCase):
 def test_daily_slot_waits_while_too_many_videos_are_unreviewed(self):
  now=datetime.datetime(2026,11,23,23,0,tzinfo=datetime.timezone.utc)
  vids=[{'tag':f'ce-202611{d:02d}-1000'} for d in (20,21,22)]
  self.assertEqual(factory_slots.pending_review(vids,[],now),3)
  self.assertEqual(factory_slots.pending_review(vids,[{'tag':'ce-20261121-1000'}],now),2)
  held=factory_slots.decision(now,[],[('zipper',None)],pending=3,cap=3);self.assertFalse(held['should_build']);self.assertIn('owner review',held['reason'])
  self.assertTrue(factory_slots.decision(now,[],[('zipper',None)],pending=2,cap=3)['should_build'])
  self.assertTrue(factory_slots.decision(now,[],[('zipper',None)])['should_build'])

class Winners(unittest.TestCase):
 def test_report_uses_owner_verdicts_and_never_raises(self):
  r=winners.report();self.assertEqual(r['policy'],'winners-v1');self.assertIn('weights',r)
  self.assertTrue(all(-1<=w<=1 for w in r['weights'].values()))
  with mock.patch.object(winners,'_read',side_effect=RuntimeError('boom')):
   self.assertEqual(winners.weights(),{});self.assertEqual(winners.hint(),'')
 def test_score_blends_views_only_when_linked(self):
  d={'reviewed':4,'saved':4,'deleted':0,'views':100,'avp':[50]}
  self.assertAlmostEqual(winners.score(d,0),.8);self.assertGreater(winners.score(d,100),.8-1e-9)
 def test_machine_is_found_from_a_title(self):
  self.assertEqual(winners._machine_of('Why a Ratchet Wrench Stops Backward Motion'),'ratchet_wrench')

class Choose(unittest.TestCase):
 def test_choose_topic_builds_a_story_pick_and_records_it(self):
  from studio_lib import production
  os.environ.pop('CE_STORY',None)
  def fake(system,prompt,**k):
   self.assertIn('STORY BRIEF' if os.environ.get('CE_STORY') else 'Choose',prompt)
   key=json.loads(prompt.split('Supported scopes: ')[1].split(' Recent examples')[0]) if False else None
   return {'topic':'What makes interlocking metal chain links grip together','mechanism':next(iter(production._LAST['available']))}
  try:
   with mock.patch.object(production,'call',side_effect=lambda s,p,**k:(lambda a:fake(s,p,**k))(0)):
    production._LAST={}
    with mock.patch.object(novelty,'available_pairs',return_value=[('zipper','staggered_teeth')]):
     production._LAST['available']={'zipper':1}
     topic=production.choose_topic()
   idea=json.loads(Path('idea.json').read_text())
   self.assertEqual(idea['story'],'staggered_teeth');self.assertEqual(idea['subject'],'zipper');self.assertEqual(os.environ['CE_STORY'],'staggered_teeth');self.assertTrue(topic)
  finally:
   if Path('idea.json').exists():Path('idea.json').unlink()
   os.environ.pop('CE_STORY',None)
if __name__=='__main__':unittest.main()
