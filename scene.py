from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QBrush, QMouseEvent, QPainter, QPaintEvent, QPen
from PyQt5.QtWidgets import QWidget

from colors import Alpha, Colors, with_alpha
from geometry import Anchors, Rect, SnapPrimitive
from layout import LayoutManager, SnapEngine


class SceneItem:
    def __init__(self):
        self._parent = None
        self._rect = Rect()
        self._selected = False
        self._resizeError = ([0.0, 0.0], [0.0, 0.0])
        self._snapAnchors = self._rect.getSnapAnchors()

    def move(self, dx, dy):
        self._rect.move(dx, dy)

    def contains(self, x, y):
        return self._rect.contains(x, y)

    def selected(self):
        return self._selected

    def setSelected(self, selected):
        self._selected = selected

    def setGeometry(self, x, y, width, height):
        self._rect.update(x, y, width, height)

    def resetResizeError(self):
        self._resizeError = ([0.0, 0.0], [0.0, 0.0])

    def getSnapAnchors(self):
        return self._snapAnchors


class SceneGroup:
    def __init__(self):
        self._parent = None
        self._children = []
        self._padding = 15
        self._selected = False

        self._snapAnchors = Anchors(
            x=[
                SnapPrimitive(self, lambda: self._rect.left()),
                SnapPrimitive(self, lambda: self._rect.right()),
                SnapPrimitive(self, lambda: self._rect.centerX()),
            ],
            y=[
                SnapPrimitive(self, lambda: self._rect.top()),
                SnapPrimitive(self, lambda: self._rect.bottom()),
                SnapPrimitive(self, lambda: self._rect.centerY()),
            ],
            w=[
                SnapPrimitive(self, lambda: self._rect.width()),
            ],
            h=[
                SnapPrimitive(self, lambda: self._rect.height()),
            ],
        )

    def addChild(self, child):
        child._parent = self
        self._children.append(child)

    def getSnapAnchors(self):
        return self._snapAnchors

    @property
    def _rect(self):
        if not self._children:
            return Rect()

        first = self._children[0]._rect

        minX = first.left()
        maxX = first.right()
        minY = first.top()
        maxY = first.bottom()

        for child in self._children[1:]:
            rect = child._rect
            minX = min(minX, rect.left())
            maxX = max(maxX, rect.right())
            minY = min(minY, rect.top())
            maxY = max(maxY, rect.bottom())

        rect = Rect(
            minX,
            minY,
            maxX - minX + 1,
            maxY - minY + 1,
        )

        rect.adjust(self._padding)
        return rect

    def move(self, dx, dy):
        for child in self._children:
            child.move(dx, dy)

    def contains(self, x, y):
        return self._rect.contains(x, y)

    def selected(self):
        return self._selected

    def setSelected(self, selected):
        self._selected = selected

    def setGeometry(self, x, y, width, height):
        self.resize(Rect(x, y, width, height))

    def resize(self, newRect):
        oldRect = self._rect.adjusted(-self._padding)
        newRect = newRect.adjusted(-self._padding)

        oldWidth = oldRect.width()
        oldHeight = oldRect.height()

        newWidth = newRect.width()
        newHeight = newRect.height()

        if oldWidth <= 0 or oldHeight <= 0:
            return

        for child in self._children:
            self._resizeChild(
                child,
                oldRect,
                newRect,
                oldWidth,
                oldHeight,
                newWidth,
                newHeight,
            )

    def _resizeChild(
        self,
        child,
        oldRect,
        newRect,
        oldWidth,
        oldHeight,
        newWidth,
        newHeight,
    ):
        rect = child._rect

        sx0 = (rect.left() - oldRect.left()) / oldWidth
        sy0 = (rect.top() - oldRect.top()) / oldHeight
        sx1 = (rect.right() - oldRect.right()) / oldWidth
        sy1 = (rect.bottom() - oldRect.bottom()) / oldHeight

        errorLeft, errorTop = child._resizeError[0]
        errorRight, errorBottom = child._resizeError[1]

        newLeft = newRect.left() + newWidth * sx0 + errorLeft
        newTop = newRect.top() + newHeight * sy0 + errorTop
        newRight = newRect.right() + newWidth * sx1 + errorRight
        newBottom = newRect.bottom() + newHeight * sy1 + errorBottom

        left = round(newLeft)
        top = round(newTop)
        right = round(newRight)
        bottom = round(newBottom)

        child._resizeError = (
            (
                newLeft - left,
                newTop - top,
            ),
            (
                newRight - right,
                newBottom - bottom,
            ),
        )

        child.setGeometry(
            left,
            top,
            right - left + 1,
            bottom - top + 1,
        )

    def finishResize(self):
        for child in self._children:
            child.resetResizeError()


