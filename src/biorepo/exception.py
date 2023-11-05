from typing import Optional


class BioReopException(Exception):
    """Base class for all exceptions raised by the biorepo package."""

    def __init__(self, msg: Optional[str] = None):
        self.msg = msg

    def __str__(self):
        return f"{self.__class__.__name__}: {self.msg}"


class BioRepoMissItem(BioReopException):
    def __init__(self, msg: str, key: str):
        self.key = key
        super().__init__("%s %s" % (msg, key))


class SourceException(BioReopException):
    """Base class for all exceptions raised by the source package."""

    def __init__(self, msg: Optional[str] = None):
        super().__init__(msg)


class ShellException(BioReopException):
    """Base class for all exceptions raised by the shell package."""

    def __init__(self, msg: Optional[str] = None):
        super().__init__(msg)


class InstallException(BioReopException):
    """Base class for all exceptions raised by the install package."""

    def __init__(self, msg: Optional[str] = None):
        super().__init__(msg)
