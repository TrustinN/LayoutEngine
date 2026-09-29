from PyQt5.QtGui import QColor


def with_alpha(color: QColor, alpha: int) -> QColor:
    return QColor(color.red(), color.green(), color.blue(), alpha)


class Alpha:
    MINIMAL = 7  # barely visible
    SUBTLE = 15  # barely visible
    LIGHT = 30  # default workspace region
    MEDIUM = 60  # selected workspace
    STRONG = 100  # hover/highlight
    SOLID = 180  # temporary emphasis


class Colors:
    # Neutral
    WHITE = QColor(255, 255, 255)
    LIGHT_GRAY = QColor(220, 220, 220)
    DARK_GRAY = QColor(80, 80, 80)

    # Blues
    SKY_BLUE = QColor(135, 206, 235)
    STEEL_BLUE = QColor(70, 130, 180)
    NAVY_BLUE = QColor(25, 25, 112)

    # Greens
    MINT = QColor(152, 255, 152)
    SAGE = QColor(188, 184, 138)
    FOREST_GREEN = QColor(34, 139, 34)

    # Purples
    LAVENDER = QColor(230, 230, 250)
    ORCHID = QColor(218, 112, 214)
    DEEP_PURPLE = QColor(106, 90, 205)

    # Reds / Pinks
    ROSE = QColor(255, 228, 225)
    CORAL = QColor(255, 127, 80)
    CRIMSON = QColor(220, 20, 60)

    # Yellows / Oranges
    CREAM = QColor(255, 253, 208)
    GOLD = QColor(255, 215, 0)
    AMBER = QColor(255, 191, 0)

    DEFAULT_COLOR = with_alpha(WHITE, Alpha.MINIMAL)
    DEFAULT_BORDER = with_alpha(WHITE, Alpha.STRONG)
