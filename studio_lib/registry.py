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
   'hold':'Present snapshot only: high water, raised float and rigid arm are already HELD. The rubber washer is already SEATED under the fixed inlet seat, its gap is zero and incoming flow is already stopped. Explain the continuing mechanical connection maintaining this held state, not the earlier lifting or closure sequence. No timer or electronics. No new rise, pivot, sealing action, closure or opening occurs in this beat.',
   'draw':'The separate draw-off outlet opens, THEN stored water falls; the float descends with it and the arm releases the inlet washer. Incoming water resumes as its seat gap reopens, while draw-off demand is larger so the net stored level falls. No water disappears magically and no suction pump is shown.',
   'refill':'The draw-off valve closes first. Inlet flow refills the tank, raising the floating ball and turning the same arm. At the upper level its washer is seated again and filling stops. This is automatic level feedback, not water creation or electricity generation.',
   'payoff':'The whole tank is visible again. High water, the raised float and the closed inlet are already HELD; only the cutaway covers return. State the payoff of automatic level control without announcing another float rise, valve movement or fresh filling cycle.'},
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
   'payoff':'The whole padlock is visible again with its shackle already raised. Wheels, bar and shackle are HELD in their final positions; only the housing panels return. Explain the payoff: a single bar can pass only when all three wheel gaps align. Do not claim another opening, reset or scrambling sequence.'},
  'source':'https://patents.google.com/patent/US5095724A/en',
  'mechanism_source':'https://patents.google.com/patent/GB2227515A/en'}
})

