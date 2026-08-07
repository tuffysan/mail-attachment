"""Operations dashboard aggregation."""


async def build_operations_dashboard(*args, **kwargs):
    from mailhub.operations.service import (
        build_operations_dashboard as _build_operations_dashboard,
    )

    return await _build_operations_dashboard(*args, **kwargs)


__all__ = ["build_operations_dashboard"]
