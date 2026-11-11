"""Write everything PCBWay needs into fab/: Gerbers, drill, job file, BOM, centroid, assembly drawing."""
import csv
import glob
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "rp2350_dev"
PCB = os.path.join(ROOT, f"{NAME}.kicad_pcb")
SCH = os.path.join(ROOT, f"{NAME}.kicad_sch")
FAB = os.path.join(ROOT, "fab")
GERBER_LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def cli(*args):
    subprocess.run(["kicad-cli", *args], check=True, capture_output=True)


def gerbers():
    out = os.path.join(FAB, "gerber")
    cli("pcb", "export", "gerbers", "-o", out + "/", "-l", GERBER_LAYERS, "--subtract-soldermask", "--check-zones",
        "--use-drill-file-origin", PCB)
    cli("pcb", "export", "drill", "-o", out + "/", "--drill-origin", "plot", "--excellon-separate-th",
        "--generate-map", "--map-format", "pdf", PCB)
    shutil.make_archive(os.path.join(FAB, f"{NAME}_gerber"), "zip", out)


def positions():
    """ref -> placement from KiCad's position file, in mm from the board origin, plus whether it is SMD only."""
    tmp = "/tmp/scratch/pos"
    os.makedirs(tmp, exist_ok=True)
    rows = {}
    for smd_only in (False, True):
        path = os.path.join(tmp, f"pos_{smd_only}.csv")
        args = ["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp",
                "--use-drill-file-origin", "-o", path, PCB]
        if smd_only:
            args.insert(-1, "--smd-only")
        cli(*args)
        with open(path) as f:
            for r in csv.DictReader(f):
                if smd_only:
                    rows[r["Ref"]]["smd"] = True
                else:
                    rows[r["Ref"]] = dict(x=float(r["PosX"]), y=float(r["PosY"]), rot=float(r["Rot"]),
                                          side=r["Side"], smd=False)
    return rows


def components():
    net = "/tmp/scratch/bom_netlist.xml"
    cli("sch", "export", "netlist", "--format", "kicadxml", "-o", net, SCH)
    comps = []
    for c in ET.parse(net).getroot().find("components"):
        props = {p.get("name"): p.get("value") for p in c.findall("property")}
        if "exclude_from_bom" in props or "dnp" in props:
            continue
        comps.append(dict(ref=c.get("ref"), value=c.findtext("value"), footprint=c.findtext("footprint"),
                          desc=c.findtext("description"), **props))
    return comps


def ref_key(ref):
    head = ref.rstrip("0123456789")
    return head, int(ref[len(head):] or 0)


def package(c):
    return c["footprint"].split(":")[1]


def bom(comps, pos):
    groups = defaultdict(list)
    for c in comps:
        groups[c["MPN"]].append(c)
    lines = sorted(groups.values(), key=lambda g: min(ref_key(c["ref"]) for c in g))
    with open(os.path.join(FAB, f"{NAME}_bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item", "Designator", "Qty", "Manufacturer", "Manufacturer Part Number", "Description",
                    "Value", "Package", "Type", "LCSC Part #", "Digikey Part #", "Alternate"])
        for i, g in enumerate(lines, 1):
            c = g[0]
            refs = sorted((x["ref"] for x in g), key=ref_key)
            kind = "SMD" if all(pos[r]["smd"] for r in refs) else "SMD + THT pins"
            w.writerow([i, ",".join(refs), len(refs), c["Manufacturer"], c["MPN"], c["desc"], c["value"], package(c),
                        kind, c.get("LCSC Part #", ""), c.get("Digikey Part #", ""), c.get("Alternate", "")])
    return len(comps), len(lines)


def centroid(comps, pos):
    with open(os.path.join(FAB, f"{NAME}_centroid.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X (mm)", "Mid Y (mm)", "Layer", "Rotation", "Value", "Package"])
        for c in sorted(comps, key=lambda c: ref_key(c["ref"])):
            p = pos[c["ref"]]
            w.writerow([c["ref"], f"{p['x']:.3f}", f"{p['y']:.3f}", "Top" if p["side"] == "top" else "Bottom",
                        f"{p['rot']:.1f}", c["value"], package(c)])


def assembly():
    cli("pcb", "export", "pdf", "-o", os.path.join(FAB, f"{NAME}_assembly.pdf"), "-l", "F.Fab,Edge.Cuts",
        "--include-border-title", "--mode-single", "--scale", "0", "--sketch-pads-on-fab-layers",
        "--crossout-DNP-footprints-on-fab-layers", PCB)


def main():
    for old in glob.glob(os.path.join(FAB, "gerber")) + glob.glob(os.path.join(FAB, f"{NAME}_*")):
        shutil.rmtree(old) if os.path.isdir(old) else os.remove(old)
    os.makedirs(FAB, exist_ok=True)
    gerbers()
    pos = positions()
    comps = components()
    missing = [c["ref"] for c in comps if c["ref"] not in pos]
    assert not missing, f"BOM parts missing from the board: {missing}"
    parts, lines = bom(comps, pos)
    centroid(comps, pos)
    assembly()
    print(f"BOM: {parts} parts on {lines} lines")


if __name__ == "__main__":
    main()
