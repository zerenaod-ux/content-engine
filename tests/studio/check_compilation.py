import subprocess,pytest
from studio_lib import compilation as C

def clip(path,sec):
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'testsrc=s=270x480:d={sec}:r=30','-f','lavfi','-i',f'sine=d={sec}','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(path)],check=True)
    return path

def rows(n):
    v=[{'tag':f't{i}','video':f'https://x/{i}.mp4','title':f'Machine {i}','mechanism':f'm{i//2}','format':'short','kind':'short','date':f'2026-11-{i+1:02d}'} for i in range(n)]
    idx=[{'tag':r['tag'],'folder':'saved'} for r in v]
    return v,idx

def test_candidates_only_saved_max_two_per_machine():
    v,idx=rows(6);idx[0]['folder']='deleted'
    v.append({'tag':'ce-long-1','video':'https://x/l.mp4','mechanism':'z','format':'compilation'})
    got=C.candidates(v,idx)
    assert 't0' not in [r['tag'] for r in got] and 'ce-long-1' not in [r['tag'] for r in got]
    from collections import Counter
    assert max(Counter(r['mechanism'] for r in got).values())<=2

def test_choose_needs_enough():
    v,_=rows(3)
    with pytest.raises(ValueError):C.choose(v,{r['tag']:50 for r in v})

def test_choose_lands_in_window():
    v,_=rows(14)
    pick,total=C.choose(v,{r['tag']:45 for r in v})
    assert 480<=total<=600

def test_build_end_to_end(tmp_path,monkeypatch):
    monkeypatch.setattr(C,'MIN_TOTAL',25.);monkeypatch.setattr(C,'MAX_TOTAL',60.);monkeypatch.setattr(C,'CLIP_MIN',1.)
    v,idx=rows(3)
    def fetch(url,dest):return clip(dest,4)
    out=tmp_path/'o'/'long.mp4'
    p=C.make(v,idx,[],tmp_path/'w',out,fetch=fetch,speaker=lambda l,w:{})
    assert out.exists() and (out.parent/'chapters.txt').exists()
    assert p['duration']>=25 and len(p['chapters'])>=2
    assert abs(C.probe(out)-p['duration'])<1
