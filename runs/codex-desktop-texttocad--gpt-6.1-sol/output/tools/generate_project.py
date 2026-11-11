from copy import deepcopy
from pathlib import Path
import json
import math
import re
import uuid
import sys
import sexpdata as sx
from design import ROOT, NAME, PARTS
from library_tools import LIBROOT, child, children, flatten_symbol, pins, tag
from custom_parts import create_footprints


def ident(text):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'atlas2350:' + text))


def quote(text):
    return json.dumps(str(text), ensure_ascii=False)


def effects(size=1.0, justify='', hidden=False):
    return f'(effects (font (size {size} {size})){" (justify " + justify + ")" if justify else ""}{" (hide yes)" if hidden else ""})'


def property_text(name, value, x, y, angle=0, hidden=False):
    return f'(property {quote(name)} {quote(value)} (at {x:.4f} {y:.4f} {angle}) {effects(1.0, hidden=hidden)})'


def transform(x, y, cx, cy, angle):
    radians = math.radians(angle)
    return (cx + x * math.cos(radians) - y * math.sin(radians),
            cy - x * math.sin(radians) - y * math.cos(radians))


def wire(start, end, key):
    return f'(wire (pts (xy {start[0]:.4f} {start[1]:.4f}) (xy {end[0]:.4f} {end[1]:.4f})) (stroke (width 0) (type default)) (uuid "{ident(key)}"))'


def label(net, x, y, angle, key):
    return f'(global_label {quote(net)} (shape bidirectional) (at {x:.4f} {y:.4f} {angle}) {effects(0.9, "left" if angle in {0, 90} else "right")} (uuid "{ident(key)}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:.4f} {y:.4f} {angle}) {effects(hidden=True)}))'


def note(text, x, y, key, size=1.4):
    return f'(text {quote(text)} (at {x} {y} 0) {effects(size, "left")} (uuid "{ident(key)}"))'


def instance(part, template, sheet_id):
    ref = part['ref']
    cx, cy, angle = part['schematic']
    cx, cy = round(cx / 1.27) * 1.27, round(cy / 1.27) * 1.27
    active = not ref.startswith(('H', 'TP', '#'))
    fields = []
    for name, value in [('Reference', ref), ('Value', part['value']),
                        ('Footprint', part['local_footprint']), ('MPN', part['mpn']),
                        ('Manufacturer', part['manufacturer']), ('Description', part['description']),
                        ('Datasheet', next((item[2] for item in children(template, 'property')
                                           if item[1] == 'Datasheet'), ''))]:
        original = next((item for item in children(template, 'property') if item[1] == name), None)
        if original:
            original_at = child(original, 'at')
            position = transform(original_at[1], original_at[2], cx, cy, angle)
        else:
            position = (cx, cy)
        if part.get('symbol') in {'R', 'C', 'L', 'Ferrite_Bead'} and name in {'Reference', 'Value'}:
            if angle in {0, 180}:
                position = (cx + (4 if name == 'Reference' else 8), cy + (-1.27 if name == 'Reference' else 1.27))
            else:
                position = (cx, cy + (-2.54 if name == 'Reference' else 2.54))
        fields.append(property_text(name, value, *position, angle if angle in {0, 180} else 0,
                                    name not in {'Reference', 'Value'}))
    instance_id = ident(ref)
    placed = f'''(symbol (lib_id "Atlas:{part['local_symbol']}") (at {cx} {cy} {angle}) (unit 1)
        (in_bom {"yes" if active else "no"}) (on_board {"no" if ref.startswith('#') else "yes"}) (dnp no) (uuid "{instance_id}")
        {''.join(fields)}
        {''.join(f'(pin {quote(child(pin, "number")[1])} (uuid "{ident(ref + ":pin:" + child(pin, "number")[1])}"))' for pin in pins(template))}
        (instances (project "{NAME}" (path "/{ident('root')}/{sheet_id}" (reference "{ref}") (unit 1)))))'''
    lines = [placed]
    visited = set()
    for pin in pins(template):
        number = child(pin, 'number')[1]
        net = part['nets'][number]
        pin_at = child(pin, 'at')
        position = transform(pin_at[1], pin_at[2], cx, cy, angle)
        position = tuple(round(value, 4) for value in position)
        if position in visited:
            continue
        visited.add(position)
        if net is None:
            lines.append(f'(no_connect (at {position[0]} {position[1]}) (uuid "{ident(ref + ":nc:" + number)}"))')
            continue
        outward = (int(pin_at[3]) + angle + 180) % 360
        radians = math.radians(outward)
        end = (position[0] + 3.81 * math.cos(radians), position[1] - 3.81 * math.sin(radians))
        lines.extend([wire(position, end, ref + ':wire:' + number),
                      label(net, *end, outward, ref + ':label:' + number)])
    return '\n'.join(lines)


