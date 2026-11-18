"""Model-written local repairs; valid chapters and metadata remain byte-for-byte intact."""
import copy,json,re
from studio_lib.providers import call
from studio_lib.longform.contract import FACTS,SOURCES,mechanism_facts

def repair_sections(plan,out,attempt=0,issues=None):
    beats=plan.get('beats',[])
    if not isinstance(beats,list) or len(beats)!=16:return plan
    bad=[i for i,b in enumerate(beats) if not isinstance(b.get('say'),str) or not 20<=len(b['say'].split())<=50]
    bad=sorted(set(bad+[int(m.group(1)) for e in issues or [] for m in [re.match(r'Section (\d+):',e)] if m and int(m.group(1))<len(beats)]))
    total=sum(len(b.get('say','').split()) for b in beats if isinstance(b.get('say'),str))
    if not bad and total<430:
        bad=sorted(range(len(beats)),key=lambda i:len(beats[i]['say'].split()))[:4]
    elif not bad and total>650:
        bad=sorted(range(len(beats)),key=lambda i:len(beats[i]['say'].split()),reverse=True)[:4]
    if not bad:return plan
    bad=sorted(bad[:4])
    raw=call('Repair only invalid narration sections. Return JSON only.',
        'Return {"replacements":[{"index":integer,"say":"32-40 spoken words"}]}. Return exactly the requested indices, no others. Correct every listed factual error; use natural causal explanation, and a question ending ? for index 0. Do not change topic, title, hook, actions or cameras. Do not write production instructions or invent parts. ERRORS: '+json.dumps(issues or [])+' REQUESTED: '+json.dumps([{'index':i,'action':beats[i]['action'],'say':beats[i].get('say'),'measured_word_count':len(beats[i].get('say','').split()),'visible_facts':mechanism_facts(plan['mechanism'])[beats[i]['action']]} for i in bad])+' MECHANISM: '+json.dumps(SOURCES[plan['mechanism']]),max_tokens=1800,temperature=.2)
    (out/f'section-repair-{attempt}.json').write_text(json.dumps(raw,indent=2))
    replacements=raw.get('replacements') if isinstance(raw,dict) else None
    if not isinstance(replacements,list) or sorted(x.get('index',-1) for x in replacements)!=bad:return plan
    result=copy.deepcopy(plan)
    for item in replacements:
        if isinstance(item.get('say'),str) and 20<=len(item['say'].split())<=50:result['beats'][item['index']]['say']=item['say']
    return result

def unsupported_comparison(topic,mechanism):
    text=topic.lower()
    if mechanism=='cam_follower':return bool(re.search(r'sinusoid|simple harmonic|dwell|vary.{0,15}(profile|eccentricity)',text))
    if mechanism=='rack_pinion':return bool(re.search(r'(diameter|pinion size).{0,45}(increas|decreas|chang|differ)|(?:larger|smaller|bigger).{0,15}pinion',text))
    return bool(re.search(r'(?:chang|vary|differ|compar).{0,25}(?:lead|pitch)|self.lock|back.driv',text))


def repair_metadata(plan,out,attempt=0):
    title=plan.get('title','');hook=plan.get('hook','')
    bad_title=not isinstance(title,str) or not re.match(r'^(How|Why)\b',title) or not 4<=len(title.split())<=8
    bad_hook=not isinstance(hook,str) or not 2<=len(hook.split())<=7 or len(hook)>40
    if not bad_title and not bad_hook:return plan
    raw=call('Repair explainer title metadata only. Return JSON only.',
      'Return {"title":"How/Why followed by plain words, 4-8 words total","hook":"2-7 simple words, at most 40 characters"}. Keep the subject unchanged; no emoji, subtitles or production jargon. TOPIC: '+json.dumps(plan.get('topic'))+' CURRENT: '+json.dumps({'title':title,'hook':hook}),max_tokens=350,temperature=.2)
    (out/f'metadata-repair-{attempt}.json').write_text(json.dumps(raw,indent=2))
    result=copy.deepcopy(plan)
    if bad_title and isinstance(raw.get('title'),str):result['title']=raw['title']
    if bad_hook and isinstance(raw.get('hook'),str):result['hook']=raw['hook']
    return result
