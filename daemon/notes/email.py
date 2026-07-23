import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send(subject: str, body: str, smtp_config: dict) -> bool:
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = smtp_config.get("user", "daemon@localhost")
        msg["To"] = smtp_config["to"]
        msg.attach(MIMEText(body, "plain"))

        enc = smtp_config.get("encryption", "ssl")
        host = smtp_config.get("host", "localhost")
        port = int(smtp_config.get("port", 465))
        user = smtp_config.get("user", "")
        password = smtp_config.get("password", "")

        if enc == "ssl":
            with smtplib.SMTP_SSL(host, port) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)

        elif enc == "tls":
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)

        else:
            # plain — local postfix or unauthenticated relay
            with smtplib.SMTP(host, port) as server:
                server.send_message(msg)

        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_note(note: dict, smtp_config: dict) -> bool:
    resource = f"[{note['resource']}] " if note.get("resource") else ""
    subject = f"[Daemon] {resource}{note['text'][:50]}"
    body = f"{note['text']}\n\nPinned: {note.get('created','')}"
    return send(subject, body, smtp_config)

def send_health_summary(summary: str, smtp_config: dict) -> bool:
    return send("[Daemon] Homelab Health Summary", summary, smtp_config)
