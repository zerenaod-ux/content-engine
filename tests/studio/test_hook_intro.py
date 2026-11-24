import subprocess,tempfile,pathlib,pytest
from studio_lib import hook_intro as h

def test_command_takes_middle_zoomed_teaser_then_full_video():
    c=' '.join(h.command('in.mp4','out.mp4',40.0))
    assert 'trim=start=18.750:duration=2.5' in c and 'eval=frame' in c and 'concat=n=2' in c

def test_real_file_gets_hook_and_is_longer(tmp_path,monkeypatch):
    monkeypatch.setenv('CE_HOOK_INTRO','on')
    src=tmp_path/'in.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=360x640:rate=30:duration=8','-f','lavfi','-i','sine=duration=8','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(src)],check=True)
    assert h.deliver(src,tmp_path/'out.mp4') is True
    assert abs(h._duration(tmp_path/'out.mp4')-(h._duration(src)+h.HOOK_SECONDS))<0.3

def test_failure_delivers_original(tmp_path):
    src=tmp_path/'bad.mp4';src.write_bytes(b'not a video')
    assert h.deliver(src,tmp_path/'out.mp4') is False and (tmp_path/'out.mp4').read_bytes()==b'not a video'

def test_wordless_uses_foley_audio(tmp_path,monkeypatch):
    monkeypatch.setenv('CE_HOOK_INTRO','on')
    src=tmp_path/'in.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=360x640:rate=30:duration=6','-f','lavfi','-i','sine=duration=6','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(src)],check=True)
    wav=tmp_path/'foley.wav';subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','anoisesrc=d=6:r=24000','-ac','1',str(wav)],check=True)
    assert h.deliver_wordless(src,wav,tmp_path/'o-wordless.mp4') is True and (tmp_path/'o-wordless.mp4').exists()
    assert h.deliver_wordless(src,tmp_path/'none.wav',tmp_path/'x.mp4') is False

def test_hook_is_off_by_default(tmp_path,monkeypatch):
    monkeypatch.delenv('CE_HOOK_INTRO',raising=False)
    src=tmp_path/'a.mp4';src.write_bytes(b'x');assert h.deliver(src,tmp_path/'b.mp4') is False and (tmp_path/'b.mp4').read_bytes()==b'x'
