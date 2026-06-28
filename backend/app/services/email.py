import base64
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from app.config import settings
from app import models

def _icon_src() -> str:
    png = Path(__file__).resolve().parents[3] / "frontend/public/favicon.png"
    if png.exists():
        return "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
    return ""


def _html_table(sets: list[models.TapeSet]) -> str:
    rows = ""
    for s in sets:
        loc = s.location.name if s.location else "—"
        exp = str(s.expires_at) if s.expires_at else "∞"
        url = f"{settings.app_url}/sets/{s.id}"
        rows += (
            f"<tr>"
            f'<td><a href="{url}" style="color:#1a5fa8;text-decoration:none">{s.name}</a></td>'
            f"<td>{loc}</td>"
            f"<td>{exp}</td>"
            f"</tr>"
        )
    return rows


def _build_html(heading: str, intro: str, sets: list[models.TapeSet]) -> str:
    rows = _html_table(sets)
    icon = _icon_src()
    icon_tag = (
        f'<td style="vertical-align:middle;padding-right:12px">'
        f'<img src="{icon}" width="36" height="36" alt="" style="display:block"></td>'
        if icon else ""
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 0">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">

        <!-- Header -->
        <tr style="background:#1e3a5f">
          <td style="padding:20px 32px">
            <table cellpadding="0" cellspacing="0"><tr>
              {icon_tag}
              <td style="vertical-align:middle">
                <span style="font-size:20px;font-weight:700;color:#fff;letter-spacing:.02em">TapeRotation</span>
              </td>
            </tr></table>
          </td>
        </tr>

        <!-- Body -->
        <tr><td style="padding:28px 32px">
          <h2 style="margin:0 0 8px;font-size:18px;color:#1e3a5f">{heading}</h2>
          {f'<p style="margin:0 0 20px;font-size:14px;color:#555">{intro}</p>' if intro else ''}

          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px">
            <thead>
              <tr style="background:#f1f5f9">
                <th style="padding:8px 12px;text-align:left;color:#555;font-weight:600;border-bottom:2px solid #e2e8f0">Набор</th>
                <th style="padding:8px 12px;text-align:left;color:#555;font-weight:600;border-bottom:2px solid #e2e8f0">Локация</th>
                <th style="padding:8px 12px;text-align:left;color:#555;font-weight:600;border-bottom:2px solid #e2e8f0">Истекает</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>

          <p style="margin:24px 0 0;font-size:13px;color:#888">
            <a href="{settings.app_url}" style="color:#1a5fa8">Открыть TapeRotation</a>
          </p>
        </td></tr>

        <!-- Footer -->
        <tr style="background:#f8fafc">
          <td style="padding:14px 32px;font-size:11px;color:#aaa;border-top:1px solid #e2e8f0">
            Автоматическое уведомление от TapeRotation &mdash; не отвечайте на это письмо.
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_notification(sets: list[models.TapeSet], subject: str, heading: str, intro: str):
    if not sets or not settings.smtp_host or not settings.notify_email:
        return

    html = _build_html(heading, intro, sets)

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from
    msg["To"] = settings.notify_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            if smtp.has_extn("STARTTLS"):
                smtp.starttls()
                smtp.ehlo()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from, settings.notify_email, msg.as_string())
            print(f"[email] Отправлено: {subject} → {settings.notify_email}")
    except Exception as e:
        print(f"[email] Ошибка отправки: {e}")


def notify_expired(db_session) -> int:
    from app.models import TapeSet, SetStatus
    today = date.today()
    sets = (
        db_session.query(TapeSet)
        .filter(TapeSet.expires_at <= today, TapeSet.status != SetStatus.returned)
        .all()
    )
    for s in sets:
        if s.status != SetStatus.expired:
            s.status = SetStatus.expired
    db_session.commit()
    send_notification(
        sets,
        subject=f"[TapeRotation] Просроченные наборы: {len(sets)} шт.",
        heading="Наборы лент с истёкшим сроком хранения",
        intro="Следующие наборы превысили срок хранения и требуют возврата в библиотеку.",
    )
    return len(sets)


def notify_expiring_soon(db_session) -> int:
    from datetime import timedelta
    from app.models import TapeSet, SetStatus
    today = date.today()
    deadline = today + timedelta(days=settings.notify_days_before)
    sets = (
        db_session.query(TapeSet)
        .filter(
            TapeSet.expires_at > today,
            TapeSet.expires_at <= deadline,
            TapeSet.status == SetStatus.in_storage,
        )
        .all()
    )
    send_notification(
        sets,
        subject=f"[TapeRotation] Скоро истекают: {len(sets)} шт.",
        heading=f"Наборы лент, срок которых истекает в ближайшие {settings.notify_days_before} дней",
        intro="Подготовьте следующие наборы к возврату в библиотеку.",
    )
    return len(sets)
