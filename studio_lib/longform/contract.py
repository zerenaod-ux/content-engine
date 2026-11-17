"""Explicit supported long-format mechanisms and measurable narrative contract."""
import math,re
ACTIONS=['question','parts','input','contact','forward','guide','reverse','distance','detail','force','work','control','limits','application','recap','payoff']
SOURCES={
 'rack_pinion':{'source':'https://khkgears.us/media/wjon4hs3/gear-solutions_khk_converting-to-linear-motion-using-rack-and-pinion.pdf','scope':'A bench rack-and-pinion with a fixed bearing, marked rotating pinion, meshing straight rack and translating carriage; not a complete car steering system.','relation':'Rack displacement equals pitch radius times pinion angle, without slip in the ideal geometry. Reverse rotation reverses travel.'},
 'lead_screw':{'source':'https://www.thomsonlinear.com/en/products/lead-screws/','scope':'A rotating lead screw in fixed supports, a nonrotating nut attached to a guided translating carriage; not a ball screw or complete motor.','relation':'Nut travel equals screw lead times turns. The guide prevents the nut from rotating; reversing rotation reverses travel.'}}
FACTS={
 'question':'The assembled mechanism is moving slowly; ask a concrete question about rotation becoming straight travel.',
 'parts':'The same assembly remains visible. Identify fixed supports, rotating input and guided translating output.',
 'input':'The marked input shaft rotates. No person or electric motor internals are shown.',
 'contact':'Close inspection shows the mechanical engagement transmitting force. This is enlarged simplified geometry, not a calibrated contact-stress simulation.',
 'forward':'Input turns forward and the guided carriage travels in one direction.',
 'guide':'The output carriage remains on two rails; the guide constrains its motion.',
 'reverse':'Input reverses and the same carriage returns in the opposite direction.',
 'distance':'Motion continues; explain the documented travel-per-turn relationship qualitatively without inventing numeric units.',
 'detail':'An enlarged view exposes the engagement while the same input and output remain connected.',
 'force':'Engagement transfers input force to the guided output. No force sensor, stress color map or numerical force measurement is shown.',
 'work':'Continued movement requires input work; friction and losses are not simulated. Never claim free energy.',
 'control':'A slower illustrative operating cycle demonstrates the direction relationship, not an electronic feedback controller.',
 'limits':'The assembly stays within its shown travel. End stops are visible; no collision, breakage or safety-certified controller is shown.',
 'application':'Explain the mechanism as a building block, not a rendered factory, vehicle or complete product.',
 'recap':'The same mechanism moves again; connect rotation, engagement and straight travel.',
 'payoff':'Finish on the original question with the mechanism still connected and moving. No unrelated topic.'}

def errors(plan):
 out=[]
 if not isinstance(plan,dict):return ['Plan must be an object']
 if plan.get('mechanism') not in SOURCES:out.append('Unsupported full-video mechanism')
 if not isinstance(plan.get('topic'),str) or len(plan.get('topic','').split())<4:out.append('Missing single topic')
 if not isinstance(plan.get('title'),str) or (not re.match(r'^(How|Why)\b',plan.get('title','')) or not 4<=len(plan.get('title','').split())<=8):out.append('Title must start How/Why')
 if not isinstance(plan.get('hook'),str) or not 2<=len(plan.get('hook','').split())<=7 or len(plan.get('hook',''))>40:out.append('Hook needs 2-7 simple words, at most 40 characters')
 beats=plan.get('beats',[])
 if not isinstance(beats,list) or [b.get('action') for b in beats if isinstance(b,dict)]!=ACTIONS:return out+['Preserve the sixteen causal actions in order']
 for b in beats:
  if not isinstance(b.get('say'),str) or not 30<=len(b.get('say','').split())<=44:out.append('Each chapter needs 30-44 spoken words')
  if b.get('camera') not in ('wide','engagement','output'):out.append('Unsupported camera')
  if re.search(r'\b(camera|render|shot|storyboard|zoom)\b',b.get('say',''),re.I):out.append('Narration must explain the mechanism, not production')
 if not beats[0].get('say','').rstrip().endswith('?'):out.append('Opening must be a question')
 if not 480<=sum(len(b.get('say','').split()) for b in beats)<=650:out.append('Narration must total 480-650 words')
 return out

def motion(t,beat,timeline=None):
 """Smooth bounded travel; rotation derives from travel, never independently."""
 if timeline:
  beats=timeline['beats'];i=min(len(beats)-1,next((j for j,b in enumerate(beats) if t<b['end']),len(beats)-1))
  targets=[0,-.4,-1.2,-.7,1.2,1.2,-1.2,1.2,-1.2,1.2,-1.2,1.2,0,.8,-.8,.8]
  b=beats[i];p=max(0,min(1,(t-b['start'])/(b['end']-b['start'])));p=p*p*(3-2*p)
  start=targets[i-1] if i else -.4;travel=start+(targets[i]-start)*p
 else:travel=1.45*math.sin(.20*t)
 if beat=='rack_pinion':return {'travel':travel,'angle':-travel/.6}
 return {'travel':travel,'angle':travel/.45*2*math.pi}

def require_media(seconds,width,height):
 if not math.isfinite(seconds) or not 120<=seconds<=300:raise ValueError('Original full video must measure 120–300 seconds')
 if width*9!=height*16:raise ValueError('Full video must be native 16:9')
