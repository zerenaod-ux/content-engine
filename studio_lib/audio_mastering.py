"""Common encoded-audio headroom for every How It Ticks production format.

Delivery still measures the encoded result. This is not a substitute for that
check, nor does it change the narrator's emotion, phrasing or pacing.
"""
def mastering_args():
    return ['-ar','48000','-af','loudnorm=I=-16:TP=-3:LRA=9,alimiter=limit=0.7:level=false']
