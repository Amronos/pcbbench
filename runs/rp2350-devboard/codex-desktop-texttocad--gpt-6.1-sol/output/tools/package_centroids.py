"""Export physical F.Fab body bounding-box centers only when explicitly invoked."""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import sexpdata
from shapely.geometry import MultiLineString, Polygon
from shapely.ops import polygonize_full


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAMES = ("pcbway-centroids.csv", "centroid-source.csv", "centroid-units.txt")
CRITICAL_REFS = tuple(f"J{i}" for i in range(1, 8)) + ("U6", "SW5")
PRECISION = 6
METHOD = "largest-area closed F.Fab body polygon; local bounding-box center transformed to board"
PCBWAY_REQUIREMENTS_URL = "https://www.pcbway.com/assembly-file-requirements.html"


def tag(node):
    return str(node[0]) if isinstance(node, list) and node else ""


def children(node, name):
    return [item for item in node[1:] if tag(item) == name]


def child(node, name):
    matches = children(node, name)
    if len(matches) > 1:
        raise ValueError(f"Duplicate {name} entry")
    return matches[0] if matches else None


def natural(ref):
    return tuple((1, int(piece)) if piece.isdigit() else (0, piece.casefold())
                 for piece in re.split(r"(\d+)", ref) if piece)


def excluded(ref):
    return ref.upper().startswith(("H", "TP"))


def mounting(footprint, ref):
    kinds = [str(pad[2]) for pad in children(footprint, "pad") if len(pad) > 2]
    surface = kinds.count("smd")
    through = kinds.count("thru_hole")
    if surface and through:
        return "SMT with plated thermal features" if ref == "U6" else "SMT+THT"
    if surface:
        return "SMT"
    if through:
        return "THT"
    raise ValueError("No identifiable SMT/THT mounting pads; no mounting classification guessed")


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Non-finite geometry value")
    return value


def pair(node):
    if node is None or len(node) != 3:
        raise ValueError("Missing or malformed two-coordinate geometry entry")
    return finite(node[1]), finite(node[2])


def fmt(value):
    value = finite(value)
    return f"{0.0 if abs(value) < 0.5 * 10 ** -PRECISION else value:.6f}"


def properties(footprint):
    result = {}
    for entry in children(footprint, "property"):
        if len(entry) < 3:
            raise ValueError("Malformed footprint property")
        key = str(entry[1]).casefold()
        if key in result:
            raise ValueError(f"Duplicate footprint property {entry[1]}")
        result[key] = str(entry[2]).strip()
    if not result.get("reference"):
        for entry in children(footprint, "fp_text"):
            if len(entry) > 2 and str(entry[1]) == "reference":
                result["reference"] = str(entry[2]).strip()
    return result


def transform(node, required=False):
    entry = child(node, "transform")
    if entry is not None:
        anchor = pair(child(entry, "translate"))
        rotation = child(entry, "rotate")
        if rotation is None or len(rotation) != 2:
            raise ValueError("Missing or malformed native transform rotation")
        angle = finite(rotation[1])
        scale_entry = child(entry, "scale")
        scale = pair(scale_entry) if scale_entry is not None else (1.0, 1.0)
    else:
        at = child(node, "at")
        if at is None:
            if required:
                raise ValueError("Footprint lacks saved transform/anchor")
            return (0.0, 0.0), 0.0, (1.0, 1.0)
        if len(at) not in (3, 4):
            raise ValueError("Malformed legacy footprint position")
        anchor = finite(at[1]), finite(at[2])
        angle = finite(at[3]) if len(at) == 4 else 0.0
        scale = (1.0, 1.0)
    if any(value <= 0 for value in scale):
        raise ValueError("Mirrored/nonpositive scale requires explicit engineering review")
    return anchor, angle, scale


def transformed(point, pose):
    anchor, angle, scale = pose
    x, y = point[0] * scale[0], point[1] * scale[1]
    cosine, sine = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    return (anchor[0] + x * cosine + y * sine,
            anchor[1] - x * sine + y * cosine)