class SceneManager(QWidget):
    def __init__(self, layout=None):
        super().__init__()

        self._items = []
        self._groups = []
        self._snapHints = None
        self._snapEngine = SnapEngine()
        self._layoutManager = LayoutManager(self._snapEngine)

        self.setLayout(layout)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def setLayout(self, layout):
        self._layout = layout

        if layout is None:
            return

        self._addSnapAnchors(layout)

        self.setGeometry(
            0,
            0,
            layout._width,
            layout._height,
        )

    def addItem(self, item):
        self._items.append(item)
        self._addSnapAnchors(item)

    def addGroup(self, group):
        self._groups.append(group)
        self._addSnapAnchors(group)

    def _addSnapAnchors(self, item):
        self._snapEngine.addAnchors(item.getSnapAnchors())

    def _setParentAnchorsActive(self, item, active):
        parent = item._parent

        while parent is not None:
            parent.getSnapAnchors().setActive(active)
            parent = parent._parent

    def getSelected(self):
        for item in self._items + self._groups:
            if item.selected():
                return item

        return None

    def _findItemAt(self, pos):
        found = None

        for item in self._items + self._groups:
            if item.contains(pos.x(), pos.y()):
                item.setSelected(True)

                if found is None:
                    found = item
            else:
                item.setSelected(False)

        return found

    def mousePressEvent(self, event: QMouseEvent):
        item = self._findItemAt(event.pos())

        if item is not None:
            self._layoutManager.beginDrag(event, item)
            item.getSnapAnchors().setActive(False)

            if self._layoutManager.isMoving():
                self._setParentAnchorsActive(item, False)

        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        item = self.getSelected()

        if item is None:
            event.accept()
            return

        self._snapHints = self._layoutManager.drag(event, item)
        self.update()

        event.accept()

    def mouseReleaseEvent(self, event):
        item, action = self._layoutManager.endDrag()

        if item is not None:
            item.getSnapAnchors().setActive(True)

            if action == "move":
                self._setParentAnchorsActive(item, True)

            if isinstance(item, SceneGroup):
                item.finishResize()

        self._snapHints = None
        self.update()

        event.accept()

    def _paintSnapLines(self, painter):
        if self._snapHints is None:
            return

        painter.setPen(QPen(Qt.red))

        if self._snapHints.snapX is not None:
            x = round(self._snapHints.snapX)
            painter.drawLine(x, 0, x, self.height())

        if self._snapHints.snapY is not None:
            y = round(self._snapHints.snapY)
            painter.drawLine(0, y, self.width(), y)

    def _paintWindow(self, painter, rect):
        painter.setBrush(QBrush(Colors.DEFAULT_COLOR))
        painter.setPen(QPen(Colors.DEFAULT_BORDER))

        qtRect = QRect(
            rect.left(),
            rect.top(),
            rect._width,
            rect._height,
        )

        painter.drawRect(qtRect.adjusted(1, 1, -1, -1))

    def _paintGrid(self, painter):
        layout = self._layout

        if layout is None:
            return

        painter.setPen(
            QPen(
                with_alpha(
                    Colors.WHITE,
                    Alpha.MEDIUM,
                )
            )
        )

        cellWidth = layout._width / layout._xDiv
        cellHeight = layout._height / layout._yDiv

        for i in range(layout._xDiv + 1):
            x = round(i * cellWidth)
            painter.drawLine(
                x,
                0,
                x,
                layout._height,
            )

        for i in range(layout._yDiv + 1):
            y = round(i * cellHeight)
            painter.drawLine(
                0,
                y,
                layout._width,
                y,
            )

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)

        self._paintGrid(painter)

        for item in self._items + self._groups:
            self._paintWindow(painter, item._rect)

        self._paintSnapLines(painter)