REGISTRY.update({
 'electric_relay':{'description':'Complete electromagnetic relay with isolated coil-control and contact/load circuits, hinged armature, return spring, real contact buttons and test lamp; not a generator, transistor, motor or mains wiring tutorial',
  'actions':['relay','cutaway','energize','attract','closed','release','off','payoff'],
  'facts':{
   'relay':'The whole connected relay module is shown with separate control and load supplies and a dark test lamp. The control switch is open and the armature is held up. Introduce a question about a small control signal operating a separate circuit. No action starts yet.',
   'cutaway':'A simplified cutaway lifts the relay cover, exposing a copper coil around a fixed iron core, a hinged armature, a return spring and two separated contact buttons. All are held in the unpowered pose. Neither supply is shared through a direct connection between control and load.',
   'energize':'The control switch closes and current builds in the coil, creating an illustrated magnetic field around the iron core. Field markers are diagrams, not visible blue objects. Actuation is enlarged and slowed so its sequence is readable. The armature remains up until the next attraction step; no lamp power yet.',
   'attract':'The increasing electromagnetic attraction draws the rigid armature down around its fixed hinge against the return spring. Its attached moving contact approaches and finally touches the fixed contact, completing the separately supplied load circuit. The test lamp lights only when the contacts touch. The coil does not generate the load power.',
   'closed':'The energized coil, attracted armature and touching contacts are already HELD, and the test lamp is already lit. Explain the maintained closed load path and electrical isolation; do not announce another contact closure or armature movement.',
   'release':'The control switch opens, coil current and its illustrated magnetic field decrease, and the return spring pivots the armature up. Contacts separate and the test lamp goes dark. These are linked changes in the same return stroke, not a second power source.',
   'off':'Control switch, raised armature and separated contacts are HELD open; the coil and lamp are already off. The return spring maintains the rest position. No new spring return or contact opening occurs here.',
   'payoff':'The whole relay cover returns while control and load remain off and the contacts remain separated. Explain that an electromagnet mechanically controls an isolated circuit. No new actuation, battery exchange or automatic restart is shown.'},
  'source':'https://www.ia.omron.com/data_pdf/guide/36/generalrelay_tg_e_3_1_1%28principles%29.pdf',
  'mechanism_source':'https://www.omron.com/global/en/technology/omrontechnics/vol50/010.html'},
 'snap_thermostat':{'description':'Complete automatic-reset snap-disc thermostat with a bimetal dome, actuator pin, hinged contact strip, fixed contact and separately supplied test lamp; enlarged slowed illustration, not a full appliance or digital sensor',
  'actions':['thermostat','cutaway','heat','snap','open','cool','reset','payoff'],
  'facts':{
   'thermostat':'The whole round thermostat housing, two terminals, supply and lit test lamp are shown. It is held cool with its contacts closed. Introduce a useful question about heat switching a circuit off without electronics. Do not claim to show an entire iron, oven, room or boiler.',
   'cutaway':'A simplified cutaway lifts the metal shell and exposes a shallow bimetal disc, a vertical insulating actuator pin and the moving and fixed contacts. The disc is cool and the contacts remain held closed. No snap yet.',
   'heat':'Illustrative thermal markers transfer heat toward the disc. Its two bonded metals respond differently to warming. The temperature condition increases while the disc retains its initial curved shape until its snap threshold; do not describe a gradual contact opening or an exact measured temperature.',
   'snap':'At its illustrative hot threshold the bimetal disc changes curvature, raising the actuator pin. That pin lifts the contact strip, separating the two contacts and interrupting the lamp circuit. The test lamp switches off only as the contacts separate. Motion is enlarged and slowed to show the parts; no glowing metal or fire.',
   'open':'The hot disc, raised pin and separated contacts are HELD, and the lamp is already dark. Explain the interrupted electrical path without announcing a second opening or another disc movement.',
   'cool':'Illustrative heat markers leave the disc as the temperature condition falls. The disc remains in its hot curvature and the contacts remain open until the lower reset condition is reached in the following beat. This is an automatic-reset model, not a manual-reset safety cutout.',
   'reset':'At the lower reset condition the disc snaps back, the pin lowers and the contact strip returns to touch the fixed contact. The lamp lights again only when the contact gap reaches zero. Do not say heat is converted into free electricity.',
   'payoff':'The shell returns around the cool, already reset thermostat and its already lit lamp. Explain temperature-controlled switching. No further heating cycle, new snap or exact temperature calibration is shown.'},
  'source':'https://www.sensience.com/bimetal-disc-thermostats/',
  'mechanism_source':'https://www.sensience.com/wp-content/uploads/2022/12/Bimetal_Catalog.pdf'},
 'clothespin':{'description':'Complete wooden spring clothespin with two rigid shaped jaws, fixed fulcrum, exposed preloaded torsion spring and a fabric fold; not a seesaw bench, spring-energy generator or clothesline-wind simulation',
  'actions':['peg','spring','squeeze','open','insert','release','grip','payoff'],
  'facts':{
   'peg':'The whole two-piece wooden clothespin is held closed with its exposed coil spring visible. Introduce a concrete question about squeezing the handles to open the opposite jaws or about holding fabric. No hands, clothesline or wind is shown.',
   'spring':'A closer view identifies the already exposed torsion spring around the fulcrum, its two legs bearing on the wooden members. The jaws and handles remain still. This object has no hidden shell to open; do not invent a cutaway or disassembly.',
   'squeeze':'Illustrated input-force arrows press the handles together. Both rigid wooden members rotate in opposite directions about the same fulcrum, widening the jaw gap at their other ends. The spring winds further and stores elastic energy supplied by the squeezing action. No real fingers or motor are depicted.',
   'open':'Handles, opened jaws and wound spring are already HELD under the maintained input. Explain that opposite ends of the two rigid levers move oppositely around their common fulcrum; do not announce another opening or claim the wood bends.',
   'insert':'A blue fabric fold slides visibly into the already open jaw gap. The jaws remain held open during insertion. No rope or clothesline is present and the fabric is not yet gripped.',
   'release':'The squeezing input is removed. The preloaded spring unwinds partway and rotates the wooden members back, moving the jaws inward until they contact the fabric. They stop at the fabric thickness, rather than passing through it or closing to zero.',
   'grip':'The jaws and fabric are HELD at contact. Remaining spring preload maintains a clamping force and friction resists fabric slipping. No fresh jaw movement, cloth travel, measured force value or guaranteed load rating is shown.',
   'payoff':'A whole-object view holds the already clamped fabric. Explain that input opens the jaws against stored spring energy and release maintains the grip. Do not announce another squeeze, release, spring motion or fabric insertion.'},
  'source':'https://patents.google.com/patent/DE29803034U1/en',
  'mechanism_source':'https://patents.google.com/patent/US2748437A/en'}
})

