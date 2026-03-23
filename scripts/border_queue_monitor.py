#!/usr/bin/env python3
"""
Monitor Estonian border queue page for Koidula & Luhamaa (vehicle class A/B)
"First available pre-reservation time" — alert when value is no longer N/A.

Page: https://www.estonianborder.eu/yphis/borderQueueInfo.action
Cells in HTML: td#frt-4 (Koidula A/B), td#frt-7 (Luhamaa A/B).

Run 24/7 (e.g. systemd, Docker, or `python scripts/border_queue_monitor.py`).
Default interval: 30 seconds. Request timeout: 90s (slow site).

Configure at least one notification channel (or BORDER_MONITOR_DRY_RUN=1):

  E-mail:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    ALERT_EMAIL (default: artjoms.grinakins@gmail.com), SMTP_FROM (optional)

  ntfy (simplest — install app ntfy, subscribe to a secret topic name):
    NTFY_TOPIC=my-secret-topic-7xK9
    NTFY_SERVER=https://ntfy.sh   (optional; your self-hosted URL if needed)
    NTFY_TOKEN=...                (optional, Bearer for private ntfy)

  Telegram:
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (numeric id or @channelusername)

  Discord:
    DISCORD_WEBHOOK_URL (channel webhook URL)

All configured channels receive each alert.

Optional:
  BORDER_QUEUE_URL, CHECK_INTERVAL_SECONDS, HTTP_TIMEOUT_SECONDS
  BORDER_MONITOR_STATE_FILE, BORDER_MONITOR_DRY_RUN=1, BORDER_MONITOR_ONCE=1, --once
  scripts/telegram.env — автоматически (если нет BORDER_MONITOR_ENV_FILE); не переопределяет уже заданные переменные
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx", file=sys.stderr)
    raise

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install beautifulsoup4: pip install beautifulsoup4", file=sys.stderr)
    raise

LOG = logging.getLogger("border_monitor")

DEFAULT_URL = "https://www.estonianborder.eu/yphis/borderQueueInfo.action"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# First available pre-reservation time — A/B column
CELL_IDS = {
    "Koidula A/B": "frt-4",
    "Luhamaa A/B": "frt-7",
}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def load_optional_env_file(path: Path) -> None:
    """KEY=value lines; does not override variables already set in the environment."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _is_na(value: str | None) -> bool:
    if value is None:
        return True
    t = " ".join(value.split()).strip()
    if not t:
        return True
    if t.upper() == "N/A":
        return True
    if t == "—" or t == "-":
        return True
    return False


def fetch_slot_times(url: str, timeout: float) -> dict[str, str | None]:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en,en-US;q=0.9"}
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out: dict[str, str | None] = {}
    for label, cell_id in CELL_IDS.items():
        td = soup.find("td", id=cell_id)
        if not td:
            LOG.warning("Cell #%s not found on page", cell_id)
            out[label] = None
            continue
        text = td.get_text(separator=" ", strip=True)
        out[label] = text if text else None
    return out


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        LOG.warning("Could not read state file %s: %s", path, e)
        return {}


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def send_email(
    subject: str,
    body: str,
    to_addr: str,
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    mail_from: str,
    use_starttls: bool,
) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = to_addr

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=60) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as smtp:
            smtp.ehlo()
            if use_starttls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)


def send_ntfy(
    subject: str,
    body: str,
    *,
    server: str,
    topic: str,
    token: str,
) -> None:
    base = server.rstrip("/")
    url = f"{base}/{topic}"
    headers = {"Title": subject[:200]}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, content=body.encode("utf-8"), headers=headers)
        r.raise_for_status()


