#coding=utf-8
# This is sloth's default configuration.
#
# The configuration file is a simple python module with module-level
# variables.  This module contains the default values for sloth's
# configuration variables.
#
# In all cases in the configuration where a python callable (such as a
# function, class constructor, etc.) is expected, it is equally possible
# to specify a module path (as string) pointing to such a python callable.
# It will then be automatically imported.

# LABELS
#
# List/tuple of dictionaries that defines the label classes
# that are handled by sloth.  For each label, there should
# be one dictionary that contains the following keys:
#
#   - 'item' : Visualization item for this label. This can be
#              any python callable or a module path string
#              implementing the visualization item interface.
#
#   - 'inserter' : (optional) Item inserter for this label.
#                  If the user selects to insert a new label of this class
#                  the inserter is responsible to actually
#                  capture the users mouse actions and insert
#                  a new label into the annotation model.
#
#   - 'hotkey' : (optional) A keyboard shortcut starting
#                the insertion of a new label of this class.
#
#   - 'attributes' : (optional) A dictionary that defines the
#                    keys and possible values of this label
#                    class.
#
#   - 'text' : (optional) A label for the item's GUI button.
LABELS = (
    {
        'attributes': {
            'class':    '1p',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'p',
        'menu':     u'1p',
        'text':     u'1p(p)',
    },
    {
        'attributes': {
            'class':    '1s',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'n',
        'menu':     u'1s',
        'text':     u'1s(s)',
    },
    {
        'attributes': {
            'class':    'IIa',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'a',
        'menu':     u'IIa',
        'text':     u'IIa(a)',
    },
    {
        'attributes': {
            'class':    'IIb',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'b',
        'menu':     u'IIb',
        'text':     u'IIb(b)',
    },
    {
        'attributes': {
            'class':    'IIc',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'c',
        'menu':     u'IIc',
        'text':     u'IIc(c)',
    },
    {
        'attributes': {
            'class':    'III',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   '3',
        'menu':     u'III',
        'text':     u'III(3)',
    },
    {
        'attributes': {
            'class':    'IIa+IIc',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   '4',
        'menu':     u'IIa+IIc',
        'text':     u'IIa+IIc(4)',
    },
    {
        'attributes': {
            'class':    'LQ',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'p',
        'menu':     u'隆起型',
        'text':     u'隆起型(p)',
    },
    {
        'attributes': {
            'class':    'JBK',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'u',
        'menu':     u'局部溃疡型',
        'text':     u'局部溃疡型(u)',
    },
    {
        'attributes': {
            'class':    'JRK',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'i',
        'menu':     u'浸润溃疡型',
        'text':     u'浸润溃疡型(i)',
    },
    {
        'attributes': {
            'class':    'MJ',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'd',
        'menu':     u'弥漫浸润型',
        'text':     u'弥漫浸润型(d)',
    },
    {
        'attributes': {
            'class':    'NX',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   's',
        'menu':     u'粘膜下瘤变',
        'text':     u'粘膜下瘤变(s)',
    },
    {
        'attributes': {
            'class':    'Eraser',
        },
        'inserter': 'sloth.items.FreehandEraser',
        'hotkey':   'Ctrl+e',
        'menu':     u'橡皮檫',
        'text':     u'橡皮檫(e)',
    },
)

DETAILS = (
    {
        'attributes': {
            'class':    'XQ',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'v',
        'menu':     u'血管缺失',
        'text':     u'血管缺失(v)',
    },
    {
        'attributes': {
            'class':    'ZJ',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'f',
        'menu':     u'皱壁集中',
        'text':     u'皱壁集中(f)',
    },
    {
        'attributes': {
            'class':    'FB',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'w',
        'menu':     u'发白',
        'text':     u'发白(w)',
    },
    {
        'attributes': {
            'class':    'FH',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'r',
        'menu':     u'发红',
        'text':     u'发红(r)',
    },
    {
        'attributes': {
            'class':    'CX',
        },
        'inserter': 'sloth.items.FreehandItemInserter',
        'item':     'sloth.items.PolygonItem',
        'hotkey':   'b',
        'menu':     u'出血',
        'text':     u'出血(b)',
    },
)

NOTES = [u'备注']

INPUTLINE = []

ITEMLINES = [u'病变大小W', u'病变大小H', u'病变大小D', u'浸润深度']

COMBOCLASS= (
    {
        'text':     u'图片类型',
        'items':     [u'白光', u'窄带光', u'超声', u'其他'],
    },
)

CHECKBOX = []


ITEMNOTES = []

ITEMCOMBOCLASS= (
    {
        'text':     u'病理主要分类',
        'items':     [u'病理分类', u'炎症及其他', u'低级别上皮内瘤变', u'高级别上皮内瘤变', u'早癌-粘膜层', u'早癌-粘膜下层', u'进展期癌'],
    },
    {
        'text':     u'病理次要分类',
        'items':     [u'病理分类', u'炎症及其他', u'低级别上皮内瘤变', u'高级别上皮内瘤变', u'早癌-粘膜层', u'早癌-粘膜下层', u'进展期癌'],
    },
)

ITEMCHECKBOX= (
)

def color_map(N=256):
    def bitget(byteval, idx):
        return ((byteval & (1 << idx)) != 0)
    cmap = []
    for i in range(N):
        r = g = b = 0
        c = i
        for j in range(8):
            r = r | (bitget(c, 0) << 7-j)
            g = g | (bitget(c, 1) << 7-j)
            b = b | (bitget(c, 2) << 7-j)
            c = c >> 3
        cmap.append([r, g, b])
    return cmap

cmap = color_map()
COLORMAP = {
    'Eraser':   cmap[0],
    '1p':       cmap[1],
    '1s':       cmap[2],
    'IIa':      cmap[3],
    'IIb':      cmap[4],
    'IIc':      cmap[9],
    'III':      cmap[10],
    'IIa+IIc':  cmap[11],
    'LQ':       cmap[12],
    'JBK':      cmap[13],
    'JRK':      cmap[14],
    'MJ':       cmap[15],
    'NX':       cmap[17],
    'XQ':       cmap[5],
    'FB':       cmap[6],
    'CX':       cmap[7],
    'FH':       cmap[8],
    'ZJ':       cmap[16],
}




# HOTKEYS
#
# Defines the keyboard shortcuts.  Each hotkey is defined by a tuple
# with at least 2 entries, where the first entry is the hotkey (sequence),
# and the second entry is the function that is called.  The function
# should expect a single parameter, the labeltool object.  The optional
# third entry -- if present -- is expected to be a string describing the
# action.
HOTKEYS = (
    ('Space',     [lambda lt: lt.currentImage().confirmAll(),
                   lambda lt: lt.currentImage().setUnlabeled(False),
                   lambda lt: lt.gotoNext()
                  ],                                         'Mark image as labeled/confirmed and go to next'),
    ('Backspace', lambda lt: lt.gotoPrevious(),              'Previous image/frame'),
    ('PgDown',    lambda lt: lt.gotoNext(),                  'Next image/frame'),
    ('PgUp',      lambda lt: lt.gotoPrevious(),              'Previous image/frame'),
    ('Tab',       lambda lt: lt.selectNextAnnotation(),      'Select next annotation'),
    ('Shift+Tab', lambda lt: lt.selectPreviousAnnotation(),  'Select previous annotation'),
    ('Ctrl+f',    lambda lt: lt.view().fitInView(),          'Fit current image/frame into window'),
    ('Del',       lambda lt: lt.deleteSelectedAnnotations(), 'Delete selected annotations'),
    ('ESC',       lambda lt: lt.exitInsertMode(),            'Exit insert mode'),
    ('Shift+l',   lambda lt: lt.currentImage().setUnlabeled(False), 'Mark current image as labeled'),
    ('Shift+c',   lambda lt: lt.currentImage().confirmAll(), 'Mark all annotations in image as confirmed'),
)

# CONTAINERS
#
# A list/tuple of two-tuples defining the mapping between filename pattern and
# annotation container classes.  The filename pattern can contain wildcards
# such as * and ?.  The corresponding container is expected to either a python
# class implementing the sloth container interface, or a module path pointing
# to such a class.
CONTAINERS = (
    ('*.json',       'sloth.annotations.container.JsonContainer'),
    ('*.msgpack',    'sloth.annotations.container.MsgpackContainer'),
    ('*.yaml',       'sloth.annotations.container.YamlContainer'),
    ('*.pickle',     'sloth.annotations.container.PickleContainer'),
    ('*.sloth-init', 'sloth.annotations.container.FileNameListContainer'),
)

# PLUGINS
#
# A list/tuple of classes implementing the sloth plugin interface.  The
# classes can either be given directly or their module path be specified
# as string.
PLUGINS = (
)