REGISTRY.update({
 'pendulum_clock':{'description':'Weight-driven wooden pendulum clock: swinging rod and brass bob, anchor escapement over a toothed escape wheel, falling weight on a cord and a seconds hand on the wheel arbor; simplified, not a spring, quartz or minute-hand clock','actions':['clock','cutaway','pendulum','escapement','tick','weight','hold','payoff'],'facts':{
 'clock':'Introduce a recognizable wooden pendulum clock: case, a seconds dial ring with one hand, a long rod with a brass bob, and a drive weight on a cord. The pendulum is already swinging.',
 'cutaway':'A simplified cutaway lifts the glass front to expose the toothed escape wheel, the anchor above it, the drive gear and the weight cord.',
 'pendulum':'The long rod and brass bob swing back and forth at a steady rhythm of one tick per second. Swing time depends on rod length, not on how heavy the bob is.',
 'escapement':'The anchor sits over the escape wheel and rocks with the pendulum. Its two pallets alternately catch and release a tooth of the toothed wheel.',
 'tick':'Each tick lets the wheel advance one small equal step, so the seconds hand steps once per tick; sixty ticks carry it once around the dial.',
 'weight':'A weight hangs on a cord wound round a drum that turns the drive gear. As the weight slowly falls, the gear turns the escape wheel. The falling weight is the only energy source.',
 'hold':'No new part moves for this explanation. At each release the anchor gives the pendulum a tiny push that replaces the energy lost to friction and air, so it keeps swinging.',
 'payoff':'The cutaway closes. Pendulum, escapement, weight and seconds hand work together as one timekeeper. No winding by hand and no second mechanism is shown.'},'source':'https://en.wikipedia.org/wiki/Escapement'},
 'zipper':{'description':'Closed-end non-locking metal zipper: Y-channel guides staggered rigid teeth; not coil, waterproof or automatic-lock sliders','actions':['zipper','cutaway','guide','mesh','closed','hold','reverse','payoff'],'facts':{
 'zipper':'Introduce two separated fabric tapes with staggered metal teeth and one slider at the open end. No hand or clothing wearer is shown.',
 'cutaway':'A simplified cutaway lifts the slider upper plate and pull tab, revealing its Y-shaped guide and central divider. Teeth remain still.',
 'guide':'The slider advances along the first section. Its converging guide brings the staggered tooth rows inward; paired heads begin interleaving behind it.',
 'mesh':'The slider continues across the middle. Rigid tooth heads enter spaces between opposite stems; the fabric tapes bend into the guided path.',
 'closed':'The slider reaches the far stop, leaving the visible tooth chain joined behind it. No automatic locking pawl is depicted.',
 'hold':'The slider and joined teeth are now held still. Explain that the shaped heads overlap opposing stems; no new sliding or force test occurs.',
 'reverse':'The slider reverses along the same chain. Its divider guides the rows apart progressively, separating the fabric tapes without bending metal teeth.',
 'payoff':'The slider remains at the open end, rows separated. The cutaway plate returns as the explanation concludes; no second closing cycle.'},'source':'https://www.ykk.com/english/ykk/tech/01.html'},
 'stapler':{'description':'Representative desk stapler with sectioned paper, manual handle, magazine spring, guided driver and inward clinching anvil; not flat-clinch or an electric gun','actions':['tool','cutaway','feed','press','clinch','hold','return','payoff'],'facts':{
 'tool':'Introduce the recognizable stapler, paper and base. The handle, driver and loaded staple are still; no pressing hand is shown.',
 'cutaway':'A simplified cutaway lifts the outer shell and exposes a paper section, magazine, feed spring, driver and shaping anvil below.',
 'feed':'The magazine spring extends to push the connected staple row forward, positioning its leading staple beneath the stationary driver.',
 'press':'Illustrated input force lowers the hinged handle and guided driver. The leading staple moves down; straight legs pierce the paper until touching the anvil.',
 'clinch':'Continued downward driver motion forces the staple legs against the anvil grooves. Legs curl inward below the paper while preserving their wire length.',
 'hold':'The staple is now clinched and held below the paper. The driver is still down; explain the completed fastening without announcing another bend.',
 'return':'The handle and driver rise while the clinched staple stays in the paper. The magazine advances the next staple without firing it.',
 'payoff':'The handle is raised and the used staple stays clinched. Cutaway sections return; no second staple is driven. This is a representative sectioned teaching model.'},'source':'https://patents.google.com/patent/US4315589A'},
 'optical_fiber':{'description':'Straight step-index optical fibre, enlarged meridional ray model with accepted angle, core and lower-index cladding; not bending, wave modes or network electronics','actions':['cable','cutaway','enter','reflect','guide','pulse','receive','payoff'],'facts':{
 'cable':'Introduce one straight optical cable between a light source and a receiving indicator. The source is off and no ray is moving yet.',
 'cutaway':'A simplified cutaway lifts front sections of jacket, cladding and core, revealing an enlarged longitudinal view. Layers remain distinct.',
 'enter':'An illustrative light pulse enters the higher-index core at a supported shallow angle and travels toward the first core-cladding boundary.',
 'reflect':'The pulse reaches lower-index cladding and changes direction back into the core by total internal reflection. Angle is measured from the normal, not from the fibre axis.',
 'guide':'The pulse continues reflecting at successive boundaries along the straight core until reaching the far end and activating the receiver indicator.',
 'pulse':'More illustrative pulses travel along that same supported path. Their slow visible movement illustrates propagation, not the real speed of light.',
 'receive':'Pulses continue arriving at the receiving end; the indicator is already active. No packet decoding, electricity generation or camera sensor internals are shown.',
 'payoff':'Cutaway layers return to show the complete cable with its receiver still active. Explain guided light without claiming perfect transmission or every launch angle is trapped.'},'source':'https://www.thefoa.org/tech/ref/basic/total_internal_reflection.html','mechanism_source':'https://ntrs.nasa.gov/api/citations/19960011720/downloads/19960011720.pdf'},
 'ratchet_wrench':{'description':'Manual ratchet wrench head: sawtooth ratchet wheel, spring-loaded pawl and hex bolt; one fixed drive direction; not a reversible, torque, impact or cordless wrench','actions':['wrench','cutaway','drive','slip','catch','repeat','hold','payoff'],'facts':{
 'wrench':'Introduce a recognizable ratchet wrench: a long handle with a red grip, a round head and one hex bolt on a fixed plate. Everything is still.',
 'cutaway':'A simplified cutaway lifts the head cover to expose the toothed ratchet wheel, the spring-loaded pawl above it and the hex bolt turned by the wheel.',
 'drive':'Illustrated input force swings the handle forward. The pawl sits in a gap and pushes the steep face of a tooth, so the wheel and the bolt turn together with the handle.',
 'slip':'The handle swings back. The pawl rides up the sloped back of each tooth and clicks into the next gap, so the wheel and the bolt stay where they are.',
 'catch':'Close-up of the forward stroke again. The spring keeps the pawl pressed into the wheel, so the pawl catches the steep face of a tooth and the wheel and bolt turn another step.',
 'repeat':'The handle swings back a second time. The pawl clicks over the teeth again and the bolt keeps the extra turn. Each forward and back stroke adds one more forward turn.',
 'hold':'No new part moves for this explanation. The steep face pushes the pawl and locks; the sloped face lets it slide away. The tooth shape makes the wheel turn one way only.',
 'payoff':'The cover closes. Handle, pawl, wheel and bolt work together as a one-way turner. No reversing switch, motor or second tool is shown.'},'source':'https://en.wikipedia.org/wiki/Ratchet_(device)'}
})
