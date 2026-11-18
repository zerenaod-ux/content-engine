"""Shared complete-output gate. Missing evidence is a failure, never a pass."""
import hashlib,json,math
from pathlib import Path
FILES=('video.mp4','audio-review.json','narration-critique.json')

def file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def check_evidence(root,kind):
    root=Path(root);errors=[]
    if kind not in ('short','original_full'):raise ValueError('Unknown production format')
    for name in FILES:
        if not (root/name).is_file():errors.append('Required evidence missing: '+name)
    if errors:return errors
    audio=json.loads((root/'audio-review.json').read_text());critique=json.loads((root/'narration-critique.json').read_text())
    if audio.get('errors')!=[]:errors.append('Encoded audio did not pass')
    if critique.get('errors')!=[]:errors.append('Narration/action contract did not pass')
    for key in ('integrated_lufs','true_peak_dbfs','independent_asr_word_error_rate'):
        value=audio.get(key)
        if not isinstance(value,(int,float)) or not math.isfinite(value):errors.append('Audio measurement missing: '+key)
    if isinstance(audio.get('independent_asr_word_error_rate'),(int,float)) and audio['independent_asr_word_error_rate']>.25:errors.append('Narration transcription mismatch')
    if isinstance(audio.get('integrated_lufs'),(int,float)) and not -20<=audio['integrated_lufs']<=-12:errors.append('Loudness outside range')
    if isinstance(audio.get('true_peak_dbfs'),(int,float)) and audio['true_peak_dbfs']>-.8:errors.append('Audio peaks outside range')
    return errors

def seal(root,kind,media):
    root=Path(root);errors=check_evidence(root,kind)
    duration=float(media['duration']);width=int(media['width']);height=int(media['height'])
    bounds=(40,70) if kind=='short' else (120,300)
    if not math.isfinite(duration) or not bounds[0]<=duration<=bounds[1]:errors.append('Encoded duration outside format range')
    if kind=='original_full' and width*9!=height*16:errors.append('Full video is not native landscape')
    if kind=='short' and height<=width:errors.append('Short video is not portrait')
    if errors:raise ValueError('Complete-output gate rejected: '+str(errors))
    names=list(FILES)+(['accepted-plan.json'] if kind=='original_full' else ['plan.json'])
    if not all((root/name).is_file() for name in names):raise ValueError('Generated plan evidence missing')
    report={'format':kind,'errors':[],'duration':duration,'width':width,'height':height,'checks':'encoded media, audio, narration contract, file integrity','hashes':{name:file_hash(root/name) for name in names},'owner_approved':False,'human_visual_review_completed':False,'human_listening_completed':False}
    (root/'quality-gate.json').write_text(json.dumps(report,indent=2));return report

def require_seal(root,kind):
    root=Path(root);path=root/'quality-gate.json'
    if not path.is_file():raise ValueError('Complete-output evidence is missing; delivery refused')
    report=json.loads(path.read_text())
    if report.get('format')!=kind or report.get('errors')!=[] or report.get('owner_approved') is not False:raise ValueError('Complete-output evidence invalid')
    required=list(FILES)+(['accepted-plan.json'] if kind=='original_full' else ['plan.json'])
    hashes=report.get('hashes',{})
    if set(hashes)!=set(required):raise ValueError('Incomplete evidence manifest')
    for name,expected in hashes.items():
        if not (root/name).is_file() or file_hash(root/name)!=expected:raise ValueError('Media or evidence changed after verification: '+name)
    errors=check_evidence(root,kind)
    if errors:raise ValueError('Complete-output evidence no longer passes: '+str(errors))
    return report
