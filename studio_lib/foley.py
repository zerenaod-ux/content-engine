"""Machine sounds made from the machine's OWN motion (owner request 2026-11-24: like the macro-gear Short, every touch makes its exact sound).
State channels (turn, slide, cut ...) are sampled over the video; each unit of travel makes a tick, a start makes a clunk, a stop makes a clack,
and moving parts add a soft friction/hum bed. Pure numpy, free, deterministic, no downloads. CE_FOLEY=off disables."""
import hashlib,os
import numpy as np
SR=24000
RATE=60            # motion samples per second
MAX_TICKS_PER_S=14.0
LEVEL=0.34         # foley peak relative to the voice master (voice is .78); ducked under speech

def _channels(module,tl):
    T=tl['duration'];n=int(T*RATE)+1;rows=[]
    for k in range(n):
        s=module.state(k/RATE,tl);rows.append({a:float(b) for a,b in s.items() if a!='beat' and isinstance(b,(int,float)) and not isinstance(b,bool)})
    names=sorted(set().union(*[set(r) for r in rows])) if rows else []
    return {c:np.array([r.get(c,0.) for r in rows]) for c in names}

def events(module,tl):
    """List of (time_s, kind, strength 0..1, channel_index) from the real motion."""
    ch=_channels(module,tl);ev=[]
    for ci,(name,x) in enumerate(sorted(ch.items())):
        span=float(x.max()-x.min())
        if span<1e-6:continue
        v=np.abs(np.gradient(x))*RATE;vmax=float(v.max()) or 1.
        moving=v>0.04*vmax
        step=max(span/28.,float(np.abs(np.diff(x)).sum())/(RATE*0+1)/220.)   # about 28 ticks per full travel, never more than ~220 per channel
        acc=0.;last=-9.;prev=False
        for k in range(1,len(x)):
            t=k/RATE
            if moving[k] and not prev:ev.append((t,'clunk',min(1.,.5+v[k]/vmax),ci))
            if prev and not moving[k]:ev.append((t,'clack',.7,ci))
            prev=bool(moving[k])
            if moving[k]:
                acc+=abs(x[k]-x[k-1])
                if acc>=step and t-last>=1./MAX_TICKS_PER_S:ev.append((t,'tick',min(1.,.25+.75*v[k]/vmax),ci));acc=0.;last=t
                elif acc>=step:acc=step*.5
    return sorted(ev)

def _burst(n,freq,decay,rng,noise=.6):
    t=np.arange(n)/SR;env=np.exp(-t/decay)
    return env*((1-noise)*np.sin(2*np.pi*freq*t+rng.uniform(0,6.28))+noise*rng.standard_normal(n))

def render(module,tl,seed='x'):
    """Foley track (float, length = duration) from the machine's motion."""
    T=tl['duration'];n=int(T*SR)+1;out=np.zeros(n);rng=np.random.default_rng(int(hashlib.md5(str(seed).encode()).hexdigest()[:8],16))
    for t,kind,strength,ci in events(module,tl):
        i=int(t*SR);base=1400+170*ci
        if kind=='tick':s=_burst(int(.045*SR),base*rng.uniform(.9,1.15),.007,rng,.55)*strength*.9
        elif kind=='clunk':
            s=_burst(int(.16*SR),110+12*ci,.05,rng,.25)*strength*1.1;c=_burst(int(.02*SR),2600,.003,rng,.9)*.25*strength;s[:len(c)]+=c
        else:s=_burst(int(.09*SR),base*.8,.018,rng,.4)*strength*.9
        j=min(len(s),n-i)
        if j>0:out[i:i+j]+=s[:j]
    # soft friction / hum bed while anything moves
    ch=_channels(module,tl)
    if ch:
        v=sum(np.abs(np.gradient(x))*RATE/(float(np.abs(np.gradient(x)).max()*RATE) or 1.) for x in ch.values() if x.max()-x.min()>1e-6)
        if np.ndim(v):
            env=np.interp(np.arange(n)/SR,np.arange(len(v))/RATE,np.clip(v/ max(1.,float(np.max(v))),0,1))
            k=np.ones(int(.04*SR))/int(.04*SR);env=np.convolve(env,k,'same')
            t=np.arange(n)/SR;noise=np.convolve(rng.standard_normal(n),np.ones(24)/24,'same')   # low-passed rustle
            out+=env*(0.07*noise*3+0.025*np.sin(2*np.pi*(86+30*env)*t))
    peak=float(np.abs(out).max()) or 1.
    return out/peak

def mix(voice,foley,sr=SR):
    """Voice master + foley ducked under speech. Both float arrays at sr."""
    n=len(voice);f=np.zeros(n);f[:min(n,len(foley))]=foley[:n]
    env=np.convolve(np.abs(voice),np.ones(int(.06*sr))/int(.06*sr),'same');env=env/(env.max()+1e-9)
    duck=1.-.62*np.clip(env*2.2,0,1)
    return voice+LEVEL*f*duck

def enabled():return os.environ.get('CE_FOLEY','on')!='off'
