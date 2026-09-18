---
layout: post
title: "GRUB: ошибка airootfs при установке из archiso"
description: "Ошибка установки GRUB с сообщением об airootfs из live-окружения archiso. Причины и пошаговое исправление для Arch Linux."
date: 2026-09-19 00:00:00 +0300
permalink: /grub-install-error-airootfs
categories:
  - linux
  - arch linux
  - configs
tags:
  - grub
  - archiso
  - airootfs
  - installation
  - bootloader
  - chroot
edit: true
---

Ошибка установки GRUB с упоминанием `airootfs` — распространённая проблема при инсталляции Arch Linux из live-окружения (archiso). Утилита `grub-install` пытается обратиться к корневой файловой системе live-среды вместо целевого диска и падает с ошибкой `failed to get canonical path of airootfs`. Причина — некорректный вход в chroot или невыполненные bind-монтирования каталогов `/dev`, `/proc`, `/sys`, `/run` перед запуском загрузчика.

## Что такое airootfs и почему GRUB на него ругается

Когда ты грузишься с установочного ISO Arch Linux, основная файловая система live-окружения называется `airootfs`. Это временный корневой rootfs, созданный archiso на базе squashfs. Весь контент live-системы живёт именно здесь — пакеты, утилиты, окружение.

Проблема возникает, когда ты запускаешь `grub-install` или `grub-mkconfig` из среды, которая недостаточно изолирована от live-окружения. Утилита определяет корневой раздел через `grub-probe`, натыкается на `airootfs` вместо реального блочного устройства и падает:

```
grub-probe: error: failed to get canonical path of `airootfs`
```

Корень проблемы прост: `grub-install` не может найти реальное блочное устройство, потому что среда live перехватывает запросы к файловой системе.

## Когда появляется ошибка

Обычно проблема всплывает в двух случаях.

### Запуск grub-install из live-окружения без chroot

Самая частая ошибка — прямой запуск установки загрузчика из shell установочного ISO. `grub-install` работает в контексте live-системы и видит только `airootfs`. Правильный путь — выполнять все команды настройки загрузчика **внутри chroot** на целевой системе.

### Пропущены bind-монтирования перед chroot

Даже если ты вошёл через `chroot /mnt`, но не смонтировал системные каталоги — загрузчик не получит доступ к нужным устройствам. Инструмент `arch-chroot` из пакета `arch-install-scripts` сам подцепляет `/dev`, `/proc`, `/sys` и `/run`. Но если ты используешь обычный `chroot`, всё придётся делать руками.

Также ошибка появляется, если в целевой системе просто не установлен пакет `grub`. Проверь:

```
# pacman -S grub efibootmgr
```

## Как исправить ошибку установки GRUB

### Шаг 1. Проверь монтирование целевой системы

Убедись, что корень примонтирован в `/mnt` и разделы на месте:

```
# lsblk
# mount | grep /mnt
```

Корневой раздел должен быть смонтирован в `/mnt`. Для UEFI EFI-раздел — в `/mnt/boot` или `/mnt/efi`. Если что-то не так, исправь:

```
# mount /dev/sdX2 /mnt
# mount --mkdir /dev/sdX1 /mnt/boot
```

### Шаг 2. Войди в chroot правильно

Используй `arch-chroot` — он автоматически выполнит bind-монтирования:

```
# arch-chroot /mnt
```

Если `arch-chroot` по какой-то причине не работает, сделай всё вручную:

```
# mount --rbind /dev /mnt/dev
# mount --rbind /proc /mnt/proc
# mount --rbind /sys /mnt/sys
# mount --rbind /run /mnt/run
# cp /etc/resolv.conf /mnt/etc/resolv.conf
# chroot /mnt /bin/bash
```

### Шаг 3. Установи и настрой загрузчик

Внутри chroot установи необходимые пакеты и выполни установку GRUB.

**UEFI-система:**

