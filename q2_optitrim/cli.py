# q2_optitrim/cli.py
from __future__ import annotations
import argparse
import sys
import qiime2
from ._optimize import optimize_truncation

def _build_parser():
    P = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    P.add_argument("--demux", required=True, help="demultiplexed .qza")
    P.add_argument("--amplicon-length", type=int, required=True)
    P.add_argument("--fwd-primer-length", type=int, required=True)
    P.add_argument("--rev-primer-length", type=int, required=True)
    P.add_argument("--fraction", type=float, default=0.20)
    P.add_argument("--trials", type=int, default=30)
    P.add_argument("--direction", choices=("maximize", "minimize"), default="maximize")
    P.add_argument("--min-trunc", type=int, default=0)
    P.add_argument("--max-trunc", type=int, default=300)
    P.add_argument("--step", type=int, default=5)
    P.add_argument("--min-overlap", type=int, default=20)
    P.add_argument("--threads", type=int, default=0)
    P.add_argument("--timeout", type=int)
    P.add_argument("--seed", type=int)
    P.add_argument("--o-params", required=True, help="output Metadata .qza")
    P.add_argument("--o-study", required=True, help="output Study JSON .qza")
    return P

def main(argv=None):
    args = _build_parser().parse_args(argv)

    demux_art = qiime2.Artifact.load(args.demux)

    md, dirfmt = optimize_truncation(
        demux=demux_art,
        amplicon_length=args.amplicon_length,
        fwd_primer_length=args.fwd_primer_length,
        rev_primer_length=args.rev_primer_length,
        fraction=args.fraction,
        trials=args.trials,
        direction=args.direction,
        min_trunc=args.min_trunc,
        max_trunc=args.max_trunc,
        step=args.step,
        min_overlap=args.min_overlap,
        threads=args.threads,
        timeout=args.timeout,
        seed=args.seed,
    )

    md.save(args.o_params)
    qiime2.Artifact.import_data(
        'OptiTrimStudy', dirfmt  # 仮 SemanticType -> plugin_setup で定義
    ).save(args.o_study)

if __name__ == "__main__":
    sys.exit(main())
