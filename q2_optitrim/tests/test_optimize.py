import qiime2
from qiime2.plugin.testing import TestPluginBase
from q2_optitrim._optimize import optimize_truncation

class OptimizeTruncationTests(TestPluginBase):
    package = 'q2_optitrim.tests'

    def test_smoketest_single(self):
        # 小さな demux アーティファクト（テストデータ要準備）
        demux = qiime2.Artifact.load(self.get_data_path('demux-small.qza'))
        md, study = optimize_truncation(
            demux=demux,
            amplicon_length=100,
            fwd_primer_length=20,
            rev_primer_length=0,
            fraction=0.5,
            trials=2,
            max_trunc=100,
            step=10,
            min_trunc=10,
            min_overlap=10,
            threads=0,
        )
        df = md.to_dataframe()
        assert not df.empty
