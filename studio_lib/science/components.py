"""Reusable explanatory diagram components, not arbitrary photorealistic scenes."""
import math
from studio_lib.science.models import lever,resistor,hydraulics,heat_contact,complementary_dna,transfer_water
ACTIONS=['overview','parts','input','change','transfer','result','limits','payoff']
SPECS={
 'lever_balance':('Ideal lever', 'https://www.grc.nasa.gov/www/k-12/WindTunnel/Activities/Pascals_principle.html',[
  'A rigid lever rests on a fixed fulcrum; ask how a longer arm helps lift a load.',
  'The input arm is twice the output arm. The fulcrum stays fixed and both ends belong to the same bar.',
  'A downward input arrow acts on the long left arm; the right load is initially lower.',
  'The long end moves down while the short end rises. Do not describe gears, motors or a person.',
  'The diagram represents torque balance: ideal force gain trades increased input travel.',
  'The right-hand load has risen; no additional energy has been created.',
  'This ideal lever ignores friction and bar weight. Arrows illustrate forces, not visible objects.',
  'The longer input arm reduces required input force while requiring greater travel.']),
 'resistive_circuit':('DC resistor circuit','https://openstax.org/books/physics/pages/19-1-ohms-law',[
  'An ideal DC source connects through an open switch to an ohmic resistor; ask why the load has no current.',
  'The source, wire loop, switch and resistor are shown as a schematic, not a real product.',
  'The source maintains voltage, but the open switch interrupts the only conductive path. No load current yet.',
  'The switch closes, completing the path through the resistor.',
  'Markers illustrate conventional current after closure, not literal electrons or their physical speed.',
  'With a closed circuit, current equals source voltage divided by resistance; the resistor dissipates electrical power.',
  'This ideal DC resistor model ignores source resistance and transients; no battery chemistry or LED is shown.',
  'Opening interrupts current; the demonstrated final circuit remains closed. Do not narrate reopening.']),
 'hydraulic_lift':('Hydraulic lift','https://www.grc.nasa.gov/www/k-12/WindTunnel/Activities/Pascals_principle.html',[
  'A simplified connected pair of hydraulic cylinders can lift a load; ask how piston areas change force.',
  'A small input piston and a larger output piston share a confined incompressible fluid.',
  'An input force pushes the small piston down. No pump motor or control valve is depicted.',
  'The small piston descends while the larger piston rises through a shorter distance.',
  'The same additional pressure reaches the connected fluid; force equals pressure times piston area.',
  'The larger piston supports greater force but moves less; the displaced fluid volumes match.',
  'This idealized equal-height calculation ignores leakage, friction, compressibility and pipe losses.',
  'Hydraulics trades input travel for output force and still requires mechanical work.']),
 'thermal_contact':('Heat between contacting bodies','https://bsesc.energy.gov/energy-basics/heat-flow',[
  'A warmer body touches a cooler body; ask which way thermal energy moves.',
  'Two adjacent blocks share a contact surface. Their colors encode temperature, not visible glowing heat.',
  'The initial temperature difference allows energy transfer from the warmer body toward the cooler one.',
  'The warmer body cools while the cooler body warms. Both solid bodies remain in place.',
  'An arrow illustrates net thermal-energy transfer through contact, not material flowing between blocks.',
  'The temperatures approach the same equilibrium value while total energy is conserved.',
  'This isolated two-body model has constant heat capacities and no phase change. Progress is illustrative, not a real-time prediction.',
  'At thermal equilibrium there is no net heat transfer between the two bodies.']),
 'dna_pairing':('DNA base pairing','https://www.genome.gov/genetics-glossary/Base-Pair',[
  'A short schematic DNA strand faces its matching bases; ask how complementary pairing works.',
  'The template has A, T, C and G bases. These colored blocks are enlarged molecular symbols.',
  'The opposite bases are aligned in complementary order. This is not a full DNA replication simulation.',
  'Complementary bases move into paired positions: A with T and C with G.',
  'Connecting rungs illustrate complementary base pairs rather than mechanical links between giant blocks.',
  'The completed schematic has complementary strands running in opposite directions, called antiparallel.',
  'This diagram omits enzymes, molecular motion, timing, the helical shape and error correction.',
  'Complementary pairing is one part of DNA structure; do not claim the whole genome has been copied.']),
 'water_transfer':('Water between reservoirs','https://www.usgs.gov/special-topics/water-science-school/water-cycle',[
  'Water is stored in two schematic reservoirs; ask what happens to their totals when water moves.',
  'Two containers are connected by an illustrative transfer path. No pump, rainfall or evaporation is depicted.',
  'The first reservoir supplies water to the second; this bookkeeping illustration does not model the driving force.',
  'The source level drops as the destination level rises, with neither volume becoming negative.',
  'The transfer path marks the direction of movement, not an engineered gravity-flow or pump layout.',
  'The amount leaving the source equals the amount entering the destination.',
  'This closed two-reservoir model omits rates, weather, energy requirements and the full water cycle.',
  'Water has changed its storage location; the combined volume remains the same.']),
}

def contract(mechanism):
    title,source,facts=SPECS[mechanism]
    return {'description':title+'; enlarged labeled explanatory diagram only',
      'actions':ACTIONS,'facts':dict(zip(ACTIONS,facts)),'source':source,
      'presentation_rules':{'style':'Silent smooth camera; all overlays and time/scale simplifications labeled. No invented visible actions.',
      'scope':'Explain only this component; never claim a whole device/process is demonstrated when it is not.'}}

