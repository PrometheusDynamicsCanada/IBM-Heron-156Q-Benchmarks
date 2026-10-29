"""Offline checks of known-answer scoring and invalid-input rejection."""
import json
from pathlib import Path
from score_counts import score

root=Path(__file__).resolve().parent/'generated'
m=json.loads((root/'manifest.json').read_text())
spec=next(s for s in m['instances'] if s['family']=='qft_phase')
n=spec['width']; correct=spec['target_bitstring']
wrong=format((spec['target_integer']+1)%(2**n),f'0{n}b')
base={'instance_id':spec['instance_id'],'backend':'synthetic','block':1,'pipeline':'synthetic'}
a=score(base|{'counts':{correct:1024}},spec,root)
b=score(base|{'counts':{wrong:1024}},spec,root)
assert a['success_probability']==1 and a['tvd']<1e-10
assert b['success_probability']==0 and b['tvd']>1-1e-10
c=score(base|{'counts':{correct:512,wrong:512}},spec,root)
assert c['success_probability']==.5
assert c['success_wilson_95'][0]<.5<c['success_wilson_95'][1]
ising=next(s for s in m['instances'] if s['family']=='ising')
iz=score(base|{'instance_id':ising['instance_id'],'counts':{'0'*ising['width']:1024}},ising,root)
assert iz['task_mean']==1
qaoa=next(s for s in m['instances'] if s['family']=='qaoa')
qz=score(base|{'instance_id':qaoa['instance_id'],'counts':{'0'*qaoa['width']:1024}},qaoa,root)
assert qz['mean_cut_over_exact_optimum']==0 and qz['success_probability']==0
for invalid in [base|{'counts':{correct:-1}},base|{'counts':{'0':1024}},base|{'counts':{correct:1024},'shots':1}]:
    try: score(invalid,spec,root)
    except ValueError: pass
    else: raise AssertionError('Invalid input was accepted')
print('PASS: QFT correct/wrong/mixture scores, Ising magnetization, MaxCut objective, intervals, invalid-count rejection.')
