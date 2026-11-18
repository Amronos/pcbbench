import argparse
from pathlib import Path

from circuits import define
from design import configure_libraries, parts
from kipy import KiCad
from kipy.schematic_types import NoConnectMarker, SchematicField


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("schematic", type=Path)
    parser.add_argument("board", type=Path, nargs="?")
    args = parser.parse_args()

    define()
    configure_libraries()
    records = {record["ref"]: record for record in parts}
    if args.board:
        with KiCad(
            headless=True, file_path=str(args.board.resolve()), timeout_ms=60000
        ) as kicad:
            for footprint in kicad.get_board().get_footprints():
                record = records[footprint.reference_field.text.value]
                record["fp"] = str(footprint.definition.id)

    with KiCad(
        headless=True, file_path=str(args.schematic.resolve()), timeout_ms=60000
    ) as kicad:
        sheet = kicad.get_schematic()
        lines, labels = sheet.get_lines(), sheet.get_labels()
        for symbol in sheet.get_symbols():
            record = records.get(symbol.reference)
            if record is None:
                continue
            symbol.value = record["value"]
            symbol.footprint_field.text.value = record["fp"]
            symbol.datasheet_field.text.value = record["ds"]
            fields = {field.name: field for field in symbol.user_fields}
            for name, value in [
                ("Manufacturer", record["mfr"]),
                ("MPN", record["mpn"]),
            ]:
                field = fields.get(name)
                if field is None:
                    field = SchematicField()
                    field.name = name
                    fields[name] = field
                field.text.value = value
                field.visible = False
            symbol.user_fields = list(fields.values())
            for pin in symbol.definition.pins:
                point = symbol.position + pin.position
                wire = next(
                    (
                        wire
                        for wire in lines
                        if wire.start == point or wire.end == point
                    ),
                    None,
                )
                if wire is None:
                    continue
                end = wire.end if wire.start == point else wire.start
                label = next((label for label in labels if label.position == end), None)
                if label is None:
                    raise ValueError(
                        f"{symbol.reference} pin {pin.number}: wire has no label"
                    )
                net = record["nets"].get(pin.number)
                if net:
                    label.text.value = net
                    sheet.update_items(label)
                else:
                    sheet.remove_items([wire, label])
                    marker = NoConnectMarker()
                    marker.position = point
                    sheet.create_items(marker)
            symbol.proto.ClearField("definition")
            sheet.update_items(symbol)
        sheet.save()


if __name__ == "__main__":
    main()
