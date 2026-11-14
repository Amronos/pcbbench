"""Write the fabrication and assembly outputs to fab/ and the project BOM to BOM.csv.

fab/gerbers/  Gerbers, Gerber job file and Excellon drill files (PTH and NPTH)
fab/<name>-bom-pcbway.csv  and  fab/<name>-centroid.csv  in PCBWay's assembly format
fab/<name>-gerbers.zip  the upload for PCBWay's PCB order form"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D  # noqa: E402
import placement as PL  # noqa: E402

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "rp2350-devboard"
PCB = f"{PROJ}/{NAME}.kicad_pcb"
FAB = f"{PROJ}/fab"
BX, BY = 100.0, 50.0
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
THT = {"J5", "J6"}
NOTES = {
    "J1": "SMD contacts plus 4 plated shell tabs; paste-in-hole or hand solder the tabs",
    "J5": "Do not populate. 2.54 mm header holes left for the user",
    "J6": "Do not populate. 2.54 mm header holes left for the user",
    "U7": "Castellated module; keep the antenna end free of other parts",
    "U1": "QFN-60, exposed pad with thermal vias",
    "U5": "VQFN-16, exposed pad with thermal vias",
    "U6": "VSON-10, exposed pad with thermal vias",
}


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def ref_key(ref):
    digits = "".join(c for c in ref if c.isdigit())
    return ref.rstrip("0123456789"), int(digits or 0)


def gerbers():
    out = f"{FAB}/gerbers"
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "--check-zones",
        "-o", out + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--excellon-separate-th", "--generate-map", "--map-format", "pdf",
        "-o", out + "/", PCB)
    zipped = shutil.make_archive(f"{FAB}/{NAME}-gerbers", "zip", out)
    print("wrote", zipped)


def bom_groups():
    groups = {}
    for p in D.parts:
        key = (p["mpn"] or p["value"], p["fp"], p["unpopulated"])
        groups.setdefault(key, []).append(p)
    return sorted(groups.values(), key=lambda ps: (ps[0]["unpopulated"], *ref_key(ps[0]["ref"])))


def bom():
    header = ["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #", "Description/Value", "Package/Footprint",
              "Type", "Notes", "LCSC #"]
    rows = []
    for i, ps in enumerate(bom_groups(), 1):
        p = ps[0]
        refs = [q["ref"] for q in ps]
        notes = "; ".join(dict.fromkeys(NOTES[r] for r in refs if r in NOTES))
        if p["unpopulated"] and not notes:
            notes = "Do not populate. Panel fiducial, copper only"
        value = " / ".join(dict.fromkeys(q["value"] for q in ps))
        rows.append([i, ",".join(refs), len(refs), p["mfr"], p["mpn"], value, p["fp"].split(":")[1],
                     "THT" if refs[0] in THT else "SMD", notes, p["lcsc"]])
    for path in (f"{FAB}/{NAME}-bom-pcbway.csv", f"{PROJ}/BOM.csv"):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        print("wrote", path)


def centroid():
    """Top-side placements in mm from the board's bottom-left corner, Y up, KiCad rotation (CCW)."""
    with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
        run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
            "-o", tmp.name, PCB)
        with open(tmp.name) as f:
            placed = list(csv.DictReader(f))
    fitted = {p["ref"] for p in D.parts if not p["unpopulated"]}
    with open(f"{FAB}/{NAME}-centroid.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Footprint", "Mid X", "Mid Y", "Layer", "Rotation", "Comment"])
        for r in sorted(placed, key=lambda r: ref_key(r["Ref"])):
            if r["Ref"] not in fitted:
                continue
            x = float(r["PosX"]) - BX
            y = float(r["PosY"]) + BY + PL.H
            w.writerow([r["Ref"], r["Package"], f"{x:.3f}", f"{y:.3f}",
                        "Top" if r["Side"] == "top" else "Bottom", f"{float(r['Rot']):.1f}", r["Val"]])
    print("wrote", f"{FAB}/{NAME}-centroid.csv")


def main():
    os.makedirs(FAB, exist_ok=True)
    gerbers()
    bom()
    centroid()


if __name__ == "__main__":
    main()
