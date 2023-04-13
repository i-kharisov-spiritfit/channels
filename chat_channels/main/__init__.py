import enum


class ACCESS_STATUS(enum.Enum):
    DENIED = 0
    ALLOW = 1
    REQUIRED_VERIFICATION = 2