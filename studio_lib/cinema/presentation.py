"""Shared presentation rules; deterministic, independent of AI and Blender."""
import math

# Representative demonstration speeds, not a universal operating specification.
RPM = {'hand_generator': 45.0, 'wind_turbine': 12.0}

def rotor_angle(mechanism, seconds):
    if mechanism not in RPM:
        raise ValueError('No validated motion profile for mechanism')
    return seconds * RPM[mechanism] * 2 * math.pi / 60

def ease(x):
    x = max(0.0, min(1.0, x))
    return x*x*x*(x*(x*6-15)+10)

def camera_pose(shots, beats, seconds, mechanism):
    # Apply framing to BOTH endpoints before interpolating. No per-beat zoom reset.
    poses=[]
    for i,(target,position) in enumerate(shots):
        scale=1.25 if mechanism=='hand_generator' and i in (1,2) else 1.0
        poses.append((target,tuple(a+(b-a)*scale for a,b in zip(target,position))))
    i=min(len(beats)-1,next((i for i,b in enumerate(beats) if seconds<b['end']),len(beats)-1))
    previous=max(0,i-1)
    duration=min(1.2,beats[i]['end']-beats[i]['start'])
    mix=ease((seconds-beats[i]['start'])/duration) if i else 1.0
    return tuple(tuple(a+(b-a)*mix for a,b in zip(poses[previous][k],poses[i][k])) for k in (0,1))

def illustration_labels(beats,mechanism=None):
    if mechanism is not None and mechanism not in ('hand_generator','wind_turbine'):return []
    labels=[]
    for b in beats:
        if b['action'] in ('generator','induction'):
            labels.append((b['start'],b['end'],'Magnetic field: schematic illustration'))
        elif b['action'] in ('load','payoff'):
            labels.append((b['start'],b['end'],'Circuit markers: illustrative, not to scale'))
        elif b['action']=='wind':
            labels.append((b['start'],b['end'],'Airflow: schematic illustration'))
    return labels
