from sqlalchemy import UniqueConstraint

from mailhub.db.base import Base
from mailhub.db.models import SystemMetadata


def test_system_metadata_is_registered() -> None:
    table = Base.metadata.tables["system_metadata"]

    assert SystemMetadata.__tablename__ == "system_metadata"
    assert set(table.columns.keys()) == {"id", "key", "value", "created_at", "updated_at"}
    assert list(table.primary_key.columns.keys()) == ["id"]


def test_system_metadata_key_is_unique_and_indexed() -> None:
    table = Base.metadata.tables["system_metadata"]

    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    index_names = {index.name for index in table.indexes}

    assert "uq_system_metadata_key" in unique_names
    assert "ix_system_metadata_key" in index_names
