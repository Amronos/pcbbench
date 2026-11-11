"""Edits the saved .kicad_pcb as text, with the board closed: 3D models the stock library lacks, the stackup,
the title block and silkscreen text angles.

kipy can't write the stackup, and editing footprint definitions through the API risks wiping pads.
Idempotent: rerun after any step that rewrites the board.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "rp2350_dev.kicad_pcb")
sys.path.insert(0, os.path.dirname(__file__))
from placement import VERTICAL_SILK  # noqa: E402

# footprint -> (model path, offset xyz mm, rotation xyz deg). The LCSC models come from easyeda2kicad.
MODELS = {
    "RF_Module:RMC20452T": ("RM2.3dshapes/RM2_box.wrl", (0, 0, 0), (0, 0, 0)),
    "Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm":
        ("RP2350A_QFN60.3dshapes/QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.step", (0, 0, 0), (0, 0, 0)),
    "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias":
        ("BQ24074RGT.3dshapes/QFN-16_L3.0-W3.0-P0.50-EP1.7.step", (0, 0, 0), (0, 0, 0)),
    "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal":
        ("JST_S2B-PH-SM4-TB.3dshapes/CONN-SMD_P2.00_S2B-PH-SM4-TB-LF-SN.step", (1.0, -3.1, 0), (0, 0, 0)),
    "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm":
        ("WS2812C-2020.3dshapes/LED-SMD_4P-L2.0-W2.0-H0.8-TL_WS2812B-2020.step", (0, 0, 0), (0, 0, 0)),
    "Connector_Card:microSD_HC_Molex_104031-0811":
        ("microSD_Molex_104031-0811.3dshapes/SIM-SMD_8P-1040310811.step", (0, 0, 0), (0, 0, 180)),
}

# PCBWay standard 4-layer 1.6 mm, 1 oz stackup (pcbway.com/blog/Engineering_Technical/stackup___pcbway.html)
COPPER, PREPREG, CORE, MASK = 0.035, 0.11, 1.13, 0.01
STACKUP = f"""\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness {MASK}))
\t\t\t(layer "F.Cu" (type "copper") (thickness {COPPER}))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness {PREPREG}) (material "FR4") (epsilon_r 4.29) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness {COPPER}))
\t\t\t(layer "dielectric 2" (type "core") (thickness {CORE}) (material "FR4") (epsilon_r 3.96) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness {COPPER}))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness {PREPREG}) (material "FR4") (epsilon_r 4.29) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness {COPPER}))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness {MASK}))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
"""


def model_block(path, offset, rot):
    xyz = lambda v: " ".join(str(c) for c in v)  # noqa: E731
    return (f'(model "${{KIPRJMOD}}/lib/3d/{path}"\n\t\t\t(offset\n\t\t\t\t(xyz {xyz(offset)})\n\t\t\t)\n'
            f'\t\t\t(scale\n\t\t\t\t(xyz 1 1 1)\n\t\t\t)\n\t\t\t(rotate\n\t\t\t\t(xyz {xyz(rot)})\n\t\t\t)\n\t\t)')


def set_models(text):
    parts = re.split(r'(?=\n\t\(footprint ")', text)
    for i, part in enumerate(parts):
        m = re.match(r'\n\t\(footprint "([^"]+)"', part)
        if not m or m.group(1) not in MODELS:
            continue
        block = model_block(*MODELS[m.group(1)])
        part, n = re.subn(r'\(model "[^"]*"\n(?:\t\t\t.*\n)*?\t\t\)', lambda _: block, part, count=1)
        assert n == 1, m.group(1)
        parts[i] = part
    return "".join(parts)


def set_stackup(text):
    text = re.sub(r"\t\t\(stackup\n.*?\n\t\t\)\n", "", text, flags=re.S)
    return text.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)


# Portrait paper lets the tall board fill the assembly drawing
PAPER_AND_TITLE = ('\t(paper "A4" portrait)\n'
                   '\t(title_block\n\t\t(title "RP2350 Wi-Fi/BLE LiPo dev board")\n\t\t(rev "A")\n\t)\n')


def set_title_block(text):
    text = re.sub(r"\t\(title_block\n.*?\n\t\)\n", "", text, flags=re.S)
    return re.sub(r'\t\(paper "[^"]+"[^)]*\)\n', PAPER_AND_TITLE, text, count=1)


def set_text_angles(text):
    for label in VERTICAL_SILK:
        text, n = re.subn(rf'(\(gr_text "{label}"\n\t\t\(at [\d.]+ [\d.]+)(?: [\d.]+)?\)', r"\1 90)", text)
        assert n == 1, label
    return text


def main(pcb=PCB):
    with open(pcb) as f:
        text = f.read()
    text = set_title_block(set_text_angles(set_stackup(set_models(text))))
    with open(pcb, "w") as f:
        f.write(text)


if __name__ == "__main__":
    main(*sys.argv[1:])
