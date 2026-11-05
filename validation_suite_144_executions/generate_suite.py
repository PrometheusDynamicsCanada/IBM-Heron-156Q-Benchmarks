"""Generate public logical inputs and exact references; never connects to hardware.
Requires qiskit and numpy. Optional --dependency-dir adds a local package directory.
"""
import argparse
import json
import hashlib
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--dependency-dir')
parser.add_argument('--output', default=str(Path(__file__).resolve().parent / 'generated'))
args = parser.parse_args()
if args.dependency_dir:
    sys.path.insert(0, str(Path(args.dependency_dir).resolve()))
import numpy as np
import qiskit
from qiskit import QuantumCircuit, qasm2, transpile
from qiskit.circuit.library import QFTGate
from qiskit.quantum_info import Statevector

out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
families = ['dense', 'bipartite', 'star', 'ising', 'qaoa', 'qft_phase']
widths = [6, 9, 12]
manifest = {'schema_version': 1, 'generator_qiskit_version': qiskit.__version__,
            'purpose': '18-instance (6Q, 9Q, 12Q) multi-QPU hardware benchmark suite across 6 circuit families',
            'main_backend_slots': ['A'], 'broadcast_backend_slots': ['B', 'C'],
            'pipelines': ['sabre_o3', 'tket', 'prometheus_candidate'],
            'shots_per_execution': 1024, 'main_blocks': 2,
            'main_executions': 108, 'broadcast_executions': 36,
            'planned_shots_excluding_pilot_controls': 147456,
            'instances': []}

for fi, family in enumerate(families):
    for wi, n in enumerate(widths):
        seed = 260026 + 100 * fi + wi
        rng = np.random.default_rng(seed)
        qc = QuantumCircuit(n)
        specification = {'family': family, 'width': n, 'seed': seed}
        ids = np.arange(2**n)
        task_values = None
        success = None
        if family in ('dense', 'bipartite', 'star'):
            if family == 'dense': edges = [(a,b) for a in range(n) for b in range(a+1,n)]
            elif family == 'bipartite': edges = [(a,b) for a in range(n//2) for b in range(n//2,n)]
            else:
                hub = int(rng.integers(n)); edges = [(hub,b) for b in range(n) if b != hub]
            specification['edges'] = edges
            for layer in range(2):
                for q in range(n):
                    qc.ry(float(rng.uniform(.2,2.8)),q)
                    qc.rz(float(rng.uniform(-2.8,2.8)),q)
                for a,b in edges: qc.cx(a,b)
            for q in range(n): qc.rx(float(rng.uniform(.1,1.5)),q)
            metric = 'squared_hellinger_fidelity'
        elif family == 'ising':
            edges = [(q,q+1) for q in range(n-1)] + [(0,n-1)]
            specification.update(edges=edges, trotter_steps=3, zz_angle=.47, x_angle=.31)
            for q in range(n): qc.ry(float(rng.uniform(.15,1.4)),q)
            for _ in range(3):
                for a,b in edges: qc.rzz(.47,a,b)
                for q in range(n): qc.rx(.31,q)
            task_values = sum(1-2*((ids>>q)&1) for q in range(n))/n
            metric = 'absolute_magnetization_error'
        elif family == 'qaoa':
            graph = set(tuple(sorted((q,(q+1)%n))) for q in range(n))
            graph.update(tuple(sorted((q,q+n//2))) for q in range(n//2))
            edges = sorted(graph)
            specification.update(edges=edges, gammas=[.41,.67], betas=[.29,.53],
                                 parameters='Fixed shared parameters; no hardware tuning')
            qc.h(range(n))
            for gamma,beta in zip(specification['gammas'],specification['betas']):
                for a,b in edges: qc.rzz(-gamma,a,b)
                for q in range(n): qc.rx(2*beta,q)
            cuts = sum(((ids>>a)^(ids>>b))&1 for a,b in edges)
            optimum = int(cuts.max())
            task_values = cuts/optimum
            threshold = int(np.ceil(.9*optimum))
            success = cuts >= threshold
            specification.update(exact_maxcut=optimum, success_cut_threshold=threshold)
            metric = 'mean_cut_over_exact_optimum'
        else:
            target = int(rng.integers(1,2**n))
            # Separable Fourier state of |target>, with little-endian qubit indexing.
            for q in range(n):
                qc.h(q); qc.p(2*np.pi*target*(2**q)/(2**n),q)
            qc.barrier()
            qc.append(QFTGate(n).inverse(),range(n))
            specification.update(target_integer=target, target_bitstring=format(target,f'0{n}b'),
                                 boundary='Preserve state-preparation/transform boundary in all pipelines')
            success = ids == target
            metric = 'target_success_probability'
        p = Statevector.from_instruction(qc).probabilities()
        assert np.isclose(p.sum(),1)
        if family == 'qft_phase': assert p[specification['target_integer']] > 1-1e-10
        qc.measure_all()
        # Public portable decomposition. Identical logical input goes to all pipelines.
        portable = transpile(qc, basis_gates=['u3','cx'], optimization_level=0, seed_transpiler=seed)
        text = qasm2.dumps(portable)
        instance_id = f'{family}_{n}q_s{seed}'
        path = out/f'{instance_id}.qasm'
        path.write_text(text,encoding='utf-8')
        restored = qasm2.loads(text).remove_final_measurements(inplace=False)
        roundtrip = Statevector.from_instruction(restored).probabilities()
        assert np.allclose(roundtrip,p,atol=1e-10)
        arrays = {'ideal_probabilities': p}
        if task_values is not None: arrays['task_values'] = task_values
        if success is not None: arrays['success_mask'] = success.astype(float)
        np.savez_compressed(out/f'{instance_id}.npz',**arrays)
        specification.update(instance_id=instance_id, qasm_file=path.name,
                             qasm_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             reference_file=f'{instance_id}.npz', primary_metric=metric,
                             broadcast=(n==9), bit_order='q[n-1]...q[0]; logical measurement order')
        manifest['instances'].append(specification)

(out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'Generated and round-trip validated {len(manifest["instances"])} logical circuits in {out}')
print('Main: 108 executions / 110592 shots. Broadcast: 36 executions / 36864 shots.')
print('No IBM credentials read and no hardware jobs submitted.')
