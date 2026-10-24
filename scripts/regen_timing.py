"""Rewrite tracks/<folder>/timing_gates for one track (after a finish / gate change) without a full build.
Keeps the gate model already set on the startinggate lines (added by dress_sx.py). Run: python3 scripts/regen_timing.py SX1"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import layouts_sx as LS
from timing import gates
from names import FOLDERS

key = sys.argv[1] if len(sys.argv) > 1 else 'SX1'
path = {'SX1': LS.sx1, 'SX2': LS.sx2, 'SX3': LS.sx3}[key]()
txt, cps, first, normal, sM, sF = gates(path, LS.STARTS[key])
f = f'{ROOT}/tracks/{FOLDERS[key]}/timing_gates'
old = open(f).read().split('\n'); suffix = next((' ' + ' '.join(l.split()[4:]) for l in old if l.startswith('[') and '@' in l), '')
out = [(l + suffix) if (l.startswith('[') and l.count('[') == 1 and suffix and '@' not in l and len(l.split()) == 4) else l for l in txt.split('\n')]
open(f, 'w', newline='\n').write('\n'.join(out))
print(key, 'finish s =', round(sF, 1), 'merge s =', round(sM, 1), 'lap', round(path.s, 1), '| checkpoints', len(cps), '| first lap', first, '| normal', normal)
