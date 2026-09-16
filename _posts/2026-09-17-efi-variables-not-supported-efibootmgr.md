---
layout: post
title: "EFI variables are not supported: как починить efibootmgr"
description: "Ошибка efibootmgr: EFI variables are not supported on this system — причины и решения для Arch Linux. Проверка UEFI-режима, efivarfs и кривых прошивок."
date: 2026-09-17 00:00:00 +0300
permalink: /efi-variables-not-supported-efibootmgr
categories:
- linux
- arch linux
- boot
tags:
- efibootmgr
- uefi
- efivarfs
- grub
- secure-boot
- troubleshooting
edit: true
---

Ошибка `efibootmgr: EFI variables are not supported on this system` появляется, когда ядру недоступен интерфейс efivarfs — либо модуль не загружен, либо система стартовала в режиме BIOS/CSM, либо прошивка просто кривая. В большинстве случаев проблема решается за пять минут: загрузкой в UEFI-режим или ручным монтированием efivarfs.

## Что значит «EFI variables are not supported»

UEFI-прошивка хранит переменные: порядок загрузки, ключи Secure Boot, настройки железа. Ядро Linux получает доступ к ним через файловую систему efivarfs, смонтированную в `/sys/firmware/efi/efivars`. Утилита `efibootmgr` работает именно через этот интерфейс.

Когда ядро не видит efivarfs, `efibootmgr` честно говорит: «переменные недоступны». Причины три:

- Система загружена в режиме BIOS или CSM (Compatibility Support Module) — в этом режиме UEFI вообще не используется.
- Модуль `efivarfs` не загружен или файловая система не смонтирована.
- Прошивка материнской платы не соответствует спецификации UEFI (редкость, но бывает на старом железе).

## Почему efibootmgr не видит переменные

Прежде всего проверь, в каком режиме ты загружаешься. Это основная причина.

### Проверка UEFI-режима

Если `/sys/firmware/efi` существует — система в UEFI-режиме. Если нет — загрузилась через BIOS/CSM:

```bash
ls /sys/firmware/efi
```

Ошибка `No such file or directory` означает, что ты в Legacy-режиме. Тут нечего чинить из-под работающей системы — перезагрузись и выбери UEFI-вариант в boot menu.

Разрядность прошивки:

```bash
cat /sys/firmware/efi/fw_platform_size
```

Вернёт `64` для 64-бит UEFI или `32` для 32-бит.

## Как проверить доступ к efivar

Допустим, `/sys/firmware/efi` на месте. Убедись, что efivarfs смонтирован:

```bash
mount | grep efivarfs
```

Пустой вывод — efivarfs не смонтирован. Монтируй вручную:

```bash
sudo mount -t efivarfs efivarfs /sys/firmware/efi/efivars
```

Если модуль ядра не загружен:

```bash
sudo modprobe efivarfs
```

После этого попробуй снова:

```bash
efibootmgr
```

Если ошибки нет и виден список записей — всё работает. Если пишет `Function not implemented`, добавь параметр ядра `efi=runtime` и перезагрузись.

Для проверки доступности переменных есть пакет `efivar`:

```bash
efivar --list
```

Список переменных без ошибок — всё в порядке.

## Как обойти проблему с кривой прошивкой

Бывает, что UEFI есть, efivarfs смонтирован, а `efibootmgr` всё равно не может записать новую загрузочную запись. Прошивка игнорирует NVRAM или отклоняет запись. На старых платах (примерно до 2013 года) это встречается регулярно.

### Загрузка в live-USB в UEFI-режиме

1. Перезагрузись в boot menu (F2, F12, F11 или Del — зависит от платы).
2. Выбери вариант с пометкой «UEFI», а не «USB» или «Legacy».
3. Если CSM/Legacy включены — отключи их. Обычно опция называется «CSM Support» или «Launch CSM».

После загрузки live проверь:

```bash
ls /sys/firmware/efi
```

Каталог должен быть доступен. Если нет — проблема в способе загрузки.

### Fallback-путь EFI без записи в NVRAM

