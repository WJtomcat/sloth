#coding=utf-8
import time
import logging
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from sloth.core.exceptions import ImproperlyConfigured
from sloth.annotations.model import AnnotationModelItem
from sloth.gui.floatinglayout import FloatingLayout
from sloth.gui.utils import MyVBoxLayout
from sloth.utils.bind import bind
from sloth.gui.noteitem import *
from sloth.gui.comboitem import ComboItem, MaskComboItem
from sloth.gui.checkboxitem import CheckBoxItem

from sloth.conf import config


LOG = logging.getLogger(__name__)


class AbstractAttributeHandler:
    def defaults(self):
        return {}

    def updateValues(self, values):
        pass

    def setItems(self, items, showItemClasses=False):
        pass

    def autoAddEnabled(self):
        return False


class AttributeHandlerFactory:
    def create(self, attribute, values):
        # Class attribute cannot be changed
        if attribute == 'class':
            return None

        # Just a value. No attribute editor needed, we just add it to the item to be inserted...
        if isinstance(values, str) or isinstance(values, float) or isinstance(values, int):
            return None

        # If it's already a handler, just return it
        if isinstance(values, AbstractAttributeHandler):
            return values

        # Else, we create our own default handler
        return DefaultAttributeHandler(attribute, values)


class DefaultAttributeHandler(QGroupBox, AbstractAttributeHandler):
    def __init__(self, attribute, values, parent=None):
        QGroupBox.__init__(self, attribute, parent)
        self._attribute = attribute
        self._current_items = []
        self._defaults = {}
        self._inputField = None
        self._inputFieldType = None
        self._insertIndex = -1
        self._insertAtEnd = False
        self._shortcuts = {}

        # Setup GUI
        self._layout = FloatingLayout()
        self.setLayout(self._layout)
        self._buttons = {}

        # Add interface elements
        self.updateValues(values)

    def focusInputField(self, selectInput=True):
        if self._inputField is not None:
            if selectInput:
                self._inputField.selectAll()
            self._inputField.setFocus(Qt.ShortcutFocusReason)

    def addShortcut(self, shortcut, widget, value):
        if widget is not None:
            if shortcut not in self._shortcuts:
                sc = QShortcut(QKeySequence(shortcut), self)
                self._shortcuts[shortcut] = sc
                if isinstance(widget, QPushButton):
                    sc.activated.connect(bind(lambda w: w.click() if not w.isChecked() else None, widget))
                elif isinstance(widget, QLineEdit):
                    sc.activated.connect(self.focusInputField)
            else:
                raise ImproperlyConfigured("Shortcut '%s' defined more than once" % shortcut)
        else:
            raise ImproperlyConfigured("Shortcut '%s' defined for value '%s' which is hidden" % (shortcut, value))

    def updateValues(self, values):
        if isinstance(values, type):
            self.addInputField(values)
        else:
            for val in values:
                v = val
                shortcut = None
                widget = None

                # Handle the case of the value being a 2-tuple consisting of (value, shortcut)
                if type(val) is tuple or type(val) is list:
                    if len(val) == 2:
                        v = val[0]
                        shortcut = val[1]
                    else:
                        raise ImproperlyConfigured("Values must be types, strings, numbers, or tuples of length 2: '%s'" % str(val))

                # Handle the case where value is a Python type
                if isinstance(v, type):
                    if v is float or v is int or v is str:
                        self.addInputField(v)
                        widget = self._inputField
                    else:
                        raise ImproperlyConfigured("Input field with type '%s' not supported" % v)

                # * marks the position where buttons for new values will be insered
                elif val == "*" or val == "<*":
                    self._insertIndex = self._layout.count()
                elif val == "*>":
                    self._insertIndex = self._layout.count()
                    self._insertAtEnd = True

                # Add the value button
                else:
                    self.addValue(v)
                    widget = self._buttons[v]

                # If defined, add the specified shortcut
                if shortcut is not None:
                    self.addShortcut(shortcut, widget, v)

    def defaults(self):
        return self._defaults

    def autoAddEnabled(self):
        return self._insertIndex >= 0

    def onInputFieldReturnPressed(self):
        val = str(self._inputField.text())
        self.addValue(val, True)
        for item in self._current_items:
            item[self._attribute] = val
        self.updateButtons()
        self.updateInputField()
        self._inputField.clearFocus()

    def addInputField(self, _type):
        if self._inputField is None:
            self._inputFieldType = _type
            self._inputField = QLineEdit()
            if _type is float:
                self._inputField.setValidator(QDoubleValidator())
            elif _type is int:
                self._inputField.setValidator(QIntValidator())

            self._layout.addWidget(self._inputField)
            self._inputField.returnPressed.connect(self.onInputFieldReturnPressed)
        elif self._inputFieldType is not _type:
            raise ImproperlyConfigured("Input field for attribute '%s' configured twice with different types %s != %s"\
                    % (self._attribute, self._inputFieldType, _type))

    def addValue(self, v, autoAddValue=False):
        if v in self._buttons: return
        if autoAddValue and self._insertIndex < 0: return
        button = QPushButton(v, self)
        button.setFlat(True)
        button.setCheckable(True)
        self._buttons[v] = button
        if autoAddValue:
            self._layout.insertWidget(self._insertIndex, button)
            if self._insertAtEnd:
                self._insertIndex += 1
        else:
            self._layout.addWidget(button)
        button.clicked.connect(bind(self.onButtonClicked, v))

    def reset(self):
        self._current_items = []
        for v, button in self._buttons.items():
            button.setChecked(False)
            button.setFlat(True)

    def getSelectedValues(self):
        return set([str(item[self._attribute]) for item in self._current_items if self._attribute in item and item[self._attribute] is not None])

    def updateInputField(self):
        if self._inputField is not None:
            self._inputField.clear()
            selected_values = self.getSelectedValues()
            if len(selected_values) > 1:
                self._inputField.setPlaceholderText(", ".join(selected_values))
            elif len(selected_values) == 1:
                it = iter(selected_values)
                self._inputField.setText(next(it))

    def updateButtons(self):
        selected_values = self.getSelectedValues()
        for val, button in self._buttons.items():
            if val in selected_values:
                if len(selected_values) > 1:
                    button.setFlat(False)
                    button.setChecked(False)
                else:
                    button.setFlat(True)
                    button.setChecked(True)
            else:
                button.setFlat(True)
                button.setChecked(False)

    def setItems(self, items, showItemClasses=False):
        self.reset()
        if showItemClasses:
            title = ", ".join(set([item['class'] for item in items]))
            self.setTitle(self._attribute + " (" + title + ")")
        else:
            self.setTitle(self._attribute)

        self._current_items = items

        self.updateButtons()
        self.updateInputField()

    def onButtonClicked(self, val):
        attr = self._attribute
        LOG.debug("Button %s: %s clicked" % (attr, val))
        button = self._buttons[val]

        # Update model item
        for item in self._current_items:
            if button.isChecked():
                item[attr] = val
            else:
                item[attr] = None

        # Unpress all other buttons
        for v, but in self._buttons.items():
            but.setFlat(True)
            if but is not button:
                but.setChecked(False)

        # Update input field
        self.updateInputField()


