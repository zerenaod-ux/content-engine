"""Known component capability boundaries, checked before media requests.

This does not establish arbitrary-topic support or semantic completeness.
"""
import re,unicodedata
SPEC_DETECT={}   # key -> topic words that select a spec machine (machines/<key>.json)
SPEC_BLOCK={}    # key -> details the machine does not depict

def scope_error(topic,mechanism=None):
    text=unicodedata.normalize('NFKC',str(topic)).lower()
    if mechanism is None:
        if re.search(r'\b(camera|lens)\b',text) and re.search(r'\b(aperture|iris|diaphragm)\b',text):mechanism='camera_iris'
        if re.search(r'photovoltaic|solar|\bpv\b',text):mechanism='photovoltaic_cell'
        elif re.search(r'wind|turbine',text):mechanism='wind_turbine'
        elif re.search(r'pump',text):mechanism='piston_pump'
        elif re.search(r'bridge',text):mechanism='bascule_bridge'
        elif re.search(r'relay',text):mechanism='electric_relay'
        elif re.search(r'thermostat|bimetal|snap.disc',text):mechanism='snap_thermostat'
        elif re.search(r'clothespin|clothes.peg',text):mechanism='clothespin'
        elif re.search(r'pendulum|escapement|grandfather clock|(?<!wrist)(?<!digital )(?<!alarm )clock',text):mechanism='pendulum_clock'
        elif re.search(r'zipper',text):mechanism='zipper'
        elif re.search(r'stapler|stapling',text):mechanism='stapler'
        elif re.search(r'optical fib|fiber.optic|fibre.optic',text):mechanism='optical_fiber'
        else:
            for k,p in SPEC_DETECT.items():
                if re.search(p,text):mechanism=k;break
    patterns={
      'pendulum_clock':r'quartz|digital|atomic|wristwatch|mainspring|spring.driven|balance wheel|minute hand|hour hand|time zone|calendar|chime|cuckoo',
      'zipper':r'waterproof|coil zipper|automatic.lock|magnetic|invisible zipper|separating pin',
      'stapler':r'electric|pneumatic|flat.clinch|tack(?:ing)?|staple gun|remove staple',
      'optical_fiber':r'bend|curv|dispersion|wavelength|single.mode|wave optic|network protocol|packet|perfect transmission',
      'electric_relay':r'solid.state|latching|reed relay|contactor|arc suppression|flyback|transistor',
      'snap_thermostat':r'digital|microprocessor|refrigerant|wax|manual.reset|melt|thermal fuse',
      'clothespin':r'clothesline tension|plastic hinge|wind load|centrifugal',
      'float_valve':r'toilet flush|steam trap|pilot.operated|diaphragm|solenoid|pump efficiency|water hammer',
      'combination_lock':r'pick(?:ing)?|bypass|decode|crack|keyhole|keyed|single.dial|safe lock|reset combination',
      'camera_iris':r'autofocus|depth.of.field|bokeh|refraction|image inversion|f.number calculation|shutter mechanism',
      'photovoltaic_cell':r'anti.{0,3}reflect|coatings?|inverter|doping|band.{0,2}gap|solar thermal',
      'wind_turbine':r'blade.{0,15}pitch|pitch.{0,15}blade|yaw|feather|inverter|transformer',
      'piston_pump':r'centrifugal|peristaltic|impeller|diaphragm',
      'bascule_bridge':r'suspension|cable.stayed|vertical.lift|swing bridge|bearing.{0,40}(?:friction|lubricat)|(?:friction|lubricat).{0,40}(?:bearing|trunnion)',
    }
    patterns.update(SPEC_BLOCK)
    if mechanism in patterns and re.search(patterns[mechanism],text):
        return 'Unsupported topic detail: the tested '+mechanism+' component does not depict this feature'
    return ''

def require_supported(topic):
    reason=scope_error(topic)
    if reason:raise ValueError(reason)

from studio_lib import machine_spec
machine_spec.ensure_loaded()
