from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDefinition:
    key: str
    label: str
    rclone_type: str | None
    fields: tuple[str, ...]
    secret_fields: tuple[str, ...] = ()


PROVIDERS: dict[str, ProviderDefinition] = {
    "local": ProviderDefinition("local", "Local folder", None, ()),
    "drive": ProviderDefinition(
        "drive", "Google Drive", "drive",
        ("client_id", "client_secret", "token", "root_folder_id"),
        ("client_secret", "token"),
    ),
    "onedrive": ProviderDefinition(
        "onedrive", "Microsoft OneDrive", "onedrive",
        ("client_id", "client_secret", "token", "drive_id", "drive_type"),
        ("client_secret", "token"),
    ),
    "dropbox": ProviderDefinition(
        "dropbox", "Dropbox", "dropbox",
        ("client_id", "client_secret", "token"),
        ("client_secret", "token"),
    ),
    "s3": ProviderDefinition(
        "s3", "Amazon S3 / S3 compatible", "s3",
        ("provider", "access_key_id", "secret_access_key", "region", "endpoint", "acl"),
        ("secret_access_key",),
    ),
    "minio": ProviderDefinition(
        "minio", "MinIO", "s3",
        ("access_key_id", "secret_access_key", "endpoint", "region"),
        ("secret_access_key",),
    ),
    "azureblob": ProviderDefinition(
        "azureblob", "Azure Blob Storage", "azureblob",
        ("account", "key", "sas_url", "endpoint"),
        ("key", "sas_url"),
    ),
    "webdav": ProviderDefinition(
        "webdav", "WebDAV / Nextcloud", "webdav",
        ("url", "vendor", "user", "pass", "bearer_token"),
        ("pass", "bearer_token"),
    ),
    "sftp": ProviderDefinition(
        "sftp", "SFTP", "sftp",
        ("host", "user", "port", "pass", "key_pem", "key_file_pass"),
        ("pass", "key_pem", "key_file_pass"),
    ),
    "smb": ProviderDefinition(
        "smb", "SMB / NAS", "smb",
        ("host", "user", "pass", "domain", "port"),
        ("pass",),
    ),
}


def provider_definition(provider: str) -> ProviderDefinition:
    try:
        return PROVIDERS[provider]
    except KeyError as exc:
        raise ValueError(f"Unsupported storage provider: {provider}") from exc
