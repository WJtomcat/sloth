from PyQt4.QtCore import pyqtSignal, QSize, Qt
from PyQt4.QtGui import QWidget, QGroupBox, QFormLayout, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QScrollArea, QLineEdit, QDoubleValidator, QIntValidator, QShortcut, QKeySequence, QSlider
from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.gui.utils import MyVBoxLayout
from sloth.utils.bind import bind
from sloth.gui.noteitem import NoteItem, MaskNoteItem
from sloth.gui.comboitem import ComboItem, MaskComboItem

class ItemEditor(QWidget):

    sliderChanged              = pyqtSignal(int)
    checkChanged               = pyqtSignal(int)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.maskNoteItem = MaskNoteItem()
        self.maskComboItem = MaskComboItem()

        self.opaquelayout = QHBoxLayout()
        self.opaque_check = QCheckBox("Hide")
        self.opaquelayout.addWidget(self.opaque_check, 0)

        self.opaque_slider = QSlider(Qt.Horizontal)
        self.opaque_slider.setMinimum(30)
        self.opaquelayout.addWidget(self.opaque_slider, 1)

        self.opaque_slider.valueChanged.connect(self.onSliderChanged)
        self.opaque_check.stateChanged.connect(self.onCheckChanged)

        self._setupGUI()


    def _setupGUI(self):
        self._layout = MyVBoxLayout()
        self.setLayout(self._layout)

        self._layout.addWidget(self.maskNoteItem, 0)
        self._layout.addWidget(self.maskComboItem, 1)
        self._layout.addStretch(1)

        self.opaqueGroup = QGroupBox()
        self.opaqueGroup.setLayout(self.opaquelayout)
        self._layout.addWidget(self.opaqueGroup, 2)
        self._layout.addStretch(2)

    def onItemChanged(self, item):
        self.maskNoteItem.onItemChanged(item)
        self.maskComboItem.onItemChanged(item)

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

        self.maskNoteItem.resetNote()
        self.maskComboItem.resetIndex()
