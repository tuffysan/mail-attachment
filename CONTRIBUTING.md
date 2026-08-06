# Contributing

1. Create a focused branch.
2. Run `make init` once.
3. Run `make check` before committing.
4. For infrastructure changes, run `make up` and verify `make ps` shows healthy services.
5. Open a pull request using the template.

Keep commits small and independently testable. Never commit `.env` or production data.
