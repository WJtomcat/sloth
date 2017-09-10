from PyQt4.QtGui import *
from sloth.annotations.model import *

class ComboItem(QComboBox):
    def __init__(self, config, parent=None, default_properties=None):
        QComboBox.__init__(self, parent)
        self.config = config
        self._prefix = ''
        self._default_properties = default_properties or {}
        self.labelclass = config['text']
        self.checkitems = config['items']
        self.image_item = None
        self.hasitemflag = False
        self.getClassesitem(config)
        self.currentIndexChanged.connect(self.changeClassesIndex)

    def getClassesitem(self, config):
        items = config['items']
        for i in items:
            self.addItem(i)

    def loadClasses(self, image_item):
        self.hasitemflag = False
        self.image_item = image_item
        if image_item is None:
            return

        lenth = len(image_item.children())
        for row in range(0, lenth):
            child = image_item.childAt(row)
            if not isinstance(child, AnnotationModelItem):
                continue
            try:
                if child['class'] != self.labelclass:
                    continue
            except KeyError:
                LOG.debug('Could not find key class in annotation item. Skipping this item. Please check your label file.')
            self.child = child
            classindex = child['index']
            self.currentIndexChanged.disconnect(self.changeClassesIndex)
            self.setCurrentIndex(classindex)
            self.currentIndexChanged.connect(self.changeClassesIndex)
            self.hasitemflag = True
            return
        self.resetClasses()

    def resetClasses(self):
        self.currentIndexChanged.disconnect(self.changeClassesIndex)
        self.setCurrentIndex(0)
        self.currentIndexChanged.connect(self.changeClassesIndex)

    def changeClassesIndex(self, index):
        if self.hasitemflag:
            self.child['index'] = index
        else:
            ann = {}
            ann.update({
                self._prefix + 'class': self.labelclass,
                self._prefix + 'index': index
            })
            ann.update(self._default_properties)
            self.image_item.addAnnotation(ann)
            self.loadClasses(self.image_item)

    #load Combo data when imageitem changed
    def onImageItemChanged(self, image_item):
        self.hasitemflag = False
        self.loadClasses(image_item)

    def comboboxChanged(self):
        tmp_index = self.currentIndex()
        self.changeClassesIndex(tmp_index)
