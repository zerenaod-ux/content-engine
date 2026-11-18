"""Bounded model-only narration length repair preserving unchanged sections."""
import copy,json
from studio_lib.providers import call

def repair_length(plan,brief,out,attempt):
    beats=plan.get('beats',[]) if isinstance(plan,dict) else []
    if len(beats)!=8 or any(not isinstance(b.get('say'),str) for b in beats):return plan
    sizes=[len(b['say'].split()) for b in beats];total=sum(sizes)
    selected={i for i,n in enumerate(sizes) if not 9<=n<=23}
    if total<140:
        gain=sum(max(0,21-sizes[i]) for i in selected)
        for i in sorted(range(8),key=lambda i:sizes[i]):
            if total+gain>=154:break
            if i not in selected:selected.add(i);gain+=max(0,21-sizes[i])
    if total>176:
        for i in sorted(range(8),key=lambda i:-sizes[i]):
            selected.add(i)
            if total-sum(max(0,sizes[j]-19) for j in selected)<=168:break
    if not selected:return plan
    indexes=sorted(selected)
    raw=call('Repair only selected spoken sections to meet the duration writing budget. Return JSON only.',
      'Return {"replacements":[{"index":integer,"say":"20-22 spoken words"}]}. Exactly the requested indices, no others. Keep the same facts and action, retain an opening question ending ? at index 0. Do not narrate camera or production. Unchanged words total '+str(sum(n for i,n in enumerate(sizes) if i not in selected))+'. Whole plan must total 140-176 words. REQUESTED: '+json.dumps([{'index':i,'say':beats[i]['say'],'action':beats[i]['action'],'facts':brief['facts'].get(beats[i]['action'],'')} for i in indexes]),max_tokens=1600,temperature=.2)
    (out/f'length-repair-{attempt}.json').write_text(json.dumps(raw,indent=2))
    rows=raw.get('replacements') if isinstance(raw,dict) else None
    if not isinstance(rows,list) or sorted(r.get('index',-1) for r in rows)!=indexes:return plan
    if any(not isinstance(r.get('say'),str) or not 9<=len(r['say'].split())<=23 for r in rows):return plan
    fixed=copy.deepcopy(plan)
    for row in rows:fixed['beats'][row['index']]['say']=row['say']
    return fixed
