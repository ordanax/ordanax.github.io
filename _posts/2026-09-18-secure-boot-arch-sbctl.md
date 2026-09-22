---
layout: post
title: "Secure Boot на Arch: полное включение через sbctl"
description: "Как включить Secure Boot на Arch Linux с помощью sbctl: создание ключей, подпись ядра и загрузчика, автоподпись при обновлениях. Пошаговое руководство."
date: 2026-09-18 00:00:00 +0300
permalink: /secure-boot-arch-sbctl
categories:
- linux
- arch linux
- security
- kernel-boot
tags:
- secure-boot
- sbctl
- uefi
- signing
- bootloader
edit: true
---


Secure Boot на Arch Linux включается через утилиту `sbctl`: ставишь пакет, создаёшь ключи, подписываешь ядро и загрузчик, записываешь ключи в прошивку и активируешь Secure Boot в BIOS. Занимает минут десять, если прошивка не кривая.

## Что такое Secure Boot и зачем он нужен

Secure Boot — механизм в UEFI-прошивке, который проверяет подписи EFI-бинарников перед загрузкой. Если подпись неизвестна или отсутствует, прошивка отказывается загружать файл. Цель — защита от подмены загрузчика и ядра до момента, когда ОС берёт контроль. Secure Boot не заменяет шифрование диска — это дополнительный слой.

## Как проверить текущее состояние Secure Boot

Проверь, что видит система:

```bash
sbctl status
```

Утилита покажет, установлены ли ключи и в каком режиме прошивка — User Mode (Secure Boot активен) или Setup Mode (ключи можно менять). Альтернатива — `bootctl status`, строка `Secure Boot:`.

