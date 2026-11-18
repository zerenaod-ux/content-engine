"""Versioned, reusable delivery profiles using supported TTS prosody controls.

These are pacing/emphasis cues, not a claim of neural emotional-style support.
"""
import hashlib,json
VOICE='en-US-AndrewNeural'
POLICY_VERSION='expressive-v1'
WRITING_RULES=('Write energetic, natural spoken explanation: a curious opening question, '
    'a brief anticipation before the mechanism reveal, clear emphasis on the causal change, '
    'and an upbeat payoff. Use short clauses and natural punctuation without changing facts. '
    'No stage directions, emotion tags, shouting, invented danger, or horror framing for ordinary science topics.')

def delivery(action,index,total):
    if index==0:
        tone,rate,pitch,volume,pause='curious','+22%','+6Hz','+0%',.32
    elif index==total-1:
        tone,rate,pitch,volume,pause='upbeat payoff','+30%','+5Hz','+2%',.24
    elif action in ('generator','induction','absorb','separate','pivot'):
        tone,rate,pitch,volume,pause='focused discovery','+22%','+2Hz','+0%',.30
    elif action in ('load','balance','pass','outlet'):
        tone,rate,pitch,volume,pause='emphasized result','+32%','+5Hz','+2%',.22
    else:
        tone,rate,pitch,volume,pause='energetic explanation','+30%','+3Hz','+0%',.20
    return dict(policy=POLICY_VERSION,tone=tone,rate=rate,pitch=pitch,volume=volume,pause_after=pause)

def cache_key(text,profile):
    return hashlib.sha256(json.dumps([text,VOICE,profile,'WordBoundary'],sort_keys=True).encode()).hexdigest()
