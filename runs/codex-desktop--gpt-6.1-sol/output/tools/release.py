from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
import finish_board as cad
import pymupdf
from shapely.geometry import Point, Polygon, box
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parent.parent
FAB = ROOT / 'fab'
NAME = 'Aster2350'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')


def run(*arguments):
    environment = dict(os.environ, KICAD_DOCUMENTS_HOME=str(ROOT / '.kicad'))
    subprocess.run([CLI, *map(str, arguments)], cwd=ROOT, env=environment, check=True)


def natural(reference):
    return [int(part) if part.isdigit() else part for part in re.split(r'(\d+)', reference)]


def write_csv(path, fields, rows):
    with path.open('w', newline='') as output:
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        writer.writerows(rows)


def purchased_parts(board):
    parts = []
    for footprint in cad.tags(board, 'footprint'):
        properties = {item[1]: item[2] for item in cad.tags(footprint, 'property')}
        reference = properties.get('Reference', '')
        if not properties.get('MPN') or reference.startswith('TP'):
            continue
        position = cad.tag(footprint, 'at')
        parts.append(dict(reference=reference, value=properties['Value'], mpn=properties['MPN'],
                          manufacturer=properties['Manufacturer'], footprint=footprint[1],
                          x=position[1], y=position[2], rotation=position[3] if len(position)>3 else 0,
                          assembly='THT' if reference in ('J2', 'J6', 'J7') else 'SMT', object=footprint))
    return sorted(parts, key=lambda part: natural(part['reference']))


def tables(parts):
    descriptions = {component['ref']: component['description'] for component in json.loads((ROOT/'design-data.json').read_text())}
    grouped = defaultdict(list)
    for part in parts:
        grouped[(part['mpn'], part['manufacturer'], part['value'], part['footprint'], part['assembly'])].append(part)
    bom = []
    for index, (key, group) in enumerate(sorted(grouped.items(), key=lambda item: natural(item[1][0]['reference'])), 1):
        mpn, manufacturer, value, footprint, assembly = key
        bom.append(dict(Item=index, References=' '.join(part['reference'] for part in group), Quantity=len(group),
                        Value=value, Manufacturer=manufacturer, MPN=mpn, Footprint=footprint,
                        Assembly=assembly, Side='Top', Populate='Yes',
                        Description=descriptions[group[0]['reference']]))
    write_csv(FAB/'BOM.csv', list(bom[0]), bom)
    placements = [dict(Designator=part['reference'], Value=part['value'], Footprint=part['footprint'],
                       Mid_X_mm=f"{part['x']-100:.4f}", Mid_Y_mm=f"{165-part['y']:.4f}",
                       Rotation_deg=f"{part['rotation']%360:.3f}", Layer='Top', Assembly=part['assembly']) for part in parts]
    write_csv(FAB/'placements.csv', list(placements[0]), placements)
    write_csv(FAB/'placements-THT.csv', list(placements[0]), [row for row in placements if row['Assembly']=='THT'])
    return len(bom)


