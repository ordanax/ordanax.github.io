---
layout: post
title: "Часовой пояс, время и синхронизация в Arch Linux"
description: "Как выставить часовой пояс, включить NTP-синхронизацию и починить сбивающееся время в Arch Linux. Команды timedatectl и настройка systemd-timesyncd."
date: 2026-09-19 00:00:00 +0300
permalink: /chasovoy-poyas-vremya-ntp
categories:
- linux
- arch linux
- configs
tags:
- timedatectl
- ntp
- time
- systemd-timesyncd
- timezone
edit: true
---

Часовой пояс в Arch Linux выставляется одной командой: `timedatectl set-timezone Europe/Moscow`. Автосинхронизация времени через NTP включается так: `timedatectl set-ntp true`. После этих двух команд время будет точным и правильным. Дальше разберём каждую опцию.

## Как проверить текущее время и зону

Посмотри, что показывает система:

```
timedatectl status
```

В выводе увидишь:

- **Local time** — локальное время с учётом часового пояса.
- **Universal time** — UTC (нулевой меридиан).
- **RTC time** — время аппаратных часов (BIOS/UEFI).
- **Time zone** — текущий пояс, например `Europe/Moscow (MSK, +0300)`.
- **System clock synchronized** — синхронизирован ли системный час с NTP-сервером.
- **NTP service** — активна ли служба синхронизации.

Если видишь `NTP service: inactive` — время не синхронизируется и может уплыть. Если `RTC in local TZ: yes` — аппаратные часы настроены на локальное время, что часто ломает dualboot. Детали синхронизации (сервер, offset, jitter) покажет `timedatectl timesync-status`.

## Как установить часовой пояс

### Через timedatectl

Список доступных поясов: `timedatectl list-timezones`. Можно фильтровать: `timedatectl list-timezones | grep Moscow`.

Установка:

```
sudo timedatectl set-timezone Europe/Moscow
```

Команда создаёт симлинк `/etc/localtime` на файл из `/usr/share/zoneinfo/`. Вся система, включая запущенные программы, сразу начнёт показывать время в новом поясе.

### Через tzselect

Не хочешь копаться в списках — используй `tzselect` без sudo: утилита задаст пару вопросов (континент, город) и подскажет нужное значение TZ, которое потом выставишь через `timedatectl` из списка выше.

### Автоматически по геолокации

В GNOME и KDE Plasma пояс определяется автоматически — включи переключатель в настройках «Дата и время».

## Как включить автосинхронизацию времени

### systemd-timesyncd — что это и зачем

По умолчанию в Arch Linux стоит **systemd-timesyncd** — лёгкий SNTP-клиент. Он не тянет полную NTP-реализацию, а просто запрашивает время у одного сервера и выставляет его. Для десктопа этого достаточно.

Включить синхронизацию одной командой:

```
sudo timedatectl set-ntp true
```

Служба `systemd-timesyncd.service` запустится и будет синхронизировать время при наличии сети. Проверь:

```
timedatectl status
```

Строки `System clock synchronized: yes` и `NTP service: active` — всё в порядке.

### Настройка NTP-серверов

По умолчанию используются серверы пула `0.arch.pool.ntp.org`. Поменять их можно в `/etc/systemd/timesyncd.conf`, секция `[Time]`:

```
[Time]
NTP=0.arch.pool.ntp.org 1.arch.pool.ntp.org 2.arch.pool.ntp.org 3.arch.pool.ntp.org
FallbackNTP=0.pool.ntp.org 1.pool.ntp.org
```

После правки перезапусти службу: `sudo systemctl restart systemd-timesyncd`.

### Логи синхронизации

Если что-то идёт не так, смотри логи:

```
journalctl -u systemd-timesyncd
```

Там видно, к какому серверу подключается служба и какой offset получается.

### Chrony — альтернатива для продвинутых

Нужна высокая точность или ноутбук, который часто переключается между сетями? Поставь **chrony**: `sudo pacman -S chrony`. Он быстрее сходится к эталонному времени и лучше работает с нестабильными соединениями. Перед установкой отключи systemd-timesyncd: `sudo timedatectl set-ntp false`.

## Windows и локальное время — как подружить

Классика: после запуска Windows в dualboot время сбивается на час. Причина — Windows считает аппаратные часы (RTC) локальными, а Linux — UTC. Каждая ОС воспринимает правку другой как сдвиг.

