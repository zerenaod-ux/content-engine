import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_lib import novelty
from studio_lib.registry import REGISTRY
from studio_lib.production import choose_topic

class NoveltyPolicyTests(unittest.TestCase):
 def test_new_title_cannot_reuse_the_same_machine_scene(self):
  for status in ('created','scheduled','published','skipped','deleted','saved'):
   with self.subTest(status=status):
    rows=[{'topic':'How a drawbridge counterweight works','mechanism':'bascule_bridge','state':status}]
    self.assertTrue(novelty.reason('Why bridge road barriers close first','bascule_bridge',rows))

 def test_cross_format_and_shared_visual_family_are_not_loopholes(self):
  rows=[{'title':'Wind turbine internal generator','mechanism':'wind_turbine','format':'short'}]
  self.assertTrue(novelty.reason('How a hand crank generator lights a lamp','hand_generator',rows))
  rows=[{'mechanism':'dna_pairing','format':'original_full','state':'created'}]
  self.assertTrue(novelty.reason('How water moves between reservoirs','water_transfer',rows))   # rack_pinion now has its own spec family, so use a pair that still shares one

 def test_completed_video_cannot_resume_even_for_same_owner(self):
  row={'topic':'How solar cells power a lamp','mechanism':'photovoltaic_cell','owner':'test','state':'created','failed':True}
  self.assertTrue(novelty.reason(row['topic'],'photovoltaic_cell',[row],owner='test'))

 def test_only_unfinished_same_owner_reservation_can_continue(self):
  row={'topic':'How a cam follower moves','mechanism':'cam_follower','state':'reserved','owner':'test'}
  self.assertFalse(novelty.reason(row['topic'],'cam_follower',[row],owner='test'))
  self.assertTrue(novelty.reason(row['topic'],'cam_follower',[row],owner='another'))
  row['video']='already-rendered.mp4'
  self.assertTrue(novelty.reason(row['topic'],'cam_follower',[row],owner='test'))

 def test_unknown_visual_recipe_is_held(self):
  self.assertTrue(novelty.reason('A new sounding title','renamed_old_scene',[]))

 def test_missing_history_never_resets_forever_memory(self):
  with tempfile.TemporaryDirectory() as root:
   with self.assertRaisesRegex(ValueError,'missing'):novelty.records(root)

 def test_empty_but_valid_json_cannot_reset_originality_memory(self):
  with tempfile.TemporaryDirectory() as root:
   base=Path(root)/'data/scenes';base.mkdir(parents=True)
   for name in ('novelty-ledger','history','videos','topic-ledger'):(base/(name+'.json')).write_text('[]')
   with self.assertRaisesRegex(ValueError,'emptied'):novelty.records(root)

 def test_permanent_memory_survives_removed_index_entry(self):
  with tempfile.TemporaryDirectory() as root:
   base=Path(root)/'data/scenes';base.mkdir(parents=True)
   for name in ('history','videos','topic-ledger'):(base/(name+'.json')).write_text('[]')
   (base/'novelty-ledger.json').write_text(json.dumps([{'topic':'Old solar video','visual_family':'photovoltaic_cell','state':'skipped'}]))
   self.assertTrue(novelty.reason('Why solar contacts collect charge','photovoltaic_cell',novelty.records(root)))

 def test_exhausted_library_holds_instead_of_using_the_paused_kit_and_force_flag_still_works(self):
  from studio_lib import stories
  rows=[{'mechanism':key,'state':'created'} for key in REGISTRY]+[{'visual_family':novelty.FAMILIES[k]+'::'+s['id'],'story':s['id'],'state':'created'} for k in REGISTRY for s in stories.stories_for(k)]
  with tempfile.TemporaryDirectory() as root:
   base=Path(root);(base/'history.json').write_text('[]');(base/'videos.json').write_text('[]')
   with patch('studio_lib.production.novelty.records',return_value=rows),patch('studio_lib.production.call') as model:
    with self.assertRaisesRegex(ValueError,'No unused hand-built machine or story remains'):choose_topic(base/'history.json')
    model.assert_not_called()
    with patch.dict(os.environ,{'CE_FORCE_RECIPE':'true'}),patch('studio_lib.production.recipe_topic',return_value='How a new thing works') as recipe:
     self.assertEqual(choose_topic(base/'history.json'),'How a new thing works');recipe.assert_called_once()

 def test_legacy_clip_compiler_is_retired(self):
  import ce_long
  with self.assertRaisesRegex(ValueError,'forbidden'):ce_long.main()

 def test_completed_video_replacement_stops_before_any_external_write(self):
  import deliver_daily_correction
  with patch.object(deliver_daily_correction,'github') as remote:
   with self.assertRaisesRegex(ValueError,'retired'):deliver_daily_correction.main()
   remote.assert_not_called()

 def test_first_encoded_media_is_remembered_even_before_quality_review(self):
  with tempfile.TemporaryDirectory() as root,patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GH_TOKEN':'fixture','GITHUB_RUN_ID':'new'}):
   video=Path(root)/'fixture.mp4';video.write_bytes(b'not real media: hash fixture only')
   seed=[{'topic':'Old solar explanation','visual_family':'photovoltaic_cell','state':'historical'}]
   with patch('studio_lib.service_queue.read_document',return_value=(seed,'sha')),patch('studio_lib.service_queue.write_document') as write:
    novelty.record_created('Why a wind turbine rotates','wind_turbine',video)
    row=write.call_args[0][1][-1]
    self.assertEqual(row['state'],'created');self.assertEqual(row['visual_family'],'rotary_generator')
    self.assertTrue(novelty.reason('Why wind blades turn a shaft','wind_turbine',[row],owner='new'))

if __name__=='__main__':unittest.main()
