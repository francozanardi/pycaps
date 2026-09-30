from abc import ABC, abstractmethod
from typing import Optional
import os

class Template(ABC):

    def __init__(self, name: str):
        self._name = name

    @abstractmethod
    def get_json_path(self) -> str:
        pass

    def get_folder_path(self) -> str:
        return os.path.dirname(self.get_json_path())

    def get_config(self) -> dict:
        import json
        with open(self.get_json_path(), "r", encoding="utf-8") as f:
            return json.load(f)

    def get_css_path(self) -> Optional[str]:
        config = self.get_config()
        css_file = config.get("css")
        if css_file:
            return os.path.join(self.get_folder_path(), css_file)
        return None

    def get_css(self) -> str:
        css_path = self.get_css_path()
        if css_path and os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def get_resources_path(self) -> Optional[str]:
        config = self.get_config()
        resources_folder = config.get("resources")
        if resources_folder:
            return os.path.join(self.get_folder_path(), resources_folder)
        return None
