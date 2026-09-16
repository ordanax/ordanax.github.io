---
layout: post
title: "Один EFI-раздел для дуалбута: правильное монтирование ESP"
description: "Как монтировать общий ESP при дуалбуте Arch Linux и Windows. Команды, точки монтирования и защита Windows Boot Manager."
date: 2026-09-17 00:00:00 +0300
permalink: /odin-efi-razdel-dualboot
categories:
- linux
- arch linux
- boot
tags:
- efi
- dualboot
- systemd-boot
- grub
- esp
- mount
edit: true
---

При дуалбуте Arch Linux и Windows используется один общий EFI System Partition — раздел FAT32, который Windows создала при установке (обычно 100–512 МБ на начале диска). Его монтируют в `/efi` или `/boot` перед установкой Arch, а загрузчик пишет свои файлы рядом с Windows Boot Manager. Главное — не форматировать этот раздел и не трогать папку `EFI/Microsoft`.

## Зачем один ESP на две системы

UEFI-прошивка ищет загрузчик только на FAT32-разделе с флагом ESP. На диске с дуалбутом он один, и обе системы делят его:

```
EFI/
├── BOOT/bootx64.efi       # fallback
├── Microsoft/Boot/...      # Windows Boot Manager
└── arch/                   # загрузчик Arch
```

Windows создаёт ESP на 100 МБ. Этого минимума хватает, но тесновато. Рекомендация ArchWiki — 1 ГБ, если есть возможность расширить. Один раздел вместо двух упрощает жизнь: прошивка видит одну точку, и навигация по файлам проще.

## Как найти ESP перед установкой Arch

Найди раздел с файловой системой FAT32 и флагом `EFI System`:

```bash
lsblk -f
```

Ищи строку с `vfat` — обычно первый раздел на диске (`/dev/sda1` или `/dev/nvme0n1p1`). Убедись, что это не MSR-раздел (16 МБ, без файловой системы) и не Recovery (500+ МБ, NTFS). Если сомневаешься — смонтируй и проверь наличие папки `EFI/`:

```bash
mount /dev/sda1 /mnt/test && ls /mnt/test/EFI/
```

## Как монтировать ESP перед установкой

Правильный момент — до `pacstrap`. Из live-USB:

```bash
mkdir -p /mnt/efi
mount /dev/sda1 /mnt/efi
```

В `/etc/fstab` пропиши монтирование (UUID возьми из `blkid`):

```
UUID=XXXX-XXXX  /efi  vfat  rw,relatime,fmask=0133,dmask=0022  0 1
```

Опции `fmask=0133,dmask=0022` запрещают запись в ESP обычным пользователям — страховка от порчи файлов Windows.

После `chroot` и базовой настройки ставь загрузчик. Для systemd-boot:

```bash
bootctl install
```

Для GRUB:

```bash
grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id=GRUB
```

Сравни с [установкой за 15 минут](https://ordanax.github.io/ustanovka-archlinux-2019-za-15-minut) — там монтирование ESP — один из первых шагов.

## Как не сломать загрузку Windows

Три правила, нарушение которых вернёт тебя в Recovery-среду:

**Не форматируй ESP.** Ни `mkfs.fat`, ни что бы то ни было. Один формат — Windows не загрузится, пока не восстановишь загрузчик через `bcdboot`.

**Не удаляй `EFI/Microsoft`.** Там лежит `bootmgfw.efi` — единственный файл, который Windows использует для старта.

**Не трогай NVRAM-записи.** Команда `efibootmgr` покажет записи `Windows Boot Manager`. Не удаляй их без понимания последствий. Если Windows пропала из меню — смотри [восстановление GRUB](https://ordanax.github.io/dualboot-windows-propala-iz-grub).

А вот fallback-путь `EFI/BOOT/bootx64.efi` — аварийный выход. Если Arch перезаписал его (GRUB с `--removable`), Windows доступна напрямую через `EFI/Microsoft/Boot/bootmgfw.efi`. Проблемы с UEFI-переменными (прошивка не видит записи) — отдельная тема, описанная в [статье про efibootmgr](https://ordanax.github.io/efi-variables-not-supported-efibootmgr).

## Что делать, если ESP слишком маленький

Windows создаёт ESP на 100 МБ. Этого хватает для загрузчика (5–10 МБ), но тесновато для ядер и initramfs. Каждый образ занимает 10–80 МБ.

**Чистый вариант — монтировать в `/efi`, оставив `/boot` на корневом разделе.** Тогда на ESP живёт только загрузчик, а ядра в ext4/btrfs. Это современная рекомендация ArchWiki и самый аккуратный подход для дуалбута.

**Если хочешь ядра на ESP** — расширь раздел из-под Windows (`diskmgmt.msc`, сожми C:, новый раздел) или используй XBOOTLDR: создай раздел типа `Linux extended boot` (`EA00` в gdisk), смонтируй в `/boot`, а ESP оставь в `/efi` для загрузчика. Поддерживается systemd-boot.

**Костыль — чистить ESP вручную:**

```bash
ls /mnt/efi/EFI/arch/
```

Удаляй старые `vmlinuz-linux-old` и `initramfs-linux-old.img`. Но правильнее расширить раздел или перенести ядра на корневой.

## Частые вопросы

**Обязательно монтировать ESP в `/efi` или можно в `/boot`?**

Можно и так, и так. В `/boot` проще (ядра и загрузчик вместе), но нужно больше места. В `/efi` чище — только загрузчик. Рекомендация Arch 2026 — `/efi`.

**Можно ли отформатировать ESP и поставить Arch заново без потери Windows?**

Нет. Формат уничтожит Windows Boot Manager. Восстановить его можно командой `bcdboot C:\Windows /s S: /f UEFI` из Recovery-среды, где `S:` — смонтированный ESP.

**systemd-boot или GRUB — что лучше для дуалбута?**

systemd-boot проще: он сам находит все EFI-приложения на ESP (включая Windows). GRUB требует `os-prober` или ручной настройки.

## Заключение

Один ESP для Arch и Windows — штатная ситуация. Найди его через `lsblk -f`, смонтируй в `/efi` до `pacstrap`, не форматируй и не удаляй папку `EFI/Microsoft`. systemd-boot проще для дуалбута, GRUB требует больше настроек. Если ESP мал — монтируй в `/efi` и держи ядра на корневом разделе.

## Полезные ресурсы

- [EFI system partition](https://wiki.archlinux.org/title/EFI_system_partition) на ArchWiki: размеры, точки монтирования, расширение ESP
- [Unified Extensible Firmware Interface](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface) на ArchWiki: UEFI-переменные и efibootmgr
- [Чек-лист установки Arch Linux](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019) — полный список действий при установке
