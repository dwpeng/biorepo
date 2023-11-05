import os
from typing import Any, Dict, List, Optional


class Envirment:
    def __init__(self, name: str, value: Optional[str] = None):
        self._value = value is None
        self.name = name
        self.value = value

    def lower(self):
        if self.value is None:
            return None
        return self.name.lower()

    def upper(self):
        if self.value is None:
            return None
        return self.name.upper()

    def to_dict(self):
        return {"name": self.name, "value": self.value}

    def __repr__(self):
        return f"<Envirment name={self.name} value={self.value}>"

    def __str__(self):
        return f"{self.name}={self.value}"

    def __eq__(self, other):
        if isinstance(other, Envirment):
            return self.name == other.name and self.value == other.value
        return False

    @classmethod
    def from_environ(cls) -> List["Envirment"]:
        return [Envirment(name, os.environ.get(name)) for name in os.environ]

    @classmethod
    def from_dict(cls, dict: Dict[str, Any]) -> List["Envirment"]:
        return [
            Envirment(env_name, str(env_value)) for env_name, env_value in dict.items()
        ]

    @classmethod
    def from_list(cls, envs: List[str]) -> List["Envirment"]:
        return [Envirment(env) for env in envs]

    def set(self):
        os.environ[self.name] = self.value or ""

    def unset(self):
        if self.name in os.environ:
            del os.environ[self.name]
