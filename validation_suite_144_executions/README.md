# Prometheus Dynamics - 144-Execution Multi-QPU Hardware Validation Suite (IBM Heron 156Q)

Empirical 3-way hardware benchmark suite comparing **Prometheus**, **Qiskit SABRE O3**, and **Quantinuum TKET** across three physical 156-qubit IBM Heron r2 quantum processors (`ibm_marrakesh`, `ibm_fez`, and `ibm_kingston`).

All 18 logical OpenQASM 2.0 circuits (`6Q`, `9Q`, and `12Q` across 6 algorithm families), exact noiseless reference distributions, pre-execution SHA-256 circuit and target-backend commitments, raw canonical hardware measurement counts (`144` physical circuit runs / `147,456` shots), and standalone offline scoring tools are included in this directory.

---

## 1. Hardware Execution Summary & IBM Quantum Job Ledger

All compiled circuit SHA-256 hashes and 9-qubit multi-QPU target-dispatch decisions (`P-Dispatch`) were frozen prior to hardware execution in [`commitments_hardware.json`](./commitments_hardware.json).

| Batch Slot | Target Processor | IBM Quantum Job ID | Circuits Executed | Shots / Circuit | Total Shots | Official QPU Usage |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Slot A (Block 1)** | **`ibm_marrakesh`** *(156Q)* | `dbghgkdrd2mc73cuo0jg` | `54` (`18 x 3`) | `1,024` | `55,296` | `17.0s` |
| **Slot A (Block 2)** | **`ibm_marrakesh`** *(156Q)* | `dbghgroiudkc73e4gvig` | `54` (`18 x 3`) | `1,024` | `55,296` | `17.0s` |
| **Slot B (9Q Broadcast)** | **`ibm_fez`** *(156Q)* | `dbghh7ljm0ks73egl000` | `18` (`6 x 3`) | `1,024` | `18,432` | `7.0s` |
| **Slot C (9Q Broadcast)** | **`ibm_kingston`** *(156Q)* | `dbgjtecdgr2s73crlre0` | `18` (`6 x 3`) | `1,024` | `18,432` | `7.0s` |
| **Total** | **3 Heron r2 QPUs** | **4 Packed `SamplerV2` Jobs** | **`144` Executions** | **`1,024`** | **`147,456` Shots** | **`48.0s`** |

### Key Empirical Outcomes
- **Scoreboard 1 (3-Way Hardware Performance on Primary Backend A, `2 x 1,024` Shots):** Prometheus outperformed `SABRE O3` on **`16 / 18` (`88.9%`)** workload instances and outperformed `Quantinuum TKET` on **`15 / 18` (`83.3%`)** workload instances on each family's primary task metric, winning **`6 / 6` (`100%`) of all `12Q` instances** and **`3 / 3` (`100%`) of `QAOA MaxCut` instances** (`6Q`, `9Q`, `12Q`), including a **`4.21x` (`0.0762` vs. `0.0181` SABRE / `0.0005` TKET)** target-state recovery advantage on `qft_phase_12q_s260528`.
- **Scoreboard 2 (Multi-QPU Broadcast & Pre-Committed Dispatch across `ibm_marrakesh`, `ibm_fez`, `ibm_kingston`):** Pre-committed `P-Dispatch` selected `C:ibm_kingston` before execution and outperformed fixed single-backend `SABRE O3` on **`6 / 6` (`100%`)** of the `9Q` broadcast cohort across `ibm_marrakesh` (`Fixed A`) and `ibm_fez` (`Fixed B`), and on `5 / 6` (`83.3%`) vs. `SABRE O3` on `ibm_kingston` (`Fixed C`).

---

## 2. Benchmark Family Specifications (`6Q`, `9Q`, `12Q`)

