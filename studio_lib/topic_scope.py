"""Known component capability boundaries, checked before media requests.

This does not establish arbitrary-topic support or semantic completeness.
"""
import re,unicodedata

def scope_error(topic,mechanism=None):
    text=unicodedata.normalize('NFKC',str(topic)).lower()
    if mechanism is None:
        if re.search(r'photovoltaic|solar|\bpv\b',text):mechanism='photovoltaic_cell'
        elif re.search(r'wind|turbine',text):mechanism='wind_turbine'
        elif re.search(r'pump',text):mechanism='piston_pump'
        elif re.search(r'bridge',text):mechanism='bascule_bridge'
    patterns={
      'photovoltaic_cell':r'anti.{0,3}reflect|coatings?|inverter|doping|band.{0,2}gap|solar thermal',
      'wind_turbine':r'blade.{0,15}pitch|pitch.{0,15}blade|yaw|feather|inverter|transformer',
      'piston_pump':r'centrifugal|peristaltic|impeller|diaphragm',
      'bascule_bridge':r'suspension|cable.stayed|vertical.lift|swing bridge',
    }
    if mechanism in patterns and re.search(patterns[mechanism],text):
        return 'Unsupported topic detail: the tested '+mechanism+' component does not depict this feature'
    return ''

def require_supported(topic):
    reason=scope_error(topic)
    if reason:raise ValueError(reason)