class LabelEditor(QScrollArea):
    def __init__(self, items, parent, insertionMode=False):
        QScrollArea.__init__(self, parent)
        self._editor = parent
        self._items = items
        self._insertion_mode = insertionMode

        # Find all classes
        self._label_classes = set([item['class'] for item in items if 'class' in item])
        n_classes = len(self._label_classes)
        LOG.debug("Creating editor for %d item classes: %s" % (n_classes, ", ".join(list(self._label_classes))))

        # Widget layout
        self._layout = QVBoxLayout()
        self._content = QWidget()
        self._content.setLayout(self._layout)

        attributes = set()
        for lc in self._label_classes:
            attributes |= set(self._editor.getLabelClassAttributes(lc))

        attributes = list(attributes)
        attributes.sort()
        for attr in attributes:
            handler = self._editor.getHandler(attr)
            if handler is not None:
                if len(items) > 1:
                    valid_items = [item for item in items
                                   if attr in self._editor.getLabelClassAttributes(item['class'])]
                    handler.setItems(valid_items, True)
                else:
                    handler.setItems(items)
                self._layout.addWidget(handler)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self._content)

    def sizeHint(self):
        minsz = self.minimumSize()
        sz = self._layout.minimumSize()
        left, top, right, bottom = self.getContentsMargins()
        return QSize(max(minsz.width(), sz.width() + left + right), max(minsz.height(), sz.height() + top + bottom))

    def labelClasses(self):
        return self._label_classes

    def currentProperties(self):
        if len(self._items) == 1:
            return self._items[0]
        else:
            return {}

    def insertionMode(self):
        return self._insertion_mode


