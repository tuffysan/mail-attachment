from datetime import datetime

from pydantic import BaseModel, Field


class StorageDestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: str
    base_path: str = Field(default="", max_length=2048)
    config: dict[str, str] = Field(default_factory=dict)
    is_enabled: bool = True


class StorageDestinationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    base_path: str | None = Field(default=None, max_length=2048)
    config: dict[str, str] | None = None
    is_enabled: bool | None = None


class StorageDestinationResponse(BaseModel):
    id: str
    name: str
    provider: str
    base_path: str
    is_enabled: bool
    configured_fields: list[str]
    last_test_status: str | None
    last_test_message: str | None
    last_test_at: datetime | None


class StorageTestResponse(BaseModel):
    status: str
    message: str


class ProviderResponse(BaseModel):
    key: str
    label: str
    fields: list[str]
    secret_fields: list[str]


class LocalStoragePermissionsResponse(BaseModel):
    path: str
    exists: bool
    uid: int | None
    gid: int | None
    owner: str | None
    group: str | None
    mode: str | None
    writable: bool
    executable: bool


class LocalStoragePermissionsUpdate(BaseModel):
    mode: str = Field(pattern=r"^0?[0-7]{3}$")
    recursive: bool = False
