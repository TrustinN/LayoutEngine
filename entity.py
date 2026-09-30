from dataclasses import dataclass, field


@dataclass
class SnapPrimitive:
    item: object
    axis: str
    edge: str
    getter: callable
    _active: bool = True

    def value(self):
        return self.getter(self.item)

    def setActive(self, active):
        self._active = active


@dataclass
class Anchors:
    x: list[SnapPrimitive] = field(default_factory=list)
    y: list[SnapPrimitive] = field(default_factory=list)
    w: list[SnapPrimitive] = field(default_factory=list)
    h: list[SnapPrimitive] = field(default_factory=list)

    def add(self, anchors: "Anchors"):
        self.x.extend(anchors.x)
        self.y.extend(anchors.y)
        self.w.extend(anchors.w)
        self.h.extend(anchors.h)

    def remove(self, anchors: "Anchors"):
        for primitive in anchors.x:
            if primitive in self.x:
                self.x.remove(primitive)

        for primitive in anchors.y:
            if primitive in self.y:
                self.y.remove(primitive)

        for primitive in anchors.w:
            if primitive in self.w:
                self.w.remove(primitive)

        for primitive in anchors.h:
            if primitive in self.h:
                self.h.remove(primitive)

    def closestX(self, value):
        return self._closest(value, self.x)

    def closestY(self, value):
        return self._closest(value, self.y)

    def closestW(self, value):
        return self._closest(value, self.w)

    def closestH(self, value):
        return self._closest(value, self.h)

    def _closest(self, value, anchors):
        closest = None
        distance = None

        for anchor in anchors:
            if not anchor._active:
                continue

            newDistance = abs(anchor.value() - value)

            if distance is None or newDistance < distance:
                closest = anchor
                distance = newDistance

        return closest

    def setActive(self, active):
        for primitive in self.x:
            primitive.setActive(active)

        for primitive in self.y:
            primitive.setActive(active)

        for primitive in self.w:
            primitive.setActive(active)

        for primitive in self.h:
            primitive.setActive(active)

    def clear(self):
        self.x.clear()
        self.y.clear()
        self.w.clear()
        self.h.clear()

    def __repr__(self):
        return (
            "Anchors(\n"
            f"\tx={self.x},\n"
            f"\ty={self.y},\n"
            f"\tw={self.w},\n"
            f"\th={self.h}\n"
            ")"
        )


class Rect:
    def __init__(self, x=0, y=0, width=400, height=200):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

        self._snapAnchors = Anchors(
            x=[
                SnapPrimitive(self, "x", "left", lambda item: item.left()),
                SnapPrimitive(self, "x", "right", lambda item: item.right()),
                SnapPrimitive(self, "x", "center", lambda item: item.centerX()),
            ],
            y=[
                SnapPrimitive(self, "y", "top", lambda item: item.top()),
                SnapPrimitive(self, "y", "bottom", lambda item: item.bottom()),
                SnapPrimitive(self, "y", "center", lambda item: item.centerY()),
            ],
            w=[
                SnapPrimitive(self, "w", "width", lambda item: item.width()),
            ],
            h=[
                SnapPrimitive(self, "h", "height", lambda item: item.height()),
            ],
        )

    def update(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self._x = x
        if y is not None:
            self._y = y
        if width is not None:
            self._width = width
        if height is not None:
            self._height = height

    def left(self):
        return self._x

    def right(self):
        return self._x + self._width - 1

    def top(self):
        return self._y

    def bottom(self):
        return self._y + self._height - 1

    def width(self):
        return self._width

    def height(self):
        return self._height

    def centerX(self):
        return self._x + self._width / 2

    def centerY(self):
        return self._y + self._height / 2

    def contains(self, x, y):
        return self.left() <= x <= self.right() and self.top() <= y <= self.bottom()

    def move(self, dx, dy):
        self._x += dx
        self._y += dy

    def adjust(self, padding):
        self._x -= padding
        self._y -= padding
        self._width += 2 * padding
        self._height += 2 * padding

    def adjusted(self, padding):
        return Rect(
            self._x - padding,
            self._y - padding,
            self._width + 2 * padding,
            self._height + 2 * padding,
        )

    def getSnapAnchors(self):
        return self._snapAnchors

    def __repr__(self):
        return (
            f"Rect(x={self._x}, y={self._y}, "
            f"width={self._width}, height={self._height})"
        )


class GridLayout:
    def __init__(self, width, height, xDiv, yDiv):
        self._width = width
        self._height = height
        self._xDiv = xDiv
        self._yDiv = yDiv

        self._snapAnchors = Anchors()

        self._snapAnchors.w.append(
            SnapPrimitive(
                self,
                "w",
                "width",
                lambda item: item._width / item._xDiv,
            )
        )

        self._snapAnchors.h.append(
            SnapPrimitive(
                self,
                "h",
                "height",
                lambda item: item._height / item._yDiv,
            )
        )

        for i in range(self._xDiv + 1):
            self._snapAnchors.x.append(
                SnapPrimitive(
                    self,
                    "x",
                    "grid",
                    lambda item, i=i: i * item._width / item._xDiv,
                )
            )

        for i in range(self._yDiv + 1):
            self._snapAnchors.y.append(
                SnapPrimitive(
                    self,
                    "y",
                    "grid",
                    lambda item, i=i: i * item._height / item._yDiv,
                )
            )

    def getSnapAnchors(self):
        return self._snapAnchors


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
                SnapPrimitive(
                    self,
                    "x",
                    "left",
                    lambda item: item._rect.left(),
                ),
                SnapPrimitive(
                    self,
                    "x",
                    "right",
                    lambda item: item._rect.right(),
                ),
                SnapPrimitive(
                    self,
                    "x",
                    "center",
                    lambda item: item._rect.centerX(),
                ),
            ],
            y=[
                SnapPrimitive(
                    self,
                    "y",
                    "top",
                    lambda item: item._rect.top(),
                ),
                SnapPrimitive(
                    self,
                    "y",
                    "bottom",
                    lambda item: item._rect.bottom(),
                ),
                SnapPrimitive(
                    self,
                    "y",
                    "center",
                    lambda item: item._rect.centerY(),
                ),
            ],
            w=[
                SnapPrimitive(
                    self,
                    "w",
                    "width",
                    lambda item: item._rect.width(),
                ),
            ],
            h=[
                SnapPrimitive(
                    self,
                    "h",
                    "height",
                    lambda item: item._rect.height(),
                ),
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
        oldRect = self._rect

        if oldRect.width() == width and oldRect.height() == height:
            self.move(
                x - oldRect.left(),
                y - oldRect.top(),
            )
            return

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
