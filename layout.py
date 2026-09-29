from dataclasses import dataclass

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QMouseEvent

from geometry import Anchors, Rect


class SnapEngine:
    def __init__(self):
        self._anchors = Anchors()

    def addAnchors(self, anchors: Anchors):
        self._anchors.add(anchors)

    def removeAnchors(self, anchors: Anchors):
        self._anchors.remove(anchors)

    def _snap(self, value, primitive, threshold=5):
        if primitive is None:
            return value

        target = primitive.value()

        if abs(value - target) <= threshold:
            return target

        return value

    def snapX(self, x):
        return self._snap(
            x,
            self._anchors.closestX(x),
        )

    def snapY(self, y):
        return self._snap(
            y,
            self._anchors.closestY(y),
        )

    def snapW(self, width):
        return self._snap(
            width,
            self._anchors.closestW(width),
        )

    def snapH(self, height):
        return self._snap(
            height,
            self._anchors.closestH(height),
        )

    def getSnapXDelta(self, x):
        return int(round(self.snapX(x))) - x

    def getSnapYDelta(self, y):
        return int(round(self.snapY(y))) - y


@dataclass
class LayoutResult:
    snapX: float | None = None
    snapY: float | None = None


class LayoutManager:
    RESIZE_THRESHOLD = 15

    def __init__(self, snapEngine: SnapEngine):
        self._snapEngine = snapEngine

        self._lastMousePos = None
        self._dragOffset = QPoint(0, 0)
        self._dragOriginRect = None
        self._resizeMask = None
        self._dragAction = None
        self._dragItem = None

    def beginDrag(self, event: QMouseEvent, item):
        self._lastMousePos = event.pos()
        self._dragOffset = QPoint(0, 0)
        self._dragItem = item

        rect = item._rect

        self._dragOriginRect = Rect(
            rect._x,
            rect._y,
            rect._width,
            rect._height,
        )

        if self._isDragAction(item, event.pos()):
            self._dragAction = "move"
            return

        self._dragAction = "resize"
        self._resizeMask = self._getResizeMask(rect, event.pos())

    def endDrag(self):
        item = self._dragItem
        action = self._dragAction

        self._dragItem = None
        self._dragAction = None
        self._resizeMask = None

        return item, action

    def isMoving(self):
        return self._dragAction == "move"

    def _isDragAction(self, item, pos, threshold=RESIZE_THRESHOLD):
        dragRegion = item._rect.adjusted(-threshold)

        return dragRegion.contains(
            pos.x(),
            pos.y(),
        )

    def _getResizeMask(self, rect, pos):
        threshold = self.RESIZE_THRESHOLD

        return [
            abs(pos.y() - rect.top()) <= threshold,
            abs(pos.x() - rect.right()) <= threshold,
            abs(pos.y() - rect.bottom()) <= threshold,
            abs(pos.x() - rect.left()) <= threshold,
        ]

    def drag(self, event: QMouseEvent, item):
        if self._lastMousePos is None:
            return LayoutResult()

        self._dragOffset += event.pos() - self._lastMousePos

        if self._dragAction == "move":
            result = self._moveItem(item)
        else:
            result = self._resizeItem(item)

        self._lastMousePos = event.pos()

        return result

    def _moveItem(self, item):
        origin = self._dragOriginRect

        offsetX = self._dragOffset.x()
        offsetY = self._dragOffset.y()

        left = origin.left() + offsetX
        right = origin.right() + offsetX
        top = origin.top() + offsetY
        bottom = origin.bottom() + offsetY

        snapLeft = self._snapEngine.getSnapXDelta(left)
        snapRight = self._snapEngine.getSnapXDelta(right)

        snapTop = self._snapEngine.getSnapYDelta(top)
        snapBottom = self._snapEngine.getSnapYDelta(bottom)

        snapX = 0
        snapY = 0
        snapXValue = None
        snapYValue = None

        if snapLeft != 0:
            snapX = snapLeft
            snapXValue = left + snapX
        elif snapRight != 0:
            snapX = snapRight
            snapXValue = right + snapX

        if snapTop != 0:
            snapY = snapTop
            snapYValue = top + snapY
        elif snapBottom != 0:
            snapY = snapBottom
            snapYValue = bottom + snapY

        left += snapX
        right += snapX
        top += snapY
        bottom += snapY

        item.setGeometry(
            left,
            top,
            right - left + 1,
            bottom - top + 1,
        )

        return LayoutResult(
            snapX=snapXValue,
            snapY=snapYValue,
        )

    def _resizeItem(self, item):
        origin = self._dragOriginRect

        offsetX = self._dragOffset.x()
        offsetY = self._dragOffset.y()

        left = origin.left()
        right = origin.right()
        top = origin.top()
        bottom = origin.bottom()

        snapXValue = None
        snapYValue = None

        if self._resizeMask[0]:
            top += offsetY
            snapYValue = self._applySnapY(top)

            if snapYValue is not None:
                top = snapYValue

        if self._resizeMask[1]:
            right += offsetX
            snapXValue = self._applySnapX(right)

            if snapXValue is not None:
                right = snapXValue

        if self._resizeMask[2]:
            bottom += offsetY
            snapYValue = self._applySnapY(bottom)

            if snapYValue is not None:
                bottom = snapYValue

        if self._resizeMask[3]:
            left += offsetX
            snapXValue = self._applySnapX(left)

            if snapXValue is not None:
                left = snapXValue

        item.setGeometry(
            left,
            top,
            right - left + 1,
            bottom - top + 1,
        )

        return LayoutResult(
            snapX=snapXValue,
            snapY=snapYValue,
        )

    def _applySnapX(self, value):
        delta = self._snapEngine.getSnapXDelta(value)

        if delta == 0:
            return None

        return value + delta

    def _applySnapY(self, value):
        delta = self._snapEngine.getSnapYDelta(value)

        if delta == 0:
            return None

        return value + delta
