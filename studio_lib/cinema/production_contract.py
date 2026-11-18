"""Measurable presentation requirements separate from successful media encoding."""
import math

# Required causal parts must be framed together during these explanatory beats.
# Detail views may omit context only when that context is not being explained.
ESSENTIAL_PARTS = {
    'lever_balance': {
        'overview': ['rigid_bar', 'fulcrum', 'load_crate'],
        'parts': ['rigid_bar', 'fixed_pivot_pin', 'load_crate'],
        'input': ['input_weight', 'input_force', 'rigid_bar'],
        'change': ['rigid_bar', 'fixed_pivot_pin', 'load_crate'],
        'transfer': ['rigid_bar', 'input_travel', 'output_travel'],
        'result': ['load_crate', 'rigid_bar'],
        'payoff': ['rigid_bar', 'fulcrum', 'load_crate'],
    },
    'hydraulic_lift': {
        'overview': ['small_piston', 'large_piston', 'load'],
        'parts': ['small_piston', 'large_piston', 'confined_fluid'],
        'input': ['small_piston', 'confined_fluid'],
        'change': ['small_piston', 'large_piston', 'load'],
        'transfer': ['small_piston', 'large_piston', 'confined_fluid'],
        'result': ['large_piston', 'load'],
    },
}


def framing_errors(projected, required, margin=.025):
    errors=[]
    for name in required:
        points=projected.get(name, [])
        if not points:
            errors.append(name+': framing evidence missing')
            continue
        if any(not all(math.isfinite(v) for v in p) or p[2]<=0 or not margin<=p[0]<=1-margin or not margin<=p[1]<=1-margin for p in points):
            errors.append(name+': essential part is clipped or behind the camera')
    return errors