Важно: чтобы записать свои ключи, прошивка должна быть в Setup Mode. Если она в User Mode — зайди в BIOS и удали текущий Platform Key (опция «Clear Secure Boot Keys»). Об особенностях UEFI — в статье про [ошибку EFI variables not supported](https://ordanax.github.io/efi-variables-not-supported-efibootmgr).

## Что такое sbctl и почему это стандарт

`sbctl` (Secure Boot Key Manager) — утилита от Foxboron, делающая включение Secure Boot на Arch делом пяти команд. До неё приходилось возиться с `efitools` и openssl, подписывая каждый бинарник отдельно. Сейчас `sbctl` — стандарт де-факто: генерирует ключи (PK, KEK, db), записывает их в прошивку, подписывает EFI-файлы и автоматически подписывает обновлённые ядра через pacman hook.

## Как создать ключи и записать их в прошивку

### Установка

```bash
sudo pacman -S sbctl
```

### Генерация ключей

```bash
sudo sbctl create-keys
```

Ключи сохраняются в `/etc/efi-keys/`. Не теряй папку — при переустановке системы только с ними восстановишь доступ к подписанным бинарникам.

### Запись ключей в прошивку

```bash
sudo sbctl enroll-keys -m
```

Флаг `-m` добавляет ключи Microsoft в базу доверия. Это критично для dualboot с Windows — иначе файлы, подписанные Microsoft (включая драйверы NVIDIA), не будут загружаться. На некоторых Lenovo ThinkPad и ASUS TUF замена ключей без Microsoft может привести к brick. Если сомневаешься — ставь с `-m`.

## Как подписать ядро и загрузчик

### Определяем, что подписывать

```bash
sudo sbctl verify
```

Утилита проверит EFI-файлы в `/boot` и покажет неподписанные. Стандартный набор для systemd-boot:

```bash
sudo sbctl sign -s /boot/vmlinuz-linux
sudo sbctl sign -s /boot/EFI/BOOT/BOOTX64.EFI
sudo sbctl sign -s /boot/EFI/systemd/systemd-bootx64.efi
```

Флаг `-s` копирует подписанный файл в `/usr/lib/`, чтобы pacman hook обновлял подписи автоматически. Для GRUB вместо systemd-boot подписывается `grubx64.efi`.

### Проверка

```bash
sudo sbctl list
sudo sbctl verify
```

`list` покажет подписанные файлы, `verify` — подтвердит порядок.

### Автоподпись при обновлениях

Пакет `sbctl` ставит pacman hook автоматически: после каждого обновления ядра hook переподписывает бинарник. Исключение — `systemd-boot-update.service`: загрузчик обновляется после ребута, и hook может не подхватить новый файл. Решение — подписать бинарник напрямую в `/usr/lib/`:

```bash
sudo sbctl sign -s -o /usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed /usr/lib/systemd/boot/efi/systemd-bootx64.efi
```

`bootctl install` подхватит файл с расширением `.efi.signed`.

## Как включить Secure Boot в BIOS

Когда ключи записаны и ядро подписано:

1. Перезагрузись и зайди в BIOS (F2, Del, Esc — зависит от платы).
2. В разделе Security включи Secure Boot.
3. Убедись, что Setup Mode выключен (Secure Boot должен быть в User Mode).
4. Сохрани и перезагрузись.

Если система загрузилась — всё работает. `sbctl status` теперь должен показывать `Secure Boot: enabled`.

## Что такое MokManager и когда он нужен

MokManager (Machine Owner Key Manager) — утилита из пакета `shim`, которая позволяет добавлять собственные ключи (MOK) через интерфейс при загрузке. Это обходной путь для прошивок, которые не дают записать ключи напрямую в базу Secure Boot.

На практике MokManager нужен редко — `sbctl` справляется напрямую. Но бывают случаи: прошивка не входит в Setup Mode, нужно добавить ключ для конкретного драйвера без полной замены базы, или машина корпоративная с заблокированными настройками. Если `sbctl enroll-keys` отработал без ошибок — MokManager не нужен.

## Какие проблемы бывают с Secure Boot

### Драйвер NVIDIA не загружается

Если модули NVIDIA не подписаны, после включения Secure Boot будет чёрный экран без GUI. Подпиши модули вручную:

```bash
sudo sbctl sign -s /usr/lib/modules/$(uname -r)/kernel/drivers/video/nvidia-drm.ko.zst
```

### Система не грузится после включения Secure Boot

Самые частые причины:

- Забыл подписать загрузчик или ядро. Перезагрузись с live-USB (Secure Boot выключи) и проверь `sbctl verify`.
- Прошивка не приняла ключи — проверь `sbctl status`.
- Ядро из AUR (zen, hardened) — подпиши его: `sudo sbctl sign -s /boot/vmlinuz-linux-zen`.

## Частые вопросы

### Обязательно ли использовать sbctl?

Нет, есть альтернативы: `systemd-ukify` (systemd v254+, пакет в core), ручной процесс через `efitools` и `sbsigntools`, утилита `sbupdate`. Но `sbctl` — самый удобный вариант и стандарт де-факто.

### Подписывает ли sbctl только ядро?

Нет, sbctl подписывает любой EFI-бинарник: ядро, загрузчик, UKI, модули. Про сборку и подписание UKI читай в статье про [разрешение проблем с gop-simpledrm и UKI](https://ordanax.github.io/gop-simpledrm-uki-razreshenie).

### Можно ли откатить Secure Boot?

Да. Выключи Secure Boot в BIOS или удали ключи — вернёшься в исходное состояние. Подписанные бинарники продолжат работать, просто прошивка перестанет их проверять.

### Как быть с dualboot Windows?

При `sbctl enroll-keys -m` ключи Microsoft добавляются в базу доверия, и Windows Boot Manager загрузится без проблем. Проблемы возможны, только если Windows сменит ключ загрузчика — тогда придётся переподписать.

## Заключение

Secure Boot на Arch через `sbctl` — это реально и не больно. Десять минут: ставишь пакет, генерируешь ключи, подписываешь ядро и загрузчик, записываешь ключи с флагом `-m`, включаешь Secure Boot в BIOS. Дальше обновления ядра подписываются автоматически. Главное — проверь, что прошивка входит в Setup Mode и принимает ключи. Если прошивка кривая, смотри статью про [EFI variables not supported](https://ordanax.github.io/efi-variables-not-supported-efibootmgr). А если ставишь Arch с нуля — загляни в [пошаговое руководство по установке](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya) или в [установку с LVM](https://ordanax.github.io/ustanovka-arch-s-lvm).

## Полезные ресурсы

- [ArchWiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot) — полная документация по Secure Boot в Arch Linux
- [ArchWiki: Unified Kernel Image](https://wiki.archlinux.org/title/Unified_kernel_image) — создание и подписание UKI