def validate(board, parts, bom_lines):
    schematic = ET.parse(FAB/'schematic-netlist.xml').getroot()
    schematic_pins = {}
    for net in schematic.findall('./nets/net'):
        name = net.attrib['name']
        if name.startswith('unconnected-'):
            continue
        for pin in net.findall('node'):
            if not pin.attrib['ref'].startswith('#'):
                schematic_pins[(pin.attrib['ref'], pin.attrib['pin'])] = name
    board_pins = {}
    mounting_pads = []
    for footprint in cad.tags(board, 'footprint'):
        properties = {item[1]: item[2] for item in cad.tags(footprint, 'property')}
        reference = properties['Reference']
        for pad in cad.tags(footprint, 'pad'):
            net = cad.tag(pad, 'net')
            if not net:
                continue
            if net[1].startswith('unconnected-'):
                continue
            key = reference, str(pad[1])
            if str(pad[1])=='MP' and reference in ('J4', 'J5') and net[1]=='GND':
                mounting_pads.append(key)
            board_pins[key] = net[1]
    mismatches = [dict(reference=key[0], pin=key[1], schematic=schematic_pins.get(key), pcb=board_pins.get(key))
                  for key in sorted(set(schematic_pins)|set(board_pins)) if schematic_pins.get(key)!=board_pins.get(key)]
    erc = json.loads((FAB/'ERC.json').read_text())
    drc = json.loads((FAB/'DRC.json').read_text())
    erc_items = [item for sheet in erc.get('sheets', []) for item in sheet.get('violations', [])]
    non_ground_inner = [segment for segment in cad.tags(board, 'segment') if cad.tag(segment,'layer')[1]=='In1.Cu' and cad.tag(segment,'net')[1]!='GND']
    copper = list(cad.copper_items(board))
    antenna = box(151,100,179,111)
    antenna_items = [item for item in copper if item['shape'].intersection(antenna).area > 0.000001]
    antenna_pours = []
    for zone in cad.tags(board,'zone'):
        for filled in cad.tags(zone,'filled_polygon'):
            points = cad.tag(filled,'pts')
            if points and Polygon([point[1:3] for point in cad.tags(points,'xy')]).intersection(antenna).area > 0.000001:
                antenna_pours.append(cad.tag(zone,'uuid')[1])
    pads = [item for item in copper if item['kind']=='pad' and 'F.Cu' in item['layers'] and str(item['object'][2])=='smd']
    pad_drill_intersections = []
    for via in cad.tags(board,'via'):
        position = cad.tag(via,'at')[1:3]
        hole = Point(position).buffer(cad.tag(via,'drill')[1]/2)
        for pad in pads:
            if pad['shape'].intersection(hole).area > 0.000001:
                pad_drill_intersections.append(dict(position=position, net=cad.tag(via,'net')[1], pad=pad['object'][1]))
    report = dict(board=NAME, revision='A', design_date='2026-11-09', release_date=datetime.now(timezone.utc).date().isoformat(), physical_validation=False,
                  purchased_components=len(parts), bom_lines=bom_lines,
                  top_smt=sum(part['assembly']=='SMT' for part in parts), top_tht=sum(part['assembly']=='THT' for part in parts),
                  schematic_pad_net_mismatches=mismatches, grounded_connector_mount_pads=mounting_pads,
                  erc_violations=len(erc_items), drc_violations=len(drc.get('violations', [])),
                  unconnected_items=len(drc.get('unconnected_items', [])), schematic_parity=drc.get('schematic_parity', []),
                  in1_non_ground_segments=len(non_ground_inner), layers=['F.Cu','In1.Cu','In2.Cu','B.Cu'],
                  antenna_copper_items=len(antenna_items), antenna_copper_pours=len(antenna_pours),
                  via_drill_open_smd_pad_intersections=pad_drill_intersections,
                  width_mm=80, height_mm=65,
                  minimum_track_mm=min(cad.tag(segment,'width')[1] for segment in cad.tags(board,'segment')),
                  via_sizes=sorted(set((cad.tag(via,'size')[1],cad.tag(via,'drill')[1]) for via in cad.tags(board,'via'))),
                  assembly_origin='Lower-left board corner (KiCad X100 Y165); X right, Y up; mm; top rotation CCW',
                  limitations=['Unbuilt prototype: first article and DFM approval required.',
                               'USB impedance requires the fabricator-approved stack and coupon.',
                               'No functional/programming firmware included; see README.md and ASSEMBLY.md.'])
    (FAB/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    assert len(parts)==121 and not mismatches and not non_ground_inner and not antenna_items and not antenna_pours and not pad_drill_intersections, report
    assert not erc_items and not drc.get('violations') and not drc.get('unconnected_items') and not drc.get('schematic_parity'), report
    return report


def fabrication_drawing(board):
    path = FAB/'fabrication-drawing.pdf'
    document = canvas.Canvas(str(path), pagesize=landscape(A4))
    document.setTitle('Aster2350 Rev A fabrication specification')
    document.setFont('Helvetica-Bold', 17)
    document.drawString(16*mm, 194*mm, 'ASTER2350  /  REV A  /  FABRICATION')
    scale = 1.65*mm
    origin_x, origin_y = 20*mm, 53*mm
    document.setLineWidth(0.7)
    document.rect(origin_x, origin_y, 80*scale, 65*scale)
    document.setFont('Helvetica', 10)
    document.drawCentredString(origin_x+40*scale, origin_y-7*mm, '80.00 mm')
    document.drawString(origin_x+81*scale, origin_y+32*scale, '65.00 mm')
    document.setDash(3, 2)
    document.rect(origin_x+51*scale, origin_y+54*scale, 28*scale, 11*scale)
    document.setDash()
    document.setFont('Helvetica', 7)
    document.drawString(origin_x+52*scale, origin_y+59*scale, 'RF ANTENNA: NO COPPER / METAL')
    for footprint in cad.tags(board, 'footprint'):
        props = {item[1]: item[2] for item in cad.tags(footprint,'property')}
        if not props.get('Reference','').startswith('H'):
            continue
        position = cad.tag(footprint,'at')
        document.circle(origin_x+(position[1]-100)*scale, origin_y+(165-position[2])*scale, 1.35*scale)
    document.drawString(origin_x, origin_y-14*mm, 'Origin (0,0): lower left. Four NPTH mounting holes: diameter 2.70 mm.')
    document.setFont('Helvetica', 9)
    lines = ['4-layer FR-4 / Tg >=150 C / ENIG / lead-free', '1.60 mm +/-10%; green mask, white legend both sides',
             'Copper: nominal 35 um finished each layer', 'L1 F.Cu: components, signals and local ground',
             'L2 In1.Cu: ground reference; no signal tracks', 'L3 In2.Cu: 3.3 V pour plus signal tracks',
             'L4 B.Cu: signals, ground and local VSYS region', 'Min track / space: 0.10 / 0.10 mm',
             'Ordinary vias: 0.60 land / 0.30 finished drill', 'One local escape via: 0.50 / 0.20 mm',
             'Annular ring: 0.15 mm; no HDI or via-in-pad', 'USB: 90 ohm differential +/-10% controlled impedance',
             'Nominal top dielectric: 0.10 mm; confirm stack', 'Fabricator must provide coupon/report and DFM',
             'Plated USB shell slots: use PTH Excellon routing', 'NPTH and plated drills supplied separately',
             '100% electrical test against IPC-D-356', 'No components on bottom; all BOM parts fitted',
             'Panelization by assembler, outside RF keepout', 'FIRST ARTICLE HOLD; unvalidated prototype']
    for index, line in enumerate(lines):
        document.drawString(174*mm, (172-index*6)*mm, line)
    document.setFont('Helvetica', 8)
    document.drawString(16*mm, 14*mm, 'Gerber Edge.Cuts and drill coordinates control geometry. This illustration does not replace fabrication data. See ASSEMBLY.md.')
    document.save()


def assembly_drawing():
    path = FAB/'assembly-top.pdf'
    source = pymupdf.open(stream=path.read_bytes(), filetype='pdf')
    document = pymupdf.open()
    page = document.new_page(width=1190.55, height=841.89)
    page.insert_text((40,40), 'ASTER2350 / REV A / TOP ASSEMBLY', fontsize=20)
    page.insert_text((40,62), 'All 121 BOM parts fitted. 118 SMT + J2/J6/J7 THT; solder all four J1 plated shell tabs.', fontsize=11)
    page.show_pdf_page(pymupdf.Rect(40,90,1150,780), source, 0,
                       clip=pymupdf.Rect(98*mm,98*mm,182*mm,168*mm))
    page.insert_text((40,808), 'Top view; pin numbers and pin-1 marks shown. Match placement datums to BOM/CSV. Not a dimensional fabrication drawing.', fontsize=10)
    document.save(path, garbage=4, deflate=True)


def package():
    archive = FAB/'Aster2350-RevA-PCBWay.zip'
    members = sorted(path for path in FAB.rglob('*') if path.is_file() and path not in (archive, FAB/'SHA256SUMS'))
    source_members = [ROOT/'README.md', ROOT/f'{NAME}.kicad_pro', ROOT/f'{NAME}.kicad_pcb', ROOT/f'{NAME}.kicad_sch',
                      ROOT/'processor.kicad_sch', ROOT/'power.kicad_sch', ROOT/'interfaces.kicad_sch',
                      ROOT/'fp-lib-table', ROOT/'sym-lib-table', ROOT/'design-data.json']
    source_members += [path for path in (ROOT/'libraries').rglob('*') if path.is_file()]
    source_members += [ROOT/'references/SOURCES.md', ROOT/'tools/requirements.txt', *sorted((ROOT/'tools').glob('*.py'))]
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in members:
            output.write(path, 'fab/'+str(path.relative_to(FAB)))
        for path in source_members:
            output.write(path, 'source/'+str(path.relative_to(ROOT)))
    manifest_files = [*members, archive]
    (FAB/'SHA256SUMS').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(FAB))+'\n' for path in manifest_files))


