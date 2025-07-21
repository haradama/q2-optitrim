from __future__ import annotations

import gzip
import json
import os
import random
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import optuna
import pandas as pd
import qiime2
from qiime2 import Metadata
from qiime2.plugins import demux, dada2
from q2_types.per_sample_sequences import (
    SingleLanePerSamplePairedEndFastqDirFmt,
    SingleLanePerSampleSingleEndFastqDirFmt,
)
from .formats import OptiTrimStudyDirFmt


# ───────── helpers ─────────
def _is_paired(art: qiime2.Artifact) -> bool:
    return "PairedEndSequencesWithQuality" in str(art.type)


def _subsample_once(
    art: qiime2.Artifact, *, fraction: float, paired: bool
) -> qiime2.Artifact:
    fn = demux.methods.subsample_paired if paired else demux.methods.subsample_single
    try:
        return fn(sequences=art, fraction=fraction, drop_empty=True).subsampled_sequences
    except TypeError:  # older q2-demux
        return fn(sequences=art, fraction=fraction).subsampled_sequences


def _first_len(fq: Path) -> int:
    with gzip.open(fq, "rt") as fh:
        next(fh)
        return len(next(fh).strip())


def _guess_lengths(art: qiime2.Artifact, paired: bool) -> Tuple[int, int]:
    if paired:
        fmt = art.view(SingleLanePerSamplePairedEndFastqDirFmt)
        m = fmt.manifest.view(pd.DataFrame)
        return (_first_len(Path(m.iloc[0]["forward"])),
                _first_len(Path(m.iloc[0]["reverse"])))
    fmt = art.view(SingleLanePerSampleSingleEndFastqDirFmt)
    m = fmt.manifest.view(pd.DataFrame)
    return _first_len(Path(m.iloc[0]["forward"])), 0


def _run_dada2(
    demux_art: qiime2.Artifact,
    trunc_f: int,
    trunc_r: int,
    trim_f: int,
    trim_r: int,
    min_overlap: int,
    threads: int,
    paired: bool,
):
    """Execute DADA2 in a temp dir so that intermediates are auto-deleted."""
    with tempfile.TemporaryDirectory() as tmp:
        old_tmp = os.environ.get("TMPDIR")
        os.environ["TMPDIR"] = tmp
        try:
            if paired:
                return dada2.methods.denoise_paired(
                    demultiplexed_seqs=demux_art,
                    trunc_len_f=trunc_f,
                    trunc_len_r=trunc_r,
                    trim_left_f=trim_f,
                    trim_left_r=trim_r,
                    min_overlap=min_overlap,
                    n_threads=threads,
                )
            return dada2.methods.denoise_single(
                demultiplexed_seqs=demux_art,
                trunc_len=trunc_f,
                trim_left=trim_f,
                n_threads=threads,
            )
        finally:
            if old_tmp is not None:
                os.environ["TMPDIR"] = old_tmp
            else:
                os.environ.pop("TMPDIR", None)


def _make_objective(
    ss_art: qiime2.Artifact,
    amp_len: int,
    primer_f: int,
    primer_r: int,
    min_overlap: int,
    min_trunc: int,
    max_trunc: int,
    step: int,
    threads: int,
):
    paired = _is_paired(ss_art)
    read_fwd, read_rev = _guess_lengths(ss_art, paired)

    def obj(trial: optuna.trial.Trial) -> float:
        trunc_f = trial.suggest_int(
            "trunc_f", min_trunc, min(max_trunc, read_fwd), step=step
        )

        if paired:
            min_r_need = amp_len + min_overlap - trunc_f
            min_r_allow = max(min_trunc, min_r_need, 0)
            max_r_allow = min(max_trunc, read_rev, read_fwd + read_rev - trunc_f)
            if min_r_allow > max_r_allow:
                raise optuna.TrialPruned()

            trunc_r = trial.suggest_int(
                "trunc_r", min_r_allow, max_r_allow, step=step
            )
        else:
            trunc_r = 0
            if trunc_f < amp_len:
                raise optuna.TrialPruned()

        try:
            res = _run_dada2(
                ss_art,
                trunc_f,
                trunc_r,
                primer_f,
                primer_r if paired else 0,
                min_overlap,
                threads,
                paired,
            )
        except Exception as e:
            trial.set_user_attr("errmsg", str(e)[:200])
            return 0.0

        df = res.denoising_stats.view(qiime2.Metadata).to_dataframe()
        if (df["non-chimeric"] == 0).any():
            return 0.0
        return (df["non-chimeric"] / df["input"]).mean()

    return obj, paired, (read_fwd, read_rev)


# ───────── QIIME 2-exposed 関数 ─────────
def optimize_truncation(
    demux: qiime2.Artifact,
    amplicon_length: int,
    fwd_primer_length: int,
    rev_primer_length: int,
    fraction: float = 0.20,
    trials: int = 30,
    direction: str = "maximize",
    min_trunc: int = 0,
    max_trunc: int = 300,
    step: int = 5,
    min_overlap: int = 20,
    threads: int = 0,
    timeout: int | None = None,
    seed: int | None = None,
) -> (Metadata, OptiTrimStudyDirFmt):
    """Optuna で DADA2 トリミング長を探索し、推奨パラメータを返す。"""

    # reproducibility
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    paired = _is_paired(demux)

    # ---- subsample ----
    ss_art = _subsample_once(
        demux, fraction=fraction, paired=paired
    )

    # ---- objective ----
    obj, paired, lens = _make_objective(
        ss_art=ss_art,
        amp_len=amplicon_length,
        primer_f=fwd_primer_length,
        primer_r=rev_primer_length,
        min_overlap=min_overlap,
        min_trunc=min_trunc,
        max_trunc=max_trunc,
        step=step,
        threads=threads,
    )

    sampler = optuna.samplers.TPESampler(
        multivariate=True, seed=seed
    )
    study = optuna.create_study(
        direction=direction, sampler=sampler
    )
    study.optimize(
        obj, n_trials=trials, timeout=timeout,
    )

    best = study.best_params

    # ---- assemble result dict ----
    out: Dict[str, Any] = {
        ("trunc_len_f" if paired else "trunc_len"): best["trunc_f"],
        "trim_left_f": fwd_primer_length,
        "min_overlap": min_overlap,
        "n_threads": threads,
    }
    if paired:
        out["trunc_len_r"] = best["trunc_r"]
        out["trim_left_r"] = rev_primer_length

    # Metadata 出力（行名: 'recommended'）
    md = Metadata(pd.DataFrame([out], index=["recommended"]))

    # Study JSON 出力
    dirfmt = OptiTrimStudyDirFmt()
    with dirfmt.study_json.open() as fh:
        json.dump(
            {
                "best_params": out,
                "best_value": study.best_value,
                "n_trials": len(study.trials),
                "direction": direction,
                "read_lengths": {"forward": lens[0], "reverse": lens[1]},
                "paired": paired,
            },
            fh,
            indent=2,
        )

    return md, dirfmt
