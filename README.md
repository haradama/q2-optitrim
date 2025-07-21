# q2‑optitrim

A [QIIME 2](https://qiime2.org) community plugin for **automatic optimisation of DADA2 truncation parameters** using [Optuna](https://optuna.org) and a lightweight read subsampling strategy.

* **Single‑ and paired‑end** support  
* Hyperparameter search on a **fraction of your data**
* Outputs both a **recommended parameter table** and a **JSON summary** of the Optuna study  
* Seamless integration with QIIME 2 command‑line workflows

> **Status**: Experimental. Early adopters and feedback welcome!  

---

## Installation

The instructions below install the **latest development version** of *q2‑optitrim*.  
For production analyses you should use tagged release versions once they become available.

### Prerequisites

1. Install [Miniconda](https://conda.io/miniconda.html) if you haven’t already.  
2. Update conda:

```bash
conda update conda
```

### Clone the repository

```bash
git clone https://github.com/haradama/q2-optitrim.git
cd q2-optitrim
```

### Create and activate a fresh conda environment

```bash
conda env create -n q2-optitrim-dev \
  --file ./environment-files/q2-optitrim-qiime2-amplicon-dev.yml

conda activate q2-optitrim-dev
```

</details>

### 3. Install the plugin

```bash
make install
```

> If you need the *stable* QIIME 2 distribution, swap the `-dev.yml` for
> `q2-optitrim-qiime2-amplicon-release.yml`.

### 4. Refresh the QIIME 2 plugin cache

```bash
qiime dev refresh-cache
```

You should now see **`optitrim`** listed when you run:

```bash
qiime info
```

---

## Quick start

### Optimising truncation lengths

```bash
qiime optitrim optimize-truncation \
  --i-demux demux.qza \
  --p-amplicon-length 250 \
  --p-fwd-primer-length 20 \
  --p-rev-primer-length 20 \
  --p-fraction 0.20 \
  --p-trials 30 \
  --o-params recommended-params.qza \
  --o-study optitrim-study.qza
```

* `recommended-params.qza` – one‑row **Metadata** containing the optimal `trunc_len_*`, `trim_left_*`, etc.
* `optitrim-study.qza` – a **JSON** file with the Optuna study summary (best score, trial history).

#### Inspect the recommended parameters

```bash
qiime metadata tabulate \
  --m-input-file recommended-params.qza \
  --o-visualization recommended-params.qzv
qiime tools view recommended-params.qzv
```

### Running DADA2 with the optimised values

```bash
# Example for paired-end data
qiime dada2 denoise-paired \
  --i-demultiplexed-seqs demux.qza \
  --p-trunc-len-f 230 \
  --p-trunc-len-r 200 \
  --p-trim-left-f 20 \
  --p-trim-left-r 20 \
  --p-min-overlap 20 \
  --o-table table.qza \
  --o-representative-sequences rep-seqs.qza \
  --o-denoising-stats stats.qza
```

Simply substitute the numbers with those found in `recommended-params.qza`.

## Testing

After installation, run:

```bash
make test
```

All unit tests should pass with no failures (warnings are usually okay).

## Contributing

Pull requests, bug reports and feature suggestions are warmly welcomed!
Please open an issue first if you plan major work so we can discuss design.

---

## Citation

If you use **q2‑optitrim** in a publication, please cite:

```
Harada M. (2025) q2-optitrim: Optuna‑driven optimisation of DADA2 parameters. GitHub repository. https://github.com/haradama/q2-optitrim
```

For QIIME 2 itself, see the [QIIME 2 citation guidelines](https://qiime2.org).

## License

This work is distributed under the terms of the *Modified BSD License*.
See the [LICENSE](LICENSE) file for full text.

## About

*q2‑optitrim* was created with the [QIIME 2 plugin template](https://develop.qiime2.org) and is **not** part of the core QIIME 2 distribution. Support is best‑effort via the [QIIME 2 Forum](https://forum.qiime2.org).
Author: Masafumi Harada – Contributions welcome!
