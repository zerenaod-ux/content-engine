"""The parts the scene engine can draw, in one place. The writer prompt and the checker both read this, so they can never disagree."""
# type: (required fields, optional fields, what it is)
CATALOG = {
 'sky':    ([], ['preset', 'sun', 'clouds', 'hills'], 'Background. MUST be the first part. preset: "day", "dusk", "night", "desert", "snow" (outdoors) or "space", "ocean" (underwater), "body" (inside a body), "lab", "clean" (plain).'),
 'ground': ([], ['y', 'kind'], 'Ground with its surface at height y (default 0); kind: grass, sand, snow, rock, seabed, floor. Things at y<0 are seen underground (cut-away). Leave it out for space or inside-the-body scenes.'),
 'emoji':  (['char'], ['x', 'y', 'size', 'rot', 'alpha', 'flip', 'bob', 'orbit'], 'ANY object as ONE emoji character: animals, people, organs, vehicles, tools, planets, food, buildings. x,y = its centre, size 50-220, rot in degrees, bob = gentle floating, flip mirrors it. orbit {"cx","cy","rx","ry","period","phase"} makes it circle a point.'),
 'path':   (['d'], ['x', 'y', 'scale', 'rot', 'fill', 'stroke', 'lw', 'alpha', 'draw', 'orbit'], 'Draw ANY custom shape yourself with an SVG path string d (like a simple icon about 100 units big, centred on 0,0; y goes DOWN inside d). Placed at x,y. draw 0..1 draws its outline on gradually.'),
 'ellipse': (['x', 'y', 'rx', 'ry'], ['rot', 'fill', 'stroke', 'lw', 'alpha', 'orbit'], 'Oval centred at x,y (cells, lenses, lakes seen from above, orbits).'),
 'line':   (['pts'], ['color', 'w', 'progress', 'dash', 'speed', 'alpha'], 'Line through points that draws itself with progress 0..1 (rays, signals, paths of travel). dash [10,10] with speed makes it move.'),
 'text':   (['x', 'y', 'text'], ['size', 'color', 'alpha', 'rot', 'outline'], 'Big plain text or a number on the picture (max 12 letters), for values like 100°C.'),
 'bar':    (['x', 'y'], ['w', 'h', 'value', 'color', 'bg', 'alpha'], 'Upright meter that fills with value 0..1 (temperature, pressure, energy, speed, charge).'),
 'particles': (['kind', 'x', 'y'], ['on', 'w', 'dir', 'speed', 'count', 'size', 'rgb'], 'Stream of small things from x,y. kind: drops, sparks, smoke, steam, bubbles, dust, fire, snow, leaves, glitter. on 0..1 switches it. dir in degrees (90 = up). w = width of the source.'),
 'rect':   (['x', 'y', 'w', 'h'], ['r', 'fill', 'stroke', 'lw', 'alpha', 'rot'], 'Box with its bottom-left corner at x,y. r = corner radius. Use for walls, machines, containers.'),
 'circle': (['r'], ['x', 'y', 'fill', 'stroke', 'lw', 'alpha', 'orbit'], 'Circle centred at x,y.'),
 'poly':   (['pts'], ['fill', 'stroke', 'lw', 'close', 'alpha'], 'Any shape from points [[x,y],...]. close:false with only a stroke draws a line (wire, rope, ramp).'),
 'water':  (['x0', 'x1', 'y0', 'level'], [], 'Body of water between x0 and x1 with its bottom at y0; level = height (y) of the surface. Animate level to fill or drain.'),
 'pipe':   (['pts'], ['w', 'progress', 'flow', 'color'], 'Pipe along points. progress 0..1 = how far water has filled it from the first point; flow 0..1 shows moving water.'),
 'wire':   (['pts'], ['w', 'progress', 'pulse', 'color'], 'Electric wire or cable along points. progress 0..1 = how far the power has travelled from the first point; pulse 0..1 shows it moving.'),
 'tower':  (['x'], ['y', 'legH', 'w', 'h', 'level', 'roof'], 'Water tank on legs, centred at x, standing on y. level 0..1 = how full.'),
 'pump':   (['x', 'y'], ['r', 'spin'], 'Pump with a spinning rotor. spin = turns speed (0 = stopped, 9 = fast).'),
 'house':  (['x'], ['y', 'w', 'h', 'lit', 'wall', 'roof', 'cut'], 'House with its bottom-left at x,y; cut-away so you see inside. lit 0..1 = window light.'),
 'stream': (['x', 'y1', 'y0'], ['w', 'on'], 'Water falling straight down from y1 (top) to y0 (bottom) at x. on 0..1.'),
 'spray':  (['x', 'y'], ['dir', 'on', 'power', 'floor'], 'Droplets shooting out and arcing down from x,y. dir 1 = right, -1 = left. power 0..1.'),
 'tree':   (['x'], ['y', 's', 'grow', 'kind'], 'Tree at x standing on y. s = size, grow 0..1, kind "round" or pine by default.'),
 'plant':  (['x'], ['y', 's', 'grow', 'color'], 'Small plant that grows a flower as grow goes 0 to 1.'),
 'wheel':  (['x', 'y'], ['r', 'spin', 'teeth', 'fill'], 'Gear / turbine / water wheel centred at x,y that turns. spin = speed, negative turns the other way.'),
 'arrow':  (['from', 'to'], ['progress', 'both', 'color', 'w', 'head'], 'Arrow from [x,y] to [x,y] that grows with progress 0..1. both:true = two heads (to show a distance).'),
 'label':  (['x', 'y', 'text'], ['size', 'show', 'bg', 'color'], 'Short tag in CAPITALS (max 16 letters) at x,y. show 0..1 fades it in and out.'),
 'night':  (['amount'], [], 'Darkens the whole picture (0 = day, 1 = night) and shows stars. Put it near the end of the parts list.'),
 'glow':   (['x', 'y'], ['r', 'alpha', 'rgb'], 'Soft light at x,y (lamp, spark, heat). rgb like "255,225,120". Put it after night to shine in the dark.'),
}
# fields that may be a fixed number OR keyframes [[time, value], ...]
ANIM = {'x', 'y', 'w', 'h', 'r', 'alpha', 'level', 'progress', 'flow', 'spin', 'lit', 'on', 'power', 'grow', 'show', 'amount', 'y0', 'pulse', 'size', 'rot', 'scale', 'draw', 'value', 'rx', 'ry'}
PRESETS = {'day', 'dusk', 'night', 'desert', 'snow', 'space', 'ocean', 'body', 'lab', 'clean'}
GROUNDS = {'grass', 'sand', 'snow', 'rock', 'seabed', 'floor'}
PARTICLES = {'drops', 'sparks', 'smoke', 'steam', 'bubbles', 'dust', 'fire', 'snow', 'leaves', 'glitter'}
POINT_LISTS = {'pts'}; POINTS = {'from', 'to'}
SOUNDS_DUR = {'hum', 'flow', 'spray', 'sparkle', 'whoosh', 'zip', 'rumble', 'splash'}      # optional 4th value = seconds
SOUNDS_FREQ = {'chime', 'tick'}                                                           # optional 4th value = pitch in Hz
SOUNDS_PLAIN = {'slice', 'whump', 'pop', 'thunk', 'click', 'snip', 'powerdown'}
SOUNDS = SOUNDS_DUR | SOUNDS_FREQ | SOUNDS_PLAIN

def catalog_text():
    return '\n'.join('- %s: needs %s; may have %s. %s' % (k, ', '.join(r) or 'nothing', ', '.join(o) or 'nothing', d) for k, (r, o, d) in CATALOG.items())
