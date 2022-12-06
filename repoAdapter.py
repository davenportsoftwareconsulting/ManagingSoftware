from enum import Enum

class ExternalRepoInterface(Enum):
    BITBUCKET = 0
    ADO = 1
    GIT = 2


class repoAdapter:

    def __init__(self) -> None:
        pass