```
# pacman -S grub efibootmgr
# grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
# grub-mkconfig -o /boot/grub/grub.cfg
```

Если EFI-размонтирован в `/efi`, замени `--efi-directory=/boot` на `--efi-directory=/efi`.

**BIOS/MBR-система:**

```
# pacman -S grub
# grub-install --target=i386-pc /dev/sda
# grub-mkconfig -o /boot/grub/grub.cfg
```

Важно: для BIOS указывай именно диск (`/dev/sda`, `/dev/nvme0n1`), а не раздел (`/dev/sda1`).

### Шаг 4. Проверь результат

```
# ls /boot/grub/grub.cfg
# efibootmgr -v
```

Если файл конфигурации на месте и вывод `efibootmgr` показывает запись GRUB — всё в порядке. Выходи из chroot (`exit`), размонтируй и перезагружайся.

## Как подстраховаться при установке загрузчика

### Всегда проверяй текущее окружение

Перед запуском `grub-install` убедись, что ты внутри chroot. Выполни `cat /etc/hostname` — должен показать имя целевой системы, а не live-окружения. Выполни `pwd` — корень должен быть `/`.

### Используй arch-chroot вместо ручного chroot

`arch-chroot` автоматически настраивает bind-монтирования и копирует `resolv.conf`. Это исключает классическую ошибку «забыл примонтировать `/dev`». Если хочешь разобраться в процессе инсталляции глубже — смотри [пошаговое руководство по установке Arch Linux](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya).

### Сохрани вывод grub-install

Перед выходом из chroot сохрани лог установки. Если после перезагрузки окажется чёрный экран — загляни в руководство по исправлению [чёрного экрана после установки](https://ordanax.github.io/ne-gruzitsya-posle-ustanovki-chernyi-ekran). А если GRUB поломался уже после установки — поможет статья о [переустановке GRUB после поломки](https://ordanax.github.io/pereustanovka-grub-posle-polomki).

## Частые вопросы

### Что значит «failed to get canonical path of airootfs»?

`grub-probe` не смог определить реальное блочное устройство для корневой ФС. Причина — ты запускаешь команду из live-окружения или из chroot с неправильно смонтированными каталогами `/dev`, `/proc`, `/sys`. Решение — войти через `arch-chroot` и повторить.

### Можно ли запускать grub-install из live, если указать --boot-directory?

Теоретически да, с ключом `--boot-directory=/mnt/boot`. Но это не решает проблему определения корневого устройства. Надёжнее всегда работать из chroot.

### Что делать, если grub-install пишет «target not found»?

Проверь, что пакет `grub` установлен в chroot (`pacman -S grub`). Убедись, что для BIOS указан именно диск, а не раздел. Для UEFI укажи `--target=x86_64-efi` и правильный `--efi-directory`.

### Поможет ли переустановка GRUB при повреждении?

Да. Если загрузчик установлен некорректно или повреждён, его можно переустановить по тому же алгоритму. Подробнее — в статье о переустановке GRUB после поломки.

## Заключение

Ошибка «airootfs» при установке GRUB — типичная проблема при работе из live-окружения archiso. Загрузчик запущен вне chroot или без необходимых bind-монтирований. Исправление: войди через `arch-chroot /mnt`, убедись, что пакеты `grub` и `efibootmgr` установлены, и запусти `grub-install` с правильными параметрами. Для BIOS указывай диск, для UEFI — целевой EFI-каталог. Если возникли трудности с разметкой — проверь [разметку диска GPT/MBR](https://ordanax.github.io/razmetka-diska-gpt-mbr).

## Полезные ресурсы

- [GRUB — ArchWiki](https://wiki.archlinux.org/title/GRUB) — полная документация по загрузчику: установка, настройка, исправление проблем
- [Installation guide — ArchWiki](https://wiki.archlinux.org/title/Installation_guide) — официальное руководство по установке Arch Linux
