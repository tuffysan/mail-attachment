from email.message import EmailMessage
import io, zipfile

from mailhub.mail.engine import parse_message, safe_filename

def test_safe_filename_removes_path_characters():
    assert "/" not in safe_filename("../../invoice?.pdf")

def test_parse_message_extracts_attachment_and_zip():
    msg = EmailMessage()
    msg["From"] = "sender@example.com"
    msg["To"] = "inbox@example.com"
    msg["Subject"] = "Invoice"
    msg.set_content("Hello")
    msg.add_attachment(b"PDF", maintype="application", subtype="pdf", filename="invoice.pdf")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("inside.txt", b"hello")
    msg.add_attachment(buffer.getvalue(), maintype="application", subtype="zip", filename="docs.zip")
    parsed = parse_message(10, msg.as_bytes(), True, 10, 10000)
    assert parsed.uid == 10
    assert {x.filename for x in parsed.attachments} >= {"invoice.pdf", "docs.zip", "inside.txt"}
