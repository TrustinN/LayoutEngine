from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QBrush, QMouseEvent, QPainter, QPaintEvent, QPen
from PyQt5.QtWidgets import QWidget

from colors import Alpha, Colors, with_alpha
from entity import SceneGroup
from snap import LayoutManager, SnapEngine


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

    def mouseReleaseEvent(self, event: QMouseEvent):
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

        for match in self._snapHints:
            primitive = match.primitive
            value = round(primitive.value())

            if primitive.axis == "x":
                painter.drawLine(
                    value,
                    0,
                    value,
                    self.height(),
                )

            elif primitive.axis == "y":
                painter.drawLine(
                    0,
                    value,
                    self.width(),
                    value,
                )

    def _paintWindow(self, painter, rect):
        painter.setBrush(QBrush(Colors.DEFAULT_COLOR))
        painter.setPen(QPen(Colors.DEFAULT_BORDER))

        qtRect = QRect(
            round(rect.left()),
            round(rect.top()),
            round(rect.width()),
            round(rect.height()),
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
