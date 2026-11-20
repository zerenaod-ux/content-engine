"""One stock narrator identity for every future How It Ticks format."""
VOICE='af_heart'
PROVIDER='kokoro-onnx-cpu'
VERSION='how-it-ticks-narrator-v4-heart-clean'

def matches(timeline):
 return timeline.get('voice')==VOICE and timeline.get('voice_provider')==PROVIDER and timeline.get('voice_policy')==VERSION
