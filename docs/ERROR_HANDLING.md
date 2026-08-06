# Error handling

Commit 002B introduces one consistent API error format for expected
application errors, request validation errors, ordinary HTTP errors and
unexpected exceptions.

## Response format

Errors use `application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Resource not found",
  "status": 404,
  "detail": "Mailbox was not found",
  "instance": "/api/v1/mailboxes/123",
  "code": "mailbox_not_found",
  "request_id": "01J..."
}
```

Request validation errors also include an `errors` array with safe field
locations, messages and validation types.

## Application exceptions

Raise typed errors from service code:

```python
from mailhub.core.errors import NotFoundError

raise NotFoundError(
    "Email account was not found",
    code="email_account_not_found",
)
```

Available base exceptions:

- `ValidationError`
- `UnauthorizedError`
- `ForbiddenError`
- `NotFoundError`
- `ConflictError`
- `ServiceUnavailableError`

## Security

Unexpected exception messages and stack traces are never returned to the
client. The full exception is written to the server log with the request ID,
while the client receives a generic message.

## Migration guidance

Existing `HTTPException` usage remains supported. New domain and service code
should prefer the typed application exceptions so error codes remain stable
for frontend and API clients.
