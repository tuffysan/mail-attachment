import grp
import os
import pwd
import stat
from pathlib import Path

ALLOWED_LOCAL_ROOTS = (
    Path("/data/routed"),
    Path("/data/attachments"),
)


def _safe_local_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("Local storage path must be absolute")

    resolved = path.resolve(strict=False)

    for root in ALLOWED_LOCAL_ROOTS:
        resolved_root = root.resolve(strict=False)
        if resolved == resolved_root or resolved_root in resolved.parents:
            return resolved

    raise ValueError(
        "Local storage permissions can only be managed below "
        "/data/routed or /data/attachments"
    )


def _name_for_uid(uid: int) -> str | None:
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return None


def _name_for_gid(gid: int) -> str | None:
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return None


def inspect_local_permissions(value: str) -> dict[str, object]:
    path = _safe_local_path(value)
    exists = path.exists()

    if not exists:
        return {
            "path": str(path),
            "exists": False,
            "uid": None,
            "gid": None,
            "owner": None,
            "group": None,
            "mode": None,
            "writable": False,
            "executable": False,
        }

    info = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "uid": info.st_uid,
        "gid": info.st_gid,
        "owner": _name_for_uid(info.st_uid),
        "group": _name_for_gid(info.st_gid),
        "mode": f"{stat.S_IMODE(info.st_mode):04o}",
        "writable": os.access(path, os.W_OK),
        "executable": os.access(path, os.X_OK),
    }


def _chmod_tree(path: Path, directory_mode: int) -> None:
    file_mode = directory_mode & ~0o111

    for root, directories, files in os.walk(path, followlinks=False):
        root_path = Path(root)

        if root_path.is_symlink():
            continue

        os.chmod(root_path, directory_mode)

        for name in directories:
            child = root_path / name
            if not child.is_symlink():
                os.chmod(child, directory_mode)

        for name in files:
            child = root_path / name
            if not child.is_symlink():
                os.chmod(child, file_mode)


def set_local_permissions(
    value: str,
    mode: str,
    *,
    recursive: bool = False,
) -> dict[str, object]:
    path = _safe_local_path(value)
    path.mkdir(parents=True, exist_ok=True)

    parsed_mode = int(mode, 8)
    if parsed_mode < 0o700 or parsed_mode > 0o777:
        raise ValueError("Mode must be between 0700 and 0777")

    if recursive:
        _chmod_tree(path, parsed_mode)
    else:
        os.chmod(path, parsed_mode)

    return inspect_local_permissions(str(path))