def valid_polygon(points, label):
    if len(points) < 3:
        raise ValueError(f"{label} has fewer than three vertices")
    polygon = Polygon(points)
    if polygon.is_empty or not polygon.is_valid or polygon.area <= 1e-10:
        raise ValueError(f"Invalid or zero-area {label}; no geometry repair guessed")
    return polygon


def body_polygon(footprint):
    candidates = []
    lines = {}
    ignored = set()
    for graphic in footprint[1:]:
        kind = tag(graphic)
        if not kind.startswith("fp_"):
            continue
        layer = child(graphic, "layer")
        if layer is None or str(layer[1]) != "F.Fab":
            continue
        if kind not in ("fp_rect", "fp_poly", "fp_line"):
            ignored.add(kind)
            continue
        pose = transform(graphic)
        if kind == "fp_rect":
            start, end = pair(child(graphic, "start")), pair(child(graphic, "end"))
            corners = ((start[0], start[1]), (end[0], start[1]),
                       (end[0], end[1]), (start[0], end[1]))
            polygon = valid_polygon([transformed(p, pose) for p in corners], kind)
            candidates.append((polygon, "closed fp_rect"))
        elif kind == "fp_poly":
            pts = child(graphic, "pts")
            if pts is None or any(tag(p) != "xy" for p in pts[1:]):
                raise ValueError("Unsupported or missing fp_poly vertices")
            polygon = valid_polygon([transformed(pair(p), pose) for p in pts[1:]], kind)
            candidates.append((polygon, "closed fp_poly (implicit closing edge)"))
        else:
            start = transformed(pair(child(graphic, "start")), pose)
            end = transformed(pair(child(graphic, "end")), pose)
            start = tuple(round(v, PRECISION) for v in start)
            end = tuple(round(v, PRECISION) for v in end)
            if start != end:
                key = tuple(sorted((start, end)))
                lines[key] = (start, end)
    dangling_count = 0
    if lines:
        polygons, cuts, dangles, invalid = polygonize_full(MultiLineString(list(lines.values())))
        if not invalid.is_empty:
            raise ValueError("Invalid closed F.Fab fp_line rings; no repair guessed")
        dangling_count = len(cuts.geoms) + len(dangles.geoms)
        for polygon in polygons.geoms:
            body = valid_polygon(list(polygon.exterior.coords), "closed fp_line loop")
            candidates.append((body, "closed fp_line loop; endpoint rounding 0.000001 mm"))
    if not candidates:
        raise ValueError("No closed physical F.Fab rect/poly/line body; no anchor/courtyard fallback")
    candidates.sort(key=lambda item: item[0].area, reverse=True)
    chosen, source = candidates[0]
    for other, _ in candidates[1:]:
        if math.isclose(other.area, chosen.area, rel_tol=1e-9, abs_tol=1e-10):
            if not chosen.equals(other):
                raise ValueError("Equal-largest F.Fab polygons disagree; body selection ambiguous")
    info = {
        "methodology": METHOD,
        "selected_geometry": source,
        "closed_polygon_candidates": len(candidates),
        "ignored_open_line_features": dangling_count,
        "ignored_f_fab_kinds": ",".join(sorted(ignored)),
        "body_area_local_mm2": fmt(chosen.area),
        "body_outline_local_mm_json": json.dumps(list(chosen.exterior.coords), separators=(",", ":")),
    }
    return chosen, info


def source_template(ref, footprint_name, mpn):
    keys = (
        "Designator", "MPN", "footprint", "mounting", "centroid_csv_included",
        "centroid_csv_exclusion_reason", "status", "error", "methodology",
        "selected_geometry", "closed_polygon_candidates", "ignored_open_line_features",
        "ignored_f_fab_kinds", "body_area_local_mm2", "body_outline_local_mm_json",
        "local_bbox_min_x_mm", "local_bbox_min_y_mm", "local_bbox_max_x_mm",
        "local_bbox_max_y_mm", "local_body_center_x_mm", "local_body_center_y_mm",
        "anchor_board_x_mm", "anchor_board_y_down_mm", "anchor_cartesian_y_mm",
        "rotation_kicad_deg", "scale_x", "scale_y", "offset_board_x_mm",
        "offset_board_y_down_mm", "body_center_board_x_mm", "body_center_board_y_down_mm",
        "MidX", "MidY", "Layer", "world_bbox_min_x_mm", "world_bbox_min_y_down_mm",
        "world_bbox_max_x_mm", "world_bbox_max_y_down_mm",
    )
    row = dict.fromkeys(keys, "")
    row.update(Designator=ref, MPN=mpn, footprint=footprint_name, methodology=METHOD)
    return row


