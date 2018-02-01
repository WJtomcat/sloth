from PyQt4.QtGui import QWidget, QTextEdit, QGroupBox, QVBoxLayout

import sys
reload(sys)
sys.setdefaultencoding('utf8')


class ImageInfo(QWidget):

    def __init__(self, config, parent=None):
        QWidget.__init__(self, parent)
        self.infotable = QTextEdit()
        self.infotable.setReadOnly(True)
        self._setupGUI()

    def _setupGUI(self):        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.infotable)
        self.setLayout(self.layout)

    def onImageItemChanged(self, image_item):
        if image_item is None:
            self.infotable.clear()
            return
        image_item = image_item.getAnnotations()

        ann = ''
        patientinf = image_item['patientinf']
        keys = ['name', 'age', 'sex']
        for i in keys:
            try:
                if i == 'age':
                    tmp = i + ':  \n' + str(patientinf[i]) + '\n \n'
                else:
                    tmp = i + ':  \n' + patientinf[i] + '\n \n'
                ann += tmp
            except KeyError:
                continue
        ann += '\n'
        self.infotable.setText(ann)

        ann = ''
        endoscopyinfo = image_item['endoscopyinfo']
        keys = ['hp'.decode('utf-8'), 'description'.decode('utf-8'), 'conclusion'.decode('utf-8'), 'report_date'.decode('utf-8'), 'label'.decode('utf-8')]
        print(keys)
        for i in keys:
            try:
                tmp = i + ':  \n' + str(endoscopyinfo[i]) + '\n \n'
                ann += tmp
            except KeyError:
                continue
        ann += '\n'
        self.infotable.append(ann)

        ann = ''
        pathologyinfo = image_item['pathologyinfo']
        print(pathologyinfo)
        keys = ['text'.decode('utf-8'), 'accept_date'.decode('utf-8')]
        for i in keys:
            try:
                print('try once')
                tmp = i + ':  \n' + str(pathologyinfo[i]) + '\n \n'
                ann += tmp
            except KeyError:
                print('keyerror')
                continue
        ann += '\n'
        self.infotable.append(ann)
