"""Variety: stop two similar videos in a row. (owner 2026-11-27: 'no creativity, similar videos')
prefer() drops machines of the same KIND as the latest video when anything different is still available.
hook_style() rotates the style of the opening question so consecutive videos do not start alike."""
KIND={
 'gears':{'rack_pinion','worm_gear','chain_sprocket','winch_crane','geneva_drive','ratchet_wrench'},
 'linkage':{'wiper_linkage','crank_slider','scissor_jack','lever_fulcrum','cam_follower'},
 'rope':{'pulley_lift'},
 'lock':{'pin_lock','combination_lock'},
}
HOOKS=('a surprising everyday puzzle about the result',
       'what would go wrong if one key part were missing',
       'a size or number comparison that sounds impossible',
       'a what-happens-if question about the first moving part')
def kind(m):
 for k,v in KIND.items():
  if m in v:return k
 return m
def last_machine(rows):
 for r in reversed(rows):
  m=r.get('mechanism') or r.get('subject')
  if isinstance(m,str) and m:return m
def prefer(pairs,rows):
 last=last_machine(rows)
 if not last:return pairs
 other=[p for p in pairs if kind(p[0])!=kind(last)]
 return other or pairs
def hook_style(rows):
 n=sum(1 for r in rows if r.get('mechanism') or r.get('subject'))
 return HOOKS[n%len(HOOKS)]
