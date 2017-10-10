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


class MaskComboItem(QComboBox):
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        self._item = None
        self.currentIndexChanged.connect(self.indexUpdate)
        self.addItem('default')
        self.addItem('A')
        self.addItem('B')
        self.addItem('C')
        self.addItem('D')

    def onItemChanged(self, item):
        self._item = item
        self.loadIndex()

    def loadIndex(self):
        if self._item is None:
            self.resetIndex()
            return
        if not self._item.isSelected():
            self.resetIndex()
            self._item = None
            return
        index = self._item.dataToIndex()
        self.currentIndexChanged.disconnect(self.indexUpdate)
        self.setCurrentIndex(index)
        self.currentIndexChanged.connect(self.indexUpdate)

    def indexUpdate(self):
        if self._item is None:
            return
        index = self.currentIndex()
        self._item.updateModel(index=index)

    def resetIndex(self):
        self.currentIndexChanged.disconnect(self.indexUpdate)
        self.setCurrentIndex(0)
        self.currentIndexChanged.connect(self.indexUpdate)
