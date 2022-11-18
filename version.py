SW_VERSION = "0.0.1"


def get_firmware_version(version=SW_VERSION):
    version = version.replace(".", "")[:3]  # Todo: Currently we can only show three digits. Implement display scroll
    if version.isdigit():
        return version


def is_newer_version(v1):
    for i, j in zip(map(int, v1.split(".")), map(int, SW_VERSION.split("."))):
        if i == j:
            continue
        return i > j
    return len(v1.split(".")) > len(SW_VERSION.split("."))
