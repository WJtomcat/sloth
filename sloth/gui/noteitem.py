from PyQt4.QtGui import *
from sloth.annotations.model import *

class NoteItem(QTextEdit):
    def __init__(self, parent=None, default_properties=None):
        QTextEdit.__init__(self, parent)
        self.hasitemflag = False
        self.labelclass = 'notes'
        self._prefix = ''
        self._default_properties = {}
        self.image_item = None
        self.textChanged.connect(self.inputupdate)

    def loadNote(self, image_item):
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
            self.textChanged.disconnect(self.inputupdate)
            text = child['text']
            self.setText(text)
            self.textChanged.connect(self.inputupdate)
            self.hasitemflag = True
            return
        self.resetNote()

    def resetNote(self):
        self.textChanged.disconnect(self.inputupdate)
        self.setText('')
        self.textChanged.connect(self.inputupdate)

    def inputupdate(self):
        if self.image_item is None:
            return
        text = unicode(self.toPlainText())
        if self.hasitemflag:
            self.child['text'] = text

        else:
            ann = {}
            ann.update({
                self._prefix + 'class': self.labelclass,
                self._prefix + 'text': text
            })
            ann.update(self._default_properties)
            self.image_item.addAnnotation(ann)
            lenth = len(self.image_item.children())
            for row in range(0, lenth):
                child = self.image_item.childAt(row)
                if not isinstance(child, AnnotationModelItem):
                    continue
                try:
                    if child['class'] != self.labelclass:
                        continue
                except KeyError:
                    LOG.debug('Could not find key class in annotation item. Skipping this item. Please check your label file.')
                self.child = child
                self.hasitemflag = True
                return


class MaskNoteItem(QTextEdit):
    def __init__(self, parent=None, default_properties=None):
        QTextEdit.__init__(self, parent)
        self._item = None
        self.textChanged.connect(self.inputupdate)

    def onItemChanged(self, item):
        self._item = item
        self.loadNote()

    def loadNote(self):
        if self._item is None:
            self.resetNote()
            return
        if not self._item.isSelected():
            self.resetNote()
            self._item = None
            return
        note = self._item.dataToNote()
        if note == '':
            self.resetNote()
            return
        else:
            self.setText(note)

    def inputupdate(self):
        if self._item is None:
            return
        text = unicode(self.toPlainText())
        self._item.updateModel(note=text)

    def resetNote(self):
        self.textChanged.disconnect(self.inputupdate)
        self.setText('')
        self.textChanged.connect(self.inputupdate)
