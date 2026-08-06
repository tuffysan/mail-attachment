from pydantic import BaseModel, Field, field_validator


class SetupStatusResponse(BaseModel):
    completed: bool
    language: str
    timezone: str
    has_email_account: bool
    has_storage_destination: bool
    has_rule: bool


class SetupPreferencesRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    language: str = Field(default="sv", pattern="^[a-z]{2}(-[A-Z]{2})?$")
    timezone: str = Field(default="Europe/Stockholm", min_length=1, max_length=100)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone") from exc
        return value


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=12, max_length=1024)


class SetupCompleteRequest(BaseModel):
    acknowledge_backup: bool
    acknowledge_secret_storage: bool


class SetupCompleteResponse(BaseModel):
    completed: bool
