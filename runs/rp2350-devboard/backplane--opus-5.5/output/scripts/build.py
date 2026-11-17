"""Full pipeline: schematic -> PCB -> (optional) autoroute -> refill -> DRC.

  python3 build.py finish   rebuild the PCB from design.py + PLACE + routes.sexp, refill zones, DRC
  python3 build.py place    rebuild the unrouted PCB (placement only)
  python3 build.py route    regenerate schematic + PCB and re-run Freerouting from scratch
                            (the last few connections of the shipped board were then finished with
                            KiCad's router through the IPC SketchRoute command; see README)
"""
import os, subprocess, sys, shutil, time
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, '..', 'boards', 'rp2350-dev')
PCB = os.path.join(B, 'rp2350-dev.kicad_pcb')
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
J = [os.path.join(os.path.expanduser('~/tools'), d, 'bin', 'java') for d in os.listdir(os.path.expanduser('~/tools')) if d.startswith('jdk-25')][0]
FR = os.path.expanduser('~/tools/fr25.jar')
FR19 = os.path.expanduser('~/tools/fr19.jar')
ROUTES = os.path.join(HERE, 'routes.sexp')
WORK = '/tmp/route'

def run(cmd, **kw):
    print('+', ' '.join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, check=True, **kw)

def refill():
    run([K, 'pcb', 'drc', '--refill-zones', '--save-board', '-o', '/tmp/drc_fill.rpt', PCB], capture_output=True)

def prune_dangling():
    """Remove copied RPi stubs that DRC reports as dangling (their far end was outside the copy region)."""
    import json, math
    sys.path.insert(0, HERE)
    from sexp import parse, find, findall
    d = json.load(open(os.path.join(HERE, 'drc.json')))
    fixed = set(json.load(open(os.path.join(HERE, 'fixed_uuids.json'))))
    pf = os.path.join(HERE, 'pruned_uuids.json')
    pruned = set(json.load(open(pf))) if os.path.exists(pf) else set()
    t = parse(open(PCB).read())
    segs = [s for s in findall(t, 'segment') if find(s, 'uuid')[1] in fixed]
    n0 = len(pruned)
    for v in d['violations']:
        if v['type'] != 'track_dangling':
            continue
        import re
        for it in v['items']:
            px, py = it['pos']['x'], it['pos']['y']
            m = re.search(r'length ([0-9.]+) mm', it['description'])
            if not m:
                continue
            L = float(m.group(1))
            for s in segs:
                a = (float(find(s, 'start')[1]), float(find(s, 'start')[2]))
                b = (float(find(s, 'end')[1]), float(find(s, 'end')[2]))
                if abs(math.hypot(a[0] - b[0], a[1] - b[1]) - L) > 0.002:
                    continue
                if min(math.hypot(a[0] - px, a[1] - py), math.hypot(b[0] - px, b[1] - py),
                       math.hypot((a[0] + b[0]) / 2 - px, (a[1] + b[1]) / 2 - py)) < 0.03:
                    pruned.add(find(s, 'uuid')[1])
    json.dump(sorted(pruned), open(pf, 'w'))
    print('pruned dangling copied segments:', len(pruned) - n0)
    return len(pruned) > n0


def place():
    for it in range(4):
        run([sys.executable, os.path.join(HERE, 'gen_pcb.py')])
        refill()
        run([K, 'pcb', 'drc', '--format', 'json', '-o', os.path.join(HERE, 'drc.json'), PCB], capture_output=True)
        if not prune_dangling():
            break


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'
    os.makedirs(WORK, exist_ok=True)
    if step in ('all', 'route'):
        run([sys.executable, os.path.join(HERE, 'gen_sch.py')])
        place()
        run([sys.executable, os.path.join(HERE, 'dsn.py'), 'export', PCB, WORK + '/b.dsn'])
        passes = sys.argv[2] if len(sys.argv) > 2 else '60'
        # Freerouting 1.9.0 (Java 21) gave the best results; it needs a display, so run it under xvfb-run.
        jar = FR if os.environ.get('FR') == '25' else FR19
        t0 = time.time()
        if jar == FR:
            args = [J, '-jar', jar, '-de', WORK + '/b.dsn', '-do', WORK + '/b.ses', '-mp', passes,
                    '--gui.enabled=false', '--usage_and_diagnostic_data.disable_analytics=true']
        else:
            j21 = [os.path.join(os.path.expanduser('~/tools'), d, 'bin', 'java') for d in os.listdir(os.path.expanduser('~/tools')) if d.startswith('jdk-21')][0]
            args = ['xvfb-run', '-a', j21, '-jar', jar, '-de', WORK + '/b.dsn', '-do', WORK + '/b.ses', '-mp', passes]
        with open(WORK + '/fr.log', 'w') as lf:
            subprocess.run(args, stdout=lf, stderr=subprocess.STDOUT, cwd=WORK)
        print('freerouting took %.0fs' % (time.time() - t0))
        run([sys.executable, os.path.join(HERE, 'dsn.py'), 'import', PCB, WORK + '/b.ses', ROUTES])
    if step in ('all', 'route', 'finish'):
        for it in range(3):
            run([sys.executable, os.path.join(HERE, 'gen_pcb.py'), ROUTES])
            refill()
            run([K, 'pcb', 'drc', '--schematic-parity', '--format', 'json', '-o', os.path.join(HERE, 'drc.json'), PCB], capture_output=True)
            if not prune_dangling():
                break
        run([sys.executable, os.path.join(HERE, 'drc_summary.py'), os.path.join(HERE, 'drc.json')])
    if step == 'place':
        place()

if __name__ == '__main__':
    main()
