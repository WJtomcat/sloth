#coding=utf-8
from PyQt4.QtCore import pyqtSignal, QSize, Qt
from PyQt4.QtGui import QWidget, QGroupBox, QFormLayout, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QScrollArea, QLineEdit, QDoubleValidator, QIntValidator, QShortcut, QKeySequence, QSlider
from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.gui.utils import MyVBoxLayout
from sloth.utils.bind import bind
from sloth.gui.noteitem import NoteItem, MaskNoteItem, MaskLineItem
from sloth.gui.comboitem import ComboItem, MaskComboItem
from sloth.gui.checkboxitem import MaskCheckBoxItem

class ItemEditor(QGroupBox):

    def __init__(self, config, parent=None):
        QGroupBox.__init__(self, parent)

        self._note_items = []
        self._line_items = []
        self._combo_items = []
        self._check_items = []

        for label in config.ITEMNOTES:
            self.addNoteItem(label)

        for label in config.ITEMLINES:
            self.addLineItem(label)

        for label in config.ITEMCHECKBOX:
            self.addCheckBoxItem(label)

        for label in config.ITEMCOMBOCLASS:
            self.addComboClass(label)

        self._setupGUI()
        self.setDisabled(True)
        self.hide()

    def addLineItem(self, label_config):
        lineitem = MaskLineItem(label_config)
        self._line_items.append(lineitem)

    def addComboClass(self, label_config):
        if 'text' not in label_config:
            raise ImproperlyConfigured("Combobox with no text found")
        attrs = label_config['text']
        if 'items' not in label_config:
            raise ImproperlyConfigured("Combobox with no items found")
        items = label_config['items']
        combobox = MaskComboItem(label_config)
        self._combo_items.append(combobox)

    def _setupGUI(self):
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        if len(self._line_items) != 0:
            box = QGroupBox(u'病灶量化信息', self)
            layout = QFormLayout()
            box.setLayout(layout)
            for item in self._line_items[:-1]:
                layout.addRow(item.labelclass, item)
            self._layout.addWidget(box)

        if len(self._combo_items) != 0:
            box = QGroupBox(u'病理诊断', self)
            layout = QFormLayout()
            box.setLayout(layout)
            for item in self._combo_items:
                layout.addRow(item.labelclass, item)
            layout.addRow(u'浸润深度', self._line_items[-1])
            self._layout.addWidget(box)

        self._layout.addStretch(1)

    def onItemChanged(self, item):
        if item is not None:
            # self.tab.setCurrentIndex(self.tab.indexOf(self))
            self.show()
            self.setEnabled(True)
        else:
            # self.tab.setCurrentIndex(0)
            self.hide()
            self.setDisabled(True)
        for i in self._note_items:
            i.onItemChanged(item)
        for i in self._combo_items:
            i.onItemChanged(item)
        for i in self._check_items:
            i.onItemChanged(item)
        for i in self._line_items:
            i.onItemChanged(item)

    def onItemDisSelected(self):
        self.onItemChanged(None)

    def onCheckChanged(self, state):
        self.checkChanged.emit(state)

    def onImageItemChanged(self, image_item):
        self.resetItem()

    def resetItem(self):
        self.onItemDisSelected()
        for i in self._note_items:
            i.resetNote()
        for i in self._combo_items:
            i.resetIndex()
        for i in self._line_items:
            i.resetNote()
