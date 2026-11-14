import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET


def ref_key(part):
    prefix, number = re.fullmatch(r"([A-Za-z]+)(\d+)", part["ref"]).groups()
    return prefix, int(number)


def write_bom(records, output):
    groups = {}
    for part in sorted(records, key=ref_key):
        key = part["mfr"], part["mpn"], part["fp"]
        groups.setdefault(key, []).append(part)

    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        ["refs", "qty", "value", "MPN", "manufacturer", "footprint", "datasheet"]
    )
    for (manufacturer, mpn, footprint), group in groups.items():
        writer.writerow(
            [
                " ".join(part["ref"] for part in group),
                len(group),
                "; ".join(dict.fromkeys(part["value"] for part in group)),
                mpn,
                manufacturer,
                footprint,
                "; ".join(dict.fromkeys(part["ds"] for part in group)),
            ]
        )


def read_netlist(path):
    for component in ET.parse(path).findall("components/comp"):
        fields = {
            field.attrib["name"]: field.text or ""
            for field in component.findall("fields/field")
        }
        yield {
            "ref": component.attrib["ref"],
            "value": component.findtext("value"),
            "mpn": fields["MPN"],
            "mfr": fields["Manufacturer"],
            "fp": component.findtext("footprint"),
            "ds": component.findtext("datasheet"),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist", help="KiCad XML export from the final schematic")
    args = parser.parse_args()
    if args.netlist:
        records = read_netlist(args.netlist)
    else:
        from circuits import define
        from design import parts

        define()
        records = parts
    write_bom(records, sys.stdout)


if __name__ == "__main__":
    main()
