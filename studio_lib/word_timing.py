"""Independent word timing for the fixed narrator; no guessed word rate."""
import functools,os
@functools.lru_cache(maxsize=1)
def model():
 if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Production word timing requires the cloud runner')
 from faster_whisper import WhisperModel
 return WhisperModel('tiny.en',device='cpu',compute_type='int8')
def measured_words(path):
 segments,_=model().transcribe(str(path),language='en',word_timestamps=True,beam_size=3,condition_on_previous_text=False)
 return [{'text':w.word.strip(),'start':float(w.start),'end':float(w.end)} for segment in segments for w in (segment.words or []) if w.word.strip()]
