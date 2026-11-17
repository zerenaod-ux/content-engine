"""Broad topic intake with honest rendering boundaries; no generation side effects.

A seed source is a research starting point, never evidence that an arbitrary
claim or a new renderer has already been verified.
"""
import argparse,json,re
from pathlib import Path
from studio_lib.science.components import SPECS

FAMILIES={
 'mechanisms': {'examples':['zipper','bicycle gears','door lock','hydraulic lift'],
  'parts':['joints','gears','levers','connected rigid bodies'],
  'checks':['connection continuity','gear ratios','clearance','energy input'],
  'sources':['https://openstax.org/books/physics/pages/9-3-simple-machines']},
 'electricity': {'examples':['hand-cranked generator','transformer','battery','electric motor'],
  'parts':['circuit','switch','coil','magnet','load'],
  'checks':['closed circuit before load current','voltage versus current','stationary versus rotating parts'],
  'sources':['https://www.eia.gov/energyexplained/electricity/how-electricity-is-generated.php']},
 'fluids': {'examples':['piston pump','siphon','hydraulic brake','water tap'],
  'parts':['pipes','reservoirs','pistons','one-way valves'],
  'checks':['conservation of volume','valve order','pressure direction'],
  'sources':['https://www.grc.nasa.gov/www/k-12/WindTunnel/Activities/Pascals_principle.html']},
 'heat_materials': {'examples':['heat exchanger','thermos','melting ice','metal expansion'],
  'parts':['temperature field','contact surfaces','flow path','phase boundary'],
  'checks':['hot-to-cold heat transfer','energy accounting','phase versus temperature'],
  'sources':['https://bsesc.energy.gov/energy-basics/heat-flow']},
 'biology': {'examples':['DNA replication','cell membrane','plant roots','lungs'],
  'parts':['membranes','molecules','transport paths','binding sites'],
  'checks':['scale labels','time labels','process specificity','no literal giant particles'],
  'sources':['https://www.genome.gov/genetics-glossary/DNA-Replication']},
 'earth_nature': {'examples':['water cycle','cloud formation','river erosion','evaporation'],
  'parts':['reservoirs','phase transitions','flows','environment'],
  'checks':['matter conservation','energy input','time and scale disclosure'],
  'sources':['https://www.usgs.gov/special-topics/water-science-school/water-cycle']},
}
CAUSAL_MODELS={'mechanisms':'lever','electricity':'resistor','fluids':'hydraulics','heat_materials':'heat_contact','biology':'complementary_dna','earth_nature':'transfer_water'}

PATTERNS={
 'mechanisms':r'\b(gear|gears|zipper|lock|lever|seesaw|bridge|bicycle|pulley|crank|hydraulic lift)\b',
 'electricity':r'\b(electric|electricity|electrical|generator|battery|motor|circuit|solar|transformer|lamp)\b',
 'fluids':r'\b(pump|siphon|hydraulic|hydraulics|valve|plumbing|tap|fluid)\b',
 'heat_materials':r'\b(heat|thermal|thermos|melting|freezing|metal|material|materials|insulation)\b',
 'biology':r'\b(dna|cell|cells|membrane|plant|plants|root|roots|lung|lungs|biology|bacteria)\b',
 'earth_nature':r'\b(cloud|clouds|river|erosion|evaporation|water cycle|rain|volcano)\b',
}

def topic_brief(topic):
    if not isinstance(topic,str) or not 3<=len(topic.strip())<=300:
        raise ValueError('Topic must be 3-300 characters')
    text=topic.strip().lower()
    families=[k for k,p in PATTERNS.items() if re.search(p,text)]
    # Closed inventory: no generator-of-any-kind -> turbine substitution.
    matches=[]
    if re.search(r'\bwind[ -]+turbine\b',text):matches.append('wind_turbine')
    if re.search(r'\bhand[ -]?(crank|cranked|cranking)\b',text) and re.search(r'\bgenerator\b',text):matches.append('hand_generator')
    prototypes=[]
    for name,pattern in {
      'lever_balance':r'\b(lever|seesaw)\b',
      'resistive_circuit':r'\b(resistor|ohmic|resistive circuit)\b',
      'hydraulic_lift':r'\bhydraulic (lift|press|jack)\b',
      'thermal_contact':r'\b(thermal contact|heat between|heat transfer between|contacting bodies)\b',
      'dna_pairing':r'\b(dna base pair|dna base pairing|complementary dna|base pairs)\b',
      'water_transfer':r'\b(water between reservoirs|water transfer between|two reservoirs)\b',
    }.items():
        if re.search(pattern,text):prototypes.append(name)
    excludes=re.search(r'\b(compare|versus|vs|not|without|solar|steam|diesel|nuclear|hydroelectric|pump|battery|transformer)\b',text)
    mechanism=matches[0] if len(matches)==1 and not excludes else None
    prototype=prototypes[0] if len(prototypes)==1 and not matches and not re.search(r'\b(compare|versus|vs|replication|engine|charger|grid|weather)\b',text) else None
    mechanism=mechanism or prototype
    family_for={'lever_balance':'mechanisms','resistive_circuit':'electricity','hydraulic_lift':'fluids','thermal_contact':'heat_materials','dna_pairing':'biology','water_transfer':'earth_nature'}
    if prototype and family_for[prototype] not in families:families.append(family_for[prototype])
    requirements=sorted({x for k in families for x in FAMILIES[k]['checks']})
    return {'topic':topic.strip(),'families':families or ['unclassified'],
      'render_status':('implemented_diagram_unverified' if prototype else 'supported_cinematic_component') if mechanism else 'research_and_component_work_required',
      'mechanism':mechanism,'automatic_quality_approved':False,
      'foundation_models':[{'id':CAUSAL_MODELS[k],'status':'unit_tested_foundation_only','render_component_available':False} for k in families],
      'candidate_parts':sorted({x for k in families for x in FAMILIES[k]['parts']}),
      'seed_sources':sorted({x for k in families for x in FAMILIES[k]['sources']}),
      'component_assumptions':SPECS[prototype][0]+'; simplified diagram, end-to-end quality unverified' if prototype else None,
      'sources_verified_for_this_topic':False,'required_checks':requirements,
      'research_requirements':['Find topic-specific authoritative references; seed links alone are insufficient.',
        'Map every causal narration claim to its supporting source and visible action.',
        'Declare physical connections, representative operating speed and scale/time assumptions.',
        'Label invisible processes as schematic illustrations.',
        'Implement and test missing components before claiming render support.'],
      'next_step':'Generate within the component contract only when owner authorizes media.' if mechanism else 'Research the exact topic and implement missing components; do not substitute an unrelated scene.'}

def require_component(topic,out=None):
    brief=topic_brief(topic)
    if out is not None:(Path(out)/'topic-brief.json').write_text(json.dumps(brief,indent=2))
    if not brief['mechanism']:
        raise ValueError('Topic has no supported cinematic component; see topic-brief.json. No model, voice or render request was made.')
    return brief['mechanism']

def main():
    p=argparse.ArgumentParser(description='Prepare a topic research/capability brief only; never generates media.')
    p.add_argument('--topic',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(topic_brief(a.topic),indent=2))
if __name__=='__main__':main()
