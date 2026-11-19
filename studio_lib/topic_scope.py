"""Known component capability boundaries, checked before media requests.

This does not establish arbitrary-topic support or semantic completeness.
"""
import re,unicodedata

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
    patterns={
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
    if mechanism in patterns and re.search(patterns[mechanism],text):
        return 'Unsupported topic detail: the tested '+mechanism+' component does not depict this feature'
    return ''

def require_supported(topic):
    reason=scope_error(topic)
    if reason:raise ValueError(reason)
