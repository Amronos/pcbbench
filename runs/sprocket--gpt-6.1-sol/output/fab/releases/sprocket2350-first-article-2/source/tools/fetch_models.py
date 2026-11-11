#!/usr/bin/env python3
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[1] / "lib" / "3d"
KICAD_COMMIT = "afa6aab16f43a736cd062b8c853863e753653921"
KICAD_RAW = (
    "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/"
    f"{KICAD_COMMIT}/"
)
RPI_ZIP = (
    "https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/"
    "RP-010328-CA-1-RP2350A%20Minimal%20KiCAD.zip"
)
RPI_BOARD = "RPI-RP2350A-MINIMAL_R4-S1_public/RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb"
MODELS = (
    {
        "requested": "Connector_JST.3dshapes/JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal.step",
        "status": "community-same-part",
        "source_url": "https://raw.githubusercontent.com/ElectronicCats/BastWAN/master/Hardware/bast-wan.pretty/packages3d/S2B-PH-SM4-TB(LF)(SN)--3DModel-STEP-56544.STEP",
        "source_model": "S2B-PH-SM4-TB(LF)(SN).STEP",
        "notes": "Community/distributor-style same-part model, not proven manufacturer provenance. Width 7.9 mm, housing height 5.5 mm, Y-up with tails to Y=-0.1 mm. Requires rotation X=90 degrees to become Z-up and footprint-specific Y translation. Raw model is not a zero-transform drop-in. Redistribution rights not independently verified.",
    },
    {
        "requested": "Inductor_SMD.3dshapes/L_Coilcraft_XxL4020.step",
        "status": "package-substitute",
        "source_model": "Inductor_SMD.3dshapes/L_Coilcraft_XAL4020-XXX.step",
        "notes": "XAL, not board MPN XFL4020-222MEC. Model envelope 4.3 x 4.3 x 2.1 mm matches XFL maximum envelope; terminals and markings are not verified equivalent.",
    },
    {
        "requested": "Package_DFN_QFN.3dshapes/QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm.step",
        "status": "manufacturer-same-part",
        "source_url": RPI_ZIP,
        "source_model": "rpi_rp2350a.step",
        "notes": "Extracted unchanged from Raspberry Pi's RP2350A Minimal KiCad design. Nominal 7 x 7 x 0.85 mm, 60 pins, 0.4 mm pitch, EP 3.4 x 3.4 mm. Pin-1 alignment with this board has not been checked in a 3D viewer.",
    },
    {
        "requested": "Package_DFN_QFN.3dshapes/VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
        "status": "package-substitute",
        "source_model": "Package_DFN_QFN.3dshapes/WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
        "notes": "16 pins, 3 x 3 mm, pitch 0.5 mm, EP 1.6 x 1.6 mm match. Model height 0.90 mm is within TI RGT0016B 1.0 mm maximum. Generic WQFN, not a BQ24074 manufacturer model.",
    },
    {
        "requested": "Package_SON.3dshapes/Texas_DRC0010J.step",
        "status": "package-substitute",
        "source_model": "Package_SON.3dshapes/VSON-10-1EP_3x3mm_P0.5mm_EP1.65x2.4mm.step",
        "notes": "10 pins, 3 x 3 mm, pitch 0.5 mm, EP 1.65 x 2.4 mm match TI DRC0010J. Height 0.93 mm is within its 0.8-1.0 mm body range. Generic model does not reproduce the DRC0010J thermal-pad extensions.",
    },
    {
        "requested": "Package_DFN_QFN.3dshapes/TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm.step",
        "status": "package-substitute",
        "source_model": "Package_DFN_QFN.3dshapes/VDFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.7mm.step",
        "notes": "8 pins, 2 x 2 mm, pitch 0.5 mm match. Height 0.78 mm is within Maxim T822 0.80 mm maximum. EP is 0.9 x 1.7 mm, NOT requested 0.8 x 1.2 mm. Visualization only, not an exact MAX17048 package.",
    },
)


def download(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=90) as response:
        return response.read()


def inspect_step(data):
    text = data.decode("utf-8")
    if not text.lstrip().startswith("ISO-10303-21;"):
        raise ValueError("Not STEP data (possibly an LFS pointer or HTML)")
    for token in ("HEADER;", "FILE_SCHEMA", "DATA;", "MANIFOLD_SOLID_BREP"):
        if token not in text:
            raise ValueError(f"STEP is missing {token}")
    if not text.rstrip().endswith("END-ISO-10303-21;"):
        raise ValueError("STEP has an incomplete terminator")
    if not re.search(r"SI_UNIT\s*\(\s*\.MILLI\.\s*,\s*\.METRE\.\s*\)", text):
        raise ValueError("STEP does not declare millimetre units")
    points = [
        tuple(float(value) for value in match.split(","))
        for match in re.findall(r"CARTESIAN_POINT\s*\([^,]*,\s*\(([^)]+)\)", text)
        if len(match.split(",")) == 3
    ]
    if not points:
        raise ValueError("STEP has no 3D Cartesian points")
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "solid_entities": text.count("MANIFOLD_SOLID_BREP("),
        "cartesian_point_extents_mm": [
            [min(p[axis] for p in points), max(p[axis] for p in points)]
            for axis in range(3)
        ],
    }


def extract_rpi(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        board = archive.read(RPI_BOARD).decode("utf-8")
        match = re.search(
            r'\(name "rpi_rp2350a\.step"\)\s*\(type model\)\s*\(data \|([^|]+)\|\s*\)',
            board,
        )
        if not match:
            raise ValueError("RP2350A embedded STEP not found in official archive")
        compressed = base64.b64decode(re.sub(r"\s+", "", match[1]), validate=True)
        model = subprocess.run(
            ["zstd", "-d", "-c"], input=compressed, capture_output=True, check=True
        ).stdout
        license_text = archive.read("RPI-RP2350A-MINIMAL_R4-S1_public/LICENSE.txt")
        return model, license_text


def main():
    parser = argparse.ArgumentParser(description="Fetch six STEP models with explicit provenance and substitution limits.")
    parser.add_argument("--check", action="store_true", help="Verify existing models offline against manifest hashes")
    args = parser.parse_args()
    if args.check:
        records = json.loads((ROOT / "manifest.json").read_text())["models"]
        for record in records:
            stats = inspect_step((ROOT / record["requested"]).read_bytes())
            if stats != record["verification"]:
                raise ValueError(f"Model differs from manifest: {record['requested']}")
            print(f"OK {record['requested']}")
        return

    ROOT.mkdir(parents=True, exist_ok=True)
    records = []
    for model in MODELS:
        record = dict(model)
        record.setdefault("source_url", KICAD_RAW + record["source_model"])
        data = download(record["source_url"])
        if record["status"] == "manufacturer-same-part":
            record["archive_sha256"] = hashlib.sha256(data).hexdigest()
            data, license_text = extract_rpi(data)
            (ROOT / "RaspberryPi-LICENSE.txt").write_bytes(license_text)
            record["archive_member"] = RPI_BOARD
        record["verification"] = inspect_step(data)
        path = ROOT / record["requested"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"OK {record['status']} {record['requested']}: {len(data)} bytes")
        records.append(record)
    (ROOT / "KiCad-LICENSE.md").write_bytes(download(KICAD_RAW + "LICENSE.md"))
    manifest = {"kicad_commit_checked": KICAD_COMMIT, "models": records}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
