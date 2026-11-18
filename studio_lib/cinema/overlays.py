"""Minimal presentation defaults: a short opening hook, optional speech captions."""
import re
from studio_lib.cinema.presentation import illustration_labels

def hook_errors(hook):
    if not isinstance(hook,str) or not hook.strip():return ['A short opening hook is required.']
    if len(hook)>40 or len(hook.split())>7:return ['Hook must use at most seven words and 40 characters.']
    if re.search(r'\b(schematic|illustrative|progress|simulation|render|semantic)\b',hook,re.I):return ['Hook needs simple curiosity words, not production/disclosure jargon.']
    return []

def events(timeline):
    rows=[];beats=timeline.get('beats',[]);hook=timeline.get('hook','')
    if hook and not hook_errors(hook):
        rows.append({'start':0,'end':min(3.5,beats[0]['end'] if beats else 3.5),'text':hook,'role':'hook','position':(360,170),'size':48,'alignment':8})
    mechanism=timeline.get('mechanism')
    if timeline.get('diagram') and beats:
        rows.append({'start':max(3.5,beats[0]['end']),'end':timeline['duration'],'text':'Illustration','role':'badge','position':(70,1160),'size':20,'alignment':1})
    for start,end,text in illustration_labels(beats,mechanism):
        short={'Magnetic field: schematic illustration':'Magnetic field · illustration',
               'Circuit markers: illustrative, not to scale':'Current path · illustration',
               'Airflow: schematic illustration':'Airflow · illustration'}[text]
        rows.append({'start':start,'end':end,'text':short,'role':'effect','position':(360,90),'size':24,'alignment':8})
    return rows
