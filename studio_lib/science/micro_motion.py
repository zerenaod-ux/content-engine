"""Reusable labeled microscopic-motion illustration, not molecular dynamics."""
import math

def lattice(center,temperature,clock,side):
    # Temperature controls illustrative amplitude; the clock is presentation
    # time, never a claim about molecular size or vibration frequency.
    amplitude=.025+.10*max(0,min(1,(temperature-10)/80))
    out=[]
    for row in range(3):
        for col in range(3):
            phase=row*2.1+col*1.4+side*.7
            x=center[0]+(col-1)*.52+amplitude*math.sin(clock*5+phase)
            z=center[2]+(row-1)*.52+amplitude*math.cos(clock*4.2+phase)
            out.append({'id':f'micro_{side}_{row}_{col}','at':(x,center[1],z),'radius':.10})
    return out

def transfer_markers(progress,clock):
    # Symbols show a net energy-transfer direction. They are NOT material
    # particles crossing the interface. Symbols vanish at equilibrium.
    active=0<progress<.999
    return [{'id':'energy_symbol_'+str(i),'at':(-.8+1.6*((clock*.6+i/3)%1),-.82,1.65+i*.35),'radius':.045,'visible':active} for i in range(3)]
