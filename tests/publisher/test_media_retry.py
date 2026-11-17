import ast,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
source=ast.parse(Path('ce_publisher.py').read_text())
function=next(x for x in source.body if isinstance(x,ast.FunctionDef) and x.name=='create_approved_post')
class MediaRetryTests(unittest.TestCase):
    def run_submit(self,responses):
        api=Mock(side_effect=responses);ns={'api':api,'time':time}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'ce_publisher.py','exec'),ns)
        with patch('time.sleep'):result=ns['create_approved_post']({'channelId':'test','text':'approved'})
        return result,api
    def test_explicit_video_fetch_error_retried_once_then_stops_on_success(self):
        error={'data':{'createPost':{'message':'Invalid post: Video could not be read from its URL.'}}}
        success={'data':{'createPost':{'post':{'id':'saved'}}}}
        result,api=self.run_submit([error,success]);self.assertEqual(api.call_count,2);self.assertEqual(result,success)
    def test_success_and_unrelated_errors_never_create_duplicates(self):
        for response in ({'data':{'createPost':{'post':{'id':'saved'}}}},{'data':{'createPost':{'message':'Unauthorized'}}}):
            result,api=self.run_submit([response]);self.assertEqual(api.call_count,1)
    def test_retries_are_bounded(self):
        error={'data':{'createPost':{'message':'Video could not be read from its URL.'}}}
        result,api=self.run_submit([error]*3);self.assertEqual(api.call_count,3)
