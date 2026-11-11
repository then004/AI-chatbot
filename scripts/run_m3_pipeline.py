import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.pipeline import run_pipeline

p = argparse.ArgumentParser()
p.add_argument('idea')
p.add_argument('--output-root')
p.add_argument('--price', type=float)
p.add_argument('--units', type=float)
p.add_argument('--variable-cost', type=float)
p.add_argument('--fixed-cost', type=float)
a = p.parse_args()
b = None
if all(x is not None for x in (a.price, a.units, a.variable_cost, a.fixed_cost)):
    b = {'price': a.price, 'units': a.units, 'variable_cost': a.variable_cost, 'fixed_cost': a.fixed_cost}
print(json.dumps(run_pipeline(a.idea, b, output_root=a.output_root), ensure_ascii=False))
