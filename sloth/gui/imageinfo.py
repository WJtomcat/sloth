#coding=utf-8
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import sys


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
        keys = [u'hp', u'description', u'conclusion', u'report_date', u'label']
        # keys = [unicode('hp', 'utf-8'), unicode('description', 'utf-8'), unicode('conclusion', 'utf-8'), unicode('report_data', 'utf-8'), unicode('label', 'utf-8')]
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
        keys = [u'text', u'accept_date']
        for i in keys:
            try:
                tmp = i + ':  \n' + str(pathologyinfo[i]) + '\n \n'
                ann += tmp
            except KeyError:
                continue
        ann += '\n'
        self.infotable.append(ann)
