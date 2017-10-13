from PyQt4.QtCore import pyqtSignal, QSize, Qt
from PyQt4.QtGui import QWidget, QGroupBox, QFormLayout, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QScrollArea, QLineEdit, QDoubleValidator, QIntValidator, QShortcut, QKeySequence, QSlider
from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.gui.utils import MyVBoxLayout
from sloth.utils.bind import bind
from sloth.gui.noteitem import NoteItem, MaskNoteItem
from sloth.gui.comboitem import ComboItem, MaskComboItem
from sloth.gui.checkboxitem import MaskCheckBoxItem

class ItemEditor(QWidget):

    sliderChanged              = pyqtSignal(int)
    checkChanged               = pyqtSignal(int)

    def __init__(self, config, parent=None):
        QWidget.__init__(self, parent)

        self.opaquelayout = QHBoxLayout()
        self.opaque_check = QCheckBox("Hide")
        self.opaquelayout.addWidget(self.opaque_check, 0)

        self.opaque_slider = QSlider(Qt.Horizontal)
        self.opaque_slider.setMinimum(30)
        self.opaquelayout.addWidget(self.opaque_slider, 1)

        self.opaque_slider.valueChanged.connect(self.onSliderChanged)
        self.opaque_check.stateChanged.connect(self.onCheckChanged)

        self._note_items = []
        self._combo_items = []
        self._check_items = []
        self._setupGUI()

        for label in config.ITEMNOTES:
            self.addNoteItem(label)

        for label in config.ITEMCOMBOCLASS:
            self.addComboClass(label)

        for label in config.ITEMCHECKBOX:
            self.addCheckBoxItem(label)

    def addNoteItem(self, label_config):
        noteItem = MaskNoteItem(label_config)
        self._note_items.append(noteItem)
        box = QGroupBox(label_config, self)
        layout = FloatingLayout()
        box.setLayout(layout)
        layout.addWidget(noteItem)
        self._layout.addWidget(box)

    def addComboClass(self, label_config):
        if 'text' not in label_config:
            raise ImproperlyConfigured("Combobox with no text found")
        attrs = label_config['text']
        if 'items' not in label_config:
            raise ImproperlyConfigured("Combobox with no items found")
        items = label_config['items']
        combobox = MaskComboItem(label_config)
        self._combo_items.append(combobox)
        box = QGroupBox(attrs, self)
        layout = FloatingLayout()
        box.setLayout(layout)
        layout.addWidget(combobox)
        self._layout.addWidget(box)

    def addCheckBoxItem(self, label_config):
        if 'text' not in label_config:
            raise ImproperlyConfigured("CheckBoxItem with no text found")
        attrs = label_config['text']
        if 'items' not in label_config:
            raise ImproperlyConfigured("CheckBoxItem with no items found")
        items = label_config['items']
        checkBox = MaskCheckBoxItem(label_config, attrs)
        self._check_items.append(checkBox)
        self._layout.addWidget(checkBox)

    def _setupGUI(self):
        self._layout = MyVBoxLayout()
        self.setLayout(self._layout)

        self.opaqueGroup = QGroupBox()
        self.opaqueGroup.setLayout(self.opaquelayout)
        self._layout.addWidget(self.opaqueGroup, 1)
        self._layout.addStretch(1)

    def onItemChanged(self, item):
        for i in self._note_items:
            i.onItemChanged(item)
        for i in self._combo_items:
            i.onItemChanged(item)
        for i in self._check_items:
            i.onItemChanged(item)

    def onItemDisSelected(self):
        self.onItemChanged(None)

    def onCheckChanged(self, state):
        self.checkChanged.emit(state)

    def onSliderChanged(self, value):
        self.sliderChanged.emit(value)

    def onImageItemChanged(self, image_item):
        self.opaque_slider.valueChanged.disconnect(self.onSliderChanged)
        self.opaque_slider.setValue(60)
        self.opaque_slider.valueChanged.connect(self.onSliderChanged)

        self.opaque_check.stateChanged.disconnect(self.onCheckChanged)
        self.opaque_check.setCheckState(Qt.Unchecked)
        self.opaque_check.stateChanged.connect(self.onCheckChanged)

        self.resetItem()

    def resetItem(self):
        for i in self._note_items:
            i.resetNote()
        for i in self._combo_items:
            i.resetIndex()
