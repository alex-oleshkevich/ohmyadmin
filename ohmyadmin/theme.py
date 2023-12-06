import dataclasses


@dataclasses.dataclass
class Theme:
    title: str = "OhMyAdmin!"
    logo: str = ""
    favicon: str = ""
    navbar_color: str = "red"