def collect(design, pcb, expected_count, expected_surface_count=112):
    if not isinstance(design, list) or tag(pcb) != "kicad_pcb":
        raise ValueError("Expected design.json list and native kicad_pcb root")
    metadata = {}
    for item in design:
        ref = str(item.get("ref", "")).strip()
        if not ref or ref in metadata:
            raise ValueError(f"Missing/duplicate design reference {ref!r}")
        metadata[ref] = item
    footprints = {}
    for footprint in children(pcb, "footprint"):
        fields = properties(footprint)
        ref = fields.get("reference", "")
        if not ref or ref in footprints:
            raise ValueError(f"Missing/duplicate PCB reference {ref!r}")
        footprints[ref] = footprint, fields
    expected = {ref for ref in metadata if not excluded(ref)}
    actual = {ref for ref in footprints if not excluded(ref)}
    errors = []
    if expected != actual:
        errors.append(f"Reference mismatch: missing PCB={sorted(expected - actual, key=natural)}, "
                      f"missing design={sorted(actual - expected, key=natural)}")
    if len(actual) != expected_count:
        errors.append(f"Expected {expected_count} real components, found {len(actual)}")
    rows, sources = [], []
    for ref in sorted(actual | expected, key=natural):
        meta = metadata.get(ref, {})
        mpn = str(meta.get("mpn", "")).strip()
        footprint, fields = footprints.get(ref, (None, {}))
        name = str(footprint[1]) if footprint is not None else ""
        source = source_template(ref, name, mpn)
        try:
            if footprint is None or not meta or not mpn:
                raise ValueError("Missing saved footprint or design full MPN")
            if fields.get("mpn") and fields["mpn"] != mpn:
                raise ValueError("Saved PCB and design MPN disagree")
            layer_entry = child(footprint, "layer")
            if layer_entry is None or str(layer_entry[1]) != "F.Cu":
                raise ValueError("Only top components supported by the requested F.Fab transform")
            attributes = child(footprint, "attr")
            if attributes is not None and any(str(a) in ("dnp", "exclude_from_bom") for a in attributes[1:]):
                raise ValueError("Real component marked DNP or excluded from BOM")
            mount = mounting(footprint, ref)
            include = mount != "THT"
            source.update(mounting=mount, centroid_csv_included="yes" if include else "no",
                          centroid_csv_exclusion_reason="" if include else "Pure THT; manual placement from source report")
            pose = transform(footprint, required=True)
            anchor, angle, scale = pose
            source.update(anchor_board_x_mm=fmt(anchor[0]), anchor_board_y_down_mm=fmt(anchor[1]),
                          anchor_cartesian_y_mm=fmt(-anchor[1]), rotation_kicad_deg=fmt(angle),
                          scale_x=fmt(scale[0]), scale_y=fmt(scale[1]), Layer="Top")
            polygon, info = body_polygon(footprint)
            source.update(info)
            minx, miny, maxx, maxy = polygon.bounds
            center = (minx + maxx) / 2, (miny + maxy) / 2
            world = transformed(center, pose)
            world_outline = Polygon([transformed(p, pose) for p in polygon.exterior.coords])
            source.update(local_bbox_min_x_mm=fmt(minx), local_bbox_min_y_mm=fmt(miny),
                          local_bbox_max_x_mm=fmt(maxx), local_bbox_max_y_mm=fmt(maxy),
                          local_body_center_x_mm=fmt(center[0]), local_body_center_y_mm=fmt(center[1]),
                          offset_board_x_mm=fmt(world[0] - anchor[0]),
                          offset_board_y_down_mm=fmt(world[1] - anchor[1]),
                          body_center_board_x_mm=fmt(world[0]), body_center_board_y_down_mm=fmt(world[1]),
                          MidX=fmt(world[0]), MidY=fmt(-world[1]), status="OK")
            for key, value in zip(("world_bbox_min_x_mm", "world_bbox_min_y_down_mm",
                                   "world_bbox_max_x_mm", "world_bbox_max_y_down_mm"), world_outline.bounds):
                source[key] = fmt(value)
            if include:
                rows.append(dict(Designator=ref, MidX=source["MidX"], MidY=source["MidY"],
                                 Layer="Top", Rotation=fmt(angle % 360), MPN=mpn))
        except ValueError as error:
            source.update(status="ERROR", error=str(error))
            errors.append(f"{ref}: {error}")
        sources.append(source)
    if len(rows) != expected_surface_count:
        errors.append(f"Expected {expected_surface_count} surface-mounted centroid rows, found {len(rows)}")
    return rows, sources, errors


