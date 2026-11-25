import json,pytest
from studio_lib import machine_writer as W,machine_spec

def good():
    code=W.example_code()
    facts={a:'This beat shows the %s step of the simplified model, and it does not show the real internals.'%a for a in W.ACTIONS}
    return {'title':'Demo gear lift','description':'Two gears and a spring in a simplified cutaway; not a real lift','words':['demo gear lift'],'parts':['plate','gear','spring','door'],
     'subjects':[['plate','gear']]*8,'cues':{'cutaway':['cover','cutaway'],'payoff':['result','finally']},'facts':facts,'source':'https://en.wikipedia.org/wiki/Gear','code':code}

@pytest.mark.parametrize('bad,why',[
 ('import os\n','import not allowed'),('import subprocess\n','import not allowed'),
 ('x=open("a")\n','name not allowed'),('x=().__class__\n','private attribute'),
 ('def f():\n while True:pass\n','While'),('x=getattr(1,"a")\n','name not allowed'),
 ('x="{0.__class__}"\n','double underscores'),('from studio_lib import director\n','import not allowed'),
 ('class A:pass\n','ClassDef'),('from studio_lib.registry import REGISTRY\n','import not allowed')])
def test_code_gate_rejects(bad,why):
    base=W.example_code()
    with pytest.raises(W.WriterError,match=why):W.check_code(base+'\n'+bad)

def test_needs_all_functions():
    with pytest.raises(W.WriterError,match='must define'):W.check_code('def state(t,tl):return {}\n')

def test_example_passes_gate_and_derives_contract():
    m=W.build_module('studio_lib.mw_t',W.example_code())
    moves,holds=W.derive_contract(m)
    assert '2' in moves and holds

def test_sandbox_accepts_good_machine_and_spec_installs(tmp_path):
    spec=W.run_sandbox(good(),'mw_demo_gear_lift',tmp_path/'w')
    assert spec['picture_check']['faces']>0 and spec['contract']['visible']
    folder=tmp_path/'machines';W.save(spec,folder)
    machine_spec.validate(json.loads((folder/'mw_demo_gear_lift.json').read_text()))
    comps={};keys=machine_spec.load_all(comps,root=folder)
    assert keys==['mw_demo_gear_lift'] and 'mw_demo_gear_lift' in comps

def test_sandbox_reports_runtime_crash_as_feedback(tmp_path):
    d=good();d['code']=d['code'].replace("cut=ease(progress(t,b[1]))","cut=1/0+ease(progress(t,b[1]))")
    with pytest.raises(W.WriterError):W.run_sandbox(d,'mw_crash',tmp_path/'w')

def test_still_machine_is_rejected(tmp_path):
    d=good();d['code']=d['code'].replace("turn=3.1416*(ease(progress(t,b[2]))+ease(progress(t,b[4])))","turn=0.0").replace("cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7])))","cut=0.0")
    with pytest.raises(W.WriterError,match='measurable movement'):W.run_sandbox(d,'mw_still',tmp_path/'w')

def test_write_retries_with_feedback(tmp_path):
    calls=[]
    def ask(prompt):
        calls.append(prompt)
        if len(calls)==1:
            d=good();d['code']='import os\n'+d['code'];return d
        return good()
    spec=W.write('demo gear lift',ask=ask,workdir=tmp_path/'w')
    assert spec['writer_tries']==2 and 'import not allowed' in calls[1]

def test_write_gives_up_after_ten(tmp_path):
    def ask(p):d=good();d['code']='import os\n'+d['code'];return d
    with pytest.raises(W.WriterError,match='10 tries'):W.write('x machine',ask=ask,workdir=tmp_path/'w')

def test_pick_idea_skips_existing_and_respects_limit(tmp_path):
    first=W.pick_idea(tmp_path)
    assert first and first in W.IDEAS
    for i in range(W.MAX_WRITTEN):(tmp_path/('mw_a%d.json'%i)).write_text('{"title":"x%d"}'%i)
    assert W.pick_idea(tmp_path) is None
