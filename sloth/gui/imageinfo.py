from PyQt4.QtGui import QWidget, QTextEdit, QGroupBox, QVBoxLayout

import sys
reload(sys)
sys.setdefaultencoding('utf8')


class ImageInfo(QWidget):

    def __init__(self, config, parent=None):
        QWidget.__init__(self, parent)
        self.patient_info = QTextEdit()
        # self.patient_info.setEnabled(False)
        self.endoscopy_info = QTextEdit()
        # self.endoscopy_info.setEnabled(False)
        self.pathology_info = QTextEdit()
        # self.pathology_info.setEnabled(False)

        self._setupGUI()

    def _setupGUI(self):
        self.patientBox = QGroupBox('Patient Information')
        self.endoscopyBox = QGroupBox('Endoscopy Information')
        self.pathologyBox = QGroupBox('Pathology Information')
        self.patient_layout = QVBoxLayout()
        self.endoscopy_layout = QVBoxLayout()
        self.pathology_layout = QVBoxLayout()
        self.patient_layout.addWidget(self.patient_info)
        self.endoscopy_layout.addWidget(self.endoscopy_info)
        self.pathology_layout.addWidget(self.pathology_info)
        self.patientBox.setLayout(self.patient_layout)
        self.endoscopyBox.setLayout(self.endoscopy_layout)
        self.pathologyBox.setLayout(self.pathology_layout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.patientBox)
        self.layout.addWidget(self.endoscopyBox)
        self.layout.addWidget(self.pathologyBox)
        self.setLayout(self.layout)

    def onImageItemChanged(self, image_item):
        if image_item is None:
            self.patient_info.clear()
            self.endoscopy_info.clear()
            self.pathology_info.clear()
            return
        image_item = image_item.getAnnotations()

        ann = ''
        patientinf = image_item['patientinf']
        keys = ['name', 'age', 'sex']
        for i in keys:
            try:
                if i == 'age':
                    tmp = i + ': ' + str(patientinf[i]) + '\n'
                else:
                    tmp = i + ': ' + patientinf[i] + '\n'
                ann += tmp
            except KeyError:
                continue
        self.patient_info.setText(ann)

        ann = ''
        endoscopyinfo = image_item['endoscopyinfo']
        keys = ['hp'.decode('utf-8'), 'description'.decode('utf-8'), 'conclusion'.decode('utf-8'), 'report_date'.decode('utf-8'), 'label'.decode('utf-8')]
        print(keys)
        for i in keys:
            try:
                tmp = i + ':' + str(endoscopyinfo[i]) + '\n'
                ann += tmp
            except KeyError:
                continue
        print(ann)
        self.endoscopy_info.setText(ann)

        ann = ''
        pathologyinfo = image_item['pathologyinfo']
        print(pathologyinfo)
        keys = ['text'.decode('utf-8'), 'accept_date'.decode('utf-8')]
        for i in keys:
            try:
                print('try once')
                tmp = i + ':' + str(pathologyinfo[i]) + '\n'
                ann += tmp
            except KeyError:
                print('keyerror')
                continue
        self.pathology_info.setText(ann)
