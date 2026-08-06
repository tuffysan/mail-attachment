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


def _test_connection_sync(
    host: str,
    port: int,
    username: str,
    password: str,
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

        connection.login(username, password)
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
    password: str,
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
        mailbox,
        use_ssl,
        timeout_seconds,
    )
