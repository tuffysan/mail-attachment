from pathlib import Path
import tomllib


def test_runtime_dependency_manifest_contains_core_services() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = [
        item.lower()
        for item in pyproject["project"]["dependencies"]
    ]

    for required in (
        "asyncpg",
        "redis",
        "pwdlib",
        "fastapi",
        "sqlalchemy",
        "httpx",
        "cryptography",
    ):
        assert any(
            dependency.startswith(required)
            for dependency in dependencies
        ), f"Missing runtime dependency: {required}"
