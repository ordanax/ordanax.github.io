---
layout: post
title: "Bluetooth-звук пропадает при блокировке: WirePlumber suspend"
description: "Почему Bluetooth-колонка замолкает после блокировки экрана и сна, и как отключить suspend-профили WirePlumber, чтобы звук не пропадал."
date: 2026-09-16 00:00:00 +0300
permalink: /bluetooth-zvuk-wireplumber-suspend
categories:
- linux
- arch linux
- configs
- hardware
tags:
- bluetooth
- pipewire
- wireplumber
- audio
- suspend
- troubleshooting
edit: true
---


Bluetooth-звук пропадает после блокировки экрана или ухода в сон: WirePlumber переводит bluetooth-узел в suspend-профиль и не возвращает его обратно. Лечится это отключением suspend для bluetooth-устройств в конфиге WirePlumber и перезапуском звуковых сервисов. BlueZ autoconnect тут ни при чём.

## Что происходит с Bluetooth-звуком при блокировке

В современном Arch Linux звуком заведует PipeWire, а его сессионным менеджером работает WirePlumber. WirePlumber решает, какие узлы активны, а какие можно усыпить. При смене активного профиля, при блокировке экрана или уходе в сон он переводит bluetooth-устройство в suspend-профиль. Просыпается система, а узел остаётся спящим. Колонка подключена, индикатор горит, а звука нет.

Suspend-профили придумали для экономии энергии. Пока устройство молчит, зачем держать его активным? Логика здравая, но на Bluetooth-колонках она даёт сбой: после пробуждения узел не возвращается в running.

У меня это выглядело так. Колонка BTS-012, блокирую экран, возвращаюсь, а музыка молчит. Переподключаю колонку вручную, звук возвращается. Через пару дней надоело, начал копать.

Autoconnect в BlueZ эту проблему не решает. Он отвечает за переподключение устройства после разрыва связи, а тут связь не рвётся. Узел просто спит внутри WirePlumber. Поэтому первым делом я проверил autoconnect, потом выключил его, потом включил обратно. Ничего не менялось. Тогда я полез в журнал.

## Как проверить, что виноват WirePlumber

Сначала посмотри на состояние bluetooth-узла:

```bash
wpctl status
```

В выводе ищи свою колонку. Если узел в состоянии suspended, а не running, картина ясна.

Дальше проверь журнал WirePlumber:

```bash
journalctl --user -u wireplumber | grep -i suspend
```

Там будут строки про suspend-профили. У меня журнал прямо показывал, как узел уходит в suspend при блокировке.

И убедись, что все три сервиса живы:

```bash
systemctl --user list-units | grep -iE 'wireplumber|pipewire'
```

Если wireplumber, pipewire и pipewire-pulse в списке и активны, переходим к лечению.

## Как отключить suspend для Bluetooth-устройств

WirePlumber читает конфиги из `~/.config/wireplumber/main.lua.d/`. Создай там файл, который запрещает suspend для bluetooth-узлов.

```bash
mkdir -p ~/.config/wireplumber/main.lua.d
```

В файле, например `51-bluetooth-no-suspend.lua`, выставляешь для bluetooth-узлов `suspend-node = false` и настраиваешь правила `bluez_monitor`. Примерно так:

```lua
rule = {
  matches = {
    {
      { "node.name", "matches", "bluez_output.*" },
    },
  },
  apply_properties = {
    ["node.suspend-node"] = false,
  },
}

table.insert(bluez_monitor.rules, rule)
```

Точный синтаксис зависит от версии WirePlumber, но смысл один: bluetooth-узлы больше не усыпляются.

После правки перезапусти звуковые сервисы:

```bash
systemctl --user restart wireplumber pipewire pipewire-pulse
```

Проверь `wpctl status` ещё раз. Узел колонки должен оставаться в состоянии running. Заблокируй экран, подожди, разблокируй. Звук на месте.

Если после перезапуска колонка не появилась в `wpctl status`, подожди пару секунд или переподключи устройство. WirePlumber подхватывает конфиг при старте, так что перезапуск обязателен.

## Типичные проблемы

**Autoconnect включён, а звук всё равно пропадает.** Нормально. Autoconnect не управляет suspend-профилями, он только переподключает устройство после разрыва. Проблема глубже, в WirePlumber.

**Звук пропадает и при переключении устройств.** Тот же механизм. Смена активного профиля тоже усыпляет bluetooth-узел. Отключение suspend решает и этот случай.

**После перезапуска сервисов колонка отвалилась.** Переподключи её вручную один раз. Дальше она будет вести себя нормально.

## Частые вопросы

**Почему колонка подключена, но звука нет?**
Устройство подключено на уровне BlueZ, но звуковой узел внутри WirePlumber уснул. PipeWire не возвращает его в активное состояние после пробуждения системы.

**Autoconnect решит проблему?**
Нет. Autoconnect отвечает за переподключение после разрыва связи, а не за состояние узла в WirePlumber.

**Нужно ли перезапускать PipeWire после правки конфига?**
Да. Без перезапуска WirePlumber не перечитает конфиг. Команда: `systemctl --user restart wireplumber pipewire pipewire-pulse`.

**Это касается только Bluetooth?**
Нет, suspend-профили работают и для других устройств. Но чаще всего проблема заметна именно на Bluetooth-колонках.

**Что делать, если звук всё равно пропадает?**
Проверь, что файл конфига лежит в правильной папке и WirePlumber его подхватил. Смотри `wpctl status` после перезапуска: узел должен быть running.

## Заключение

Bluetooth-звук после блокировки экрана пропадает не из-за BlueZ, а из-за WirePlumber, который усыпляет bluetooth-узел. Отключение suspend для bluetooth-устройств в `~/.config/wireplumber/main.lua.d/` и перезапуск звуковых сервисов решают проблему раз и навсегда. У меня колонка BTS-012 больше не замолкает.

Если система у тебя зависает при высокой нагрузке, глянь статью про фикс зависаний: https://ordanax.github.io/high_cpu_freeze_fix. А если только собираешь окружение, пригодится установка Hyprland: https://ordanax.github.io/hyprland-arch-linux, или GNOME: https://ordanax.github.io/gnome-ustanovka-linux.

## Полезные ресурсы

- [WirePlumber на ArchWiki](https://wiki.archlinux.org/title/WirePlumber)
- [PipeWire на ArchWiki](https://wiki.archlinux.org/title/PipeWire)