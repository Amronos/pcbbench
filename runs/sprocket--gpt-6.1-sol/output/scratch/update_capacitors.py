import sys
from pathlib import Path
from kipy import KiCad
from kipy.proto.common.types.base_types_pb2 import DocumentType

root = Path('/home/ubuntu/pcbbench-run')
sys.path.insert(0, str(root / 'tools'))
from design import parts

expected = {part.ref: part for part in parts}
with KiCad(headless=True, timeout_ms=120000) as k:
    k.open_document(str(root / 'sprocket2350.kicad_sch'), DocumentType.DOCTYPE_SCHEMATIC)
    schematic = k.get_schematic()
    for symbol in schematic.get_symbols():
        if symbol.reference not in {'C6', 'C20'}:
            continue
        part = expected[symbol.reference]
        symbol.value = part.value
        symbol.footprint_field.text.value = part.footprint
        symbol.datasheet_field.text.value = part.datasheet
        for field in symbol.user_fields:
            if field.name == 'MPN':
                field.text.value = part.mpn
            elif field.name == 'Manufacturer':
                field.text.value = part.manufacturer
        symbol.proto.ClearField('definition')
        schematic.update_items(symbol)
    schematic.save()