def send_telegram(subject: str, body: str, *, bot_token: str, chat_id: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    text = f"{subject}\n\n{body}"
    if len(text) > 4000:
        text = text[:3997] + "..."
    payload = {"chat_id": chat_id, "text": text}
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(data)


def send_discord_webhook(subject: str, body: str, *, webhook_url: str) -> None:
    content = f"**{subject}**\n{body}"
    if len(content) > 1900:
        content = content[:1897] + "..."
    with httpx.Client(timeout=30.0) as client:
        r = client.post(webhook_url, json={"content": content})
        r.raise_for_status()


def send_all_notifications(
    subject: str,
    body: str,
    *,
    dry_run: bool,
    smtp_cfg: dict[str, Any] | None,
    alert_to: str,
    ntfy_topic: str,
    ntfy_server: str,
    ntfy_token: str,
    telegram_token: str,
    telegram_chat: str,
    discord_webhook: str,
) -> None:
    if dry_run:
        LOG.info("Would notify:\nSubject: %s\n%s", subject, body)
        return

    if smtp_cfg:
        send_email(subject, body, alert_to, **smtp_cfg)
        LOG.info("E-mail sent to %s", alert_to)

    if ntfy_topic:
        send_ntfy(subject, body, server=ntfy_server, topic=ntfy_topic, token=ntfy_token)
        LOG.info("ntfy sent to topic %s", ntfy_topic)

    if telegram_token and telegram_chat:
        send_telegram(subject, body, bot_token=telegram_token, chat_id=telegram_chat)
        LOG.info("Telegram message sent")

    if discord_webhook:
        send_discord_webhook(subject, body, webhook_url=discord_webhook)
        LOG.info("Discord webhook posted")


def run_loop(*, once: bool = False) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Optional file (Telegram): copy scripts/telegram.env.example -> scripts/telegram.env
    env_path = os.environ.get("BORDER_MONITOR_ENV_FILE", "").strip()
    if env_path:
        load_optional_env_file(Path(env_path))
    else:
        load_optional_env_file(Path(__file__).resolve().parent / "telegram.env")

    url = os.environ.get("BORDER_QUEUE_URL", DEFAULT_URL).strip()
    interval = _env_int("CHECK_INTERVAL_SECONDS", 30)
    timeout = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "90"))
    state_path = Path(
        os.environ.get(
            "BORDER_MONITOR_STATE_FILE",
            str(Path(__file__).resolve().parent.parent / "border_monitor_state.json"),
        )
    )
    dry_run = os.environ.get("BORDER_MONITOR_DRY_RUN", "").strip() in ("1", "true", "yes")

    alert_to = os.environ.get("ALERT_EMAIL", "artjoms.grinakins@gmail.com").strip()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = _env_int("SMTP_PORT", 587)
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    mail_from = os.environ.get("SMTP_FROM", smtp_user).strip()
    use_starttls = os.environ.get("SMTP_USE_TLS", "1").strip() not in ("0", "false", "no")

    ntfy_topic = os.environ.get("NTFY_TOPIC", "").strip()
    ntfy_server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").strip().rstrip("/")
    ntfy_token = os.environ.get("NTFY_TOKEN", "").strip()

    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    has_smtp = bool(smtp_host and smtp_user and smtp_password)
    has_ntfy = bool(ntfy_topic)
    has_telegram = bool(telegram_token and telegram_chat)
    has_discord = bool(discord_webhook)

    smtp_cfg: dict[str, Any] | None = None
    if has_smtp:
        smtp_cfg = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password": smtp_password,
            "mail_from": mail_from or smtp_user,
            "use_starttls": use_starttls,
        }

    LOG.info("Monitoring %s every %s s (timeout %s s)", url, interval, timeout)
    LOG.info("Watch: %s", ", ".join(CELL_IDS.keys()))

    if dry_run:
        LOG.info("DRY RUN — no notifications will be sent")
    elif not (has_smtp or has_ntfy or has_telegram or has_discord):
        LOG.error(
            "Configure at least one channel: SMTP, NTFY_TOPIC, TELEGRAM_BOT_TOKEN+TELEGRAM_CHAT_ID, "
            "DISCORD_WEBHOOK_URL — or BORDER_MONITOR_DRY_RUN=1 for testing."
        )
        sys.exit(1)
    else:
        parts = []
        if has_smtp:
            parts.append("e-mail")
        if has_ntfy:
            parts.append("ntfy")
        if has_telegram:
            parts.append("telegram")
        if has_discord:
            parts.append("discord")
        LOG.info("Notify channels: %s", ", ".join(parts))

    state: dict[str, Any] = load_state(state_path)
    # last value we already notified about (to avoid spamming every 30s)
    last_notified: dict[str, str | None] = state.get("last_notified", {})

    while True:
        try:
            slots = fetch_slot_times(url, timeout=timeout)
            ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            line = " | ".join(f"{k}={slots.get(k)!r}" for k in CELL_IDS)
            LOG.info("[%s] %s", ts, line)

            for label, cell_id in CELL_IDS.items():
                raw = slots.get(label)
                if raw is None:
                    continue
                if _is_na(raw):
                    # slot closed again — allow future alert
                    if label in last_notified:
                        del last_notified[label]
                    continue

                prev = last_notified.get(label)
                if prev == raw:
                    continue

                subject = f"[Border] Slot available: {label}"
                body = (
                    f"Checkpoint: {label}\n"
                    f"First available pre-reservation time: {raw}\n\n"
                    f"Page: {url}\n"
                    f"Checked at: {ts}\n"
                )

                send_all_notifications(
                    subject,
                    body,
                    dry_run=dry_run,
                    smtp_cfg=smtp_cfg,
                    alert_to=alert_to,
                    ntfy_topic=ntfy_topic,
                    ntfy_server=ntfy_server,
                    ntfy_token=ntfy_token,
                    telegram_token=telegram_token,
                    telegram_chat=telegram_chat,
                    discord_webhook=discord_webhook,
                )
                if not dry_run:
                    LOG.info("Alert done for %s", label)

                last_notified[label] = raw
                state["last_notified"] = last_notified
                save_state(state_path, state)

        except Exception as e:
            LOG.exception("Check failed: %s", e)

        if once:
            break
        time.sleep(interval)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    once = "--once" in sys.argv or os.environ.get("BORDER_MONITOR_ONCE", "").strip() in (
        "1",
        "true",
        "yes",
    )
    run_loop(once=once)


if __name__ == "__main__":
    main()
