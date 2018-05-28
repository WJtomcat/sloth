"""This is the AnnotationScene module"""
from sloth.items import *
from sloth.core.exceptions import InvalidArgumentException
from sloth.annotations.model import AnnotationModelItem, ImageFileModelItem, DicomImageModelItem
from sloth.utils import toQImage
from sloth.conf import config
import logging
import functools
import time

LOG = logging.getLogger(__name__)


class AnnotationScene(QGraphicsScene):
    mousePositionChanged = pyqtSignal(float, float)
    itemChanged = pyqtSignal(PolygonItem)
    itemDisSelected = pyqtSignal()
    def __init__(self, labeltool, property_editor, items=None, inserters=None, parent=None):
        super(AnnotationScene, self).__init__(parent)

        self._model = None
        self._image_item = None
        self._inserter = None
        self._scene_item = None
        self._message = ""
        self._labeltool = labeltool

        self._itemfactory = Factory(items)
        self._inserterfactory = Factory(inserters)
        self._opaque = 0.6

        try:
            self.setBackgroundBrush(config.SCENE_BACKGROUND)
        except:
            self.setBackgroundBrush(Qt.darkGray)
        self.reset()
        self.inputflag = False
        self.inittime = None
        self.endtime = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.idletime)
        self.waitEvent = False

        self.selectionChanged.connect(self.onSelectionChanged)

        self.property_editor = property_editor
        self.finishButton = property_editor.finishButton
        self.deleteButton = property_editor.deleteButton
        self.finishButton.clicked.connect(self.onFinishButtonPressed)
        self.deleteButton.clicked.connect(self.onDeleteButtonPressed)

    def onFinishButtonPressed(self):
        if self._inserter is not None:
            self._inserter._removeLastPointAndFinish(self._image_item)
        else:
            self.finishButton.setEnabled(False)

    def onDeleteButtonPressed(self):
        self._labeltool.deleteSelectedAnnotations()

    #
    # getters/setters
    #
    def setModel(self, model):
        if model == self._model:
            # same model as the current one
            # reset caches anyway, invalidate root
            self.reset()
            return

        # disconnect old signals
        if self._model is not None:
            self._model.dataChanged.disconnect(self.dataChanged)
            self._model.rowsInserted.disconnect(self.rowsInserted)
            self._model.rowsAboutToBeRemoved.disconnect(self.rowsAboutToBeRemoved)
            self._model.rowsRemoved.disconnect(self.rowsRemoved)
            self._model.modelReset.disconnect(self.reset)

        self._model = model

        # connect new signals
        if self._model is not None:
            self._model.dataChanged.connect(self.dataChanged)
            self._model.rowsInserted.connect(self.rowsInserted)
            self._model.rowsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved)
            self._model.rowsRemoved.connect(self.rowsRemoved)
            self._model.modelReset.connect(self.reset)

        # reset caches, invalidate root
        self.reset()

    def sceneItem(self):
        return self._scene_item

    def setCurrentImage(self, current_image):
        """
        Set the index of the model which denotes the current image to be
        displayed by the scene.  This can be either the index to a frame in a
        video, or to an image.
        """
        if current_image == self._image_item:
            return

        if self.inputflag:
            self.setEndtime()
            self.addTime()
            self.inputflag = False

        if self._inserter is not None:
            self._inserter.abort()

        if current_image is None:
            self.clear()
            self._image_item = None
            self._image      = None
            self._pixmap     = None
        else:
            self.clear()
            self._image_item = current_image
            self._opaque = 0.6
            current_image._seen = True
            assert self._image_item.model() == self._model
            if isinstance(self._image_item, DicomImageModelItem):
                self._image =self._labeltool.getDcmImage(self._image_item)
            elif isinstance(self._image_item, ImageFileModelItem):
                self._image      = self._labeltool.getImage(self._image_item)
            self._pixmap     = QPixmap(toQImage(self._image))
            self._scene_item = QGraphicsPixmapItem(self._pixmap)
            self._scene_item.setZValue(-1)
            self.setSceneRect(0, 0, self._pixmap.width(), self._pixmap.height())
            self.addItem(self._scene_item)
            self.insertItems(0, len(self._image_item.children())-1, edit=True)
            self.update()

    def insertItems(self, first, last, edit=False):
        if self._image_item is None:
            return

        assert self._model is not None

        # create a graphics item for each model index
        for row in range(first, last+1):
            child = self._image_item.childAt(row)
            if not isinstance(child, AnnotationModelItem):
                continue
            try:
                label_class = child['class']
            except KeyError:
                LOG.debug('Could not find key class in annotation item. Skipping this item. Please check your label file.')
                continue
            item = self._itemfactory.create(label_class, child)
            if item is not None:
                self.addItem(item)
                if isinstance(item, PolygonItem):
                    item.opaqueChanged(self._opaque)
                if not edit:
                    item.setSelected(True)
            else:
                LOG.debug("Could not find item for annotation with class '%s'" % label_class)

    def deleteSelectedItems(self):
        # some (graphics) items may share the same model item
        # therefore we need to determine the unique set of model items first
        # must use a dict for hashing instead of a set, because objects are not hashable
        modelitems_to_delete = dict((id(item.modelItem()), item.modelItem()) for item in self.selectedItems())
        for item in modelitems_to_delete.values():
            item.delete()

    def onSliderChanged(self, value):
        opaque = float(value)/100
        self._opaque = opaque
        for item in self.items():
            if isinstance(item, PolygonItem):
                item.opaqueChanged(self._opaque)

    def onCheckChanged(self, state):
        if state == Qt.Checked:
            for item in self.items():
                if isinstance(item, PolygonItem):
                    self.removeItem(item)

        elif state == Qt.Unchecked:
            for item in self.items():
                if isinstance(item, PolygonItem):
                    self.removeItem(item)
            self.insertItems(0, len(self._image_item.children())-1)


    def onInserterFinished(self):
        self.finishButton.setEnabled(False)
        self.sender().inserterFinished.disconnect(self.onInserterFinished)
        self._labeltool.currentImageChanged.disconnect(self.sender().imageChange)
        self._labeltool.exitInsertMode()
        self._inserter = None

    def onInsertionModeStarted(self, label_class):
        # Abort current inserter
        if self._inserter is not None:
            self._inserter.abort()

        self.deselectAllItems()

        if not self.inputflag:
            self.inputflag = True
            self.inittime = time.ctime()
            self.timer.start(60000)

        # Add new inserter
        default_properties = self._labeltool.propertyeditor().currentEditorProperties()
        inserter = self._inserterfactory.create(label_class, self._labeltool, self, default_properties)
        if inserter is None:
            raise InvalidArgumentException("Could not find inserter for class '%s' with default properties '%s'" % (label_class, default_properties))
        if isinstance(inserter, FreehandItemInserter):
            inserter.setColorMap(label_class)
        inserter.inserterFinished.connect(self.onInserterFinished)
        self._labeltool.currentImageChanged.connect(inserter.imageChange)
        self._inserter = inserter
        scale = self._labeltool.mainWindow().view.getScale()
        self._inserter.setScale(scale)
        LOG.debug("Created inserter for class '%s' with default properties '%s'" % (label_class, default_properties))
        # Change cursor to cross
        self.views()[0].viewport().setCursor(Qt.CrossCursor)
        self.finishButton.setEnabled(True)


    def onInsertionModeEnded(self):
        if self.inputflag:
            tmptime = self._image_item['time']
            if len(tmptime) > 0 and self.inittime == tmptime[-1][0]:
                self.endtime = time.ctime()
                tmptime[-1][-1] = self.endtime
                self._image_item.update({'time' : tmptime})
            else:
                self.endtime = time.ctime()
                tmptime.append([self.inittime, self.endtime])
                self._image_item.update({'time' : tmptime})
        if self._inserter is not None:
            self._inserter.abort()
        self.views()[0].viewport().setCursor(Qt.ArrowCursor)

    def setEndtime(self):
        self.endtime = time.ctime()

    def setInittime(self):
        self.inittime = time.ctime()

    def addTime(self):
        if self._image_item is None:
            return
        tmptime = self._image_item['time']
        if len(tmptime) > 0 and tmptime[-1][0] == self.inittime:
            self.endtime = time.ctime()
            tmptime[-1][-1] = self.endtime
            self._image_item.update({'time' : tmptime})
        else:
            self.endtime = time.ctime()
            tmptime.append([self.inittime, self.endtime])
            self._image_item.update({'time' : tmptime})
        self.inittime = None
        self.endtime = None

    def idletime(self):
        if not self.inputflag and not self.waitEvent:
            return
        self.endtime = time.ctime()
        self.addTime()
        if self._inserter is not None:
            self.waitEvent = True
        else:
            self.inputflag = False

    def scaleChanged(self, scale):
        if self._inserter is not None:
            self._inserter.onScaleChanged(scale)

    #
    # common methods
    #
    def reset(self):
        self.clear()
        self.setCurrentImage(None)
        self.clearMessage()

    def clear(self):
        # do not use QGraphicsScene.clear(self) so that the underlying
        # C++ objects are not deleted if there is still another python
        # reference to the item somewhere else (e.g. in an inserter)
        for item in self.items():
            if item.parentItem() is None:
                self.removeItem(item)
        self._scene_item = None

    def addItem(self, item):
        QGraphicsScene.addItem(self, item)
        # TODO emit signal itemAdded

    #
    # mouse event handlers
    #
    def mousePressEvent(self, event):
        LOG.debug("mousePressEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        self.timer.start(60000)
        if self.waitEvent:
            self.inittime = time.ctime()
            self.waitEvent = False
        if self._inserter is not None:
            if not self.sceneRect().contains(event.scenePos()) and \
               not self._inserter.allowOutOfSceneEvents():
                # ignore events outside the scene rect
                return
            # insert mode
            if not self._inserter.mousePressEvent(event, self._image_item):
                QGraphicsScene.mousePressEvent(self,event)
        else:
            # selection mode
            QGraphicsScene.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        LOG.debug("mouseDoubleClickEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        self.timer.start(60000)
        if self.waitEvent:
            self.inittime = time.ctime()
            self.waitEvent = False
        if self._inserter is not None:
            if not self.sceneRect().contains(event.scenePos()) and \
                    not self._inserter.allowOutOfSceneEvents():
                # ignore events outside the scene rect
                return
            # insert mode
            self._inserter.mouseDoubleClickEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseDoubleClickEvent(self, event)

    def mouseReleaseEvent(self, event):
        LOG.debug("mouseReleaseEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        self.timer.start(60000)
        if self.waitEvent:
            self.inittime = time.ctime()
            self.waitEvent = False
        if self._inserter is not None:
            # insert mode
            self._inserter.mouseReleaseEvent(event, self._image_item)
        else:
            # selection mode
            QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        self.timer.start(60000)
        if self.waitEvent:
            self.inittime = time.ctime()
            self.waitEvent = False
        sp = event.scenePos()
        self.mousePositionChanged.emit(sp.x(), sp.y())
        #LOG.debug("mouseMoveEvent %s %s" % (self.sceneRect().contains(event.scenePos()), event.scenePos()))
        if self._inserter is not None:
            # insert mode
            if not self._inserter.mouseMoveEvent(event, self._image_item):
                QGraphicsScene.mouseMoveEvent(self, event)
        else:
            # selection mode
            QGraphicsScene.mouseMoveEvent(self, event)

    def deselectAllItems(self):
        for item in self.items():
            item.setSelected(False)

    def onSelectionChanged(self):
        if self._inserter is not None:
            return
        if len(self.selectedItems()) == 1:
            for item in self.selectedItems():
                if isinstance(item, PolygonItem):
                    self.itemChanged.emit(item)
            self.deleteButton.setEnabled(True)
        if len(self.selectedItems()) == 0:
            self.itemDisSelected.emit()
            self.deleteButton.setEnabled(False)
        model_items = [item.modelItem() for item in self.selectedItems()]
        self._labeltool.treeview().setSelectedItems(model_items)
        self.editSelectedItems()

    def onSelectionChangedInTreeView(self, model_items):
        block = self.blockSignals(True)
        selected_items = set()
        for model_item in model_items:
            for item in self.itemsFromIndex(model_item.index()):
                selected_items.add(item)
        for item in self.items():
            item.setSelected(False)
        for item in selected_items:
            if item is not None:
                item.setSelected(True)
        self.blockSignals(block)
        # self.editSelectedItems()

    def editSelectedItems(self):
        scene_items = self.selectedItems()
        if self._inserter is None or len(scene_items) > 0:
            items = [item.modelItem() for item in scene_items]
            self._labeltool.propertyeditor().startEditMode(items)

    #
    # key event handlers
    #
    def selectNextItem(self, reverse=False):
        # disable inserting
        # TODO: forward this to the ButtonArea
        self._inserter = None

        # set focus to the view, so that subsequent keyboard events are forwarded to the scene
        if len(self.views()) > 0:
            self.views()[0].setFocus(True)

        # get the current selected item if there is any
        selected_item = None
        found = True
        if len(self.selectedItems()) > 0:
            selected_item = self.selectedItems()[0]
            selected_item.setSelected(False)
            found = False

        items = [item for item in self.items()
                 if item.flags() & QGraphicsItem.ItemIsSelectable] * 2
        if reverse:
            items.reverse()

        for item in items:
            if item is selected_item:
                found = True
                continue

            if found and item is not selected_item:
                item.setSelected(True)
                break

    def selectAllItems(self):
        for item in self.items():
            item.setSelected(True)

    def keyPressEvent(self, event):
        LOG.debug("keyPressEvent %s" % event)
        self.timer.start(60000)
        if self.waitEvent:
            self.inittime = time.ctime()
            self.waitEvent = False

        if self._model is None or self._image_item is None:
            event.ignore()
            return

        if self._inserter is not None:
            # insert mode
            self._inserter.keyPressEvent(event, self._image_item)
        else:
            # selection mode
            if event.key() == Qt.Key_Delete:
                self.deleteSelectedItems()
                event.accept()

            elif event.key() == Qt.Key_Escape:
                # deselect all selected items
                for item in self.selectedItems():
                    item.setSelected(False)
                event.accept()

            elif len(self.selectedItems()) > 0:
                for item in self.selectedItems():
                    item.keyPressEvent(event)

        QGraphicsScene.keyPressEvent(self, event)

    #
    # slots for signals from the model
    # this is the implemenation of the scene as a view of the model
    #
    def dataChanged(self, indexFrom, indexTo):
        if self._image_item is None or self._image_item.index() != indexFrom.parent().parent():
            return

        item = self.itemFromIndex(indexFrom.parent())
        if item is not None:
            item.dataChanged()

    def rowsInserted(self, index, first, last):
        if self._image_item is None or self._image_item.index() != index:
            return

        self.insertItems(first, last)

    def rowsAboutToBeRemoved(self, index, first, last):
        if self._image_item is None or self._image_item.index() != index:
            return

        for row in range(first, last+1):
            items = self.itemsFromIndex(index.child(row, 0))
            for item in items:
                # if the item has a parent item, do not delete it
                # we assume, that the parent shares the same model index
                # and thus removing the parent will also remove the child
                if item.parentItem() is not None:
                    continue
                self.removeItem(item)

    def rowsRemoved(self, index, first, last):
        pass

    def itemFromIndex(self, index):
        for item in self.items():
            # some graphics items will not have an index method,
            # we just skip these
            if hasattr(item, 'index') and item.index() == index:
                return item
        return None

    def itemsFromIndex(self, index):
        items = []
        for item in self.items():
            # some graphics items will not have an index method,
            # we just skip these
            if hasattr(item, 'index') and item.index() == index:
                items.append(item)
        return items

    #
    # message handling and displaying
    #
    def setMessage(self, message):
        if self._message is not None:
            self.clearMessage()

        if message is None or message == "":
            return

        self._message = message.replace('\n', '<br />')
        self._message_text_item = QGraphicsTextItem()
        self._message_text_item.setHtml(self._message)
        self._message_text_item.setPos(20, 20)
        self.invalidate(QRectF(), QGraphicsScene.ForegroundLayer)

    def clearMessage(self):
        if self._message is not None:
            self._message_text_item = None
            self._message = None
            self.invalidate(QRectF(), QGraphicsScene.ForegroundLayer)

    def drawForeground(self, painter, rect):
        QGraphicsScene.drawForeground(self, painter, rect)

        if self._message is not None:
            assert self._message_text_item is not None

            painter.setTransform(QTransform())
            painter.setBrush(QColor('lightGray'))
            painter.setPen(QPen(QBrush(QColor('black')), 2))

            br = self._message_text_item.boundingRect()

            painter.drawRoundedRect(QRectF(10, 10, br.width()+20, br.height()+20), 10.0, 10.0)
            painter.setTransform(QTransform.fromTranslate(20, 20))
            painter.setPen(QPen(QColor('black'), 1))

            self._message_text_item.paint(painter, QStyleOptionGraphicsItem(), None)

    #
    # utility functions
    #

    # enumerate polygon annotation corners and rectangle annotation corners
    def enumerateCorners(self):
        # calculate font size
        fontsize = (self._pixmap.width()+self._pixmap.height())/150

        # decorate the paint() method with our enumerating paint
        self.enumeratePolygonItems(fontsize)
        self.enumerateRectItems(fontsize)

        self.reset()

    def enumeratePolygonItems(self, fontsize):
        oldpaint = PolygonItem.paint

        def paint(self, painter, option, widget=None):
            oldpaint(self, painter, option, widget)
            painter.setFont(QFont("Arial", fontsize))
            for i, p in enumerate(self._polygon):
                painter.drawText(p, str(i))

        functools.update_wrapper(paint, oldpaint)
        PolygonItem.paint = paint

    def enumerateRectItems(self, fontsize):
        oldpaint = RectItem.paint

        def paint(self, painter, option, widget=None):
            oldpaint(self, painter, option, widget)
            painter.setFont(QFont("Arial", fontsize))
            painter.drawText(0-fontsize, 0, str(0))
            painter.drawText(self._rect.width()+fontsize/2, 0, str(1))
            painter.drawText(self._rect.width()+fontsize/2, self._rect.height(), str(2))
            painter.drawText(0-fontsize, self._rect.height(), str(3))

        functools.update_wrapper(paint, oldpaint)
        RectItem.paint = paint

    # disable annotation corners enumeration
    def removeCorners(self):
        self.removePolygonEnumeration()
        self.removeRectEnumeration()

        self.reset()

    def removePolygonEnumeration(self):
        oldpaint = PolygonItem.paint

        def paint(self, painter, option, widget=None):
            BaseItem.paint(self, painter, option, widget)

            pen = self.pen()
            if self.isSelected():
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)

            for k in range(-1, len(self._polygon)-1):
                p1 = self._polygon[k]
                p2 = self._polygon[k+1]
                painter.drawLine(p1, p2)

        functools.update_wrapper(paint, oldpaint)
        PolygonItem.paint = paint

    def removeRectEnumeration(self):
        oldpaint = RectItem.paint

        def paint(self, painter, option, widget=None):
            BaseItem.paint(self, painter, option, widget)

            pen = self.pen()
            if self.isSelected():
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())

        functools.update_wrapper(paint, oldpaint)
        RectItem.paint = paint
