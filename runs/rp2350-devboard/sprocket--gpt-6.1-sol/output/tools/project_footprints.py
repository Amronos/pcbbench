import argparse
import copy
import hashlib
import re
from pathlib import Path

from kipy import KiCad

TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]')
NICKNAME = "Sprocket"
LIBRARY_PATH = Path("lib") / f"{NICKNAME}.pretty"


def expressions(text):
    depth = 0
    for token in TOKENS.finditer(text):
        if token.group() == "(":
            if depth == 1:
                start = token.start()
            depth += 1
        elif token.group() == ")":
            depth -= 1
            if depth == 1:
                yield start, token.end()


def parse(text):
    stack = []
    for token in TOKENS.findall(text):
        if token == "(":
            node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif token == ")":
            result = stack.pop()
        else:
            stack[-1].append(token)
    return result


def render(node, indent=0):
    if all(isinstance(item, str) for item in node):
        return "(" + " ".join(node) + ")"
    atoms = []
    children = []
    for item in node:
        if isinstance(item, str):
            atoms.append(item)
        else:
            children.append("  " * (indent + 1) + render(item, indent + 1))
    return (
        "(" + " ".join(atoms) + "\n" + "\n".join(children) + "\n" + "  " * indent + ")"
    )


def children(node, key):
    return [item for item in node if isinstance(item, list) and item[0] == key]


def strip(node, keys):
    node[:] = [
        item for item in node if not isinstance(item, list) or item[0] not in keys
    ]


def normalize(node, rotation):
    strip(node, {"uuid", "net", "pinfunction", "pintype"})
    for item in node:
        if not isinstance(item, list):
            continue
        if item[0] == "at" and len(item) >= 4:
            item[3] = format((float(item[3]) - rotation) % 360, ".10g")
        else:
            normalize(item, rotation)


def library_footprint(footprint):
    result = copy.deepcopy(footprint)
    transforms = children(result, "transform")
    if transforms:
        rotation = float(children(transforms[0], "rotate")[0][1])
        scale = children(transforms[0], "scale")[0][1:]
        if scale != ["1", "1"]:
            raise ValueError("Scaled footprints are not supported")
    else:
        at = children(result, "at")
        rotation = float(at[0][3]) if at and len(at[0]) > 3 else 0
    layer = children(result, "layer")[0]
    if layer[1] != '"F.Cu"':
        raise ValueError("Back-side footprints are not supported")
    strip(
        result, {"transform", "at", "path", "sheetname", "sheetfile", "units", "locked"}
    )
    # Instance fields remain on the board, not in a reusable land pattern.
    result[:] = [
        item
        for item in result
        if not isinstance(item, list)
        or item[0] != "property"
        or item[1] in {'"Reference"', '"Value"'}
    ]
    normalize(result, rotation)
    fields = children(result, "property")
    for field in fields:
        field[2] = '"REF**"' if field[1] == '"Reference"' else '""'
        strip(field, {"hide"})
        field.append(["hide", "yes"])
    if not any(
        text[2] == '"${REFERENCE}"'
        and children(text, "layer")[0][1] in {'"F.Fab"', '"B.Fab"'}
        for text in children(result, "fp_text")
    ):
        raise ValueError(f"{footprint[1]} has no Fab ${{REFERENCE}}")
    name = footprint[1].strip('"').split(":", 1)[-1]
    if footprint[1].startswith(f'"{NICKNAME}:'):
        name = re.sub(r"(?:_[0-9a-f]{12})+$", "", name)
    result[1] = '""'
    digest = hashlib.sha256(render(result).encode()).hexdigest()[:12]
    name = re.sub(r"[^A-Za-z0-9_.+-]", "_", name) + "_" + digest
    result[1] = f'"{name}"'
    for field in fields:
        if field[1] == '"Value"':
            field[2] = f'"{name}"'
    return name, result


def project_footprints(board_path):
    board_path = Path(board_path).resolve(strict=True)
    with KiCad(headless=True, file_path=str(board_path), timeout_ms=60000) as client:
        board = client.get_board()
        footprints = board.get_footprints()
        serialized = board.get_as_string()
        ids = {footprint.id.value for footprint in footprints}
    embedded = {}
    for start, end in expressions(serialized):
        if serialized.startswith("(footprint ", start):
            footprint = parse(serialized[start:end])
            embedded[children(footprint, "uuid")[0][1].strip('"')] = footprint
    if embedded.keys() != ids:
        raise ValueError("API serialization does not match the board footprints")

    library = board_path.parent / LIBRARY_PATH
    files = {}
    names = {}
    for uid, footprint in embedded.items():
        name, definition = library_footprint(footprint)
        # Keep the stock library format header; do not upgrade the .pretty library.
        definition[2:2] = [["version", "20260206"], ["generator", '"pcbnew"']]
        files[library / (name + ".kicad_mod")] = render(definition) + "\n"
        names[uid] = name
    library.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        path.write_text(content)
    with KiCad(headless=True, file_path=str(board_path), timeout_ms=60000) as client:
        board = client.get_board()
        for footprint in board.get_footprints():
            footprint.definition.id.library = NICKNAME
            footprint.definition.id.name = names[footprint.id.value]
            footprint.reference_field.visible = False
            footprint.value_field.visible = False
            board.update_items(footprint)
        board.save()
    return len(ids), len(files)


def main():
    parser = argparse.ArgumentParser(
        description=f"Export embedded footprints to {LIBRARY_PATH.as_posix()}."
    )
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    count, definitions = project_footprints(args.board)
    print(f"Linked {count} footprints to {definitions} project-local definitions")


if __name__ == "__main__":
    main()
