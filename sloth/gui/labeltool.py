#!/usr/bin/python
import logging, os
import functools
import fnmatch
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import  PyQt5.uic as uic
from sloth.gui import qrc_icons  # needed for toolbar icons
from sloth.gui.propertyeditor import PropertyEditor
from sloth.gui.annotationscene import AnnotationScene
from sloth.gui.frameviewer import GraphicsView
from sloth.gui.controlbuttons import ControlButtonWidget
from sloth.gui.itemeditor import ItemEditor
from sloth.gui.imageinfo import ImageInfo
from sloth.conf import config
from sloth.core.utils import import_callable
from sloth.annotations.model import AnnotationTreeView, FrameModelItem, ImageFileModelItem, CopyAnnotations, InterpolateRange, \
    DicomImageModelItem
from sloth import APP_NAME, ORGANIZATION_DOMAIN
from sloth.utils.bind import bind, compose_noargs
import hashlib
from sloth.gui.readjson import readjson

GUIDIR=os.path.join(os.path.dirname(__file__))

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

handler = logging.FileHandler('logging.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
LOG.addHandler(handler)

LOG.debug("loading labeltool.py(gui)")

class BackgroundLoader(QObject):
    finished = pyqtSignal()

    def __init__(self, model, statusbar, progress):
        QObject.__init__(self)
        self._max_levels = 3
        self._model = model
        self._statusbar = statusbar
        self._message_displayed = False
        self._progress = progress
        self._progress.setMinimum(0)
        self._progress.setMaximum(1000 * self._max_levels)
        self._progress.setMaximumWidth(150)

        self._level = 1
        self._iterator = self._model.iterator(maxlevels=self._level)
        self._pos = 0
        self._rows = self._model.root().rowCount() + 1
        self._next_rows = 0

    def load(self):
        if not self._message_displayed:
            self._statusbar.showMessage("Loading annotations...", 5000)
            self._message_displayed = True
        if self._level <= self._max_levels and self._rows > 0:
            try:
                item = next(self._iterator)
                self._next_rows += item.rowCount()
                self._pos += 1
                self._progress.setValue(int((float(self._pos) / float(self._rows) + self._level - 1) * 1000))
            except StopIteration:
                self._level += 1
                self._iterator = self._model.iterator(maxlevels=self._level)
                self._pos = 0
                self._rows = self._next_rows
                self._next_rows = 1
        else:
            LOG.debug("Loading finished...")
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self, labeltool, parent=None):
        QMainWindow.__init__(self, parent)

        self.idletimer = QTimer()
        self.loader = None

        self.labeltool = labeltool
        self.setupGui()
        self.loadApplicationSettings()
        self.onAnnotationsLoaded()

    # Slots
    def onPluginLoaded(self, action):
        self.ui.menuPlugins.addAction(action)

    def onStatusMessage(self, message=''):
        self.statusBar().showMessage(message, 5000)

    def onModelDirtyChanged(self, dirty):
        postfix = "[+]" if dirty else ""
        if self.labeltool.getCurrentFilename() is not None:
            self.setWindowTitle("%s - %s %s" % \
                (APP_NAME, QFileInfo(self.labeltool.getCurrentFilename()).fileName(), postfix))
        else:
            self.setWindowTitle("%s - Unnamed %s" % (APP_NAME, postfix))

    def onMousePositionChanged(self, x, y):
        self.posinfo.setText("%d, %d" % (x, y))

    def startBackgroundLoading(self):
        self.stopBackgroundLoading(forced=True)
        self.loader = BackgroundLoader(self.labeltool.model(), self.statusBar(), self.sb_progress)
        self.idletimer.timeout.connect(self.loader.load)
        self.loader.finished.connect(self.stopBackgroundLoading)
        self.statusBar().addWidget(self.sb_progress)
        self.sb_progress.show()
        self.idletimer.start()

    def stopBackgroundLoading(self, forced=False):
        if not forced:
            self.statusBar().showMessage("Background loading finished", 5000)
        self.idletimer.stop()
        if self.loader is not None:
            self.idletimer.timeout.disconnect(self.loader.load)
            self.statusBar().removeWidget(self.sb_progress)
            self.loader = None

    def onAnnotationsLoaded(self):
        self.labeltool.model().dirtyChanged.connect(self.onModelDirtyChanged)
        self.onModelDirtyChanged(self.labeltool.model().dirty())
        self.treeview.setModel(self.labeltool.model())
        self.scene.setModel(self.labeltool.model())
        self.selectionmodel = QItemSelectionModel(self.labeltool.model())
        self.treeview.setSelectionModel(self.selectionmodel)
        self.treeview.selectionModel().currentChanged.connect(self.labeltool.setCurrentImage)
        self.property_editor.onModelChanged(self.labeltool.model())
        self.startBackgroundLoading()

    def onCurrentImageChanged(self):
        new_image = self.labeltool.currentImage()
        self.scene.setCurrentImage(new_image)

        self.itemEditor.onImageItemChanged(new_image)
        self.property_editor.onImageItemChanged(new_image)
        self.imageinfo.onImageItemChanged(new_image)
        self.onFitToWindowModeChanged()
        self.treeview.scrollTo(new_image.index())

        if isinstance(new_image, DicomImageModelItem):
            img = self.labeltool.getDcmImage(new_image)
        else:
            img = self.labeltool.getImage(new_image)

        if img is None:
            self.controls.setFilename("")
            self.selectionmodel.setCurrentIndex(new_image.index(), QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
            return

        h = img.shape[0]
        w = img.shape[1]
        self.image_resolution.setText("%dx%d" % (w, h))

        # TODO: This info should be obtained from AnnotationModel or LabelTool
        if isinstance(new_image, FrameModelItem):
            self.controls.setFrameNumAndTimestamp(new_image.framenum(), new_image.timestamp())
        elif isinstance(new_image, ImageFileModelItem):
            self.controls.setFilename(os.path.basename(new_image['filename']))

        self.selectionmodel.setCurrentIndex(new_image.index(), QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

    def onFitToWindowModeChanged(self):
        if self.options["Fit-to-window mode"].isChecked():
            self.view.fitInView()

    def onEnumerateCornersModeChanged(self):
        if self.options["Enumerate-corners mode"].isChecked():
            self.scene.enumerateCorners()
            self.onCurrentImageChanged()
        else:
            self.scene.removeCorners()
            self.onCurrentImageChanged()

    def onCopyAnnotationsModeChanged(self):
        if self.annotationMenu["Copy from previous"].isChecked():
            self.copyAnnotations.copy()
            self.annotationMenu["Copy from previous"].setChecked(False)

    def onInterpolateRangeModeChanged(self):
        if self.annotationMenu["Interpolate range"].isChecked():
            self.interpolateRange.interpolateRange()
            self.annotationMenu["Interpolate range"].setChecked(False)

    def onScaleChanged(self, scale):
        self.zoominfo.setText("%.2f%%" % (100 * scale, ))
        self.scene.scaleChanged(scale)

    def initShortcuts(self, HOTKEYS):
        self.shortcuts = []

        for hotkey in HOTKEYS:
            assert len(hotkey) >= 2
            key = hotkey[0]
            fun = hotkey[1]
            desc = ""
            if len(hotkey) > 2:
                desc = hotkey[2]
            if type(fun) == str:
                fun = import_callable(fun)

            hk = QAction(desc, self)
            hk.setShortcut(QKeySequence(key))
            hk.setEnabled(True)
            if hasattr(fun, '__call__'):
                hk.triggered.connect(bind(fun, self.labeltool))
            else:
                hk.triggered.connect(compose_noargs([bind(f, self.labeltool) for f in fun]))
            self.ui.menuShortcuts.addAction(hk)
            self.shortcuts.append(hk)

    def initOptions(self):
        self.options = {}
        for o in ["Fit-to-window mode"]:
            action = QAction(o, self)
            action.setCheckable(True)
            self.ui.menuOptions.addAction(action)
            self.options[o] = action

        for o in ["Enumerate-corners mode"]:
            action = QAction(o, self)
            action.setCheckable(True)
            self.ui.menuOptions.addAction(action)
            self.options[o] = action

    def initAnnotationMenu(self):
        self.annotationMenu = {}
        for a in ["Copy from previous"]:
            action = QAction(a, self)
            action.setCheckable(True)
            self.ui.menuAnnotation.addAction(action)
            self.annotationMenu[a] = action

        for a in ["Interpolate range"]:
            action = QAction(a, self)
            action.setCheckable(True)
            self.ui.menuAnnotation.addAction(action)
            self.annotationMenu[a] = action



    ###
    ### GUI/Application setup
    ###___________________________________________________________________________________________
    def setupGui(self):
        self.ui = uic.loadUi(os.path.join(GUIDIR, "labeltool.ui"), self)

        # get inserters and items from labels
        # FIXME for handling the new-style config correctly
        inserters = dict([(label['attributes']['class'], label['inserter'])
                          for label in config.LABELS + config.DETAILS
                          if 'class' in label.get('attributes', {}) and 'inserter' in label])
        items = dict([(label['attributes']['class'], label['item'])
                      for label in config.LABELS + config.DETAILS
                      if 'class' in label.get('attributes', {}) and 'item' in label])

        # Property Editor
        self.property_editor = PropertyEditor(config)
        # self.ui.dockProperties.setWidget(self.property_editor)


        # self.tabwidget = QTabWidget()
        # self.tabwidget.addTab(self.property_editor, 'property_editor')
        #
        # self.itemEditor = ItemEditor(config, self.tabwidget)
        # # self.property_editor.setItemEditor(self.itemEditor)
        # self.tabwidget.addTab(self.itemEditor, 'item_editor')
        # # self.itemEditor.hide()
        # self.ui.dockProperties.setWidget(self.tabwidget)

        self.ui.dockProperties.setWidget(self.property_editor)
        self.itemEditor = ItemEditor(config, self)
        # self.property_editor.addItemEditor(self.itemEditor)

        self.imageinfo = ImageInfo(config)
        self.ui.dockImageInfo.setWidget(self.imageinfo)

        # Scene
        self.scene = AnnotationScene(self.labeltool, items=items, inserters=inserters)
        self.property_editor.insertionModeStarted.connect(self.scene.onInsertionModeStarted)
        self.property_editor.insertionModeEnded.connect(self.scene.onInsertionModeEnded)

        # SceneView
        self.view = GraphicsView(self)
        self.view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.view.setScene(self.scene)

        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.controls = ControlButtonWidget()
        #give functions as lambdas, or else they will be called with a bool as parameter
        self.controls.back_button.clicked.connect(lambda lt: self.labeltool.gotoPrevious())
        self.controls.forward_button.clicked.connect(lambda lt: self.labeltool.gotoNext())

        self.central_layout.addWidget(self.controls)
        self.central_layout.addWidget(self.view)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.initShortcuts(config.HOTKEYS)
        self.initOptions()
        self.initAnnotationMenu()

        self.treeview = AnnotationTreeView()
        self.treeview.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.ui.dockAnnotations.setWidget(self.treeview)

        self.scene.selectionChanged.connect(self.scene.onSelectionChanged)
        self.treeview.selectedItemsChanged.connect(self.scene.onSelectionChangedInTreeView)

        self.scene.itemChanged.connect(self.itemEditor.onItemChanged)
        self.scene.itemDisSelected.connect(self.itemEditor.onItemDisSelected)

        self.posinfo = QLabel("-1, -1")
        self.posinfo.setFrameStyle(QFrame.StyledPanel)
        self.statusBar().addPermanentWidget(self.posinfo)
        self.scene.mousePositionChanged.connect(self.onMousePositionChanged)

        self.image_resolution = QLabel("[no image]")
        self.image_resolution.setFrameStyle(QFrame.StyledPanel)
        self.statusBar().addPermanentWidget(self.image_resolution)

        self.zoominfo = QLabel()
        self.zoominfo.setFrameStyle(QFrame.StyledPanel)
        self.statusBar().addPermanentWidget(self.zoominfo)
        self.view.scaleChanged.connect(self.onScaleChanged)
        self.onScaleChanged(self.view.getScale())

        self.sb_progress = QProgressBar()

        # View menu
        self.ui.menu_Views.addAction(self.ui.dockProperties.toggleViewAction())
        self.ui.menu_Views.addAction(self.ui.dockAnnotations.toggleViewAction())
        self.ui.menu_Views.addAction(self.ui.dockImageInfo.toggleViewAction())

        # Annotation menu
        self.copyAnnotations = CopyAnnotations(self.labeltool)
        self.interpolateRange = InterpolateRange(self.labeltool)

        # Show the UI.  It is important that this comes *after* the above
        # adding of custom widgets, especially the central widget.  Otherwise the
        # dock widgets would be far to large.
        self.ui.show()

        ## connect action signals
        self.connectActions()

    def connectActions(self):
        ## File menu
        self.ui.actionNew.    triggered.connect(self.fileNew)
        self.ui.actionOpen.   triggered.connect(self.fileOpen)
        self.ui.actionSave.   triggered.connect(self.fileSave)
        self.ui.actionSave_As.triggered.connect(self.fileSaveAs)
        self.ui.actionExit.   triggered.connect(self.close)

        ## View menu
        self.ui.actionLocked.toggled.connect(self.onViewsLockedChanged)

        ## Help menu
        self.ui.action_About.triggered.connect(self.about)

        ## Navigation
        self.ui.action_Add_ImageDir.triggered.connect(self.addDir)
        self.ui.action_Read_Jsons.triggered.connect(self.readJsons)
        self.ui.actionNext.      triggered.connect(self.labeltool.gotoNext)
        self.ui.actionPrevious.  triggered.connect(self.labeltool.gotoPrevious)
        self.ui.actionZoom_In.   triggered.connect(functools.partial(self.view.setScaleRelative, 1.2))
        self.ui.actionZoom_Out.  triggered.connect(functools.partial(self.view.setScaleRelative, 1/1.2))

        ## Connections to LabelTool
        self.labeltool.pluginLoaded.       connect(self.onPluginLoaded)
        self.labeltool.statusMessage.      connect(self.onStatusMessage)
        self.labeltool.annotationsLoaded.  connect(self.onAnnotationsLoaded)
        self.labeltool.currentImageChanged.connect(self.onCurrentImageChanged)

        ## options menu
        self.options["Fit-to-window mode"].changed.connect(self.onFitToWindowModeChanged)
        self.options["Enumerate-corners mode"].changed.connect(self.onEnumerateCornersModeChanged)

        ## annotation menu
        self.annotationMenu["Copy from previous"].changed.connect(self.onCopyAnnotationsModeChanged)
        self.annotationMenu["Interpolate range"].changed.connect(self.onInterpolateRangeModeChanged)

    def readJsons(self):
        path = '.'
        filename = self.labeltool.getCurrentFilename()
        if (filename is not None) and (len(filename) > 0):
            path = QFileInfo(filename).path()
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dirname = dialog.getExistingDirectory(self, "%s - Add Media File" % APP_NAME, path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks);
        readjson(dirname)


    def loadApplicationSettings(self):
        settings = QSettings()
        size   = settings.value("MainWindow/Size", QSize(800, 600))
        pos    = settings.value("MainWindow/Position", QPoint(10, 10))
        state  = settings.value("MainWindow/State")
        locked = settings.value("MainWindow/ViewsLocked", False)
        if isinstance(size,   QVariant): size  = size.toSize()
        if isinstance(pos,    QVariant): pos   = pos.toPoint()
        if isinstance(state,  QVariant): state = state.toByteArray()
        if isinstance(locked, QVariant): locked = locked.toBool()
        self.resize(size)
        self.move(pos)
        if state is not None:
                self.restoreState(state)
        self.ui.actionLocked.setChecked(bool(locked))

    def saveApplicationSettings(self):
        settings = QSettings()
        settings.setValue("MainWindow/Size",        self.size())
        settings.setValue("MainWindow/Position",    self.pos())
        settings.setValue("MainWindow/State",       self.saveState())
        settings.setValue("MainWindow/ViewsLocked", self.ui.actionLocked.isChecked())
        if self.labeltool.getCurrentFilename() is not None:
            filename = self.labeltool.getCurrentFilename()
        else:
            filename = None
        settings.setValue("LastFile", filename)

    def okToContinue(self):
        if self.labeltool.model().dirty():
            reply = QMessageBox.question(self,
                    "%s - Unsaved Changes" % (APP_NAME),
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.fileSave()
        return True

    def fileNew(self):
        if self.okToContinue():
            self.labeltool.clearAnnotations()

    def fileOpen(self):
        if not self.okToContinue():
            return
        path = '.'
        filename = self.labeltool.getCurrentFilename()
        if (filename is not None) and (len(filename) > 0):
            path = QFileInfo(filename).path()

        format_str = ' '.join(self.labeltool.getAnnotationFilePatterns())
        fname = QFileDialog.getOpenFileName(self,
                "%s - Load Annotations" % APP_NAME, path,
                "%s annotation files (%s)" % (APP_NAME, format_str))
        fname, _ = fname
        if len(str(fname)) > 0:
            self.labeltool.loadAnnotations(fname)

    def fileSave(self):
        filename = self.labeltool.getCurrentFilename()
        if filename is None:
            return self.fileSaveAs()
        return self.labeltool.saveAnnotations(filename)

    def fileSaveAs(self):
        fname = os.getcwd()  # self.annotations.filename() or '.'
        format_str = ' '.join(self.labeltool.getAnnotationFilePatterns())
        fname = QFileDialog.getSaveFileName(self,
                "%s - Save Annotations" % APP_NAME, fname,
                "%s annotation files (%s)" % (APP_NAME, format_str))

        fname, _ = fname

        if len(str(fname)) > 0:
            return self.labeltool.saveAnnotations(str(fname), todel=True)
        return False

    def getMd5(self, filename):
        return ''

    def addDir(self):
        path = '.'
        filename = self.labeltool.getCurrentFilename()
        if (filename is not None) and (len(filename) > 0):
            path = QFileInfo(filename).path()

        image_types = [ '*.jpg', '*.bmp', '*.png', '*.pgm', '*.ppm', '*.tiff', '*.tif', '*.gif']

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dirname = dialog.getExistingDirectory(self, "%s - Add Media File" % APP_NAME, path, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks);

        dirname = str(dirname)
        if dirname == '':
            return
        os.chdir(dirname)

        flag = True

        for filename in os.listdir(dirname):
            fname = os.path.join(dirname, filename)
            if os.path.isabs(fname):
                fname = os.path.relpath(fname, str(path))

            for pattern in image_types:
                if fnmatch.fnmatch(fname.lower(), pattern):
                    image_md5 = self.getMd5(fname)
                    item = self.labeltool.addImageFile(fname, image_md5)
                    if flag:
                        self.labeltool.setCurrentImage(item)
                        flag = False

            if fnmatch.fnmatch(fname.lower(), '*.dcm'):
                self.readDcm(fname)

    def readDcm(self, fname):
        md5 = self.getMd5(fname)
        dcm = dicom.read_file(fname, force=True)
        depth = dcm.pixel_array.shape[0]
        item = self.labeltool.addDicomFile(fname, md5, depth)


    def onViewsLockedChanged(self, checked):
        features = QDockWidget.AllDockWidgetFeatures
        if checked:
            features = QDockWidget.NoDockWidgetFeatures

        self.ui.dockProperties.setFeatures(features)
        self.ui.dockAnnotations.setFeatures(features)


    ###
    ### global event handling
    ###______________________________________________________________________________
    def closeEvent(self, event):
        if self.okToContinue():
            self.itemEditor.close()
            self.saveApplicationSettings()
        else:
            event.ignore()

    def about(self):
        QMessageBox.about(self, "About %s" % APP_NAME,
             """<b>%s</b> version %s
             <p>This labeling application for computer vision research
             was developed at the CVHCI research group at KIT.
             <p>For more details, visit our homepage: <a href="%s">%s</a>"""
              % (APP_NAME, __version__, ORGANIZATION_DOMAIN, ORGANIZATION_DOMAIN))
