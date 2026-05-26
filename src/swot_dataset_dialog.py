import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'swot_dataset_dialog.ui'))


class QSWOTDatasetDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(QSWOTDatasetDialog, self).__init__(parent)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)