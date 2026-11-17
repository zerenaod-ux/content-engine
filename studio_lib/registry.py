"""Supported mechanisms, action contracts and factual references."""
BRIDGE_ACTIONS=['approach','stop','pivot','balance','drive','pass','lower','resume']
BRIDGE_FACTS={
 'approach':'One tall vessel waits before the low road bridge. One car approaches. Introduce the clearance problem.',
 'stop':'One car stops behind the barrier. Barriers close before the bridge moves.',
 'pivot':'The fixed steel trunnion supports the span at its hinge. The road remains closed during this explanation; actual opening starts in the next balance beat.',
 'balance':'Road rises while its rigidly attached heel counterweight swings down into its chamber.',
 'drive':'The counterweight offsets much of the load; a motor and meshing gears control motion. It does not lift for free.',
 'pass':'Bridge stays fully raised while the tall vessel passes through the channel.',
 'lower':'After the vessel clears, road lowers and counterweight swings up.',
 'resume':'Span seats and locks, barriers rise, one car crosses a continuous road.'}
REGISTRY={
 'bascule_bridge':{'description':'Single-leaf trunnion bascule drawbridge, not other bridge types','actions':BRIDGE_ACTIONS,'facts':BRIDGE_FACTS,'source':'https://www.ncdot.gov/initiatives-policies/Transportation/bridges/historic-bridges/bridge-types/Pages/bascule.aspx'},
 'photovoltaic_cell':{'description':'Solar photovoltaic panel, cell cutaway and direct-current load; not solar thermal or inverter internals','actions':['panel','light','absorb','separate','contacts','circuit','load','payoff'],'facts':{
  'panel':'A recognizable framed solar panel receives sunlight. This explanation concerns photovoltaics, not heating water.',
  'light':'Yellow moving markers depict incoming sunlight, not electrical current from the Sun. The external wires remain visible throughout; never claim wiring is absent or not shown.',
  'absorb':'Reveal a simplified enlarged semiconductor cutaway. Absorbed light transfers energy to charge carriers. State that this is a simplified view.',
  'separate':'The built-in electric field separates mobile electrons and holes. Colored markers are illustrative charge carriers, not literal giant particles or gears.',
  'contacts':'Metal contacts collect charge carriers; external wires connect the cell to a closed circuit.',
  'circuit':'A visible switch closes the external circuit; markers then depict electron flow toward a small DC load and its return path. This is not an AC inverter explanation.',
  'load':'The depicted low-voltage DC lamp lights when supplied electrical power. Individual electrons do not travel instantaneously from the Sun to the bulb.',
  'payoff':'Return to the panel and lit load: photovoltaic conversion turns absorbed light energy into electrical energy. Not all light becomes electricity.'},'source':'https://www.energy.gov/cmei/systems/how-does-solar-energy-work'},
 'piston_pump':{'description':'Single-acting reciprocating piston water pump with inlet and outlet check valves; not a centrifugal pump or engine','actions':['pump','cutaway','suction','inlet','compression','outlet','repeat','payoff'],'facts':{
  'pump':'A piston water pump moves water from a source reservoir to a receiving reservoir using mechanical input.',
  'cutaway':'Reveal a simplified cutaway: piston and rod inside a cylinder, with separate inlet and outlet check valves. No combustion.',
  'suction':'Piston withdraws, chamber volume increases and pressure falls. The pressure difference draws water from the source; the piston does not create water.',
  'inlet':'During intake the inlet check valve opens and the outlet check valve stays closed, preventing reverse flow from the outlet.',
  'compression':'Piston advances, chamber volume decreases and pressure rises; inlet check valve closes.',
  'outlet':'During delivery the outlet check valve opens and the inlet stays closed. Water moves into the delivery pipe and receiving reservoir.',
  'repeat':'Repeat the same coupled intake/delivery cycle. ONLY the delivery stroke sends water into the receiver; the intake stroke refills the chamber. Never say each stroke delivers water. Flow is pulsating.',
  'payoff':'Mechanical work drives the piston and transfers water. One-way valves keep the net flow toward the receiving reservoir.'},'source':'https://files.dep.state.pa.us/water/bsdw/operatorcertification/TrainingModules/WW-9%20Pumps%20and%20Hydraulics_WB_Final.pdf'}
}
REGISTRY['wind_turbine']={
 'description':'Direct-drive horizontal-axis wind turbine with simplified generator cutaway and demonstration lamp; not gearbox, grid or inverter internals',
 'actions':['turbine','wind','rotor','shaft','generator','induction','load','payoff'],
 'facts':{
  'turbine':'One three-bladed turbine is already turning in steady wind. Introduce conversion of moving air energy to electricity; do not claim it is stopped.',
  'wind':'Moving blue trails illustrate incoming air. Aerodynamic lift on shaped blades produces torque; the turbine does not make wind.',
  'rotor':'Three blades and their hub turn together continuously. Each blade root sits in a pitch bearing on the hub, which lets the blade twist to catch more or less wind. Blade tips are marked orange to make motion visible.',
  'shaft':'A simplified nacelle cutaway opens. A main bearing carries the heavy rotor shaft, and a red brake caliper sits over a disc on the shaft to hold the rotor still for maintenance. The shaft directly drives the generator at the same rotational speed, without a gearbox.',
  'generator':'Red and blue magnets (alternating north and south poles) spin on the rotor inside a ring of stationary coils: copper wire wound around grey iron cores. This is a simplified permanent-magnet direct-drive generator illustration.',
  'induction':'Relative motion changes magnetic flux through stationary coils and induces voltage. In the illustration a coil glows at the moment a magnet sweeps past it, and pale lines mark the magnetic field reaching that coil. Generation already occurs while the rotor turns; no switch creates the energy. Do not describe a literal stream of electrons from the wind.',
  'load':'The demonstration switch closes and a small illustrative lamp lights. Moving markers indicate an electrical path, not literal giant particles. This is not a grid-connection diagram; no rectifier or inverter internals are depicted.',
  'payoff':'The same turbine keeps turning as the nacelle cover returns. Wind kinetic energy becomes mechanical rotation and then electrical energy, with losses; no claim of perfect conversion.'},
 'source':'https://www.energy.gov/cmei/systems/how-do-wind-turbines-work'}