def csv_text(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def metadata_text(board_path, design_path, board_hash, design_hash, rows, sources, errors):
    return "\n".join((
        "PCBWay physical F.Fab body bounding-box centers",
        f"Generated UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Board: {board_path.resolve()} SHA256={board_hash}",
        f"Design metadata: {design_path.resolve()} SHA256={design_hash}",
        "Units: millimetres; absolute saved board/page origin (0,0); no auxiliary-origin subtraction.",
        "Centroid CSV: Cartesian X right, Y up; MidX=boardX, MidY=-boardY, matching native Y-negative convention.",
        "Source CSV: explicitly labeled local/board-Y-down/Cartesian coordinates; local geometry is unscaled.",
        "Centroid CSV: surface-mounted parts only, including SMT+THT and U6 with plated thermal holes.",
        "Pure THT J5/J6/J7 excluded from centroid CSV; all real parts retained in centroid-source.csv.",
        "Layer=Top denotes assembly side, not mounting technology. H*/TP* bare features excluded.",
        f"PCBWay primary requirement verified 2026-11-10: {PCBWAY_REQUIREMENTS_URL}",
        'Official requirement: "Only surface mounting parts are listed in the Centroid."',
        "Native KiCad Footprint Position export may also be supplied separately; this export deliberately",
        "provides F.Fab body-box centers instead of saved footprint anchors to avoid anchor ambiguity.",
        "Method: largest-area valid closed F.Fab fp_rect/fp_poly or polygonized closed fp_line loop.",
        "Ignore text, other layers, courtyards, antenna keepouts, arcs/circles and smaller pin1 marks.",
        "Line endpoints rounded to 0.000001 mm; no gap bridging, buffering or guessed outline repair.",
        "Center is the selected body's local bounding-box center, then transformed; not center of mass.",
        "Transform: x=anchorX+(localX*scaleX)*cos+(localY*scaleY)*sin;",
        "           y=anchorY-(localX*scaleX)*sin+(localY*scaleY)*cos.",
        "Rotation: saved KiCad top-view CCW degrees normalized to [0,360); not a verified machine zero-angle.",
        "World bbox columns bound the transformed selected body, not courtyard/keepout.",
        "Assembler must reconcile zero-angle, reels, pick nozzle/fixtures and origin against assembly-pinout.csv",
        "and assembly drawings. Pure THT centers are in the source report for manual placement only.",
        "No anchor/Part.outline/courtyard fallback. Missing/ambiguous body is ERROR in centroid-source.csv.",
        "On any error no usable pcbway-centroids.csv is emitted; --overwrite removes its obsolete predecessor.",
        f"Surface centroid rows: {len(rows)}; all-part source rows: {len(sources)}; errors: {len(errors)}",
        "Status: ERROR; incomplete output, do not use for assembly." if errors else
        "Status: geometry export only; not ERC/DRC/DFM, supplier acceptance or fabrication release approval.",
        *(f"ERROR: {error}" for error in errors),
        "",
    ))


def print_review(rows, sources, errors):
    lookup = {row["Designator"]: row for row in sources}
    print("Critical body centers: board X/right Y/down; CSV MidY is the negative of board Y")
    for ref in CRITICAL_REFS:
        source = lookup.get(ref)
        if source is None:
            print(f"{ref}: ERROR missing real component")
        elif source["status"] != "OK":
            print(f"{ref}: ERROR {source['error']}")
        else:
            print(f"{ref}: local=({source['local_body_center_x_mm']}, {source['local_body_center_y_mm']}) "
                  f"body=({source['body_center_board_x_mm']}, {source['body_center_board_y_down_mm']}) "
                  f"anchor=({source['anchor_board_x_mm']}, {source['anchor_board_y_down_mm']}) "
                  f"offset=({source['offset_board_x_mm']}, {source['offset_board_y_down_mm']}) "
                  f"MidY={source['MidY']} rotation={source['rotation_kicad_deg']} "
                  f"mounting={source['mounting']} centroid_csv={source['centroid_csv_included']}")
    print(f"Surface centroid rows: {len(rows)}; all-part source rows: {len(sources)}; {len(errors)} errors")
    for error in errors:
        print(f"ERROR: {error}")


def package(design_path, board_path, output_path, expected_count, overwrite,
            expected_surface_count=112, inspect_only=False):
    design_bytes, board_bytes = design_path.read_bytes(), board_path.read_bytes()
    design_hash = hashlib.sha256(design_bytes).hexdigest()
    board_hash = hashlib.sha256(board_bytes).hexdigest()
    rows, sources, errors = collect(json.loads(design_bytes), sexpdata.loads(board_bytes.decode("utf-8")),
                                   expected_count, expected_surface_count)
    if not sources:
        raise ValueError("No real component records; nothing generated")
    if inspect_only:
        print_review(rows, sources, errors)
        print("Inspect-only: no output files or directories written")
        if errors:
            raise ValueError("Centroid inspection failed")
        return
    existing = [output_path / name for name in OUTPUT_NAMES if (output_path / name).exists()]
    if existing and not overwrite:
        raise ValueError("Centroid outputs already exist; use --overwrite only after revision review")
    payloads = {
        "centroid-source.csv": csv_text(list(sources[0]), sources),
        "centroid-units.txt": metadata_text(board_path, design_path, board_hash, design_hash, rows, sources, errors),
    }
    if not errors:
        payloads["pcbway-centroids.csv"] = csv_text(("Designator", "MidX", "MidY", "Layer", "Rotation", "MPN"), rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".centroid-package-", dir=output_path.parent) as directory:
        staged = Path(directory)
        for name, content in payloads.items():
            (staged / name).write_text(content, encoding="utf-8")
        if hashlib.sha256(design_path.read_bytes()).hexdigest() != design_hash or hashlib.sha256(board_path.read_bytes()).hexdigest() != board_hash:
            raise ValueError("Inputs changed during export; nothing committed")
        output_path.mkdir(parents=True, exist_ok=True)
        if errors and overwrite:
            (output_path / "pcbway-centroids.csv").unlink(missing_ok=True)
        for name in payloads:
            (staged / name).replace(output_path / name)
    print_review(rows, sources, errors)
    print(f"Output: {output_path.resolve()}")
    if errors:
        raise ValueError("Centroid export incomplete; inspect centroid-source.csv and centroid-units.txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=ROOT / "design.json")
    parser.add_argument("--board", type=Path, default=ROOT / "Atlas2350.kicad_pcb")
    parser.add_argument("--out", type=Path, default=ROOT / "fab" / "assembly")
    parser.add_argument("--expected-count", type=int, default=115)
    parser.add_argument("--expected-surface-count", type=int, default=112)
    parser.add_argument("--inspect-only", action="store_true", help="Read and validate geometry; print centers without writing any output")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        if args.expected_count <= 0 or args.expected_surface_count <= 0:
            raise ValueError("Expected component count must be positive")
        package(args.design.expanduser(), args.board.expanduser(), args.out.expanduser(),
                args.expected_count, args.overwrite, args.expected_surface_count, args.inspect_only)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Centroid packaging failed: {error}\n")


if __name__ == "__main__":
    main()
