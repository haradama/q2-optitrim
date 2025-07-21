from qiime2.plugin import model
import json


class OptiTrimStudyFormat(model.TextFileFormat):
    def _validate_(self, level):
        with self.open() as fh:
            json.load(fh)


class OptiTrimStudyDirFmt(model.SingleFileDirectoryFormatBase):
    study_json = model.File('study.json', format=OptiTrimStudyFormat)
