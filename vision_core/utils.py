from typing import Optional, TypeVar

T = TypeVar("T")

def safe_copy(obj: Optional[T]) -> Optional[T]:
    return obj.copy() if obj is not None else None