| Family | Construction | Primary Task Metric | Direction |
| :--- | :--- | :--- | :--- |
| `dense` | Two seeded rotation/CX layers over all qubit pairs ($K_n$) | `squared_hellinger_fidelity` | Higher is better (↑) |
| `bipartite` | Two seeded layers over complete bipartite graph $K_{n/2, n-n/2}$ | `squared_hellinger_fidelity` | Higher is better (↑) |
| `star` | Seeded central-hub entanglement and local rotations | `squared_hellinger_fidelity` | Higher is better (↑) |
| `ising` | Three fixed $ZZ / X$ Trotter steps on a periodic ring | `absolute_magnetization_error` | Lower is better (↓) |
| `qaoa` | Two-layer QAOA MaxCut on ring-plus-chord graphs | `mean_cut_over_exact_optimum` | Higher is better (↑) |
| `qft_phase` | Phase-encoded Fourier product state followed by inverse QFT | `target_success_probability` | Higher is better (↑) |

---

## Scoreboard 1: 3-Way Hardware Performance (Primary Backend A `ibm_marrakesh`, 2 Blocks x 1,024 Shots)

*(Bolding indicates the best physical score in each row; `(↑)` = higher is better, `(↓)` = lower is better.)*

| Instance | Metric | SABRE O3 (2Q / d / Score) | TKET (2Q / d / Score) | Prometheus (2Q / d / Score) |
| :--- | :--- | :---: | :---: | :---: |
| `dense_6q_s260026` | `squared_hellinger_fidelity` (↑) | 79 / 159 / 0.8753 | 94 / 168 / 0.6971 | **71 / 141 / 0.8927** |
| `dense_9q_s260027` | `squared_hellinger_fidelity` (↑) | 210 / 300 / 0.6651 | 252 / 323 / 0.5352 | **155 / 203 / 0.7101** |
| `dense_12q_s260028` | `squared_hellinger_fidelity` (↑) | 339 / 374 / 0.2111 | 619 / 662 / 0.0844 | **307 / 325 / 0.2377** |
| `bipartite_6q_s260126` | `squared_hellinger_fidelity` (↑) | 48 / 109 / 0.8225 | 54 / 106 / 0.8095 | **46 / 89 / 0.8955** |
| `bipartite_9q_s260127` | `squared_hellinger_fidelity` (↑) | 141 / 222 / 0.7081 | 227 / 327 / 0.6759 | **116 / 156 / 0.7181** |
| `bipartite_12q_s260128` | `squared_hellinger_fidelity` (↑) | 142 / 128 / 0.2683 | 355 / 348 / 0.1913 | **142 / 128 / 0.3112** |
| `star_6q_s260226` | `squared_hellinger_fidelity` (↑) | 21 / 65 / 0.8754 | **22 / 63 / 0.9240** | 21 / 64 / 0.9038 |
| `star_9q_s260227` | `squared_hellinger_fidelity` (↑) | 48 / 152 / 0.7564 | **52 / 139 / 0.7846** | 48 / 111 / 0.6911 |
| `star_12q_s260228` | `squared_hellinger_fidelity` (↑) | 86 / 180 / 0.2692 | 82 / 182 / 0.3129 | **64 / 164 / 0.4031** |
| `ising_6q_s260326` | `absolute_magnetization_error` (↓) | **70 / 225 / 0.1325** | 90 / 291 / 0.2550 | 68 / 215 / 0.1405 |
| `ising_9q_s260327` | `absolute_magnetization_error` (↓) | 101 / 308 / 0.1829 | 90 / 343 / 0.2633 | **115 / 317 / 0.1338** |
| `ising_12q_s260328` | `absolute_magnetization_error` (↓) | 72 / 289 / 0.1989 | 72 / 362 / 0.3873 | **72 / 288 / 0.1208** |
| `qaoa_6q_s260426` | `mean_cut_over_exact_optimum` (↑) | 66 / 170 / 0.6304 | 72 / 175 / 0.5666 | **64 / 199 / 0.6590** |
| `qaoa_9q_s260427` | `mean_cut_over_exact_optimum` (↑) | 105 / 209 / 0.6271 | 139 / 218 / 0.6346 | **106 / 166 / 0.6446** |
| `qaoa_12q_s260428` | `mean_cut_over_exact_optimum` (↑) | 138 / 196 / 0.6624 | 198 / 270 / 0.6363 | **138 / 192 / 0.6765** |
| `qft_phase_6q_s260526` | `target_success_probability` (↑) | 58 / 136 / 0.3906 | 57 / 187 / 0.0605 | **46 / 115 / 0.4531** |
| `qft_phase_9q_s260527` | `target_success_probability` (↑) | 175 / 323 / 0.1392 | **171 / 250 / 0.2144** | 145 / 262 / 0.1450 |
| `qft_phase_12q_s260528` | `target_success_probability` (↑) | 312 / 439 / 0.0181 | 405 / 639 / 0.0005 | **219 / 351 / 0.0762** |