class PropertyEditor(QWidget):
    # Signals
    insertionModeStarted       = pyqtSignal(str)
    insertionModeEnded         = pyqtSignal()
    insertionPropertiesChanged = pyqtSignal(object)
    editPropertiesChanged      = pyqtSignal(object)

    def __init__(self, config, parent=None):
        QWidget.__init__(self, parent)
        self.setMaximumWidth(250)
        self._class_config       = {}
        self._class_items        = {}
        self._class_prototypes   = {}
        self._attribute_handlers = {}
        self._handler_factory    = AttributeHandlerFactory()

        self._note_items = []
        self._combo_items = []
        self._check_items = []
        self._line_items = []
        self._setupGUI()

        # Add label classes from config

        for i, label in enumerate(config.LABELS):
            if i < 7:
                self.addLabelClass(label, 1)
            else:
                self.addLabelClass(label, 2)

        for i, label in enumerate(config.DETAILS):
            if i < 3:
                self.addDetailClass(label, 1)
            else:
                self.addDetailClass(label, 2)
        self.detailbox2layout.addStretch(1)

        for label in config.COMBOCLASS:
            self.addComboClass(label)

        for label in config.NOTES:
            self.addNoteItem(label)

        # for label in config.INPUTLINE:
        #     self.addInputLine(label)

        # for label in config.CHECKBOX:
        #     self.addCheckBoxItem(label)

        self._layout.addStretch(1)

    def onModelChanged(self, new_model):
        attrs = set([k for k, v in self._attribute_handlers.items() if v.autoAddEnabled()])
        if len(attrs) > 0:
            start = time.time()
            attr2vals = {}
            for item in new_model.iterator(AnnotationModelItem):
                for attr in attrs:
                    if attr in item:
                        if attr not in attr2vals:
                            attr2vals[attr] = set((item[attr], ))
                        else:
                            attr2vals[attr] |= set((item[attr], ))
            diff = time.time() - start
            LOG.info("Extracted annotation values from model in %.2fs" % diff)
            for attr, vals in attr2vals.items():
                h = self._attribute_handlers[attr]
                for val in vals:
                    h.addValue(val, True)

    def onImageItemChanged(self, image_item):
        for item in self._note_items:
            item.onImageItemChanged(image_item)
        for item in self._combo_items:
            item.onImageItemChanged(image_item)
        # for item in self._check_items:
        #     item.onImageItemChanged(image_item)

    def addLabelClass(self, label_config, boxnum):
        # Check label configuration
        if 'attributes' not in label_config:
            raise ImproperlyConfigured("Label with no 'attributes' dict found")
        attrs = label_config['attributes']
        if 'class' not in attrs:
            raise ImproperlyConfigured("Labels must have an attribute 'class'")
        label_class = attrs['class']
        if label_class in self._class_config:
            raise ImproperlyConfigured("Label with class '%s' defined more than once" % label_class)

        # Store config
        self._class_config[label_class] = label_config

        # Parse configuration and create handlers and item
        self.parseConfiguration(label_class, label_config)

        # Add label class button
        button_text = label_config['text']

        _color = label_config['attributes']['class']
        _color = config.COLORMAP[_color]


        _pixmap = QPixmap(8, 8)
        _color = QColor(_color[0], _color[1], _color[2])
        _pixmap.fill(_color)
        icon = QIcon(_pixmap)


        button = QPushButton(icon, button_text, self)
        button.setCheckable(True)
        button.setFlat(True)
        button.setStyleSheet("QPushButton{text-align : left;}")
        button.clicked.connect(bind(self.onClassButtonPressed, label_class))
        self._class_buttons[label_class] = button
        if boxnum == 1:
            self.box1layout.addWidget(button)
        else:
            self.box2layout.addWidget(button)

        # Add hotkey
        if 'hotkey' in label_config:
            hotkey = QShortcut(QKeySequence(label_config['hotkey']), self)
            hotkey.activated.connect(button.click)
            self._class_shortcuts[label_class] = hotkey

    def addDetailClass(self, label_config, boxnum):
        # Check label configuration
        if 'attributes' not in label_config:
            raise ImproperlyConfigured("Label with no 'attributes' dict found")
        attrs = label_config['attributes']
        if 'class' not in attrs:
            raise ImproperlyConfigured("Labels must have an attribute 'class'")
        label_class = attrs['class']
        if label_class in self._class_config:
            raise ImproperlyConfigured("Label with class '%s' defined more than once" % label_class)

        # Store config
        self._class_config[label_class] = label_config

        # Parse configuration and create handlers and item
        self.parseConfiguration(label_class, label_config)

        # Add label class button
        button_text = label_config['text']

        _color = label_config['attributes']['class']
        _color = config.COLORMAP[_color]


        _pixmap = QPixmap(8, 8)
        _color = QColor(_color[0], _color[1], _color[2])
        _pixmap.fill(_color)
        icon = QIcon(_pixmap)


        button = QPushButton(icon, button_text, self)
        button.setCheckable(True)
        button.setFlat(True)
        button.setStyleSheet("QPushButton{text-align : left;}")
        button.clicked.connect(bind(self.onClassButtonPressed, label_class))
        self._class_buttons[label_class] = button
        if boxnum == 1:
            self.detailbox1layout.addWidget(button)
        else:
            self.detailbox2layout.addWidget(button)

        # Add hotkey
        if 'hotkey' in label_config:
            hotkey = QShortcut(QKeySequence(label_config['hotkey']), self)
            hotkey.activated.connect(button.click)
            self._class_shortcuts[label_class] = hotkey

    def addNoteItem(self, label_config):
        noteItem = NoteItem(label_config)
        self._note_items.append(noteItem)
        box = QGroupBox(label_config, self)
        layout = FloatingLayout()
        box.setLayout(layout)
        layout.addWidget(noteItem)
        self._layout.addWidget(box)

    # def addInputLine(self, label_config):
    #     lineItem = LineEditItem(label_config)
    #     self._line_items.append(lineItem)
    #     self.lineLayout.addRow(label_config, lineItem)


    def addComboClass(self, label_config):
        if 'text' not in label_config:
            raise ImproperlyConfigured("Combobox with no text found")
        attrs = label_config['text']
        if 'items' not in label_config:
            raise ImproperlyConfigured("Combobox with no items found")
        items = label_config['items']

        combobox = ComboItem(label_config)
        self._combo_items.append(combobox)
        box = QGroupBox(attrs, self)
        layout = FloatingLayout()
        box.setLayout(layout)
        layout.addWidget(combobox)
        self._layout.addWidget(box)

    # def addCheckBoxItem(self, label_config):
    #     if 'text' not in label_config:
    #         raise ImproperlyConfigured("CheckBoxItem with no text found")
    #     attrs = label_config['text']
    #     if 'items' not in label_config:
    #         raise ImproperlyConfigured("CheckBoxItem with no items found")
    #     items = label_config['items']
    #     checkBox = CheckBoxItem(label_config, attrs)
    #     self._check_items.append(checkBox)
    #     self._layout.addWidget(checkBox)

    def parseConfiguration(self, label_class, label_config):
        attrs = label_config['attributes']

        # Add prototype item for insertion
        self._class_items[label_class] = AnnotationModelItem({ 'class': label_class })

        # Create attribute handler widgets or update their values
        for attr, vals in attrs.items():
            if attr in self._attribute_handlers:
                self._attribute_handlers[attr].updateValues(vals)
            else:
                handler = self._handler_factory.create(attr, vals)
                if handler is None:
                    self._class_items[label_class][attr] = vals
                else:
                    self._attribute_handlers[attr] = handler

        for attr in attrs:
            if attr in self._attribute_handlers:
                self._class_items[label_class].update(self._attribute_handlers[attr].defaults())

    def getHandler(self, attribute):
        if attribute in self._attribute_handlers:
            return self._attribute_handlers[attribute]
        else:
            return None

    def getLabelClassAttributes(self, label_class):
        return self._class_config[label_class]['attributes'].keys()

    def onClassButtonPressed(self, label_class):
        if self._class_buttons[label_class].isChecked():
            self.startInsertionMode(label_class)
        else:
            self.endInsertionMode()

    def startInsertionMode(self, label_class):
        self.endInsertionMode(False)
        for lc, button in self._class_buttons.items():
            button.setChecked(lc == label_class)
        LOG.debug("Starting insertion mode for %s" % label_class)
        self._label_editor = LabelEditor([self._class_items[label_class]], self, True)
        # self._layout.insertWidget(1, self._label_editor, 0)
        self.insertionModeStarted.emit(label_class)

    def endInsertionMode(self, uncheck_buttons=True):
        if self._label_editor is not None:
            LOG.debug("Ending insertion/edit mode")
            # self._label_editor.hide()
            # self._layout.removeWidget(self._label_editor)
            self._label_editor = None
        if uncheck_buttons:
            self.uncheckAllButtons()
        self.insertionModeEnded.emit()

    def uncheckAllButtons(self):
        for lc, button in self._class_buttons.items():
            button.setChecked(False)

    def markEditButtons(self, label_classes):
        for lc, button in self._class_buttons.items():
            button.setFlat(lc not in label_classes)

    def currentEditorProperties(self):
        if self._label_editor is None:
            return None
        else:
            return self._label_editor.currentProperties()

    def startEditMode(self, model_items):
        # If we're in insertion mode, ignore empty edit requests
        if self._label_editor is not None and self._label_editor.insertionMode() \
                and len(model_items) == 0:
            return

        self.endInsertionMode()
        LOG.debug("Starting edit mode for items: %s" % model_items)
        self._label_editor = LabelEditor(model_items, self)
        self.markEditButtons(self._label_editor.labelClasses())
        # self._layout.insertWidget(1, self._label_editor, 0)

    def _setupGUI(self):
        self._class_buttons = {}
        self._class_shortcuts = {}
        self._label_editor  = None

        # Label class buttons
        self._classbox = QGroupBox(u"形态分类", self)
        self._classbox_layout = QHBoxLayout()
        self._classbox_layout.setContentsMargins(0,0,0,0)
        self._classbox_layout.setSpacing(0)

        self.box1 = QGroupBox(self)
        self.box1layout = QVBoxLayout()
        self.box1layout.setContentsMargins(0,0,0,0)
        self.box1layout.setSpacing(0)

        self.box1.setLayout(self.box1layout)
        self.box2 = QGroupBox(self)
        self.box2layout = QVBoxLayout()
        self.box2layout.setContentsMargins(0,0,0,0)
        self.box2layout.setSpacing(2)
        self.box2.setLayout(self.box2layout)

        self._classbox_layout.addWidget(self.box1)
        self._classbox_layout.addWidget(self.box2)


        self._classbox.setLayout(self._classbox_layout)

        self._detailbox = QGroupBox(u"形态细节(可选)", self)
        self._detailbox_layout = QHBoxLayout()
        self._detailbox_layout.setContentsMargins(0,0,0,0)
        self._detailbox_layout.setSpacing(0)

        self.detailbox1 = QGroupBox(self)
        self.detailbox1layout = QVBoxLayout()
        self.detailbox1layout.setContentsMargins(0,0,0,0)
        self.detailbox1layout.setSpacing(0)

        self.detailbox1.setLayout(self.detailbox1layout)
        self.detailbox2 = QGroupBox(self)
        self.detailbox2layout = QVBoxLayout()
        self.detailbox2layout.setContentsMargins(0,0,0,0)
        self.detailbox2layout.setSpacing(2)
        self.detailbox2.setLayout(self.detailbox2layout)

        self._detailbox_layout.addWidget(self.detailbox1)
        self._detailbox_layout.addWidget(self.detailbox2)


        self._detailbox.setLayout(self._detailbox_layout)


        self._detailbox.setLayout(self._detailbox_layout)

        # self.labelGroup = QGroupBox()
        # self.label_layout = QHBoxLayout()
        # self.labelGroup.setLayout(self.label_layout)
        # self.label_layout.addWidget(self._classbox)
        # self.label_layout.addWidget(self._detailbox)

        # Global widget
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0,0,0,0)
        self.setLayout(self._layout)
        # self._layout.addStretch(1)
        self._layout.addWidget(self._classbox)

        self._layout.addWidget(self._detailbox)
        # self._layout.addStretch(2)

        # self.lineLayout = QFormLayout()
        # self._layout.addLayout(self.lineLayout)


    def addItemEditor(self, editor):
        self._layout.addWidget(editor)
