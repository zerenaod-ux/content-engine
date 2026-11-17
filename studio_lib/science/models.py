"""Small causal models for future topic components, with explicit assumptions.

SI units unless indicated. No renderer, network, TTS or AI calls. These models
must not be advertised as a completed animation library or predictive simulation.
"""
import math

def finite(*values):
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
        raise ValueError('Finite numeric inputs required')

def positive(*values):
    finite(*values)
    if any(x<=0 for x in values):raise ValueError('Strictly positive input required')

def lever(force,input_arm,output_arm):
    """Ideal quasi-static lever; ignores friction and lever weight."""
    finite(force);positive(input_arm,output_arm)
    return {'output_force':force*input_arm/output_arm,'input_torque':force*input_arm,
      'assumption':'Ideal lever in torque balance; force gain trades distance.'}

def resistor(voltage,resistance,closed=True):
    """Ideal DC source and ohmic resistor; not an LED or battery chemistry model."""
    finite(voltage);positive(resistance)
    if not isinstance(closed,bool):raise ValueError('Switch state must be boolean')
    current=voltage/resistance if closed else 0
    return {'current':current,'load_power':current*current*resistance,
      'assumption':'Ideal DC source, one ohmic load, ideal switch; no transient or thermal effects.'}

def hydraulics(force,input_area,output_area,input_distance):
    """Ideal equal-height cylinders, incompressible fluid, no leakage/friction."""
    finite(force,input_distance);positive(input_area,output_area)
    return {'output_force':force*output_area/input_area,
      'output_distance':input_distance*input_area/output_area,
      'pressure_increment':force/input_area,
      'assumption':'Ideal incompressible equal-height hydraulics; force gain trades travel.'}

def heat_contact(temp_a,temp_b,capacity_a,capacity_b,fraction):
    """Lumped bodies exchanging a fraction of energy needed for equilibrium.

Fraction is illustrative progress, NOT a time or material conductivity model.
Temperatures may be Celsius; capacities are joules per kelvin.
"""
    finite(temp_a,temp_b,fraction);positive(capacity_a,capacity_b)
    if not 0<=fraction<=1:raise ValueError('Progress fraction must be 0..1')
    energy=(temp_a-temp_b)/(1/capacity_a+1/capacity_b)*fraction
    return {'temp_a':temp_a-energy/capacity_a,'temp_b':temp_b+energy/capacity_b,
      'energy_a_to_b':energy,
      'assumption':'Two isolated lumped bodies, constant heat capacity, no phase change; progress is not elapsed time.'}

def complementary_dna(sequence):
    """Aligned complementary bases, not a full replication enzyme simulation.

Input is written 5-prime to 3-prime; aligned output runs 3-prime to 5-prime.
"""
    if not isinstance(sequence,str) or not sequence or len(sequence)>10000 or any(c not in 'ATCG' for c in sequence.upper()):
        raise ValueError('Use a nonempty DNA sequence containing only A, T, C and G')
    return {'template':sequence.upper(),'aligned_complement':sequence.upper().translate(str.maketrans('ATCG','TAGC')),
      'template_direction':'5 to 3','aligned_complement_direction':'3 to 5',
      'assumption':'Base-pair matching only; no enzyme, error correction, timing or cellular-scale simulation.'}

def transfer_water(source_volume,destination_volume,requested_volume):
    """Conservative two-reservoir transfer, not a weather or evaporation model."""
    finite(source_volume,destination_volume,requested_volume)
    if min(source_volume,destination_volume,requested_volume)<0:raise ValueError('Volumes cannot be negative')
    moved=min(source_volume,requested_volume)
    return {'source_volume':source_volume-moved,'destination_volume':destination_volume+moved,
      'transferred_volume':moved,
      'assumption':'Closed two-reservoir bookkeeping; rate and driving energy must be provided by a topic-specific model.'}
