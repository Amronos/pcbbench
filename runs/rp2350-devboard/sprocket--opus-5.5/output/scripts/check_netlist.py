"""Export the netlist and compare every pin's net with design.py."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D  # noqa: E402

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET = "/tmp/work/rp2350-devboard.net"
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", NET,
                f"{PROJ}/rp2350-devboard.kicad_sch"], check=True, capture_output=True)
text = open(NET).read()
actual = {}
for m in re.finditer(r'\(net\s+\(code "?\d+"?\)\s+\(name "([^"]*)"\)(.*?)\n\t\t\)', text, re.S):
    name = m.group(1)
    name = "NC" if name.startswith("unconnected-") else name.rsplit("/", 1)[-1]
    for ref, pin in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m.group(2)):
        actual[(ref, pin)] = name

errors = 0
for p in D.parts:
    for pin, net in p["nets"].items():
        got = actual.get((p["ref"], pin), "NC" if net == "NC" else "<missing>")
        if got != net:
            errors += 1
            print(f"{p['ref']}.{pin}: want {net}, got {got}")
refs = {p["ref"] for p in D.parts}
for (ref, pin), net in actual.items():
    if not ref.startswith("#") and ref not in refs:
        print("unexpected", ref, pin, net)
        errors += 1
nets = {}
for (ref, pin), net in actual.items():
    nets.setdefault(net, []).append(f"{ref}.{pin}")
singles = [n for n, v in nets.items() if len(v) == 1 and n != "NC"]
print(f"{len(actual)} pins, {len(nets)} nets, {errors} mismatches, single-pin nets: {singles}")
sys.exit(1 if errors or singles else 0)
