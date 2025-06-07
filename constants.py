import os

DIRECTORY = os.path.dirname(__file__)
APP_DATA = os.path.join(os.getenv('LOCALAPPDATA'), "Gizmo")


class LOGO:
    LIGHT = os.path.join(DIRECTORY, "media/gizmo-light-icon.png")
    DARK = os.path.join(DIRECTORY, "media/gizmo-dark-icon.png")
    ORANGE = os.path.join(DIRECTORY, "media/gizmo-orange-icon.png")


class STYLE:
    DEFAULT = os.path.join(DIRECTORY, "stylesheets/default.css")
