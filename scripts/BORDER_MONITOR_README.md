# Монитор очереди на границе (Koidula / Luhamaa, A/B)

Скрипт раз в **30 секунд** запрашивает страницу GoSwift и смотрит ячейки **First available pre-reservation time** для классов **A/B**:
- **Koidula** — элемент `#frt-4`
- **Luhamaa** — элемент `#frt-7`

Как только значение перестаёт быть `N/A` (появляется дата/время), уходит **уведомление** (Telegram / почта / др.). Повтор для того же текста не шлётся; если снова `N/A`, при следующем появлении слота уведомление снова уйдёт.

## Зависимости

```bash
pip install httpx beautifulsoup4
```

(или добавьте `beautifulsoup4` в основной `requirements.txt` проекта.)

## Уведомления в Telegram (рекомендуемый способ)

### Шаг 1. Создать бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram.
2. Отправьте `/newbot`, задайте имя и username (должен оканчиваться на `bot`).
3. Скопируйте **токен** вида `123456789:AAH...` — это `TELEGRAM_BOT_TOKEN`.

### Шаг 2. Узнать chat_id

**Личные сообщения**

1. Найдите своего бота по username и нажмите **Start** (или отправьте любое сообщение).
2. В браузере откройте (подставьте свой токен):

   `https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates`

3. В ответе JSON найдите `"chat":{"id": 123456789` — это **положительное** число, ваш `TELEGRAM_CHAT_ID`.

**Группа**

1. Добавьте бота в группу, дайте право писать сообщения (при необходимости сделайте админом).
2. Напишите в группе что-нибудь с упоминанием бота или просто сообщение после того, как бот в группе.
3. Снова откройте `getUpdates` — у группы `id` будет **отрицательным**, например `-1001234567890`. Его целиком и укажите как `TELEGRAM_CHAT_ID`.

### Шаг 3. Запуск

**Вариант А — файл `scripts/telegram.env` (удобно)**

1. Скопируйте `scripts/telegram.env.example` → `scripts/telegram.env`.
2. Впишите токен и `chat_id` (файл `telegram.env` в git не попадёт).

```bash
cd путь/к/maturity
python scripts/border_queue_monitor.py
```

Скрипт сам подхватит `scripts/telegram.env`, если переменные ещё не заданы в системе.

**Вариант B — переменные окружения**

```text
set TELEGRAM_BOT_TOKEN=123456:AAH...
set TELEGRAM_CHAT_ID=123456789
python scripts/border_queue_monitor.py
```

Другой путь к env-файлу: `BORDER_MONITOR_ENV_FILE=C:\path\to\secrets.env`.

### Проверка без реального слота

```text
set BORDER_MONITOR_DRY_RUN=1
python scripts/border_queue_monitor.py --once
```

В логе будет строка с `Koidula A/B=...` — значит сайт читается. Реальное сообщение в Telegram уйдёт только когда вместо `N/A` появится дата.

---

## Другие каналы (без Telegram)

### **ntfy**

1. Установите приложение **ntfy** (Android / iOS) или откройте [ntfy.sh](https://ntfy.sh) в браузере.
2. Придумайте **длинное случайное имя топика** (как пароль), например `border-koidula-x7K9mQ2w` — по нему любой может подписаться, поэтому не делайте топик коротким и предсказуемым.
3. В приложении: **Subscribe to topic** → введите это имя.
4. Запуск монитора:

```text
set NTFY_TOPIC=border-koidula-x7K9mQ2w
python scripts/border_queue_monitor.py
```

Сервер по умолчанию `https://ntfy.sh`. Свой сервер: `NTFY_SERVER=https://ваш-ntfy.example.com`. Для закрытого ntfy: `NTFY_TOKEN=...`.

### **Discord**

В настройках канала → **Integrations** → **Webhooks** → скопируйте URL.

```text
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
python scripts/border_queue_monitor.py
```

Можно включить **несколько каналов сразу** — уведомление уйдёт везде, где заданы переменные.

---

## Почта (Gmail), опционально

1. Включите двухфакторную аутентификацию и создайте [пароль приложения](https://myaccount.google.com/apppasswords).
2. Переменные окружения:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=ваш@gmail.com
SMTP_PASSWORD=пароль_приложения
ALERT_EMAIL=artjoms.grinakins@gmail.com
```

Запуск:

```bash
python scripts/border_queue_monitor.py
```

Для порта **587** с STARTTLS укажите `SMTP_PORT=587` (по умолчанию `SMTP_USE_TLS=1`).

## 24/7 на Linux (systemd)

Файл `/etc/systemd/system/border-monitor.service`:

```ini
[Unit]
Description=Estonian border queue monitor
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/path/to/maturity
EnvironmentFile=/path/to/maturity/scripts/telegram.env
ExecStart=/path/to/venv/bin/python scripts/border_queue_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now border-monitor.service
```

## Render.com (Background Worker + ntfy)

Твой топик: **`border-moi-st53182`**. На телефоне в ntfy уже должен быть **Subscribe** на этот же топик.

### 1. Новый сервис на Render

1. Зайди в [Render Dashboard](https://dashboard.render.com) → **New +** → **Background Worker**.
2. Подключи тот же репозиторий **maturity**, ветка **`master`**.
3. Заполни поля:

| Поле | Значение |
|------|----------|
| **Name** | например `border-monitor` |
| **Region** | ближе к EU (Frankfurt), сайт границы в Эстонии |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python scripts/border_queue_monitor.py` |

4. **Environment** → **Add Environment Variable**:
   - **Key:** `NTFY_TOPIC`  
   - **Value:** `border-moi-st53182`

   (Сервер ntfy по умолчанию `https://ntfy.sh` — менять не нужно.)

5. **Create Background Worker** → дождись успешного деплоя.

6. Открой **Logs** — должны идти строки вида  
   `Koidula A/B='N/A' | Luhamaa A/B='N/A'` каждые ~30 с.

### 2. Тариф

**Background Worker** на Render обычно **не входит в бесплатный** веб-тариф (это отдельный платный тип сервиса). Если бесплатного воркера нет — варианты: платный Worker на Render, либо запуск скрипта на своём ПК/VPS.

### 3. Тест ntfy

Пока слотов нет, push не придёт. Проверка подписки: с телефона или с ПК выполни:

```bash
curl -d "Тест с Render" https://ntfy.sh/border-moi-st53182
```

В приложении ntfy должно прийти уведомление **«Тест с Render»**.

## Параметры

| Переменная | По умолчанию |
|------------|----------------|
| `BORDER_QUEUE_URL` | страница borderQueueInfo |
| `CHECK_INTERVAL_SECONDS` | 30 |
| `HTTP_TIMEOUT_SECONDS` | 90 |
| `BORDER_MONITOR_STATE_FILE` | `border_monitor_state.json` в корне репозитория |
| `ALERT_EMAIL` | `artjoms.grinakins@gmail.com` |

Таймаут HTTP 90 с учитывает медленную загрузку сайта; страница при ответе уже содержит нужные ячейки (отдельный «ожидание 15 с» после загрузки не требуется).

## Примечание

Сайт может менять вёрстку; при поломке парсинга в логах будет предупреждение «Cell #… not found». Тогда нужно обновить ID в `CELL_IDS` в скрипте.
