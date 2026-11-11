from pathlib import Path
import csv
import json
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, HexColor, black, toColor

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'fab/assembly'
svg = ET.parse(folder / 'top-assembly-orientation.svg').getroot()
minimum_x, minimum_y, width, height = map(float, svg.attrib['viewBox'].split())
page_width, page_height = landscape(A3)
pdf = canvas.Canvas(str(folder / 'assembly-orientation.pdf'), pagesize=(page_width, page_height))
pdf.setTitle('Atlas2350 Rev A complete assembly orientation')
pdf.setFont('Helvetica-Bold', 15)
pdf.drawString(12 * mm, page_height - 13 * mm, 'ATLAS2350 REV A - COMPLETE TOP ASSEMBLY')
scale = min((page_width - 30 * mm) / width, (page_height - 40 * mm) / height)
left = (page_width - width * scale) / 2
top = page_height - 22 * mm
def point(x, y):
    return left + (float(x) - minimum_x) * scale, top - (float(y) - minimum_y) * scale
def color(value, opacity=1):
    if value.startswith('#') and len(value) == 4:
        value = '#' + ''.join(character * 2 for character in value[1:])
    chosen = toColor(value)
    return Color(1 - opacity + opacity * chosen.red, 1 - opacity + opacity * chosen.green,
                 1 - opacity + opacity * chosen.blue)
for element in svg.iter():
    tag = element.tag.rsplit('}', 1)[-1]
    values = element.attrib
    fill = values.get('fill', 'none')
    stroke = values.get('stroke', 'none')
    if fill != 'none':
        pdf.setFillColor(color(fill, float(values.get('fill-opacity', 1))))
    if stroke != 'none':
        pdf.setStrokeColor(color(stroke))
    pdf.setLineWidth(float(values.get('stroke-width', 0.1)) * scale)
    if tag in {'polygon', 'polyline'}:
        points = [point(*pair.split(',')) for pair in values['points'].split()]
        path = pdf.beginPath()
        path.moveTo(*points[0])
        for position in points[1:]:
            path.lineTo(*position)
        if tag == 'polygon':
            path.close()
        pdf.drawPath(path, stroke=int(stroke != 'none'), fill=int(fill != 'none'))
    elif tag == 'rect':
        position = point(values['x'], float(values['y']) + float(values['height']))
        pdf.rect(*position, float(values['width']) * scale, float(values['height']) * scale,
                 stroke=int(stroke != 'none'), fill=int(fill != 'none'))
    elif tag == 'circle':
        pdf.circle(*point(values['cx'], values['cy']), float(values['r']) * scale,
                   stroke=int(stroke != 'none'), fill=int(fill != 'none'))
    elif tag == 'line':
        pdf.line(*point(values['x1'], values['y1']), *point(values['x2'], values['y2']))
    elif tag == 'text':
        pdf.setFillColor(color(values.get('fill', '#111111')))
        pdf.setFont('Helvetica', float(values.get('font-size', 1)) * scale)
        pdf.drawString(*point(values['x'], values['y']), element.text or '')
pdf.setFillColor(black)
pdf.setFont('Helvetica', 8)
pdf.drawString(12 * mm, 12 * mm, 'All 115 real components populated by PCBWay. Red markers identify physical pad1 / USB A1; not universal polarity.')
pdf.drawString(12 * mm, 8 * mm, 'Envelope polygons are courtyards, including RF keepout, not physical package edges. Reconcile anchors/angles with pinout and centroid-source.csv.')
pdf.showPage()
pdf.setPageSize(A4)
rows = list(csv.DictReader((folder / 'parts.csv').open()))
page = 0
for first in range(0, len(rows), 45):
    page += 1
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(12 * mm, 282 * mm, f'Atlas2350 Rev A - population / CAD anchors - {page}')
    pdf.setFont('Helvetica', 8)
    pdf.drawString(12 * mm, 275 * mm, 'All fitted. X right / Y down, mm. Saved KiCad rotations CCW, degrees. See centroid CSV for body centers.')
    pdf.setFont('Helvetica-Bold', 8)
    for text, x in [('Ref', 12), ('Exact MPN', 30), ('X', 123), ('Y', 144), ('Rotation', 165), ('Mount', 185)]:
        pdf.drawString(x * mm, 265 * mm, text)
    for index, row in enumerate(rows[first:first + 45]):
        y = (258 - index * 5.2) * mm
        pdf.setFont('Helvetica', 7.3)
        for text, x in [(row['reference'], 12), (row['full_mpn'], 30),
                        (f'{float(row["x_mm"]):.3f}', 123), (f'{float(row["y_mm"]):.3f}', 144),
                        (f'{float(row["rotation_deg"]):.1f}', 165), (row['mounting'].split()[0], 185)]:
            pdf.drawString(x * mm, y, text)
    pdf.showPage()
