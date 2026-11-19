"""Supported mechanisms, action contracts and factual references."""
BRIDGE_ACTIONS=['approach','stop','pivot','balance','drive','pass','lower','resume']
BRIDGE_FACTS={
 'approach':'One tall vessel waits before the low road bridge. One car approaches. Introduce the clearance problem.',
 'stop':'One car stops behind the barrier. Barriers close before the bridge moves.',
 'pivot':'The fixed steel trunnion supports the span at its hinge. The road remains closed during this explanation; actual opening starts in the next balance beat.',
 'balance':'Road rises while its rigidly attached heel counterweight swings down into its chamber.',
 'drive':'The counterweight offsets much of the load; a motor and meshing gears control motion. It does not lift for free.',
 'pass':'Bridge stays fully raised while the tall vessel passes through the channel.',
 'lower':'After the vessel clears, road lowers and counterweight swings up. The rising counterweight gains gravitational potential energy while the road loses height; do not say the rising counterweight returns or releases energy. The motor controls the motion and losses remain.',
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
  'pump':'Show the complete connected source, pump and receiving reservoir first. The piston is held still for this introduction; actual withdrawal starts in suction. Later the piston and rod move horizontally along the cylinder axis, never vertically. Mechanical input transfers water.',
  'cutaway':'Reveal a simplified cutaway: piston and rod inside a cylinder, with separate inlet and outlet check valves. No combustion.',
  'suction':'Piston withdraws, chamber volume increases and pressure falls. The pressure difference draws water from the source; the piston does not create water.',
  'inlet':'During intake the inlet check valve opens and the outlet check valve stays closed, preventing reverse flow from the outlet.',
  'compression':'Piston advances, chamber volume decreases and pressure rises; inlet check valve closes.',
  'outlet':'During delivery the outlet check valve opens and the inlet stays closed. Water moves into the delivery pipe and receiving reservoir.',
  'repeat':'Repeat the same coupled intake/delivery cycle. ONLY the delivery stroke sends water into the receiver; the intake stroke refills the chamber. Never say each stroke delivers water. Flow is pulsating.',
  'payoff':'Mechanical work drives the piston and transfers water. One-way valves keep net flow toward the receiving reservoir. Discharge is pulsating, not steady or continuous; no smoothing accumulator is shown.'},'source':'https://files.dep.state.pa.us/water/bsdw/operatorcertification/TrainingModules/WW-9%20Pumps%20and%20Hydraulics_WB_Final.pdf'}
}
REGISTRY['wind_turbine']={
 'description':'Direct-drive horizontal-axis wind turbine with simplified generator cutaway and demonstration lamp; not gearbox, grid or inverter internals',
 'actions':['turbine','wind','rotor','shaft','generator','induction','load','payoff'],
 'facts':{
  'turbine':'One three-bladed turbine is already turning in steady wind. Introduce conversion of moving air energy to electricity; do not claim it is stopped.',
  'wind':'Moving blue trails illustrate incoming air. Aerodynamic lift on shaped blades produces torque; the turbine does not make wind.',
  'rotor':'Three blades and their hub turn together continuously. Blade tips are marked orange to make motion visible.',
  'shaft':'A simplified nacelle cutaway opens. The rotor shaft directly drives the generator at the same rotational speed, without a gearbox.',
  'generator':'Colored rotating magnets move inside stationary copper coils. This is a simplified permanent-magnet direct-drive generator illustration.',
  'induction':'Relative motion changes magnetic flux through stationary coils and induces voltage. Generation already occurs while the rotor turns; no switch creates the energy. Do not describe a literal stream of electrons from the wind.',
  'load':'The demonstration switch closes and a small illustrative lamp lights. Moving markers indicate an electrical path, not literal giant particles. This is not a grid-connection diagram; no rectifier or inverter internals are depicted.',
  'payoff':'The same turbine keeps turning as the nacelle cover returns. Wind kinetic energy becomes mechanical rotation and then electrical energy, with losses; no claim of perfect conversion.'},
 'source':'https://www.energy.gov/cmei/systems/how-do-wind-turbines-work'}

REGISTRY['camera_iris']={
 'description':'A complete camera body and representative lens iris with seven rigid pivoted blades, fixed pivots, moving control pins, a coupled rotating guide ring, illustrative light paths and a fixed-setting exposure illustration. Not autofocus, depth of field, shutter mechanics or a manufacturer-specific optical simulation.',
 'actions':['camera','light','cutaway','close','small','open','exposure','payoff'],
 'facts':{
  'camera':'Show a recognizable complete camera and lens first. The iris starts open and held. Introduce controlling how much light reaches the sensor, not a shutter or focus question.',
  'light':'Gold moving markers illustrate incoming light, not visible giant photons. Light travels along the lens axis. No focusing, refraction, image inversion or background blur is simulated.',
  'cutaway':'A simplified cutaway lifts the outer lens cap and camera top to expose the same iris assembly. Name the overlapping metal blades and fixed pivot pins. It is an explanatory reveal, not the camera disassembling during normal use. The aperture is still open and held.',
  'close':'The common copper-colored control ring turns. Its curved slots guide the moving blade pins; the blades pivot together about their stationary pins and narrow the central opening. No electric motor internals or independent sliding blades are shown.',
  'small':'Hold the small opening. Fewer illustrated light paths pass through; paths blocked by the blades terminate before the blade plane. The blades do not absorb every ray: the center stays open. The fixed-setting exposure illustration is dimmer.',
  'open':'The ring reverses its rotation; all seven blades pivot outward together and widen the opening. The fixed pivots stay still, and each moving pin stays on its guide slot. No gears or focus movement are shown.',
  'exposure':'With a wider opening more light passes. The checker-pattern sensor illustration is brighter with the same representative exposure time and gain. It is an exposure illustration, not simulated image formation or an actual photograph. Do not claim more sharpness, more zoom, clearer detail or doubled light.',
  'payoff':'Return to the same complete camera as the cutaway covers return. The iris stays open. Resolve how the coordinated blades regulate light. Do not say a new closing cycle or shutter action begins.'},
 'source':'https://www.nikonusa.com/learn-and-explore/c/tips-and-techniques/a-basic-look-at-the-basics-of-exposure',
 'mechanism_source':'https://patents.google.com/patent/US3132576A/en'}

