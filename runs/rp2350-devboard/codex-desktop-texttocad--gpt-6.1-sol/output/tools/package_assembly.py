"""Package assembly data from saved board geometry; run only after final review."""

import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAMES = (
    "parts.csv",
    "bom.csv",
    "placement.csv",
    "assembly-pinout.csv",
    "top-assembly-orientation.svg",
    "assembly-orientation.md",
    "manifest.json",
)


def natural(value):
    return tuple((1, int(piece)) if piece.isdigit() else (0, piece.casefold())
                 for piece in re.split(r"(\d+)", str(value)) if piece)


def excluded(ref):
    return ref.upper().startswith(("H", "TP"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"Non-finite board coordinate or angle: {value}")
    return f"{value:.6f}"


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def csv_text(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def mounting(part):
    plated = sum(pad.drill is not None and pad.drill > 0 for pad in part.pads)
    surface = sum(pad.side in ("top", "bottom") and pad.drill is None
                  for pad in part.pads)
    if plated and surface:
        return "SMT with plated thermal features" if part.ref.startswith("U") else "SMT+THT"
    if plated:
        return "THT"
    if surface:
        return "SMT"
    return "REVIEW"


def field(part, name):
    return next((str(value).strip() for key, value in part.fields.items()
                 if key.casefold() == name.casefold()), "")


def collect(design, board):
    metadata = {}
    errors = []
    for item in design:
        ref = str(item.get("ref", "")).strip()
        if not ref or ref in metadata:
            errors.append(f"Missing or duplicate design reference: {ref!r}")
        metadata[ref] = item
    footprints = {}
    for part in board.parts:
        if part.ref in footprints:
            errors.append(f"Duplicate board reference: {part.ref}")
        footprints[part.ref] = part
    expected = {ref for ref in metadata if not excluded(ref)}
    actual = {ref for ref in footprints if not excluded(ref)}
    for ref in sorted(expected - actual, key=natural):
        errors.append(f"Real design part missing from saved PCB: {ref}")
    for ref in sorted(actual - expected, key=natural):
        errors.append(f"Saved PCB part missing from design metadata: {ref}")
    records = []
    pins = []
    for ref in sorted(expected & actual, key=natural):
        meta = metadata[ref]
        part = footprints[ref]
        manufacturer = str(meta.get("manufacturer", "")).strip()
        mpn = str(meta.get("mpn", "")).strip()
        value = str(meta.get("value", "")).strip()
        if not manufacturer or not mpn or not value or not part.footprint:
            errors.append(f"Incomplete manufacturer/MPN/value/package: {ref}")
        if part.value != value:
            errors.append(f"Value mismatch {ref}: design={value!r}, PCB={part.value!r}")
        for name, declared in (("Manufacturer", manufacturer), ("MPN", mpn)):
            saved = field(part, name)
            if saved and saved != declared:
                errors.append(f"{name} mismatch {ref}: design={declared!r}, PCB={saved!r}")
        if part.dnp or not part.in_bom:
            errors.append(f"Real part is DNP or excluded from PCB BOM: {ref}")
        if part.side not in ("top", "bottom"):
            errors.append(f"Unsupported component side {ref}: {part.side!r}")
        if not part.pads:
            errors.append(f"Real component has no copper pads: {ref}")
        declared_nets = {str(key): net for key, net in meta.get("nets", {}).items()}
        saved_numbers = {pad.number for pad in part.pads}
        for pad_number in declared_nets.keys() - saved_numbers:
            errors.append(f"Design pad missing from PCB: {ref}.{pad_number}")
        reference_pad = "1" if "1" in saved_numbers else "A1" if "A1" in saved_numbers else ""
        pin1 = []
        occurrences = defaultdict(int)
        ordered_pads = sorted(part.pads, key=lambda pad: (
            natural(pad.number), pad.at[0], pad.at[1], pad.side))
        for pad in ordered_pads:
            occurrences[pad.number] += 1
            declared = declared_nets.get(pad.number)
            match = "not_declared"
            if pad.number in declared_nets:
                if declared is None:
                    match = "declared_NC"
                    if pad.net and "unconnected" not in pad.net.casefold():
                        errors.append(f"Declared NC has connected net: {ref}.{pad.number}={pad.net}")
                else:
                    match = "match" if pad.net == declared else "mismatch"
                    if match == "mismatch":
                        errors.append(f"Net mismatch {ref}.{pad.number}: design={declared!r}, PCB={pad.net!r}")
            row = {
                "reference": ref,
                "pad_number": pad.number,
                "pad_occurrence": occurrences[pad.number],
                "feature_kind": "plated_pad" if pad.drill is not None else "surface_pad",
                "pin_function": pad.name or "",
                "net": pad.net or "",
                "declared_net": declared or "",
                "net_check": match,
                "component_side": part.side,
                "pad_side": pad.side,
                "x_mm": number(pad.at[0]),
                "y_mm": number(pad.at[1]),
                "drill_mm": "" if pad.drill is None else number(pad.drill),
                "is_pin1_reference": "yes" if pad.number == reference_pad else "no",
                "polygon_board_mm_json": compact(pad.polygon),
            }
            pins.append(row)
            if pad.number == reference_pad:
                pin1.append({"pad_number": pad.number,
                             "occurrence": occurrences[pad.number],
                             "x_mm": pad.at[0], "y_mm": pad.at[1],
                             "net": pad.net or ""})
        if not pin1:
            errors.append(f"No explicit pin1 or USB A1 reference pad found: {ref}")
        holes = sorted((hole for hole in board.holes if hole.part == ref), key=lambda hole: hole.at)
        for index, hole in enumerate(holes, 1):
            pins.append({
                "reference": ref, "pad_number": "", "pad_occurrence": index,
                "feature_kind": "unnumbered_NPTH", "pin_function": "", "net": "",
                "declared_net": "", "net_check": "not_electrical",
                "component_side": part.side, "pad_side": "both",
                "x_mm": number(hole.at[0]), "y_mm": number(hole.at[1]),
                "drill_mm": number(hole.diameter), "is_pin1_reference": "no",
                "polygon_board_mm_json": "[]",
            })
        records.append({
            "reference": ref, "manufacturer": manufacturer, "full_mpn": mpn,
            "value": value, "package": part.footprint, "quantity": 1,
            "side": part.side, "mounting": mounting(part),
            "x_mm": number(part.at[0]), "y_mm": number(part.at[1]),
            "rotation_deg": number(part.rotation),
            "rotation_normalized_deg": number(part.rotation % 360),
            "pin1_pad_number": reference_pad,
            "pin1_positions_board_mm_json": compact(pin1),
            "pad_count": len(part.pads), "npth_feature_count": len(holes),
            "board_in_bom": "yes" if part.in_bom else "no",
            "board_dnp": "yes" if part.dnp else "no",
        })
    if errors:
        raise ValueError("Assembly packaging validation failed:\n" + "\n".join(errors))
    return records, pins, footprints


def grouped_bom(records):
    groups = defaultdict(list)
    for row in records:
        groups[tuple(row[key] for key in ("manufacturer", "full_mpn", "value", "package"))].append(row)
    result = []
    for key, members in sorted(groups.items(), key=lambda item: natural(item[1][0]["reference"])):
        result.append({
            "manufacturer": key[0], "full_mpn": key[1], "value": key[2], "package": key[3],
            "quantity": len(members),
            "references": ", ".join(member["reference"] for member in members),
            "sides": ", ".join(sorted({member["side"] for member in members})),
            "mounting": ", ".join(sorted({member["mounting"] for member in members})),
        })
    return result


def orientation_svg(board, records, footprints):
    points = [point for line in board.outline for point in line]
    points += [point for row in records for point in footprints[row["reference"]].outline]
    points += [tuple(map(float, (row["x_mm"], row["y_mm"]))) for row in records]
    if not points:
        raise ValueError("Saved PCB has no drawable geometry")
    min_x = min(point[0] for point in points) - 4
    min_y = min(point[1] for point in points) - 8
    width = max(point[0] for point in points) - min_x + 4
    height = max(point[1] for point in points) - min_y + 4
    drawing = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}" width="1200">',
        '<title>Saved-board top-view assembly orientation; all real SMT/THT components</title>',
        '<desc>Millimetres in absolute KiCad board coordinates. X right, Y down. '
        'Red squares mark every pin1 occurrence, or USB A1. Rotation arrows use KiCad angles. '
        'Bottom components appear dashed in the same top-view frame. Hover for part details.</desc>',
        f'<rect x="{min_x}" y="{min_y}" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{min_x + 2}" y="{min_y + 3}" font-size="1.5">Top view: mm, X right/Y down; red = pin1 or USB A1</text>',
    ]
    for line in board.outline:
        coords = " ".join(f"{point[0]},{point[1]}" for point in line)
        drawing.append(f'<polyline points="{coords}" fill="none" stroke="#111" stroke-width="0.15"/>')
    for row in records:
        part = footprints[row["reference"]]
        color = "#2463a0" if row["mounting"].startswith("SMT") else "#23733d"
        dash = ' stroke-dasharray="0.5 0.3"' if part.side == "bottom" else ""
        label = f'{part.ref}: {row["full_mpn"]}; {part.side}; {row["mounting"]}; '
        label += f'origin=({row["x_mm"]},{row["y_mm"]}) mm; rotation={row["rotation_deg"]} deg; '
        label += f'pin reference={row["pin1_positions_board_mm_json"]}'
        drawing.append(f'<g><title>{html.escape(label)}</title>')
        if part.outline:
            coords = " ".join(f"{point[0]},{point[1]}" for point in part.outline)
            drawing.append(f'<polygon points="{coords}" fill="{color}" fill-opacity="0.06" stroke="{color}" stroke-width="0.08"{dash}/>')
        x, y = part.at
        angle = math.radians(part.rotation)
        end_x, end_y = x + math.cos(angle), y - math.sin(angle)
        drawing.append(f'<line x1="{x}" y1="{y}" x2="{end_x}" y2="{end_y}" stroke="{color}" stroke-width="0.15"/>')
        drawing.append(f'<circle cx="{end_x}" cy="{end_y}" r="0.12" fill="{color}"/>')
        for pin in json.loads(row["pin1_positions_board_mm_json"]):
            drawing.append(f'<rect x="{pin["x_mm"] - 0.18}" y="{pin["y_mm"] - 0.18}" width="0.36" height="0.36" fill="#c82121"/>')
        drawing.append(f'<text x="{x + 0.25}" y="{y - 0.25}" font-family="sans-serif" font-size="0.85" fill="{color}">{html.escape(part.ref)}</text></g>')
    drawing.append("</svg>\n")
    return "\n".join(drawing)