pdf.save()
verification = json.loads((ROOT / 'checks/verification.json').read_text())
notes = canvas.Canvas(str(ROOT / 'fab/fabrication-and-assembly.pdf'), pagesize=A4)
notes.setTitle('Atlas2350 Rev A PCBWay turnkey fabrication and assembly instructions')
notes.setFont('Helvetica-Bold', 15)
notes.drawString(14 * mm, 281 * mm, 'Atlas2350 Rev A - PCBWay TURNKEY')
notes.setFont('Helvetica', 9)
lines = [
    'Quote an initial lot of five completely assembled development boards.',
    'PCBWay fabricates the PCB, supplies all exact-MPN BOM parts and assembles SMT + THT.',
    '115 real components per board; 53 BOM groups; no DNP or customer-fit components.',
    '', 'FABRICATION',
    '80 x 75 mm chamfered outline, four copper layers, finished thickness 1.6 mm.',
    'Lead-free FR-4, ENIG, green soldermask, white silkscreen; IPC Class 2 workmanship.',
    'Outer copper 1 oz, inner copper 0.5 oz; nominal dielectrics 0.12/1.255/0.12 mm.',
    'Actual cured stackup/material details require quotation; no impedance certification claimed.',
    'F/B: signals + GND. In1/In2: GND pours with documented signal escape corridors.',
    'Minimum track / clearance: 0.150 / 0.127 mm. Hole-to-copper: >=0.178 mm.',
    'Routing vias: 0.600 mm lands / 0.300 mm finished holes, 0.150 mm annular ring.',
    f'ALL {verification["fill_cap_holes_total"]} holes in drill/filled-capped-hole-schedule.csv require',
    'IPC-4761 Type VII resin filling and copper capping, including 12 U6 thermal PTHs.',
    'DO NOT fill connector component-lead holes. J6 finished holes are 0.700 mm.',
    'Keep all listed NPTH mechanical holes non-plated. Excellon slots are routed.',
    'Bare-board 100% electrical test against Atlas2350.ipc (IPC-D-356).',
    '', 'ASSEMBLY / ORIENTATION',
    'Assemble every BOM row, including THT J5/J6/J7 and USB shell stakes.',
    'Use exact packages: U2 wide SOIC8, U3 narrow SOIC8, U5 exact RNM0015A.',
    'U5 pads9/11 are SWITCH NODES, not ground; there is no exposed pad16.',
    'Use WS2812B-2020-V6 exactly. Do not substitute older LED logic-threshold variants.',
    'Top paste Gerber supplied; PCBWay reconciles stencil/profile with component datasheets.',
    'Inspect fine-pitch QFN / RNM / module thermal solder joints, including X-ray as needed.',
    'Pick-and-place centroids / CAD anchors / pin1 occurrences are separately identified.',
    'Reconcile reel zero angles, vacuum pick points and panel offsets before placement.',
    '', 'MECHANICAL / HANDLING',
    'U6 antenna extends about 6.1 mm beyond the top board edge; no copper under antenna.',
    'Panel rails, clamps and tabs must clear the module and its antenna keepout.',
    'Preserve connector access at board edges and microSD insertion/ejection clearance.',
    'No screws, battery, cable, microSD card or mating adapters are assembly components.',
    '', 'ELECTRICAL / QUALIFICATION',
    'Battery interface is CUSTOM: J2 pin1 BAT+, pin2 GND, pin3 cell-mounted 10k NTC.',
    'External protected 1S 4.2V LiPo >=500 mAh; no battery installed/shipped in this package.',
    'No application or ESP-AT firmware image supplied; IC programming is not in this order.',
    'Firmware controls USB100/500/suspend and radio enable. Default radio is disabled.',
    'External RP core LDO: firmware must set VREG.HIZ and avoid low-power VREG mode.',
    'U10 switches LED_VDD with SW5; RGB not guaranteed below LED_VDD 3.3V.',
    'Blank RGB around VBAT 3.6V under load; the main rail remains 3.296V.',
    'Unbuilt prototype: electrical/thermal/USB/RF qualification still required on first articles.',
    'Clean ERC/DRC and pin checks are design checks, not factory DFM or functional approval.',
    '', 'Read fabrication-notes.md, assembly-notes.md and test-plan.md before quotation.',
]
y = 269 * mm
for line in lines:
    notes.setFont('Helvetica-Bold' if line in {'FABRICATION', 'ASSEMBLY / ORIENTATION', 'MECHANICAL / HANDLING', 'ELECTRICAL / QUALIFICATION'} else 'Helvetica', 9)
    notes.drawString(14 * mm, y, line)
    y -= 5.0 * mm
notes.save()
print('Wrote assembly-orientation.pdf and fabrication-and-assembly.pdf')
