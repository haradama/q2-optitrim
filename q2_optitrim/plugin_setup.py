# ----------------------------------------------------------------------------
# Copyright (c) 2025, Masafumi Harada.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

from qiime2.plugin import Citations, Plugin, SemanticType, Str, Int, Float, Bool
from q2_types.feature_table import FeatureTable, Frequency
from q2_types.per_sample_sequences import SequencesWithQuality, PairedEndSequencesWithQuality, SampleData
from q2_optitrim import __version__
from q2_optitrim._optimize import optimize_truncation
from q2_optitrim.formats import OptiTrimStudyDirFmt

# SemanticType for study JSON (opaque)
OptiTrimStudy = SemanticType('OptiTrimStudy')

citations = Citations.load("citations.bib", package="q2_optitrim")

plugin = Plugin(
    name="optitrim",
    version=__version__,
    website="https://github.com/haradama/q2-optitrim",
    package="q2_optitrim",
    description="A QIIME 2 plugin template.",
    short_description="Plugin template.",
    # The plugin-level citation of 'Caporaso-Bolyen-2025' is provided as
    # an example. You can replace this with citations to other references
    # in citations.bib.
    citations=[citations['Caporaso-Bolyen-2025']]
)

plugin.register_formats(OptiTrimStudyDirFmt)
plugin.register_semantic_types(OptiTrimStudy)
plugin.register_semantic_type_to_format(
    OptiTrimStudy,
    artifact_format=OptiTrimStudyDirFmt,
)

plugin.methods.register_function(
    function=optimize_truncation,
    inputs={
        'demux': SampleData[SequencesWithQuality | PairedEndSequencesWithQuality],
    },
    parameters={
        'amplicon_length': Int,
        'fwd_primer_length': Int,
        'rev_primer_length': Int,
        'fraction': Float % plugin.Range(0, 1, inclusive_start=False, inclusive_end=True),
        'trials': Int % plugin.Range(1, None),
        'direction': Str % plugin.Choices(['maximize', 'minimize']),
        'min_trunc': Int % plugin.Range(0, None),
        'max_trunc': Int % plugin.Range(1, None),
        'step': Int % plugin.Range(1, None),
        'min_overlap': Int % plugin.Range(0, None),
        'threads': Int % plugin.Range(0, None),
        'timeout': Int % plugin.Range(1, None) | plugin.Use.default(None),
        'seed': Int | plugin.Use.default(None),
    },
    outputs=[
        ('recommended_params', qiime2.plugin.Metadata),  # Metadata 出力
        ('study', OptiTrimStudy),
    ],
    input_descriptions={
        'demux': 'Demultiplexed sequences (.qza). Single-end or paired-end.',
    },
    parameter_descriptions={
        'amplicon_length': 'Expected amplicon length (bp).',
        'fwd_primer_length': 'Forward primer length (bp to trim at 5\').',
        'rev_primer_length': 'Reverse primer length (paired reads only).',
        'fraction': 'Subsample fraction (0<x≤1) for quick optimization.',
        'trials': 'Maximum Optuna trials.',
        'direction': 'Optimization direction.',
        'min_trunc': 'Minimum allowed truncation length.',
        'max_trunc': 'Maximum allowed truncation length.',
        'step': 'Grid step size (bp).',
        'min_overlap': 'Minimum overlap for paired-end merging.',
        'threads': 'Threads passed to DADA2.',
        'timeout': 'Wall-time limit (sec).',
        'seed': 'Random seed for reproducibility.',
    },
    output_descriptions={
        'recommended_params': 'Recommended DADA2 truncation/trim parameters (Metadata).',
        'study': 'JSON summary of Optuna study.',
    },
    name='Optimize truncation lengths for DADA2',
    description=(
        "Subsample demultiplexed reads, run Optuna-driven search over "
        "DADA2 truncation lengths, and return recommended parameters."
    ),
    citations=[],
)
