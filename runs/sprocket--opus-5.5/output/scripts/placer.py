"""Compute footprint poses: FIXED parts as given, ANCHORED parts by a greedy search next to their anchor pad.

Reads courtyards and pads from the KiCad library files, so it runs without a KiCad server.
"""
import math
import os
import re
import sys

from shapely.geometry import Point, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(__file__))
import design  # noqa: E402
from placement import ANCHORED, FIXED, KEEPOUT_Y, OUTLINE_H, OUTLINE_W  # noqa: E402

LIB = os.path.join(os.environ["SPROCKET_KICAD_LIBRARIES"], "footprints")
GAP = 0.2
EDGE = 0.35
# The RM2 courtyard includes its antenna keepout, which KEEPOUT_Y covers; use the module body instead.
BODY_OVERRIDE = {"RF_Module:RMC20452T": (-8.0, -8.25, 8.0, 9.0)}
# Escape ring kept free of small parts around fine-pitch ICs, so their pins can fan out between the passives
FANOUT_RING = {"U1": 0.8}


def parts():
    return {p["ref"]: p for ps in design.SHEETS.values() for p in ps}


def parse_fp(lib_id):
    lib, name = lib_id.split(":")
    text = open(os.path.join(LIB, f"{lib}.pretty", f"{name}.kicad_mod")).read()
    xs, ys = [], []
    for m in re.finditer(r"\((fp_rect|fp_line|fp_poly|fp_circle)(.*?)\(layer \"F\.CrtYd\"\)", text, re.S):
        coords = [(float(a), float(b)) for a, b in
                  re.findall(r"\((?:start|end|xy|center) ([-\d.]+) ([-\d.]+)\)", m.group(2))]
        if m.group(1) == "fp_circle":
            (cx, cy), (ex, ey) = coords
            r = math.dist((cx, cy), (ex, ey))
            coords = [(cx - r, cy - r), (cx + r, cy + r)]
        xs += [c[0] for c in coords]
        ys += [c[1] for c in coords]
    pads = []
    for m in re.finditer(r"\(pad \"([^\"]*)\" (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+)", text):
        pads.append((m.group(1), float(m.group(3)), float(m.group(4))))
    crt = BODY_OVERRIDE.get(lib_id) or (min(xs), min(ys), max(xs), max(ys))
    return crt, pads


def rot(x, y, deg):
    t = math.radians(deg)
    return x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)


def courtyard(crt, x, y, deg):
    pts = [rot(cx, cy, deg) for cx in (crt[0], crt[2]) for cy in (crt[1], crt[3])]
    return box(x + min(p[0] for p in pts), y + min(p[1] for p in pts),
               x + max(p[0] for p in pts), y + max(p[1] for p in pts))


def pad_pos(pads, x, y, deg):
    out = {}
    for num, px, py in pads:
        dx, dy = rot(px, py, deg)
        out.setdefault(num, (x + dx, y + dy))
    return out


def place():
    ps = parts()
    fp = {ref: parse_fp(p["fp"]) for ref, p in ps.items()}
    poses, boxes, pad_xy = {}, {}, {}
    for ref, (x, y, deg) in FIXED.items():
        poses[ref] = (x, y, deg)
        boxes[ref] = courtyard(fp[ref][0], x, y, deg)
        pad_xy[ref] = pad_pos(fp[ref][1], x, y, deg)
    board = box(EDGE, max(EDGE, KEEPOUT_Y + GAP), OUTLINE_W - EDGE, OUTLINE_H - EDGE)

    def net_of(ref, pad):
        nets = ps[ref]["nets"]
        return nets.get(pad)

    for ref, (aref, apad) in ANCHORED.items():
        ax, ay = pad_xy[aref][apad]
        crt, pads = fp[ref]
        anet = net_of(aref, apad)
        blocked = unary_union([b.buffer(GAP + FANOUT_RING.get(r, 0), join_style=2) for r, b in boxes.items()])
        best = None
        step = 0.25
        for r_i in range(0, 60):
            r = r_i * step
            n = max(1, int(2 * math.pi * r / step))
            for k in range(n):
                t = 2 * math.pi * k / n
                x = round((ax + r * math.cos(t)) / 0.05) * 0.05
                y = round((ay + r * math.sin(t)) / 0.05) * 0.05
                for deg in (0, 90, 180, 270):
                    cy = courtyard(crt, x, y, deg)
                    if not board.contains(cy) or cy.intersects(blocked):
                        continue
                    pp = pad_pos(pads, x, y, deg)
                    same = [pp[p] for p in pp if ps[ref]["nets"].get(p) == anet] or list(pp.values())
                    d = min(math.dist((ax, ay), q) for q in same)
                    score = d + 0.2 * r
                    if best is None or score < best[0]:
                        best = (score, x, y, deg)
            if best is not None and r > best[0] + 1.0:
                break
        if best is None:
            raise SystemExit(f"no room for {ref} near {aref}.{apad}")
        _, x, y, deg = best
        poses[ref] = (x, y, deg)
        boxes[ref] = courtyard(crt, x, y, deg)
        pad_xy[ref] = pad_pos(pads, x, y, deg)
    missing = set(ps) - set(poses)
    if missing:
        raise SystemExit(f"unplaced: {sorted(missing)}")
    return poses, boxes, pad_xy


def preview(path, boxes, scale=20):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (int(OUTLINE_W * scale) + 1, int(OUTLINE_H * scale) + 1), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, OUTLINE_W * scale, OUTLINE_H * scale], outline="black")
    d.rectangle([0, 0, OUTLINE_W * scale, KEEPOUT_Y * scale], fill=(255, 220, 220))
    for ref, b in boxes.items():
        x0, y0, x1, y1 = b.bounds
        d.rectangle([x0 * scale, y0 * scale, x1 * scale, y1 * scale], outline="blue")
        d.text((x0 * scale + 2, y0 * scale + 1), ref, fill="black")
    im.save(path)


if __name__ == "__main__":
    poses, boxes, _ = place()
    preview("/tmp/scratch/placement.png", boxes)
    for r, p in sorted(poses.items()):
        print(r, p)
