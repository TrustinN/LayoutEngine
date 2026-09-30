from dataclasses import dataclass, field

from entity import Anchors, Rect, SnapPrimitive


class SnapEngine:
    THRESHOLD = 5

    def __init__(self):
        self._anchors = Anchors()

    def addAnchors(self, anchors: Anchors):
        self._anchors.add(anchors)

    def removeAnchors(self, anchors: Anchors):
        self._anchors.remove(anchors)

    def snapX(self, value):
        primitive = self._anchors.closestX(value)

        if primitive is None:
            return None

        if abs(value - primitive.value()) > self.THRESHOLD:
            return None

        return primitive

    def snapY(self, value):
        primitive = self._anchors.closestY(value)

        if primitive is None:
            return None

        if abs(value - primitive.value()) > self.THRESHOLD:
            return None

        return primitive

    def snapW(self, value):
        primitive = self._anchors.closestW(value)

        if primitive is None:
            return None

        if abs(value - primitive.value()) > self.THRESHOLD:
            return None

        return primitive

    def snapH(self, value):
        primitive = self._anchors.closestH(value)

        if primitive is None:
            return None

        if abs(value - primitive.value()) > self.THRESHOLD:
            return None

        return primitive


@dataclass
class SnapMatch:
    primitive: SnapPrimitive
    edge: str


@dataclass
class SnapResult:
    rect: object
    matches: list[SnapMatch] = field(default_factory=list)


class SnapResolver:
    def __init__(self, snapEngine: SnapEngine):
        self._snapEngine = snapEngine

    def resolveMove(self, oldRect, newRect):
        matches = []

        left = newRect.left()
        right = newRect.right()
        top = newRect.top()
        bottom = newRect.bottom()

        snapLeft = self._snapEngine.snapX(left)
        snapRight = self._snapEngine.snapX(right)

        snapTop = self._snapEngine.snapY(top)
        snapBottom = self._snapEngine.snapY(bottom)

        snapX = 0
        snapY = 0

        if snapLeft is not None:
            snapX = snapLeft.value() - left
            matches.append(SnapMatch(snapLeft, "left"))

        if snapRight is not None:
            if snapX == 0:
                snapX = snapRight.value() - right

            matches.append(SnapMatch(snapRight, "right"))

        if snapTop is not None:
            snapY = snapTop.value() - top
            matches.append(SnapMatch(snapTop, "top"))

        if snapBottom is not None:
            if snapY == 0:
                snapY = snapBottom.value() - bottom

            matches.append(SnapMatch(snapBottom, "bottom"))

        left += snapX
        right += snapX
        top += snapY
        bottom += snapY

        rect = Rect(
            left,
            top,
            right - left + 1,
            bottom - top + 1,
        )

        return SnapResult(
            rect=rect,
            matches=matches,
        )

    def resolveResize(self, oldRect, newRect):
        matches = []

        left = newRect.left()
        right = newRect.right()
        top = newRect.top()
        bottom = newRect.bottom()

        if oldRect.left() != newRect.left():
            primitive = self._snapEngine.snapX(left)

            if primitive is not None:
                matches.append(SnapMatch(primitive, "left"))
                left = primitive.value()

        if oldRect.right() != newRect.right():
            primitive = self._snapEngine.snapX(right)

            if primitive is not None:
                matches.append(SnapMatch(primitive, "right"))
                right = primitive.value()

        if oldRect.top() != newRect.top():
            primitive = self._snapEngine.snapY(top)

            if primitive is not None:
                matches.append(SnapMatch(primitive, "top"))
                top = primitive.value()

        if oldRect.bottom() != newRect.bottom():
            primitive = self._snapEngine.snapY(bottom)

            if primitive is not None:
                matches.append(SnapMatch(primitive, "bottom"))
                bottom = primitive.value()

        rect = Rect(
            left,
            top,
            right - left + 1,
            bottom - top + 1,
        )

        return SnapResult(
            rect=rect,
            matches=matches,
        )

    def _applyMatches(self, rect, matches):
        for match in matches:
            value = match.primitive.value()

            if match.edge == "left":
                rect._x = value

            elif match.edge == "right":
                rect._width = value - rect.left() + 1

            elif match.edge == "top":
                rect._y = value

            elif match.edge == "bottom":
                rect._height = value - rect.top() + 1

            elif match.edge == "width":
                rect._width = value

            elif match.edge == "height":
                rect._height = value


