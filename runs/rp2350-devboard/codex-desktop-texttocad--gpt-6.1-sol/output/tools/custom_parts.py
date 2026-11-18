from copy import deepcopy
import sexpdata as sx


def custom_symbol(name):
    if name == 'TLV9001IDBV':
        from library_tools import flatten_symbol, child, children, pins
        result = deepcopy(flatten_symbol('Amplifier_Operational', 'TLV9001IDCK'))
        result[1] = name
        for unit in children(result, 'symbol'):
            unit[1] = unit[1].replace('TLV9001IDCK', name)
        mapping = {'1': '3', '2': '2', '3': '4', '4': '1', '5': '5'}
        for pin in pins(result):
            child(pin, 'number')[1] = mapping[child(pin, 'number')[1]]
        for property_node in children(result, 'property'):
            if property_node[1] == 'Value':
                property_node[2] = name
            if property_node[1] == 'Footprint':
                property_node[2] = 'Package_TO_SOT_SMD:SOT-23-5'
        return result
    if name != 'TPS63070RNM':
        raise KeyError(name)
    definitions = [
        ('12', 'VIN', 'power_in', -12.7, 10.16, 0),
        ('13', 'VIN', 'passive', -12.7, 10.16, 0),
        ('14', 'EN', 'input', -12.7, 5.08, 0),
        ('1', 'PS/SYNC', 'input', -12.7, 2.54, 0),
        ('15', 'VSEL', 'input', -12.7, 0, 0),
        ('3', 'VAUX', 'power_out', -12.7, -5.08, 0),
        ('11', 'L1', 'passive', -5.08, 17.78, 270),
        ('9', 'L2', 'passive', 5.08, 17.78, 270),
        ('7', 'VOUT', 'power_out', 12.7, 10.16, 180),
        ('8', 'VOUT', 'passive', 12.7, 10.16, 180),
        ('2', 'PG', 'open_collector', 12.7, 5.08, 180),
        ('5', 'FB', 'input', 12.7, 2.54, 180),
        ('6', 'FB2', 'passive', 12.7, 0, 180),
        ('4', 'GND', 'power_in', 0, -17.78, 90),
        ('10', 'PGND', 'power_in', 2.54, -17.78, 90),
    ]
    pin_text = ''.join(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) (name "{label}" (effects (font (size 1.0 1.0)))) (number "{number}" (effects (font (size 1.0 1.0)))))'
                       for number, label, kind, x, y, angle in definitions)
    return sx.loads(f'''(symbol "{name}" (pin_names (offset 0.3)) (in_bom yes) (on_board yes)
        (property "Reference" "U" (at 0 13.97 0) (effects (font (size 1.27 1.27))))
        (property "Value" "{name}" (at 0 11.43 0) (effects (font (size 1.0 1.0))))
        (property "Footprint" "Custom:TPS63070_RNM0015A" (at 0 0 0) (effects (font (size 1.0 1.0)) (hide yes)))
        (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tps63070.pdf" (at 0 0 0) (effects (font (size 1.0 1.0)) (hide yes)))
        (symbol "{name}_0_1" (rectangle (start -10.16 15.24) (end 10.16 -15.24) (stroke (width 0.254) (type default)) (fill (type background))))
        (symbol "{name}_1_1" {pin_text}))''')


def create_footprints(root):
    folder = root / 'libraries' / 'Custom.pretty'
    folder.mkdir(parents=True, exist_ok=True)
    pads = [(1, -1.15, -0.75, 0.6, 0.25), (2, -1.15, -0.25, 0.6, 0.25),
            (3, -1.15, 0.25, 0.6, 0.25), (4, -1.15, 0.75, 0.6, 0.25),
            (5, -0.725, 1.4, 0.25, 0.6), (6, -0.225, 1.4, 0.25, 0.6),
            (7, 0.275, 1.4, 0.25, 0.6), (8, 0.775, 1.4, 0.25, 0.6),
            (9, 0.775, 0.5, 1.35, 0.25), (10, 0.6, 0, 1.7, 0.25),
            (11, 0.775, -0.5, 1.35, 0.25),
            (12, 0.775, -1.4, 0.25, 0.6), (13, 0.275, -1.4, 0.25, 0.6),
            (14, -0.225, -1.4, 0.25, 0.6), (15, -0.725, -1.4, 0.25, 0.6),
            (7, 0.525, 1.225, 0.75, 0.25), (13, 0.525, -1.225, 0.75, 0.25)]
    pad_text = ''.join(f'(pad "{number}" smd roundrect (at {x} {y}) (size {width} {height}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1){" (solder_mask_margin -0.05)" if 7 <= number <= 13 else ""})'
                       for number, x, y, width, height in pads)
    footprint = f'''(footprint "TPS63070_RNM0015A" (version 20241229) (generator "pcbnew") (layer "F.Cu")
        (descr "TI RNM0015A, land-pattern 4222000/B 03/2020, 2.5x3mm VQFN-HR-15; no separate exposed pad")
        (attr smd) (property "Reference" "REF**" (at 0 -2.4 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
        (property "Value" "TPS63070RNMR" (at 0 2.4 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
        (fp_rect (start -1.25 -1.5) (end 1.25 1.5) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))
        (fp_rect (start -1.7 -1.95) (end 1.7 1.95) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
        (fp_line (start -1.55 -1.85) (end -1.15 -1.85) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
        (fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (effects (font (size 0.65 0.65) (thickness 0.1))))
        {pad_text})'''
    (folder / 'TPS63070_RNM0015A.kicad_mod').write_text(footprint + '\n')
