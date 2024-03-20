import dataclasses


@dataclasses.dataclass
class Theme:
    logo_url: str = "/static/icon.png"
    icon_url: str = "/static/icon.png"
    navbar_color: str = "#da532c"
    background_color: str = "#ffffff"