def diagram(mechanism,p):
    if mechanism not in SPECS:raise ValueError('Unsupported diagram')
    if not isinstance(p,(int,float)) or isinstance(p,bool) or not math.isfinite(p) or not 0<=p<=1:raise ValueError('Progress 0..1 required')
    objects=[];labels=[]
    def box(name,at,size,color):objects.append(dict(id=name,kind='box',at=at,size=size,color=color))
    def ball(name,at,radius,color):objects.append(dict(id=name,kind='ball',at=at,radius=radius,color=color))
    def path(name,points,color,radius=.035):objects.append(dict(id=name,kind='line',points=points,radius=radius,color=color))
    def label(text,at):labels.append(dict(text=text,at=at))
    blue=(.08,.45,.8);red=(.85,.18,.10);gold=(.9,.65,.12);gray=(.45,.55,.6)
    if mechanism=='lever_balance':
        a=.25*p
        left=(-2*math.cos(a),0,2-2*math.sin(a));right=(math.cos(a),0,2+math.sin(a))
        path('rigid_bar',[left,right],gold,.09);box('fulcrum',(0,0,1),(.5,.6,2),gray)
        box('load',(right[0],0,right[2]+.25),(.45,.5,.5),blue)
        path('input_arrow',[(left[0],0,left[2]+1),left],red)
        label('Input: longer travel',(-2.2,0,3.5));label('Load: shorter travel',(.6,0,3.5))
        values=lever(10,2,1)
    elif mechanism=='resistive_circuit':
        closed=p>=.25
        path('wire',[(-2,0,1),(-2,0,3),(-.5,0,3)],gray)
        path('return',[(.5,0,3),(2,0,3),(2,0,1),(-2,0,1)],gray)
        path('switch',[(-.5,0,3),(.5,0,3 if closed else 3.6)],gold)
        box('source',(-2,0,2),(.45,.5,.8),blue);box('resistor',(2,0,2),(.45,.5,.8),red)
        ball('conventional_current_marker',(-2+4*max(0,p-.25)/.75,0,1),.09, gold if closed else gray)
        label('Ideal DC source',(-2,0,4));label('Ohmic resistor',(1,0,4));values=resistor(12,6,closed)
    elif mechanism=='hydraulic_lift':
        x=hydraulics(10,1,4,1.2*p);left=2-1.2*p;right=1+x['output_distance']
        path('confined_fluid',[(-2,0,left),(-2,0,.5),(1.5,0,.5),(1.5,0,right)],blue,.12)
        for xx,w in ((-2,.6),(1.5,1.2)):
            path('cylinder_'+str(xx),[(xx-w/2,0,3),(xx-w/2,0,.3),(xx+w/2,0,.3),(xx+w/2,0,3)],gray)
        box('small_piston',(-2,0,left),(.6,.6,.12),gold)
        box('large_piston',(1.5,0,right),(1.2,1.2,.12),gold)
        box('load',(1.5,0,right+.35),(.8,.8,.6),red)
        label('Small area',(-2,0,4));label('4x piston area',(1,0,4));values=x
    elif mechanism=='thermal_contact':
        x=heat_contact(90,10,2,2,p)
        for name,xx,temp in (('warm',-1,x['temp_a']),('cool',1,x['temp_b'])):
            f=(temp-10)/80;color=(.1+.75*f,.2,.85-.75*f)
            box(name,(xx,0,2),(2,1,2),color);label(f'{temp:.0f} C',(xx,0,3.5))
        path('heat_direction',[(-1,0,4),(1,0,4)],gold)
        label('Net heat: warm to cool' if p<1 else 'Equilibrium: no net heat',(-2,0,4.7));values=x
    elif mechanism=='dna_pairing':
        x=complementary_dna('ATCG')
        colors={'A':red,'T':blue,'C':gold,'G':(.2,.75,.4)}
        path('template_backbone',[(-1.7,0,.5),(-1.7,0,4.2)],gray)
        path('complement_backbone',[(2.7-p,0,.5),(2.7-p,0,4.2)],gray)
        for i,(base,match) in enumerate(zip(x['template'],x['aligned_complement'])):
            z=.8+i
            box('template_'+str(i),(-1,0,z),(.7,.4,.5),colors[base])
            box('complement_'+str(i),(2-p,0,z),(.7,.4,.5),colors[match])
            path('pair_'+str(i),[(-.6,0,z),(1.6-p,0,z)],gray,.02)
            path('template_link_'+str(i),[(-1.7,0,z),(-1.3,0,z)],gray,.03)
            path('complement_link_'+str(i),[(2.7-p,0,z),(2.3-p,0,z)],gray,.03)
            label(base,(-1,0,z+.15));label(match,(2-p,0,z+.15))
        label('5 to 3',(-1.8,0,4.6));label('3 to 5',(.8,0,4.6));values=x
    else:
        x=transfer_water(4,1,3*p)
        for name,xx,volume in (('source',-1.7,x['source_volume']),('destination',1.7,x['destination_volume'])):
            path(name+'_wall',[(xx-.7,0,3.5),(xx-.7,0,.3),(xx+.7,0,.3),(xx+.7,0,3.5)],gray)
            height=.5*volume
            box(name+'_water',(xx,0,.4+height/2),(1.3,.8,height),blue)
            label(f'{volume:.1f} volume units',(xx-.8,0,4))
        path('illustrative_transfer',[(-1,0,2.8),(1,0,2.8)],gold)
        label('Transfer bookkeeping, not flow simulation',(-2.5,0,4.8));values=x
    return {'objects':objects,'labels':labels,'values':values,
      'disclosure':'Simplified schematic; scale and progress illustrative',
      'mechanism':mechanism,'progress':p}