def main():
    board_path = ROOT/f'{NAME}.kicad_pcb'
    run('sch','erc','--format','json','--output',FAB/'ERC.json',ROOT/f'{NAME}.kicad_sch')
    run('pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--output',FAB/'DRC.json',board_path)
    run('sch','export','netlist','--format','kicadxml','--output',FAB/'schematic-netlist.xml',ROOT/f'{NAME}.kicad_sch')
    board = cad.sx.load(board_path.open())
    parts = purchased_parts(board)
    bom_lines = tables(parts)
    validate(board,parts,bom_lines)
    run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts',
        '--use-drill-file-origin','--subtract-soldermask','--check-zones','--output',FAB/'gerbers',board_path)
    run('pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-oval-format','route',
        '--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report',
        '--report-path',FAB/'drill-report.txt','--output',FAB/'drill',board_path)
    run('pcb','export','pos','--format','csv','--units','mm','--side','front','--use-drill-file-origin',
        '--exclude-bom','--exclude-dnp','--output',FAB/'placements-kicad.csv',board_path)
    with (FAB/'placements-kicad.csv').open() as source:
        native = {row['Ref']:row for row in csv.DictReader(source)}
    assert set(native)=={part['reference'] for part in parts}, (len(native),len(parts))
    for part in parts:
        row=native[part['reference']]
        assert abs(float(row['PosX'])-(part['x']-100))<0.001 and abs(float(row['PosY'])-(165-part['y']))<0.001
        assert abs((float(row['Rot'])-part['rotation'])%360)<0.001
    run('pcb','export','ipcd356','--output',FAB/'Aster2350.ipc',board_path)
    run('sch','export','pdf','--output',FAB/'schematic.pdf',ROOT/f'{NAME}.kicad_sch')
    run('pcb','export','pdf','--layers','F.Fab,Edge.Cuts','--sketch-pads-on-fab-layers',
        '--sketch-pad-numbers','--exclude-value','--black-and-white','--mode-single','--output',FAB/'assembly-top.pdf',board_path)
    assembly_drawing()
    run('pcb','export','pdf','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu','--common-layers','Edge.Cuts',
        '--mode-multipage','--output',FAB/'copper-review.pdf',board_path)
    fabrication_drawing(board)
    compatibility_copy = FAB/'Aster2350-KiCad10.kicad_pcb'
    compatibility_copy.unlink(missing_ok=True)
    run('pcb','downgrade','--target','10.0','--output',compatibility_copy,board_path)
    board_path.write_bytes((FAB/'Aster2350-KiCad10.kicad_pcb').read_bytes())
    run('pcb','drc','--schematic-parity','--format','json','--output',FAB/'DRC.json',board_path)
    final_board = cad.sx.load(board_path.open())
    validate(final_board, parts, bom_lines)
    package()
    print('Released',len(parts),'fully populated purchased components')


if __name__=='__main__':
    main()
