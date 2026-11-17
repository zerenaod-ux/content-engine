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