### Правильный путь — переключить Windows на UTC

Рекомендация ArchWiki. В Windows открой командную строку от администратора и выполни:

```
reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /d 1 /t REG_DWORD /f
```

Windows начнёт использовать UTC для аппаратных часов — как и Linux. Перезагрузись в обе системы и проверь время.

### Быстрый путь — переключить Linux на localtime

Не хочешь лезть в реестр? Скажи Linux считать аппаратные часы локальными:

```
sudo timedatectl set-local-rtc 1
```

Решение рабочее, но не идеальное: systemd может вести себя непредсказуемо при смене поясов и переходе на летнее время. Вернуть обратно: `sudo timedatectl set-local-rtc 0`.

Про проблемы с GRUB после установки Windows читай в статье [«Dualboot: Windows пропала из меню GRUB»](https://ordanax.github.io/dualboot-windows-propala-iz-grub).

## Что делать, если время сбивается

### Проверь синхронизацию

```
timedatectl status
```

Если `System clock synchronized: no` или `NTP service: inactive` — включай `sudo timedatectl set-ntp true`.

### Проверь аппаратные часы

Посмотри время RTC: `sudo hwclock --show`. Сильно отличается от системного? Синхронизируй: `sudo hwclock --systohc` — команда записывает системное время в аппаратные часы.

### Посмотри логи

```
journalctl -u systemd-timesyncd -f
```

Флаг `-f` — логи в реальном времени. Видишь ошибки подключения к серверам — проверь интернет и поменяй серверы в `/etc/systemd/timesyncd.conf`.

### Частые причины сбоя

- **Dualboot с Windows** — конфликт UTC/localtime (описано выше).
- **Нет интернета** — systemd-timesyncd не может достучаться до сервера.
- **Виртуальная машина** — время гостя «плывёт» из-за нагрузки на хост. В KVM помогает модуль `ptp_kvm`, в VirtualBox — «Гостевые дополнения».
- **Села батарейка CMOS** — время сбивается после выключения питания. Замена CR2032 решает навсегда. Что ещё проверить после установки — в [«Первый час после установки Arch»](https://ordanax.github.io/pervyi-chas-posle-ustanovki-arch).

## Частые вопросы

### Нужно ли вообще включать NTP?

Да. Без синхронизации время постепенно уплывает. Это ломает SSL-сертификаты (браузер отказывается открывать сайты), путает логи и почту.

### systemd-timesyncd или chrony?

Для большинства — **systemd-timesyncd**. Он уже стоит, не ест ресурсы и делает своё дело. Chrony нужен для высокой точности или сложных сетевых условий.

### Почему после перезагрузки время снова сбивается?

Проверь два момента: включена ли NTP-синхронизация (`timedatectl status`) и нет ли конфликта UTC/localtime в dualboot. Если всё в порядке — скорее всего, села батарейка RTC.

### Как поменять NTP-сервер на российский?

В `/etc/systemd/timesyncd.conf` пропиши `NTP=0.ru.pool.ntp.org 1.ru.pool.ntp.org 2.ru.pool.ntp.org 3.ru.pool.ntp.org`. Полный список серверов — на [pool.ntp.org](https://www.pool.ntp.org/zone/ru).

## Полезные ресурсы

- [Systemd-timesyncd — ArchWiki](https://wiki.archlinux.org/title/Systemd-timesyncd) — документация по SNTP-клиенту.
- [System time — ArchWiki](https://wiki.archlinux.org/title/System_time) — часы, RTC, dualboot, синхронизация.
- [fstab: поля на практике](https://ordanax.github.io/fstab-polya-na-praktike) — разбор полей fstab.
- [journalctl: первая загрузка](https://ordanax.github.io/chitat-journalctl-b-pervaya-zagruzka) — как читать логи systemd.
- [Установка Arch Linux 2026: пошагово](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya) — пошаговая установка Arch.

## Заключение

Настроить время в Arch Linux — дело двух команд: `timedatectl set-timezone` для пояса и `timedatectl set-ntp true` для синхронизации. В dualboot с Windows разберись с UTC/localtime, чтобы системы не воевали. А если время уплывает — сначала проверь синхронизацию, потом аппаратные часы, и только потом меняй батарейку.