def build():
    create_footprints(ROOT)
    (ROOT / 'libraries' / 'Atlas.pretty').mkdir(parents=True, exist_ok=True)
    (ROOT / 'docs').mkdir(exist_ok=True)
    (ROOT / 'checks').mkdir(exist_ok=True)
    symbol_defs = {}
    for part in PARTS:
        part['local_symbol'] = part['library'] + '_' + part['symbol']
        template = deepcopy(flatten_symbol(part['library'], part['symbol']))
        old_name = template[1]
        template[1] = part['local_symbol']
        for unit in children(template, 'symbol'):
            unit[1] = unit[1].replace(old_name, part['local_symbol'], 1)
            if part['ref'] == 'U10':
                for pin in children(unit, 'pin'):
                    if child(pin, 'number')[1] == '5':
                        pin[1] = sx.Symbol('passive')
        for property_node in children(template, 'property'):
            if property_node[1] == 'Footprint':
                property_node[2] = ''
        symbol_defs[part['local_symbol']] = template
        library, footprint = part['footprint'].split(':')
        local_name = library + '_' + footprint
        part['local_footprint'] = 'Atlas:' + local_name
        source = (ROOT / 'libraries' if library == 'Custom' else LIBROOT / 'footprints') / (library + '.pretty') / (footprint + '.kicad_mod')
        if not source.exists():
            raise FileNotFoundError(source)
        target = ROOT / 'libraries' / 'Atlas.pretty' / (local_name + '.kicad_mod')
        footprint_tree = sx.loads(source.read_text())
        footprint_tree[1] = local_name
        if part['ref'] == 'U6':
            for pad in children(footprint_tree, 'pad'):
                if pad[1] == '19' and child(pad, 'drill'):
                    child(pad, 'drill')[1] = 0.3
        target.write_text(sx.dumps(footprint_tree) + '\n')
    flag = deepcopy(flatten_symbol('power', 'PWR_FLAG'))
    flag[1] = 'PWR_FLAG'
    symbol_defs['PWR_FLAG'] = flag
    def embedded(name):
        symbol = deepcopy(symbol_defs[name])
        symbol[1] = 'Atlas:' + name
        return sx.dumps(symbol)
    library_text = '(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'
    library_text += '\n'.join(sx.dumps(symbol) for symbol in symbol_defs.values()) + '\n)\n'
    (ROOT / 'libraries' / 'Atlas.kicad_sym').write_text(library_text)
    (ROOT / 'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Atlas") (type "KiCad") (uri "${KIPRJMOD}/libraries/Atlas.kicad_sym") (options "") (descr "Self-contained Atlas2350 symbols")))\n')
    (ROOT / 'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Atlas") (type "KiCad") (uri "${KIPRJMOD}/libraries/Atlas.pretty") (options "") (descr "Self-contained verified KiCad land patterns")))\n')
    descriptions = {
        'MCU': 'RP2350A and external 1.1V core supply',
        'Memory': '4MiB QSPI NOR and 8MiB QSPI PSRAM',
        'Power': 'USB-controlled LiPo charging and 3.3V power path',
        'Interfaces': 'USB-C, microSD, Qwiic and addressable RGB',
        'Wireless': 'Wi-Fi / BLE UART coprocessor and programming',
    }
    annotations = {
        'MCU': [('150MHz nominal. External LDO supplies DVDD: VREG_FB=GND, LX=NC.\nKeep VREG_VIN and VREG_AVDD powered. Set VREG.HIZ=1 in firmware; never select low-power VREG mode.', 25, 20),
                ('IOs are 3.3V, not 5V tolerant. No SWO.\nExpansion pin19 VBUS and pin20 VSYS are outputs only: never back-power.', 230, 227)],
        'Memory': [('QSPI bus shared; CS0 is flash, GP0 is PSRAM CS1. Both chip selects pulled high.\n33R source termination on clock. Start QSPI <=31.25MHz; validate signal integrity on first articles.', 25, 20),
                   ('BOOTSEL: hold SW2, pulse RUN (SW1), release SW2 after USB enumerates.\n1k limits current if BOOTSEL is pressed while the flash chip-select output is active.', 210, 162)],
        'Power': [('USB_500_EN=0 at reset: 100mA USB mode. Set to1 only after a 500mA USB grant.\nCharger ISET=3.57k: 250mA nominal. ITERM=NC: 10% termination; TMR=NC: 5h safety timer.', 25, 20),
                  ('BATTERY: protected 1S LiPo, >=500mAh, 4.2V charging; 10k NTC required.\nJ2 pins 1=BAT+, 2=GND, 3=NTC. THIS IS A CUSTOM 3-PIN PINOUT.\nNo battery supplied or soldered. Missing NTC inhibits charging.', 25, 225),
                  ('VBAT approximately 2 * BAT_ADC; divider buffered by U9.\nVBUS_ADC is presence detection, not precision voltage measurement.\nUSB_500_EN / USB_SUSPEND_EN: 00=100mA,10=500mA,11=suspend.', 235, 210)],
        'Interfaces': [('USB2.0 device / 5V sink only; no PD, no host power sourcing.\nBoth CC pins use separate 5.1k Rd. ESD array sits at the receptacle; 27R series resistors at U1.', 25, 20),
                       ('RGB V6 only: VIH=0.55*VDD; U10 switches VSYS with PWR_EN.\nBlank RGB below VBAT about3.6V under load; limit current to15mA.\nRGB not guaranteed when LED_VDD<3.3V. I2C 3.3V/4.7k; SD SPI initially<=12.5MHz.', 258, 245)],
        'Wireless': [('ESP-AT UART1: GPIO6 RX <- RP GP20; GPIO7 TX -> RP GP21.\nGPIO4 RTS -> RP GP22 CTS; GPIO5 CTS <- RP GP23 RTS.\nUART0 GPIO20/21 is a separate 3.3V programming interface; start115200baud.', 25, 20),
                     ('Radio disabled by 10k EN pull-down at cold boot. Enable only after power budget is known.\nGP19 controls IO9 as open-drain: release for normal boot, pull low while pulsing EN for download.\nIO8 and IO2 strap high. Antenna projects beyond top PCB edge; do not enclose with metal.', 25, 211)],
    }
    for page, (sheet_name, description) in enumerate(descriptions.items(), 2):
        sheet_id = ident('sheet:' + sheet_name)
        sheet_parts = [part for part in PARTS if part['sheet'] == sheet_name]
        used = sorted({part['local_symbol'] for part in sheet_parts})
        flags = [('VBUS', 110, 160), ('GND', 135, 160)] if sheet_name == 'Interfaces' else [('ADC_AVDD', 213, 134)] if sheet_name == 'MCU' else []
        if flags:
            used.append('PWR_FLAG')
        content = f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid "{sheet_id}") (paper "A3")
            (title_block (title {quote(description)}) (date "2026-11-10") (rev "A") (company "Atlas2350") (comment 1 "PCBWay full assembly; all fitted parts specified by MPN"))
            (lib_symbols {''.join(embedded(name) for name in used)})'''
        content += '\n'.join(instance(part, symbol_defs[part['local_symbol']], sheet_id) for part in sheet_parts)
        for flag_index, (net, x, y) in enumerate(flags):
            ref = '#FLG' + str(page * 10 + flag_index)
            flag_part = {'ref': ref, 'schematic': (x, y, 0), 'local_symbol': 'PWR_FLAG',
                         'local_footprint': '', 'mpn': '', 'manufacturer': '', 'value': 'PWR_FLAG',
                         'description': 'External or passively filtered supply', 'nets': {'1': net}}
            content += instance(flag_part, flag, sheet_id)
        content += '\n'.join(note(text, x, y, sheet_name + ':note:' + str(index), 1.2)
                             for index, (text, x, y) in enumerate(annotations[sheet_name]))
        content += '\n(embedded_fonts no))\n'
        (ROOT / (sheet_name.lower() + '.kicad_sch')).write_text(content)
    root = f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid "{ident('root')}") (paper "A3")
        (title_block (title "Atlas2350 connected LiPo development board") (date "2026-11-10") (rev "A") (company "Atlas2350") (comment 1 "RP2350A + QSPI flash/PSRAM + Wi-Fi/BLE + USB-C + LiPo")) (lib_symbols)'''
    for index, (sheet_name, description) in enumerate(descriptions.items()):
        x = 35 + (index % 3) * 122
        y = 63 + (index // 3) * 80
        sheet_id = ident('sheet:' + sheet_name)
        root += f'''(sheet (at {x} {y}) (size 100 36) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
            (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid "{sheet_id}")
            (property "Sheetname" {quote(sheet_name)} (at {x} {y - 2} 0) {effects(1.5, 'left bottom')})
            (property "Sheetfile" "{sheet_name.lower()}.kicad_sch" (at {x} {y + 39} 0) {effects(1.1, 'left top')})
            (instances (project "{NAME}" (path "/{ident('root')}" (page "{index + 2}")))))'''
        root += note(description, x + 4, y + 18, 'overview:' + sheet_name, 1.2)
    root += note('Atlas2350 Rev A | 80 x 75mm, four layers, 1.6mm FR-4, ENIG\nAll components top-side; PCBWay includes SMT and through-hole connectors.\nFabrication: 0.127mm clearance, 0.15mm signal width, 0.30mm drills / 0.60mm vias.\nFilled/capped through vias required at QFN exposed pads and module thermal pad.', 35, 31, 'overview:spec', 1.3)
    root += note('DECISIONS\n3.3V buck-boost powers MCU, memories, SD and radio from USB or LiPo.\nExternal 1.1V LDO avoids the RP2350 internal buck magnetic-polarity/layout dependency.\nExternal 3-wire protected battery required: BAT+, GND, 10k NTC. No battery or microSD card in assembly BOM.\nWi-Fi/BLE is an ESP32-C3 coprocessor, not native RP2350 functionality; firmware required.\nFactory assemble every BOM row. Mechanical holes and bare test pads are not components.\nNo DNI/DNP component options. See README and fab/assembly-notes.md before ordering.', 35, 225, 'overview:decisions', 1.3)
    root += '(sheet_instances (path "/" (page "1"))) (embedded_fonts no))\n'
    (ROOT / f'{NAME}.kicad_sch').write_text(root)
    project = {'meta': {'filename': f'{NAME}.kicad_pro', 'version': 1},
               'board': {'design_settings': {'rules': {'min_clearance': 0.127, 'min_track_width': 0.15,
                          'min_via_diameter': 0.6, 'min_through_hole_diameter': 0.3,
                          'min_via_annular_width': 0.15, 'min_copper_edge_clearance': 0.25,
                          'min_hole_to_hole': 0.25, 'min_silk_clearance': 0.15,
                          'min_silk_text_height': 0.8, 'min_silk_text_thickness': 0.15},
                          'rule_severities': {}, 'drc_exclusions': []}},
               'net_settings': {'meta': {'version': 4}, 'classes': [
                   {'name': 'Default', 'clearance': 0.127, 'track_width': 0.15,
                    'via_diameter': 0.6, 'via_drill': 0.3, 'diff_pair_width': 0.15,
                    'diff_pair_gap': 0.15, 'diff_pair_via_gap': 0.25}]},
               'erc': {'erc_exclusions': [], 'meta': {'version': 0}, 'pin_map': [], 'rule_severities': {}}}
    if '--schematics-only' not in sys.argv:
        (ROOT / f'{NAME}.kicad_pro').write_text(json.dumps(project, indent=2) + '\n')
    (ROOT / 'design.json').write_text(json.dumps(PARTS, indent=2) + '\n')
    print(f'Generated {len(PARTS)} footprints and six schematic sheets with local libraries')


if __name__ == '__main__':
    build()