class LayoutManager:
    RESIZE_THRESHOLD = 10

    def __init__(self, snapEngine):
        self._snapResolver = SnapResolver(snapEngine)

        self._item = None
        self._action = None
        self._dragOrigin = None
        self._dragOffset = None
        self._resizeEdges = None

    def beginDrag(self, event, item):
        self._item = item
        self._dragOrigin = self._copyRect(item._rect)

        x = event.pos().x()
        y = event.pos().y()

        if self._isResize(item, x, y):
            self._action = "resize"
            self._resizeEdges = self._getResizeEdges(item, x, y)
            self._dragOffset = (
                x - item._rect.left(),
                y - item._rect.top(),
            )
        else:
            self._action = "move"
            self._resizeEdges = None
            self._dragOffset = (
                x - item._rect.left(),
                y - item._rect.top(),
            )

    def drag(self, event, item):
        if self._item is None:
            return None

        if self._action == "move":
            return self._dragMove(event, item)

        if self._action == "resize":
            return self._dragResize(event, item)

        return None

    def endDrag(self):
        item = self._item
        action = self._action

        self._item = None
        self._action = None
        self._dragOrigin = None
        self._dragOffset = None
        self._resizeEdges = None

        return item, action

    def isMoving(self):
        return self._action == "move"

    def isResizing(self):
        return self._action == "resize"

    def _dragMove(self, event, item):
        x = event.pos().x()
        y = event.pos().y()

        newX = x - self._dragOffset[0]
        newY = y - self._dragOffset[1]

        oldRect = self._dragOrigin

        newRect = Rect(
            newX,
            newY,
            oldRect.width(),
            oldRect.height(),
        )

        result = self._snapResolver.resolveMove(
            oldRect,
            newRect,
        )

        item.setGeometry(
            result.rect.left(),
            result.rect.top(),
            result.rect.width(),
            result.rect.height(),
        )

        return result.matches

    def _dragResize(self, event, item):
        x = event.pos().x()
        y = event.pos().y()

        oldRect = self._dragOrigin

        left = oldRect.left()
        top = oldRect.top()
        right = oldRect.right()
        bottom = oldRect.bottom()

        if "left" in self._resizeEdges:
            left = x

        if "right" in self._resizeEdges:
            right = x

        if "top" in self._resizeEdges:
            top = y

        if "bottom" in self._resizeEdges:
            bottom = y

        newRect = Rect(
            left,
            top,
            right - left + 1,
            bottom - top + 1,
        )

        result = self._snapResolver.resolveResize(
            oldRect,
            newRect,
        )

        item.setGeometry(
            result.rect.left(),
            result.rect.top(),
            result.rect.width(),
            result.rect.height(),
        )

        return result.matches

    def _isResize(self, item, x, y):
        rect = item._rect

        if abs(x - rect.left()) <= self.RESIZE_THRESHOLD:
            return True

        if abs(x - rect.right()) <= self.RESIZE_THRESHOLD:
            return True

        if abs(y - rect.top()) <= self.RESIZE_THRESHOLD:
            return True

        if abs(y - rect.bottom()) <= self.RESIZE_THRESHOLD:
            return True

        return False

    def _getResizeEdges(self, item, x, y):
        rect = item._rect
        edges = []

        if abs(x - rect.left()) <= self.RESIZE_THRESHOLD:
            edges.append("left")

        if abs(x - rect.right()) <= self.RESIZE_THRESHOLD:
            edges.append("right")

        if abs(y - rect.top()) <= self.RESIZE_THRESHOLD:
            edges.append("top")

        if abs(y - rect.bottom()) <= self.RESIZE_THRESHOLD:
            edges.append("bottom")

        return edges

    def _copyRect(self, rect):
        return Rect(
            rect.left(),
            rect.top(),
            rect.width(),
            rect.height(),
        )
