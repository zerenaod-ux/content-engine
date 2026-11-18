import io,json,os,tempfile,unittest,urllib.error
from unittest.mock import patch
from studio_lib.providers import call
class ProviderJSONTests(unittest.TestCase):
    def test_failed_json_generation_retries_without_strict_format(self):
        error=urllib.error.HTTPError('https://test.invalid/chat/completions',400,'bad',{},io.BytesIO(json.dumps({'error':{'message':'Failed to generate JSON. Please adjust your prompt.'}}).encode()))
        requests=[]
        def request(url,key,body):
            requests.append(body)
            if len(requests)==1:raise error
            return {'choices':[{'message':{'content':'{"question":"How does this small piston help lift a heavier load?"}'}}]}
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GROQ_API_KEY':'fake-not-a-real-key','CE_METRICS_PATH':d+'/metrics.json'},clear=True),patch('studio_lib.providers.llm._models',return_value=['test-model']),patch('studio_lib.providers.llm._req',side_effect=request):
            result=call('Question','Facts',max_tokens=450)
        self.assertIn('question',result)
        self.assertIn('response_format',requests[0])
        self.assertNotIn('response_format',requests[1])
        self.assertGreaterEqual(requests[1]['max_tokens'],1200)
