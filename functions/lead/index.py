"""Приём заявок с лендинга xmark.oplot-it.ru — Yandex Cloud Functions (ru-central1).

Заявка не покидает РФ: браузер отправляет её напрямую сюда (Vercel отдаёт только статику).
Функция:
  1. проверяет Origin, метод, размер и поля;
  2. сохраняет заявку JSON-файлом в бакет Object Storage (BUCKET) — журнал заявок и согласий;
  3. если заданы SMTP_* — отправляет уведомление на NOTIFY_TO.

Переменные окружения:
  BUCKET           имя бакета Object Storage (обязательно)
  ALLOWED_ORIGINS  через запятую, по умолчанию https://xmark.oplot-it.ru
  NOTIFY_TO        адрес для уведомлений, по умолчанию office@oplot-it.ru
  SMTP_HOST, SMTP_PORT (465), SMTP_USER, SMTP_PASS — почта отправителя (необязательно)

Доступ к бакету — по IAM-токену сервисного аккаунта функции (context.token), ключи не нужны.
"""
import base64
import json
import os
import re
import smtplib
import ssl
import time
import urllib.request
import uuid
from email.message import EmailMessage

ALLOWED = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "https://xmark.oplot-it.ru").split(",") if o.strip()]
BUCKET = os.environ.get("BUCKET", "")
NOTIFY_TO = os.environ.get("NOTIFY_TO", "office@oplot-it.ru")
FIELDS = {"name": 100, "company": 200, "phone": 40, "seats": 20, "comment": 2000}
PHONE_RE = re.compile(r"^[0-9+()\-\s]{6,40}$")


def _resp(code, body, origin):
    headers = {"Content-Type": "application/json; charset=utf-8", "Vary": "Origin"}
    if origin in ALLOWED:
        headers.update({
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "86400",
        })
    return {"statusCode": code, "headers": headers, "body": json.dumps(body, ensure_ascii=False)}


def _store(lead, token):
    key = time.strftime("leads/%Y/%m/%d/", time.gmtime()) + lead["id"] + ".json"
    req = urllib.request.Request(
        f"https://storage.yandexcloud.net/{BUCKET}/{key}",
        data=json.dumps(lead, ensure_ascii=False, indent=2).encode(),
        method="PUT",
        headers={"Content-Type": "application/json; charset=utf-8", "X-YaCloud-SubjectToken": token},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        if r.status >= 300:
            raise RuntimeError(f"storage HTTP {r.status}")
    return key


def _notify(lead):
    host, user, pwd = os.environ.get("SMTP_HOST"), os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS")
    if not (host and user and pwd):
        return False
    msg = EmailMessage()
    msg["Subject"] = f"Заявка X-Mark: {lead['company'] or lead['name']}"
    msg["From"] = user
    msg["To"] = NOTIFY_TO
    msg.set_content("\n".join([
        f"Имя: {lead['name']}",
        f"Компания: {lead['company']}",
        f"Телефон: {lead['phone']}",
        f"Рабочих мест: {lead['seats']}",
        f"Комментарий: {lead['comment']}",
        "",
        f"Получено: {lead['received_at']} UTC, id {lead['id']}",
        f"Согласие на обработку ПДн: {lead['consent']} (политика {lead['consent_policy']})",
    ]))
    with smtplib.SMTP_SSL(host, int(os.environ.get("SMTP_PORT", "465")), context=ssl.create_default_context(), timeout=10) as s:
        s.login(user, pwd)
        s.send_message(msg)
    return True


def handler(event, context):
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    origin = headers.get("origin", "")
    method = event.get("httpMethod", "")

    if method == "OPTIONS":
        return _resp(204 if origin in ALLOWED else 403, {}, origin)
    if method != "POST":
        return _resp(405, {"error": "method"}, origin)
    if origin not in ALLOWED:
        return _resp(403, {"error": "origin"}, origin)

    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8", "replace")
    if len(raw) > 8000:
        return _resp(413, {"error": "too large"}, origin)
    try:
        data = json.loads(raw)
    except ValueError:
        return _resp(400, {"error": "json"}, origin)

    if data.get("website"):  # поле-ловушка для ботов
        return _resp(200, {"ok": True}, origin)

    lead = {k: str(data.get(k, "")).strip()[:limit] for k, limit in FIELDS.items()}
    if not lead["name"] or not PHONE_RE.match(lead["phone"]):
        return _resp(422, {"error": "Укажите имя и телефон"}, origin)
    if data.get("consent") is not True:
        return _resp(422, {"error": "Нужно согласие на обработку персональных данных"}, origin)

    lead.update({
        "id": uuid.uuid4().hex,
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "consent": True,
        "consent_policy": "https://xmark.oplot-it.ru/privacy.html",
        "source": origin,
        "user_agent": headers.get("user-agent", "")[:300],
    })

    token = (getattr(context, "token", None) or {}).get("access_token")
    if not BUCKET or not token:
        return _resp(500, {"error": "storage not configured"}, origin)
    try:
        _store(lead, token)
    except Exception as e:  # noqa: BLE001
        print(f"store failed: {e}")
        return _resp(502, {"error": "Не удалось сохранить заявку"}, origin)

    try:
        _notify(lead)
    except Exception as e:  # noqa: BLE001 — заявка уже сохранена, уведомление не критично
        print(f"notify failed: {e}")

    return _resp(200, {"ok": True, "id": lead["id"]}, origin)
