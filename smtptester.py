#!/usr/bin/env python3
"""
SMTP mail Tester - sends HTML email via designated SMTP server
Usage: python smtptester.py
"""

import smtplib
import ssl
import sys
import re
import os
import random
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate, make_msgid
from email import encoders

# ── Config ─────────────────────────────────────────────────────────────────
SMTP_HOST      = "SMTPHOST"
SMTP_PORT      = 465
SENDER_ACCOUNT = "SENDER ADDRESS"
SMTP_PASSWORD  = ""          # <-- leave empty to be prompted for password
SENDER         = f"SENDER NAME <{SENDER_ACCOUNT}>"
RECIPIENT      = "RECIPIENT"
SUBJECT        = "SUBJECT"

FILLER_WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur",
    "adipiscing", "elit", "sed", "erat", "nibh", "lacus",
    "iaculis", "volutpat", "blandit", "aliquam", "nulla",
    "feugiat", "viverra", "mauris", "ornare", "massa",
]


def prompt_multiline(prompt_text: str) -> str:
    print(prompt_text)
    print("  (type your content; finish with a single '.' on an empty line)")
    lines = []
    while True:
        line = input()
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines)


def randomize_text(original: str) -> str:
    words = original.split()
    result = []
    result += random.choices(FILLER_WORDS, k=random.randint(2, 5))
    for word in words:
        result.append(word)
        if random.random() > 0.4:
            result += random.choices(FILLER_WORDS, k=random.randint(1, 3))
    result += random.choices(FILLER_WORDS, k=random.randint(2, 5))
    return " ".join(result)


def wrap_html(raw: str) -> str:
    if "<html" in raw.lower():
        return raw
    body_content = raw.replace("\n\n", "</p><p>").replace("\n", "<br>\n")
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body style="font-family: Arial; font-size: 14px;">
  <p>{body_content}</p>
</body>
</html>"""


def build_message(html_body: str, attachment_path: str = None, encode_base64_body: bool = False) -> MIMEMultipart:
    if attachment_path:
        msg = MIMEMultipart("mixed")
        alt = MIMEMultipart("alternative")
    else:
        msg = MIMEMultipart("alternative")
        alt = msg

    msg["From"]       = SENDER
    msg["To"]         = RECIPIENT
    msg["Subject"]    = SUBJECT
    msg["Date"]       = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=SENDER_ACCOUNT.split("@")[-1])
    msg["X-Mailer"]   = "MailDefenseTester/1.2"

    plain = re.sub(r"<[^>]+>", "", html_body).strip()

    plain_part = MIMEText(plain, "plain", "utf-8")
    html_part  = MIMEText(html_body, "html", "utf-8")

    if encode_base64_body:
        encoders.encode_base64(plain_part)
        encoders.encode_base64(html_part)

    alt.attach(plain_part)
    alt.attach(html_part)

    if attachment_path:
        msg.attach(alt)
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

    return msg


def send(msg: MIMEMultipart) -> None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    password = SMTP_PASSWORD
    if not password:
        password = getpass.getpass("SMTP password: ")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as smtp:
        smtp.login(SENDER_ACCOUNT, password)
        smtp.sendmail(SENDER_ACCOUNT, [RECIPIENT], msg.as_string())


def main():
    print("=" * 60)
    print(" <<< SMTP Mail Tester >>>")
    print("=" * 60)

    attachment_path = None
    use_file = input("Attach a file? [y/N]: ").strip().lower()
    if use_file == "y":
        while True:
            path = input("File path: ").strip()
            if os.path.isfile(path):
                attachment_path = path
                break
            else:
                print("File not found.")

    count = int(input("How many emails to send? [1]: ") or "1")

    randomize = False
    if count > 1:
        randomize = input("Randomize content? [y/N]: ").lower() == "y"

    encode_base64_body = input("Encode body base64? [y/N]: ").lower() == "y"

    raw_body = prompt_multiline("Body")
    html_body = wrap_html(raw_body)

    print("\n── HTML preview ─────────────────────────────")
    print(html_body[:800] + ("…" if len(html_body) > 800 else ""))
    print("────────────────────────────────────────────")

    print("\n── Sending details ──────────────────────────")
    print(f"Count        : {count}")
    print(f"Randomized   : {'YES' if randomize else 'NO'}")
    print(f"Base64 Encode: {'YES' if encode_base64_body else 'NO'}")
    if attachment_path:
        print(f"Attachment   : {os.path.basename(attachment_path)} ({os.path.getsize(attachment_path):,} bytes)")
    else:
        print("Attachment   : NONE")
    print("────────────────────────────────────────────")

    confirm = input("\nSend? [Y/n]: ").lower()
    if confirm == "n":
        return

    for i in range(count):
        body = wrap_html(randomize_text(raw_body)) if randomize else html_body
        msg = build_message(body, attachment_path, encode_base64_body)
        send(msg)
        print(f"[{i+1}/{count}] Sent")


if __name__ == "__main__":
    main()