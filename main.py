from PyQt5.QtWidgets import QApplication

from entity import GridLayout, SceneGroup, SceneItem
from scene import SceneManager


class App(QApplication):
    def __init__(self, argv=[]):
        super().__init__(argv)

        self.manager = SceneManager()
        self.manager.show()

        self.primaryScreen().geometry()
        screen = self.manager.screen().geometry()
        self.manager.show()

        grid = GridLayout(screen.width(), screen.height(), 10, 10)
        self.manager.setLayout(grid)

        items = [SceneItem() for i in range(2)]
        group = SceneGroup()
        group.addChild(items[0])
        group.addChild(items[1])
        self.manager.addGroup(group)
        for item in items:
            self.manager.addItem(item)


if __name__ == "__main__":
    app = App()
    app.exec()