Когда прошивка не принимает записи через `efibootmgr`, есть обходной путь — поставить загрузчик в стандартный fallback-каталог `EFI/BOOT/bootx64.efi`. Спецификация требует, чтобы прошивка загружала этот файл, если других записей нет.

С GRUB это делается так:

```bash
sudo grub-install --removable --target=x86_64-efi
```

Флаг `--removable` ставит GRUB в `EFI/BOOT/bootx64.efi` на EFI-разделе без обращения к NVRAM. Прошивка подхватит его автоматически. Минус — нельзя держать несколько загрузчиков через efibootmgr, но для одиночной установки Arch это нормально.

### Secure Boot

Если Secure Boot включён, прошивка загружает только подписанные EFI-приложения. Неподписанный GRUB будет отклонён. Варианты:

- Отключи Secure Boot в настройках прошивки (раздел «Security»).
- Подпиши загрузчик с помощью `sbctl`.
- Используй Unified Kernel Image (UKI), который проще подписать.

Проверка текущего состояния:

```bash
mokutil --sb-state
```

## Типичные ситуации и решения

### «Function not implemented» при выводе списка переменных

Частая проблема на realtime-ядрах. Решение — параметр `efi=runtime` в cmdline:

```bash
sudo nano /etc/default/grub
# GRUB_CMDLINE_LINUX_DEFAULT="quiet efi=runtime"
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

### efibootmgr не создаёт запись

Проверь, не закончилось ли место в NVRAM. Удали мусорные записи:

```bash
efibootmgr --unicode
sudo efibootmgr --delete-bootnum --bootnum XXXX
```

Если не помогает — fallback-путь через `--removable`.

### Система не грузится после установки загрузчика

Смонтируй EFI-раздел и убедись, что файлы на месте:

```bash
ls /boot/EFI/arch/
ls /boot/EFI/BOOT/
```

Если загрузчик пропал из меню прошивки, поможет статья [не грузится после установки: чёрный экран](https://ordanax.github.io/ne-gruzitsya-posle-ustanovki-chernyi-ekran).

## Частые вопросы

### Обязательно ли монтировать efivarfs вручную?

В большинстве случаев systemd монтирует efivarfs автоматически при загрузке. Если `mount | grep efivarfs` пуст — монтируй вручную или добавь запись в `/etc/fstab`:

```
efivarfs /sys/firmware/efi/efivars efivarfs nosuid,nodev,noexec,ro 0 0
```

Учти: `ro` делает переменные доступными только для чтения. Для `efibootmgr` нужно `rw`.

### Можно ли использовать efibootmgr на системе с BIOS/CSM?

Нет. efibootmgr работает только с UEFI. Если материнская плата не поддерживает UEFI, загрузчик ставится через MBR (GRUB в legacy-режиме). Подробнее — в [чек-листе по установке Arch](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019).

### Что безопаснее: отключить Secure Boot или подписать загрузчик?

Подписание безопаснее — Secure Boot защищает от подмены загрузчика. Но если цель — просто поставить Arch, отключение тоже вариант. Опция в BIOS/UEFI Setup, раздел «Security».

### Почему переменные пропадают после перезагрузки?

Некоторые прошивки (особенно ноутбуки Lenovo с «OS Optimized Defaults») сбрасывают NVRAM. Решение — fallback-путь `EFI/BOOT/bootx64.efi` или отключение опции сброса в BIOS.

## Заключение

Ошибка `EFI variables are not supported` почти всегда означает одно из двух: система загружена в Legacy-режиме или efivarfs не смонтирован. Проверь наличие `/sys/firmware/efi`, смонтируй efivarfs, убедись, что Secure Boot не блокирует загрузчик. Если прошивка кривая — `grub-install --removable` решит проблему без записи в NVRAM. Пошаговую установку с нуля смотри в [руководстве по установке Arch](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya) и [быстрой установке за 15 минут](https://ordanax.github.io/ustanovka-archlinux-2019-za-15-minut).

## Полезные ресурсы

- [ArchWiki: Unified Extensible Firmware Interface](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface) — полная документация по UEFI в Arch Linux
- [ArchWiki: EFI system partition](https://wiki.archlinux.org/title/EFI_system_partition) — создание и настройка ESP
