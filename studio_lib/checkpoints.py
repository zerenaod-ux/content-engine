"""Atomic, integrity-checked automatic-stage checkpoints; never credentials."""
import hashlib,json,time
from pathlib import Path
from studio_lib.schema import check
STAGES={'needs_repair','needs_audit','checked_scene','narrated','rendered','complete'}
def signature(topic,namespace='general-scene'):
    # Provider routing changes must not discard an already generated scene.
    root=Path(__file__).resolve().parent
    return hashlib.sha256((topic.strip()+namespace).encode()+(root/'schema.py').read_bytes()).hexdigest()
class Checkpoint:
    def __init__(self,topic,root='.ce-cache/studio-stages',validator=check,namespace='general-scene'):
        self.topic=topic;self.validator=validator;self.key=signature(topic,namespace);self.path=Path(root)/(self.key+'.json')
    def load(self):
        try:
            envelope=json.loads(self.path.read_text());data=envelope['data']
            raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
            if hashlib.sha256(raw).hexdigest()!=envelope['sha256']:return None
            if data['topic']!=self.topic or data['signature']!=self.key or data['stage'] not in STAGES:return None
            if data['stage']!='needs_repair' and self.validator(data['scene']):return None
            return data
        except (OSError,ValueError,TypeError,KeyError):return None
    def save(self,stage,scene,errors=None,**fields):
        if stage not in STAGES:raise ValueError('unknown checkpoint stage')
        if stage!='needs_repair' and self.validator(scene):raise ValueError('cannot cache invalid scene as an accepted stage')
        data=dict(topic=self.topic,signature=self.key,stage=stage,scene=scene,errors=errors or [],saved_at=time.time(),manual_scene_edits=False,**fields)
        raw=json.dumps(data,sort_keys=True,separators=(',',':')).encode();envelope={'sha256':hashlib.sha256(raw).hexdigest(),'data':data}
        self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(envelope,indent=2));temp.replace(self.path)
        return data
