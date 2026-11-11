from copy import deepcopy
from pathlib import Path
import sexpdata as sx
from functools import lru_cache

LIBROOT = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')


def tag(node):
    return str(node[0]) if isinstance(node, list) and node else ''


def child(node, key, default=None):
    return next((item for item in node if tag(item) == key), default)


def children(node, key):
    return [item for item in node if tag(item) == key]


@lru_cache(maxsize=None)
def library_symbols(library):
    tree = sx.loads((LIBROOT / 'symbols' / f'{library}.kicad_sym').read_text())
    return {item[1]: item for item in children(tree, 'symbol')}


@lru_cache(maxsize=None)
def flatten_symbol(library, name):
    if library == 'Custom':
        from custom_parts import custom_symbol
        return custom_symbol(name)
    symbols = library_symbols(library)

    def resolve(symbol_name):
        result = deepcopy(symbols[symbol_name])
        parent = child(result, 'extends')
        if parent:
            inherited = resolve(parent[1])
            own_properties = {item[1] for item in children(result, 'property')}
            result.remove(parent)
            result.extend(deepcopy(item) for item in inherited[2:]
                          if tag(item) == 'symbol' or
                          (tag(item) == 'property' and item[1] not in own_properties))
            for item in children(result, 'symbol'):
                item[1] = symbol_name + '_' + item[1].rsplit('_', 2)[1] + '_' + item[1].rsplit('_', 2)[2]
        return result

    return resolve(name)


def pins(symbol):
    result = []
    for unit in children(symbol, 'symbol'):
        result.extend(children(unit, 'pin'))
    return result


def pin_description(symbol):
    return [{'number': child(pin, 'number')[1], 'name': child(pin, 'name')[1],
             'type': str(pin[1]), 'at': child(pin, 'at')[1:]} for pin in pins(symbol)]


if __name__ == '__main__':
    import json
    choices = [('MCU_RaspberryPi', 'RP2350A'), ('Battery_Management', 'BQ24074RGT'),
               ('Regulator_Switching', 'TPS63031DSK'), ('RF_Module', 'ESP32-C3-WROOM-02'),
               ('Memory_RAM', 'APS6404L-3SQRx-SN'), ('Memory_Flash', 'W25Q32JVSS'),
               ('Power_Protection', 'USBLC6-2SC6'), ('LED', 'WS2812B-2020'),
               ('Connector', 'USB_C_Receptacle_USB2.0'), ('Connector', 'Micro_SD_Card_Det')]
    for library, name in choices:
        print(library, name)
        print(json.dumps(pin_description(flatten_symbol(library, name)), indent=2))
