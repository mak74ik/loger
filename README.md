# 🏴‍☠️ loger (1073)

> **Darknet BBS Autonomous Program Discovery & Real-Time Terminal Log Hub**  
> *Port `1073` (`l-1, o-0, g-7, e-3`)*

[![License: MIT](https://img.shields.io/badge/License-MIT-00ff66.svg)](https://opensource.org/licenses/MIT)
[![Port 1073](https://img.shields.io/badge/port-1073-39ff14.svg)](http://127.0.0.1:1073)
[![Aesthetic](https://img.shields.io/badge/style-4chan%20%2F%20darknet%20textboard-black.svg)]()

```text
+-----------------------------------------------------------------------------------------------+
|  1073 // L-O-G-E // DARKNET BBS ARCHIVE & RECEPTOR PROTOCOL                                   |
|  ANONYMOUS NODE MONITOR // TAILSCALE MESH 127.0.0.1:1073                                 |
+-----------------------------------------------------------------------------------------------+
```

**`loger`** — хакерский минималистичный инструмент мониторинга и стриминга логов для homelab серверов в эстетике старых форумов (4chan / BBS / Darknet Textboards). 

Автоматически обнаруживает запущенные сервисы (Docker, systemd, открытые сокеты), стримит логи и доступен одновременно в **Linux-терминале** (включая прямой `curl`), и через **Darknet Web-дашборд на порту 1073**.

---

## 💻 SSH & Terminal Commands

```bash
# Вывести текстовую доску активных программ и сокетов:
loger status

# Реалтайм стрим логов в матричном стиле (Ctrl+C для выхода):
loger logs

# Интерактивный визард добавления нового эндпоинта программы:
loger new

# Быстрое добавление эндпоинта с аргументами:
loger add "CyberBridge Node" "http://127.0.0.1:8888" --port 8888 --category "Gateway"

# Управление фоновым демоном:
loger stop       # Остановить службу loger на порту 1073
loger start      # Запустить службу loger
loger restart    # Перезагрузить службу
loger reset      # Сбросить добавленные эндпоинты к чистым дефолтам

# Справка по всем командам:
loger help
```

---

## 📟 Прямой доступ из терминала через cURL

Если кто-то заходит через SSH или опрашивает сервер из терминала, `loger` автоматически определяет `curl` и возвращает чистый цветной ANSI-дашборд:

```bash
curl http://127.0.0.1:1073
```

---

## 🌐 Darknet Web Board (Порт 1073)

Откройте в браузере: **`http://127.0.0.1:1073`**

- **Стиль 4chan / Darknet Textboard:** Фосфорный зелёный `#00ff66`, цитаты `>greentext`, номера постов `No. 1073001`, тумблер кинескопных линий CRT.
- **Интерактивная доска `/b/`:** Карточки найденных сервисов с пингом, статусом `ONLINE` и ссылками быстрого перехода.
- **Живая лента `/live/`:** Потоковый терминальный провод (SSE) с логами и фильтрацией.
- **Форма `/new/`:** Регистрация новых адресов прямо в браузере.

---

## 📜 License

MIT License © 2026 [mak74ik](https://github.com/mak74ik)
