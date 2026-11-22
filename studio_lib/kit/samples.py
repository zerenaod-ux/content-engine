"""Hand-checked sample recipes used to prove the kit (NOT scheduled; the idea bank will write recipes later)."""
DOOR_LATCH={'title':'How a door latch clicks shut','theme':'warm',
 'parts':[{'id':'frame','kind':'frame','x':0,'z':0,'w':7,'h':3.4},
  {'id':'handle','kind':'lever','pivot':[-2.2,1.7],'length':1.8,'angle0':0},
  {'id':'bolt','kind':'slider','origin':[1.0,1.7],'size':[2.6,.7],'axis':'x','travel':1.1},
  {'id':'spring','kind':'spring','a':[3.0,1.7],'b':{'part':'bolt'}},
  {'id':'pin','kind':'pin','center':[-2.2,1.7],'r':.2}],
 'labels':{'handle':'Handle','bolt':'Latch bolt','spring':'Spring'},
 'links':[{'type':'couple','driver':'handle','driven':'bolt','ratio':-1.0,'offset':0}],
 'drive':[{'beat':2,'part':'handle','to':-.9},{'beat':3,'part':'handle','to':-.9},{'beat':4,'part':'handle','to':0},{'beat':5,'part':'handle','to':0}]}
GEAR_CRANK={'title':'How a hand mixer spins the beaters','theme':'cool',
 'parts':[{'id':'frame','kind':'frame','x':0,'z':0,'w':7,'h':4.2},
  {'id':'crank','kind':'lever','pivot':[-2.4,2.0],'length':1.2,'angle0':0},
  {'id':'big','kind':'gear','center':[-2.4,2.0],'r':1.1,'teeth':22},
  {'id':'left','kind':'gear','center':[-.3,2.0],'r':1.0,'teeth':20},
  {'id':'right','kind':'gear','center':[1.7,2.0],'r':1.0,'teeth':20}],
 'labels':{'crank':'Crank','big':'Drive gear','left':'Beater gear'},
 'links':[{'type':'mesh','a':'big','b':'left'},{'type':'mesh','a':'left','b':'right'},{'type':'couple','driver':'big','driven':'crank','ratio':1.0}],
 'drive':[{'beat':1,'part':'big','to':6.28},{'beat':2,'part':'big','to':12.5},{'beat':3,'part':'big','to':18.8},{'beat':4,'part':'big','to':25.1},{'beat':5,'part':'big','to':31.4}]}
