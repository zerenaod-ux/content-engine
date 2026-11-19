"""One stock narrator identity for every future How It Ticks format."""
VOICE='am_fenrir'
PROVIDER='kokoro-onnx-cpu'
VERSION='how-it-ticks-narrator-v2'

def matches(timeline):
 return timeline.get('voice')==VOICE and timeline.get('voice_provider')==PROVIDER and timeline.get('voice_policy')==VERSION
