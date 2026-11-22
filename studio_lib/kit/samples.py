"""Hand-checked sample recipes used to prove the kit (NOT scheduled; the recipe writer makes new ones)."""
DOOR_LATCH={'object':'door latch','title':'How a door latch clicks shut','theme':'warm',
 'parts':[{'id':'frame','kind':'frame','x':0,'z':0,'w':7,'h':3.6},
  {'id':'handle','kind':'lever','pivot':[-1.7,2.6],'length':1.6,'angle0':0},
  {'id':'bolt','kind':'slider','origin':[-0.3,1.9],'size':[3.2,3.0],'axis':'x','travel':1.0,'dir':-1},
  {'id':'spring','kind':'spring','a':[3.3,1.9],'b':{'part':'bolt'}},
  {'id':'pin','kind':'pin','center':[-1.7,2.6],'r':.2}],
 'labels':{'handle':'Handle','bolt':'Latch bolt','spring':'Spring'},
 'links':[{'type':'yoke','lever':'handle','slider':'bolt','sign':-1}],
 'drive':[{'beat':2,'part':'handle','to':-1.0},{'beat':3,'part':'handle','to':-1.0},{'beat':4,'part':'handle','to':0},{'beat':5,'part':'handle','to':0}]}
GEAR_CRANK={'object':'hand mixer','title':'How a hand mixer spins the beaters','theme':'cool',
 'parts':[{'id':'frame','kind':'frame','x':0,'z':0,'w':7,'h':4.2},
  {'id':'crank','kind':'lever','pivot':[-2.4,2.0],'length':.9,'angle0':0},
  {'id':'big','kind':'gear','center':[-2.4,2.0],'r':1.1,'teeth':22},
  {'id':'left','kind':'gear','center':[-.3,2.0],'r':1.0,'teeth':20},
  {'id':'right','kind':'gear','center':[1.7,2.0],'r':1.0,'teeth':20}],
 'labels':{'crank':'Crank','big':'Drive gear','left':'Beater gear'},
 'links':[{'type':'mesh','a':'big','b':'left'},{'type':'mesh','a':'left','b':'right'},{'type':'couple','driver':'big','driven':'crank','ratio':1.0}],
 'drive':[{'beat':1,'part':'big','to':6.28},{'beat':2,'part':'big','to':12.5},{'beat':3,'part':'big','to':18.8},{'beat':4,'part':'big','to':25.1},{'beat':5,'part':'big','to':31.4}]}
CAM_PRESS={'object':'cam press','title':'How a cam lifts a plunger','theme':'dark',
 'parts':[{'id':'frame','kind':'frame','x':0,'z':0,'w':5,'h':4.0},
  {'id':'cam','kind':'cam','center':[0,1.3],'r':.9,'e':.35},
  {'id':'plunger','kind':'slider','origin':[0,2.15],'size':[.9,.6],'axis':'z','travel':.7},
  {'id':'spring','kind':'spring','a':[0,3.8],'b':{'part':'plunger'}}],
 'labels':{'cam':'Cam','plunger':'Plunger','spring':'Return spring'},
 'links':[{'type':'cam','cam':'cam','follower':'plunger'}],
 'drive':[{'beat':1,'part':'cam','to':3.0},{'beat':2,'part':'cam','to':6.3},{'beat':3,'part':'cam','to':9.4},{'beat':4,'part':'cam','to':12.6},{'beat':5,'part':'cam','to':15.7}]}
ROPE_LIFT={'object':'pulley','title':'How a pulley lowers a weight','theme':'cool',
 'parts':[{'id':'frame','kind':'frame','x':0,'z':0,'w':5,'h':4.4},
  {'id':'wheel','kind':'pulley','center':[0,3.4],'r':.8},
  {'id':'weight','kind':'slider','origin':[.8,2.6],'size':[.7,.7],'axis':'z','travel':1.7,'dir':-1},
  {'id':'pin','kind':'pin','center':[0,3.4],'r':.15}],
 'labels':{'wheel':'Pulley','weight':'Weight','pin':'Axle'},
 'links':[{'type':'rope','pulley':'wheel','slider':'weight','ratio':1.0}],
 'drive':[{'beat':2,'part':'wheel','to':.8},{'beat':3,'part':'wheel','to':1.6},{'beat':4,'part':'wheel','to':2.1},{'beat':5,'part':'wheel','to':.6}]}
SAMPLES=('DOOR_LATCH','GEAR_CRANK','CAM_PRESS','ROPE_LIFT')
def with_facts(recipe):
 import copy;r=copy.deepcopy(recipe)
 r['facts']={a:'Fixture description of what is visible during the '+a+' beat of this simplified model.' for a in ('intro','reveal','step1','step2','step3','step4','hold','payoff')}
 return r