def orientation_guide(records, manifest):
    lines = [
        "# Saved-board assembly orientation guide", "",
        f'Generated UTC: {manifest["generated_utc"]}', "",
        f'Board: `{manifest["board_path"]}`',
        f'Board SHA-256: `{manifest["board_sha256"]}`', "",
        "This package records saved geometry; it does not run or certify ERC, DRC, DFM, firmware testing or production release.", "",
        "All coordinates are millimetres in the absolute KiCad board/page frame: (0,0) is the saved board coordinate origin, X increases right and Y increases down in the top view. No auxiliary-origin subtraction, bottom-view mirroring or placement centroid correction is applied. Placement X/Y is the saved footprint anchor, not a calculated package centroid. Pad X/Y is the actual transformed pad center (hole center for plated pads).", "",
        "Rotation is the saved KiCad footprint angle in degrees, counter-clockwise as viewed from the top. The normalized column is modulo360. Machine zero-angle/reel orientation must be reconciled by the assembler; these exports do not invent an IPC or pick-and-place rotation conversion. Bottom-side parts retain the same top-view coordinates; convert for a machine only after its convention is established.", "",
        "The SVG includes every real component, including THT and mixed packages. Envelope polygons are footprint courtyards, including the RF antenna keepout, not physical package edges. Red squares are all occurrences of literal pad1; USB-C without literal pad1 uses contact A1, explicitly labeled in the tables. Pin1 is a numbering/orientation reference, not a universal polarity mark. Nonpolar parts still have numbered pads. Repeated shell, switch and thermal pad numbers are retained as separate occurrences in assembly-pinout.csv. Unnumbered NPTH features belonging to real components have separate non-electrical rows; H*/TP* features are excluded.", "",
        "Assembly all real components in parts.csv/bom.csv, including through-hole connectors and mixed SMT/THT shell stakes. SMT modules with plated thermal features are identified separately from THT lead-mounted components. Consult assembly-pinout.csv for actual pad geometry/net assignments; do not infer lead holes from component category alone.", "",
        "Package is the actual saved footprint library identifier. Manufacturer/full MPN/value are validated against design.json and saved fields where present. H*/TP* features are excluded, not DNP; real parts marked DNP/excluded, missing parts, conflicting values/fields or declared-net mismatches stop packaging rather than silently omitting them.", "",
        "## Complete component orientation table", "",
        "| Ref | Full MPN | Side / mounting | X mm | Y mm | KiCad angle ° | Pin1/contact reference positions mm |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in records:
        positions = "; ".join(f'{pin["pad_number"]}[{pin["occurrence"]}]=({number(pin["x_mm"])},{number(pin["y_mm"])})'
                              for pin in json.loads(row["pin1_positions_board_mm_json"]))
        cells = [row["reference"], row["full_mpn"], f'{row["side"]} / {row["mounting"]}',
                 row["x_mm"], row["y_mm"], row["rotation_deg"], positions]
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    lines.extend(["", "## Files", ""])
    lines.extend(f"- `{name}`" for name in OUTPUT_NAMES)
    lines.extend(["", "No application firmware, fabrication copper exports or bare-board drill files are generated by this script.", ""])
    return "\n".join(lines)


def package(design_path, board_path, output_path, overwrite=False):
    from cad import kicad_pcb

    if output_path.resolve() in (design_path.resolve(), board_path.resolve()):
        raise ValueError("Output directory cannot be an input file")
    design_hash = digest(design_path)
    board_hash = digest(board_path)
    design = json.loads(design_path.read_text(encoding="utf-8"))
    if not isinstance(design, list):
        raise ValueError("design.json must contain a list of parts")
    board = kicad_pcb.read(board_path)
    records, pins, footprints = collect(design, board)
    if not records:
        raise ValueError("No real assembly components found")
    if digest(design_path) != design_hash or digest(board_path) != board_hash:
        raise ValueError("Inputs changed during packaging; save the final board and retry")
    bom = grouped_bom(records)
    generated = datetime.now(timezone.utc).isoformat()
    manifest = {
        "generated_utc": generated, "board_path": str(board_path.resolve()),
        "design_path": str(design_path.resolve()), "board_sha256": board_hash,
        "design_sha256": design_hash, "units": "mm", "origin": "absolute KiCad board/page (0,0)",
        "axes": "top view; X right, Y down", "rotation": "saved KiCad degrees CCW in top view",
        "placement_anchor": "saved footprint anchor; not a computed centroid",
        "pad_coordinates": "transformed board-coordinate pad/hole centers",
        "excluded_reference_prefixes": ["H", "TP"],
        "excluded_saved_board_references": sorted((ref for ref in footprints if excluded(ref)), key=natural),
        "component_count": len(records), "bom_group_count": len(bom),
        "pinout_row_count": len(pins), "sides": dict((side, sum(row["side"] == side for row in records)) for side in ("top", "bottom")),
        "release_status": "not assessed; script does not run ERC/DRC/DFM or approve fabrication",
        "files": list(OUTPUT_NAMES),
    }
    placements = [{key: row[key] for key in (
        "reference", "value", "full_mpn", "package", "quantity", "side", "mounting",
        "x_mm", "y_mm", "rotation_deg", "rotation_normalized_deg", "pin1_pad_number",
        "pin1_positions_board_mm_json")} for row in records]
    payloads = {
        "parts.csv": csv_text(list(records[0]), records),
        "bom.csv": csv_text(list(bom[0]), bom),
        "placement.csv": csv_text(list(placements[0]), placements),
        "assembly-pinout.csv": csv_text(list(pins[0]), pins),
        "top-assembly-orientation.svg": orientation_svg(board, records, footprints),
        "assembly-orientation.md": orientation_guide(records, manifest),
    }
    manifest["output_sha256"] = {name: hashlib.sha256(text.encode("utf-8")).hexdigest()
                                 for name, text in payloads.items()}
    payloads["manifest.json"] = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    existing = [output_path / name for name in OUTPUT_NAMES if (output_path / name).exists()]
    if existing and not overwrite:
        raise ValueError("Assembly outputs already exist; review then use --overwrite to replace this set")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".assembly-package-", dir=output_path.parent) as directory:
        staged = Path(directory)
        for name, text in payloads.items():
            (staged / name).write_text(text, encoding="utf-8")
        if digest(design_path) != design_hash or digest(board_path) != board_hash:
            raise ValueError("Inputs changed before output commit; nothing packaged")
        output_path.mkdir(parents=True, exist_ok=True)
        for name in OUTPUT_NAMES:
            (staged / name).replace(output_path / name)
    print(f"Packaged {len(records)} real components in {len(bom)} BOM groups; {len(pins)} pinout rows")
    print(f"Output: {output_path.resolve()}")
    for name in OUTPUT_NAMES:
        print(name)


def main():
    parser = argparse.ArgumentParser(description="Package all real parts from a saved final PCB; invoke only after owner requests post-DRC packaging.")
    parser.add_argument("--design", type=Path, default=ROOT / "design.json")
    parser.add_argument("--board", type=Path, default=ROOT / "Atlas2350.kicad_pcb")
    parser.add_argument("--out", type=Path, default=ROOT / "fab" / "assembly")
    parser.add_argument("--overwrite", action="store_true", help="Replace the named assembly output set after review")
    args = parser.parse_args()
    try:
        package(args.design.expanduser(), args.board.expanduser(), args.out.expanduser(), args.overwrite)
    except (OSError, ValueError, ImportError) as error:
        parser.exit(1, f"Assembly packaging failed: {error}\n")


if __name__ == "__main__":
    main()
