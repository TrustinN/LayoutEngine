from dataclasses import dataclass, field


class Rect:
    def __init__(self, x=0, y=0, width=400, height=200):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

        self._snapAnchors = Anchors(
            x=[
                SnapPrimitive(self, self.left),
                SnapPrimitive(self, self.right),
                SnapPrimitive(self, self.centerX),
            ],
            y=[
                SnapPrimitive(self, self.top),
                SnapPrimitive(self, self.bottom),
                SnapPrimitive(self, self.centerY),
            ],
            w=[
                SnapPrimitive(self, self.width),
            ],
            h=[
                SnapPrimitive(self, self.height),
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
            SnapPrimitive(self, lambda: self._width / self._xDiv)
        )
        self._snapAnchors.h.append(
            SnapPrimitive(self, lambda: self._height / self._yDiv)
        )

        for i in range(self._xDiv + 1):
            self._snapAnchors.x.append(
                SnapPrimitive(
                    self,
                    lambda i=i: i * self._width / self._xDiv,
                )
            )

        for i in range(self._yDiv + 1):
            self._snapAnchors.y.append(
                SnapPrimitive(
                    self,
                    lambda i=i: i * self._height / self._yDiv,
                )
            )

    def getSnapAnchors(self):
        return self._snapAnchors


class SnapPrimitive:
    def __init__(self, item, getter):
        self._item = item
        self._getter = getter
        self._active = True

    def value(self):
        return self._getter()

    def setActive(self, active):
        self._active = active

    def __repr__(self):
        return f"SnapPrimitive({self.value()})"


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
