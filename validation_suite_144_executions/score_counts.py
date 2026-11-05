"""Score canonical logical bitstring counts against generated public references.
Pure offline analysis. Does not infer layouts, mitigation, confidence or causality.
Usage: python score_counts.py results.json --manifest generated/manifest.json
"""
import argparse
import json
from pathlib import Path
import numpy as np

def score(record, instance, reference_dir):
    n=instance['width']
    counts=record['counts']
    if not counts: raise ValueError('Empty counts')
    q=np.zeros(2**n)
    for key,value in counts.items():
        if len(key)!=n or any(c not in '01' for c in key):
            raise ValueError(f'Expected {n}-bit canonical logical bitstrings, got {key!r}')
        if not isinstance(value,int) or isinstance(value,bool) or value<0:
            raise ValueError('Counts must be nonnegative integers')
        q[int(key,2)] += value
    shots=int(q.sum())
    if shots<=0: raise ValueError('No shots')
    if record.get('shots',shots)!=shots: raise ValueError('Declared shots disagree with counts')
    q/=shots
    with np.load(reference_dir/instance['reference_file'],allow_pickle=False) as ref:
        p=ref['ideal_probabilities']
        coefficient=float(np.sqrt(p*q).sum())
        result={k:record[k] for k in ['instance_id','backend','block','pipeline']}
        result.update(shots=shots, squared_hellinger_fidelity=coefficient**2,
                      bhattacharyya_coefficient=coefficient,
                      tvd=float(abs(p-q).sum()/2),
                      observed_entropy_bits=float(-np.sum(q[q>0]*np.log2(q[q>0]))),
                      ideal_entropy_bits=float(-np.sum(p[p>0]*np.log2(p[p>0]))))
        if 'task_values' in ref:
            values=ref['task_values']; observed=float(q@values); ideal=float(p@values)
            result.update(task_mean=observed, ideal_task_mean=ideal,
                          task_mean_absolute_error=abs(observed-ideal))
            # Shot uncertainty only; not calibration/instance variation.
            result['task_mean_shot_standard_error']=float(np.sqrt(max(0,float(q@(values**2))-observed**2)/shots))
            if instance['family']=='qaoa': result['mean_cut_over_exact_optimum']=observed
            if instance['family']=='ising': result['absolute_magnetization_error']=abs(observed-ideal)
        if 'success_mask' in ref:
            prob=float(q@ref['success_mask'])
            z=1.959963984540054; denom=1+z*z/shots
            center=(prob+z*z/(2*shots))/denom
            half=z*np.sqrt(prob*(1-prob)/shots+z*z/(4*shots*shots))/denom
            result.update(success_probability=prob, success_wilson_95=[max(0,float(center-half)),min(1,float(center+half))])
            if instance['family']=='qft_phase': result['target_success_probability']=prob
        for key in ['job_id','quantum_seconds','quantum_seconds_scope','compile_seconds','selection_seconds',
                    'circuit_sha256','calibration_timestamp','logical_mapping_verified']:
            if key in record: result[key]=record[key]
        return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results')
    parser.add_argument('--manifest',default=str(Path(__file__).resolve().parent/'generated/manifest.json'))
    parser.add_argument('--output',default='scored_results.json')
    args=parser.parse_args()
    path=Path(args.manifest)
    manifest=json.loads(path.read_text(encoding='utf-8'))
    specs={r['instance_id']:r for r in manifest['instances']}
    records=json.loads(Path(args.results).read_text(encoding='utf-8'))
    seen=set(); output=[]
    for r in records:
        key=tuple(r[k] for k in ['instance_id','backend','block','pipeline'])
        if key in seen: raise ValueError(f'Duplicate result key: {key}')
        seen.add(key)
        output.append(score(r,specs[r['instance_id']],path.parent))
    Path(args.output).write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(f'Scored {len(output)} executions. Intervals quantify shot uncertainty only.')

if __name__=='__main__': main()
