import argparse
from pathlib import Path

from kipy import KiCad
from kipy.proto.common.types.base_types_pb2 import DocumentType

from design import parts


def validate_symbols(symbols):
    expected = {part.ref: part for part in parts}
    seen = set()
    for symbol in symbols:
        if symbol.reference.startswith('#'):
            continue
        if symbol.reference not in expected:
            raise ValueError(f'{symbol.reference}: unexpected schematic part')
        if symbol.reference in seen:
            raise ValueError(f'{symbol.reference}: duplicate schematic part')
        seen.add(symbol.reference)
        part = expected[symbol.reference]
        if symbol.value != part.value or symbol.footprint_field.text.value != part.footprint:
            raise ValueError(f'{part.ref}: schematic differs from design.py')
        metadata = {field.name: field.text.value for field in symbol.user_fields}
        if metadata.get('MPN') != part.mpn or metadata.get('Manufacturer') != part.manufacturer:
            raise ValueError(f'{part.ref}: schematic part metadata differs from design.py')
    missing = expected.keys() - seen
    if missing:
        raise ValueError(f'Missing schematic parts: {", ".join(sorted(missing))}')


def main():
    argparse.ArgumentParser(description='Sync schematic nets without replacing routed footprints.').parse_args()
    root = Path(__file__).resolve().parent.parent
    with KiCad(headless=True, timeout_ms=120000) as k:
        k.open_document(str(root / 'sprocket2350.kicad_sch'), DocumentType.DOCTYPE_SCHEMATIC)
        schematic = k.get_schematic()
        validate_symbols(schematic.get_symbols())
        netlist = str(root / 'sprocket2350.net')
        schematic.export_netlist(netlist)
        k.open_document(str(root / 'sprocket2350.kicad_pcb'), DocumentType.DOCTYPE_PCB)
        board = k.get_board()
        result = board.import_netlist(netlist, update_footprints=False,
                                      delete_extra_footprints=False, transfer_groups=False)
        print(result.report)
        if result.error_count:
            raise ValueError('Netlist import failed; board not saved')
        board.save()


if __name__ == '__main__':
    main()
