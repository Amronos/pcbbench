import argparse
from pathlib import Path

from kipy import KiCad
from kipy.proto.board import board_commands_pb2 as board_commands


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("netlist", type=Path)
    args = parser.parse_args()

    with KiCad(
        headless=True, file_path=str(args.board.resolve()), timeout_ms=60000
    ) as kicad:
        board = kicad.get_board()
        result = board.import_netlist(
            str(args.netlist.resolve()),
            match_mode=board_commands.NMM_REFERENCE,
            update_footprints=False,
        )
        if result.error_count:
            raise RuntimeError(result)
        board.save()
        print(result)


if __name__ == "__main__":
    main()
