from PyQt4.QtGui import *
from sloth.annotations.model import *

class CheckBoxItem(QGroupBox):
    def __init__(self, config, attrs, parent=None, default_properties=None):
        QGroupBox.__init__(self, attrs, parent)
        self.config = config
        self._prefix = ''
        self._default_properties = default_properties or {}
        self.labelclass = config['text']
        self.checkitems = {}
        self.image_item = None
        self.hasitemflag = False
        self.layout = None
        self.setupGui()

    def setupGui(self):
        self.layout = QVBoxLayout()
        items = self.config['items']
        for i in items:
            checkbox = QCheckBox(i)
            checkbox.setTristate()
            checkbox.stateChanged.connect(self.changeCheck)
            self.checkitems[i] = checkbox
            self.layout.addWidget(checkbox)
        self.setLayout(self.layout)


    def loadCheck(self, image_item):
        self.hasitemflag = False
        self.image_item = image_item
        if image_item is None:
            self.resetCheck()
            return
        self.child = None
        length = len(image_item.children())
        for row in range(0, length):
            child = image_item.childAt(row)
            if not isinstance(child, AnnotationModelItem):
                continue
            try:
                if child['class'] != self.labelclass:
                    continue
            except KeyError:
                LOG.debug('Could not find key class in annotation item. Skipping this item. Please check your label file.')
            self.child = child
        if self.child is not None:
            for text, item in self.checkitems.items():
                item.stateChanged.disconnect(self.changeCheck)
                tmp = self.child[text]
                item.setCheckState(tmp)
                item.stateChanged.connect(self.changeCheck)
        else:
            self.resetCheck()

    def resetCheck(self):
        for item in self.checkitems.values():
            item.stateChanged.disconnect(self.changeCheck)
            item.setCheckState(1)
            item.stateChanged.connect(self.changeCheck)

    def changeCheck(self, _):
        if self.image_item is None:
            return
        if self.hasitemflag:
            for text, item in self.checkitems:
                self.child[text] = item.checkState()
        else:
            ann = {}
            ann.update({ self._prefix + 'class': self.labelclass })
            for text, item in self.checkitems.items():
                ann.update({self._prefix + text : item.checkState() })
            ann.update(self._default_properties)
            self.image_item.addAnnotation(ann)
            self.loadCheck(self.image_item)

    def onImageItemChanged(self, image_item):
        self.hasitemflag = False
        self.loadCheck(image_item)

class MaskCheckBoxItem(QGroupBox):
    def __init__(self, config, parent=None):
        QGroupBox.__init__(self, title=config['text'])
        self.labelclass = config['text']
        self._item = None
        self.items = config['items']
        self.checkitems = {}
        self.setupGui()

    def setupGui(self):
        self.layout = QVBoxLayout()
        for i in self.items:
            checkbox = QCheckBox(i)
            checkbox.setTristate()
            checkbox.stateChanged.connect(self.changeCheck)
            self.checkitems[i] = checkbox
            self.layout.addWidget(checkbox)
        self.setLayout(self.layout)
        self.resetCheck()

    def changeCheck(self, _):
        if self._item is None:
            return
        else:
            ann = {}
            for text, item in self.checkitems.items():
                ann.update({text: item.checkState})
            self._item.updateTo(self.labelclass, ann)

    def resetCheck(self):
        for item in self.checkitems.values():
            item.stateChanged.disconnect(self.changeCheck)
            item.setCheckState(1)
            item.stateChanged.connect(self.changeCheck)

    def loadCheck(self):
        if self._item is None:
            self.resetIndex()
            return
        if not self._item.isSelected():
            self.resetCheck()
            self._item = None
            return
        check = self._item.dataTo(self.labelclass)
        if check == '':
            self.resetCheck()
            return
        else:
            for text, item in self.checkitems.items():
                item.stateChanged.disconnect(self.changeCheck)
                tmp = check[text]
                item.setCheckState(tmp)
                item.stateChanged.connect(self.changeCheck)
