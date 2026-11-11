#!/usr/bin/env python3
"""Project symbol library: RM2 module + VBAT / VSYS power symbols."""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import parse, dump, find, findall, Q
import design as D
S = '/home/ubuntu/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'boards', D.NAME)

def prop(name, val, x, y, hide=False):
    e = ['property', Q(name), Q(val), ['at', x, y, 0], ['effects', ['font', ['size', 1.27, 1.27]]]]
    if hide: e[-1].append(['hide', 'yes'])
    return e
def pin(num, name, typ, x, y, ang, ln=2.54):
    return ['pin', typ, 'line', ['at', x, y, ang], ['length', ln],
            ['name', Q(name), ['effects', ['font', ['size', 1.27, 1.27]]]],
            ['number', Q(num), ['effects', ['font', ['size', 1.27, 1.27]]]]]

rm2 = ['symbol', Q('RM2'), ['pin_names', ['offset', 1.016]], ['exclude_from_sim', 'no'], ['in_bom', 'yes'],
       ['on_board', 'yes'],
       prop('Reference', 'U', -12.7, 19.05), prop('Value', 'RM2', 5.08, 19.05),
       prop('Footprint', 'RF_Module:RMC20452T', 0, -25.4, True),
       prop('Datasheet', 'https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf', 0, -27.94, True),
       prop('Description', 'Raspberry Pi Radio Module 2 (RMC20452T), CYW43439 2.4GHz Wi-Fi 4 + Bluetooth 5.2, gSPI', 0, -30.48, True),
       prop('ki_keywords', 'wifi bluetooth ble cyw43439 rm2', 0, 0, True),
       ['symbol', Q('RM2_0_1'), ['rectangle', ['start', -12.7, 17.78], ['end', 12.7, -17.78],
                                 ['stroke', ['width', 0.254], ['type', 'default']], ['fill', ['type', 'background']]]]]
u = ['symbol', Q('RM2_1_1')]
L = [('16', 'VIN', 'power_in'), ('14', 'VDDIO', 'power_in'), None, ('12', 'WL_ON', 'input'), ('13', 'BT_ON', 'input'),
     None, ('9', 'CS', 'input'), ('3', 'SCLK', 'input'), ('5', 'DATA_IN', 'input'), ('6', 'DATA_OUT', 'output'),
     ('10', '~{IRQ}', 'output')]
y = 12.7
for e in L:
    if e: u.append(pin(e[0], e[1], e[2], -15.24, y, 0))
    y -= 2.54
Rr = [('8', 'GPIO0', 'bidirectional'), ('18', 'GPIO1', 'bidirectional'), ('17', 'GPIO2', 'bidirectional'), None,
      ('2', 'NC', 'no_connect'), ('19', 'NC', 'no_connect'), ('20', 'NC', 'no_connect')]
y = 12.7
for e in Rr:
    if e: u.append(pin(e[0], e[1], e[2], 15.24, y, 180))
    y -= 2.54
for i, n in enumerate(('1', '4', '7', '11', '15', '21')):
    u.append(pin(n, 'GND', 'power_in' if i == 0 else 'passive', -6.35 + 2.54 * i, -20.32, 90))
rm2.append(u)
rm2.append(['embedded_fonts', 'no'])

lib = ['kicad_symbol_lib', ['version', 20241209], ['generator', Q('kicad_symbol_editor')],
       ['generator_version', Q('9.0')], rm2]
src = open(f'{S}/symbols/power.kicad_symdir/VBUS.kicad_sym').read()
for n in ('VBAT', 'VSYS'):
    e = parse(src.replace('VBUS', n))
    lib.append(findall(e, 'symbol')[0])
open(os.path.join(OUT, D.NAME + '.kicad_sym'), 'w').write(dump(lib) + '\n')
open(os.path.join(OUT, 'sym-lib-table'), 'w').write(
    '(sym_lib_table\n\t(version 7)\n\t(lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.kicad_sym")(options "")(descr "Project symbols"))\n)\n' % (D.NAME, D.NAME))
print('lib written')