REGISTRY.update({
 'float_valve':{
  'description':'Complete storage tank with a direct-acting ball float, rigid pivoted arm, inlet washer/seat and separate draw-off valve; not a toilet flush, steam trap or electrically controlled pump',
  'actions':['tank','cutaway','fill','throttle','hold','draw','refill','payoff'],
  'facts':{
   'tank':'Show the whole connected storage tank, inlet pipe and draw-off outlet. Introduce a simple question about stopping a tank from overfilling without electronic sensing. Water and the low float are HELD for context; do not say they start rising or filling yet.',
   'cutaway':'A simplified cutaway lifts the front and lid to reveal the low floating ball, a rigid arm on a fixed pivot, and inlet valve washer under its seat. Name the simplified cutaway naturally. Water and the float are still held low; filling starts only in the next beat. No invisible electronics.',
   'fill':'Inlet water markers begin flowing and the water level rises. Buoyancy raises the partly submerged float, rotating its rigid arm around a fixed pivot. The rod length stays constant. Markers represent flow, not a measured flow rate; time is compressed.',
   'throttle':'As water rises toward the upper level, the float rises further. The same pivoted arm lifts a guided valve stem and rubber washer toward a fixed inlet seat, shrinking its gap and reducing incoming flow. The washer meets the seat at the end and inlet flow stops; the rising ball does NOT itself plug the pipe.',
   'hold':'High water, float, arm and seated washer are HELD. The inlet gap is closed and no inlet markers cross the seat. Explain the consequence: buoyancy communicated through the lever shuts the inlet, rather than a timer or electronics. Do not announce a new rise, closure, or opening.',
   'draw':'The separate draw-off outlet opens, THEN stored water falls; the float descends with it and the arm releases the inlet washer. Incoming water resumes as its seat gap reopens, while draw-off demand is larger so the net stored level falls. No water disappears magically and no suction pump is shown.',
   'refill':'The draw-off valve closes first. Inlet flow refills the tank, raising the floating ball and turning the same arm. At the upper level its washer is seated again and filling stops. This is automatic level feedback, not water creation or electricity generation.',
   'payoff':'Return to the whole tank. High water, the raised float and the closed inlet are already HELD; only the cutaway covers return. State the payoff of automatic level control without announcing another float rise, valve movement or fresh filling cycle.'},
  'source':'https://www.boiswood.co.uk/content/uploads/brochure/mankenberg-nv71-tank-float-valve.pdf',
  'mechanism_source':'https://tectul.com/en/conduccion-de-fluidos/valvulas/ficha-tecnica-valvula-flotador-bronce'},
 'combination_lock':{
  'description':'Recognizable three-wheel padlock with a simplified exposed gate-and-fence mechanism, spring-guided locking bar and lifting shackle; not a real model, bypass technique, key lock or single-dial safe',
  'actions':['lock','cutaway','first','second','third','release','pull','payoff'],
  'facts':{
   'lock':'Show the complete padlock and closed U-shaped shackle with three scrambled wheels. Ask why the shackle stays locked until all three wheels line up. The shackle and wheels are HELD; no opening or rotating begins yet. No keyhole, key, electricity or pulling hand is shown.',
   'cutaway':'A simplified cutaway lifts the housing panels to expose three separate wheels around a fixed horizontal axle, their real rim notches called gates, and one spring-guided locking bar spanning all three. Name the simplified cutaway once. All wheels and the shackle remain still here.',
   'first':'Only the FIRST wheel turns toward its aligned position, bringing its notch upward under the bar. The second and third wheels stay scrambled, so their solid rims still block the bar and the shackle stays closed. Manual input is implied; do not invent a hand or motor.',
   'second':'Only the SECOND wheel turns into alignment. The first is held aligned; the third wheel still presents its solid rim, preventing the bar from descending. One or two aligned gates are not enough; no opening yet.',
   'third':'The THIRD wheel turns until all three gates line up. ONLY when the last gate provides clearance can the spring-guided locking bar settle into the notches, moving its attached locking tab clear of the short shackle leg. The shackle is still down; it does not automatically jump open.',
   'release':'All wheels are HELD aligned and the locking bar is ALREADY seated in their gates. Its tab is already clear of the shackle notch. Explain why the three aligned gaps permit release, without announcing a new bar drop, wheel rotation or shackle lift.',
   'pull':'An external pull lifts the U-shaped shackle AFTER the bar is clear. The long leg stays captured in the housing and the short leg clears its socket. Wheels and bar remain aligned and held; no unlocking without the correct positions, no automatic spring ejection and no rotation of the shackle.',
   'payoff':'Return to the whole padlock with its shackle already raised. Wheels, bar and shackle are HELD in their final positions; only the housing panels return. Explain the payoff: a single bar can pass only when all three wheel gaps align. Do not claim another opening, reset or scrambling sequence.'},
  'source':'https://patents.google.com/patent/US5095724A/en',
  'mechanism_source':'https://patents.google.com/patent/GB2227515A/en'}
})
