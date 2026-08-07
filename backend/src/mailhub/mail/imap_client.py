import asyncio
import imaplib
import socket
import ssl
from dataclasses import dataclass


@dataclass(frozen=True)
class ImapTestResult:
    ok: bool
    message: str
    message_count: int | None = None


def _oauth_auth_string(username: str, access_token: str) -> bytes:
    return f"user={username}\x01auth=Bearer {access_token}\x01\x01".encode("utf-8")


def _test_connection_sync(
    host: str,
    port: int,
    username: str,
    password: str | None,
    access_token: str | None,
    mailbox: str,
    use_ssl: bool,
    timeout_seconds: float,
) -> ImapTestResult:
    connection: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None
    try:
        if use_ssl:
            context = ssl.create_default_context()
            connection = imaplib.IMAP4_SSL(
                host=host,
                port=port,
                ssl_context=context,
                timeout=timeout_seconds,
            )
        else:
            connection = imaplib.IMAP4(host=host, port=port, timeout=timeout_seconds)

        if access_token:
            connection.authenticate(
                "XOAUTH2",
                lambda _: _oauth_auth_string(username, access_token),
            )
        elif password:
            connection.login(username, password)
        else:
            return ImapTestResult(False, "No usable IMAP credential is configured")

        status, data = connection.select(mailbox, readonly=True)
        if status != "OK":
            return ImapTestResult(False, f"Mailbox {mailbox!r} could not be opened")

        count = int(data[0]) if data and data[0] else 0
        return ImapTestResult(True, "Connection and mailbox access succeeded", count)
    except (imaplib.IMAP4.error, OSError, socket.timeout, ssl.SSLError) as exc:
        return ImapTestResult(False, str(exc))
    finally:
        if connection is not None:
            try:
                connection.logout()
            except Exception:
                pass


async def test_imap_connection(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None = None,
    access_token: str | None = None,
    mailbox: str,
    use_ssl: bool,
    timeout_seconds: float,
) -> ImapTestResult:
    return await asyncio.to_thread(
        _test_connection_sync,
        host,
        port,
        username,
        password,
        access_token,
        mailbox,
        use_ssl,
        timeout_seconds,
    )