## Scoreboard 2: Multi-QPU Broadcast & Pre-Committed Dispatch (9Q Cohort, Block 1 Equal-Shot Comparison)

*(Fixed A = `ibm_marrakesh`, Fixed B = `ibm_fez`, Fixed C = `ibm_kingston`. Pre-committed `P-Dispatch` beat Fixed A `SABRE O3` on `6 / 6`, Fixed B `SABRE O3` on `6 / 6`, and Fixed C `SABRE O3` on `5 / 6` instances.)*

| Instance | Metric | Fixed A (SABRE / Prometheus) | Fixed B (SABRE / Prometheus) | Fixed C (SABRE / Prometheus) | Pre-Committed P-Dispatch |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `dense_9q_s260027` | `squared_hellinger_fidelity` (↑) | 0.6721 / 0.6980 | 0.6586 / 0.7653 | 0.7506 / **0.7937** | **0.7937** (`C:ibm_kingston`) |
| `bipartite_9q_s260127` | `squared_hellinger_fidelity` (↑) | 0.6904 / 0.7147 | 0.7580 / 0.7657 | **0.8034** / 0.7918 | 0.7918 (`C:ibm_kingston`) |
| `star_9q_s260227` | `squared_hellinger_fidelity` (↑) | 0.7453 / 0.6769 | 0.8130 / 0.8201 | 0.8016 / **0.8276** | **0.8276** (`C:ibm_kingston`) |
| `ising_9q_s260327` | `absolute_magnetization_error` (↓) | 0.1874 / 0.1124 | 0.2512 / 0.1673 | 0.1553 / **0.0920** | **0.0920** (`C:ibm_kingston`) |
| `qaoa_9q_s260427` | `mean_cut_over_exact_optimum` (↑) | 0.6234 / 0.6388 | 0.6608 / **0.6742** | 0.6664 / 0.6667 | 0.6667 (`C:ibm_kingston`) |
| `qft_phase_9q_s260527` | `target_success_probability` (↑) | 0.1055 / 0.1231 | 0.2119 / 0.2871 | 0.3174 / **0.3486** | **0.3486** (`C:ibm_kingston`) |

---

## 3. Standalone Offline Verification

Recompute all 144 execution scores from the raw hardware bitstring counts in [`results_hardware.json`](./results_hardware.json) against the exact reference distributions in [`generated/`](./generated/):

```bash
python check_scoring.py
python score_counts.py results_hardware.json --manifest generated/manifest.json --output scored_results_hardware.json
```

### Files in This Directory
- [`generated/`](./generated/) - 18 portable OpenQASM 2.0 logical circuits (`*.qasm`), exact reference distributions (`*.npz`), and [`manifest.json`](./generated/manifest.json).
- [`commitments_hardware.json`](./commitments_hardware.json) - Pre-execution SHA-256 circuit and backend-dispatch commitments.
- [`results_hardware.json`](./results_hardware.json) - Raw canonical logical measurement counts and IBM Quantum Job IDs across all 144 hardware executions (`147,456` shots).
- [`scored_results_hardware.json`](./scored_results_hardware.json) - Per-execution metrics computed by `score_counts.py`.
- [`scoreboard_summary_hardware.json`](./scoreboard_summary_hardware.json) & [`scoreboard_report_hardware.md`](./scoreboard_report_hardware.md) - Machine-readable and Markdown scoreboards for Scoreboards 1 and 2.
- [`generate_suite.py`](./generate_suite.py), [`score_counts.py`](./score_counts.py), [`check_scoring.py`](./check_scoring.py) - Deterministic circuit generator, offline count scorer, and unit test suite.
