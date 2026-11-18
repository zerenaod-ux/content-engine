"""Model-written local repairs; valid chapters and metadata remain byte-for-byte intact."""
import copy,json,re
from studio_lib.providers import call
from studio_lib.longform.contract import FACTS,SOURCES,mechanism_facts

def repair_sections(plan,out,attempt=0):
    beats=plan.get('beats',[])
    if not isinstance(beats,list) or len(beats)!=16:return plan
    bad=[i for i,b in enumerate(beats) if not isinstance(b.get('say'),str) or not 30<=len(b['say'].split())<=44]
    if not bad:return plan
    bad=bad[:4]
    raw=call('Repair only invalid narration sections. Return JSON only.',
        'Return {"replacements":[{"index":integer,"say":"32-40 spoken words"}]}. Return exactly the requested indices, no others. Keep meaning and factual scope, natural causal explanation, and a question ending ? for index 0. Do not change topic, title, hook, actions or cameras. Do not write production instructions or invent parts. REQUESTED: '+json.dumps([{'index':i,'action':beats[i]['action'],'say':beats[i].get('say'),'visible_facts':mechanism_facts(plan['mechanism'])[beats[i]['action']]} for i in bad])+' MECHANISM: '+json.dumps(SOURCES[plan['mechanism']]),max_tokens=1800,temperature=.2)
    (out/f'section-repair-{attempt}.json').write_text(json.dumps(raw,indent=2))
    replacements=raw.get('replacements') if isinstance(raw,dict) else None
    if not isinstance(replacements,list) or sorted(x.get('index',-1) for x in replacements)!=bad:return plan
    if any(not isinstance(x.get('say'),str) or not 30<=len(x['say'].split())<=44 for x in replacements):return plan
    result=copy.deepcopy(plan)
    for item in replacements:result['beats'][item['index']]['say']=item['say']
    return result

def unsupported_comparison(topic,mechanism):
    text=topic.lower()
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
