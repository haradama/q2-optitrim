from qiime2.plugin import model
import json

class OptiTrimStudyFormat(model.TextFileFormat):
    """単一 JSON ファイル（Optuna Study summary）."""
    def _validate_(self):
        with self.open() as fh:
            json.load(fh)

class OptiTrimStudyDirFmt(model.SingleFileDirectoryFormat):
    study_json = model.File('study.json', format=OptiTrimStudyFormat)