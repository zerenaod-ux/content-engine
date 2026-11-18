"""Optional release archive, with durable Pages media as the required archive."""
import json,urllib.error

def release_or_record(api,get,path,body,out=None):
    old=get(path)
    if old:return old
    try:return api('POST','releases',body)
    except urllib.error.HTTPError as e:
        if e.code!=403:raise
        # GitHub may forbid a release tag on a test-branch source commit even
        # when Pages contents are writable. Never broaden credentials or silently
        # claim a release exists; the immutable Pages copy is already durable.
        if out is not None:
            out.write_text(json.dumps({'release_archive':'unavailable','status':403,'durable_media':'immutable GitHub Pages commit','source_run':body.get('body','').split('Source run: ')[-1]},indent=2))
        print('Release archive was refused; retaining the durable Pages media and explicit archive warning',flush=True)
        return None
