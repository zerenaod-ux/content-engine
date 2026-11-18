import importlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
class FullDeliveryTests(unittest.TestCase):
 def test_failed_provenance_or_format_cannot_write_a_review_card(self):
  env={'GITHUB_REPOSITORY':'zerenaod-ux/content-engine','GH_TOKEN':'test-placeholder','GITHUB_RUN_ID':'123','SOURCE_RUN':'123'}
  with patch.dict(os.environ,env):module=importlib.import_module('studio_lib.longform.deliver')
  base={'format':'original_full','manual_script_or_video_edits':False,'selected_by_system':True,'reused_short_assets':False,'duration':150,'width':1280,'height':720}
  for changes in ({'format':'compilation'},{'selected_by_system':False},{'reused_short_assets':True},{'duration':39},{'width':720,'height':1280}):
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);(root/'result.json').write_text(json.dumps(dict(base,**changes)));(root/'accepted-plan.json').write_text('{}')
    with patch.object(module,'Path',return_value=root),patch.object(module,'api') as request,patch.object(module,'put_file') as write:
     with self.assertRaises(ValueError):module.main()
     request.assert_not_called();write.assert_not_called()
 def test_repeated_delivery_reuses_closed_card_and_retains_one_index_entry(self):
  from studio_lib.quality_gate import seal
  from studio_lib.longform import deliver as module
  cards=[];catalog=[];created=[]
  run={'head_branch':'studio-cinematic-proof','name':'Original How It Ticks full video','created_at':'2026-11-18T00:00:00Z','head_sha':'a'*40,'html_url':'https://github.com/example/repo/actions/runs/123'}
  tag='ce-long-20261118-0000'
  def api(method,path,body=None):
   if path.startswith('actions/runs/'):return run
   if method=='GET' and path.startswith('issues?'):return cards
   if method=='POST' and path=='issues':
    created.append(body);cards.append({'body':body['body'],'state':'closed','number':1});return cards[-1]
   raise AssertionError((method,path))
  def put(path,content,branch,merge=None):
   if merge is not None:merge(catalog)
   return {'commit':{'sha':'b'*40}}
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   (root/'result.json').write_text(json.dumps({'format':'original_full','manual_script_or_video_edits':False,'selected_by_system':True,'reused_short_assets':False,'duration':150,'width':1280,'height':720}))
   (root/'accepted-plan.json').write_text(json.dumps({'title':'How a Lead Screw Moves Things','topic':'How a lead screw moves a carriage'}))
   (root/'video.mp4').write_bytes(b'x'*100001)
   (root/'audio-review.json').write_text(json.dumps({'errors':[],'integrated_lufs':-16,'true_peak_dbfs':-1.5,'independent_asr_word_error_rate':0}))
   (root/'narration-critique.json').write_text('{"errors":[]}');seal(root,'original_full',{'duration':150,'width':1280,'height':720})
   with patch.object(module,'Path',return_value=root),patch.object(module,'api',side_effect=api),patch.object(module,'get',side_effect=lambda path:{'id':1,'assets':[{'name':tag+'.mp4'}]} if path.startswith('releases/') else {'id':1}),patch.object(module,'put_file',side_effect=put):
    module.main();module.main()
  self.assertEqual(len(created),1);self.assertEqual(len(catalog),1);self.assertEqual(cards[0]['state'],'closed')
  self.assertNotIn('ce-approve',created[0]['labels'])
