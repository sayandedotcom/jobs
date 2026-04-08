import uuid


def cuid() -> str:
    return "c" + uuid.uuid4().hex[:23].lower()
