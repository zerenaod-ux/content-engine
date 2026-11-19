"""Replace only an undecided diagnostic card with its verified correction."""
import json,os,re,shutil,subprocess,time,urllib.error
from pathlib import Path
from studio_lib.service_queue import github,read_document,write_document
from studio_lib.quality_gate import require_seal

def guard(card,tag):
 labels={x['name'] for x in card.get('labels',[])}
 if card.get('state')!='open' or labels&{'ce-approve','ce-skip'}:raise ValueError('Preserve existing owner decision; correction cannot replace this card')
 if tag not in card.get('body',''):raise ValueError('Correction target does not match the existing review card')

def updated_rows(rows,tag,url,source):
 matches=[row for row in rows if row.get('tag')==tag]
 if len(matches)!=1:raise ValueError('Existing diagnostic index entry is missing or ambiguous')
 result=json.loads(json.dumps(rows));row=next(row for row in result if row.get('tag')==tag)
 if row.get('video')!=url:
  prior=row.setdefault('previous_versions',[])
  if row.get('video') and row['video'] not in prior:prior.append(row['video'])
  row['video']=url
 row['correction_source_run']=str(source);return result

def command(*args):return subprocess.check_output(args,text=True).strip()
def main():
 raise ValueError('Completed-video replacement is retired by the permanent no-repeat rule; preserve the existing review decision')

if __name__=='__main__':main()
