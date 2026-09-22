---
layout: post
title: "Переустановить GRUB после поломки: пошаговая инструкция"
description: "Как переустановить GRUB после поломки: chroot из live-окружения, grub-install для UEFI и BIOS, grub-mkconfig. Инструкция для Arch Linux."
date: 2026-09-19 00:00:00 +0300
permalink: /pereustanovka-grub-posle-polomki
categories:
- linux
- arch linux
- configs
- kernel-boot
tags:
- grub
- bootloader
- uefi
- bios
- recovery
- arch linux
edit: true
---


GRUB чинится из live-окружения: загружаешься с установочного ISO, монтируешь разделы, заходишь в систему через arch-chroot и запускаешь две команды — grub-install и grub-mkconfig. Весь ремонт занимает минут десять, и переустанавливать Arch ради сломанного загрузчика не нужно.

## Когда нужно переустанавливать GRUB

Самый частый сценарий — после обновления или правки конфигов система уходит в rescue-режим с приглашением `grub rescue>`. Это значит, что GRUB не находит свои модули или файл grub.cfg. Иногда загрузчик пропадает из меню UEFI, а иногда система просто не стартует — чёрный экран вместо меню.

Переустановка нужна, когда:

- после обновления GRUB система не грузится;
- пропала запись в UEFI (например, после сброса настроек прошивки);
- ты перенёс систему на новый диск или SSD;
- Windows перезаписала загрузчик при установке.

Если видишь приглашение `grub rescue>`, сначала попробуй починить загрузку прямо из него — об этом отдельная статья [«GRUB rescue: что делать»](https://ordanax.github.io/grub-rescue-chto-delat). Не вышло — переустанавливай по инструкции ниже. А если система вообще не показывает ни одного меню и уходит в чёрный экран, разберись сначала с причинами: [«Не грузится после установки: чёрный экран»](https://ordanax.github.io/ne-gruzitsya-posle-ustanovki-chernyi-ekran).

## Как зайти в систему из live-окружения, если GRUB сломан

Тебе понадобится установочный ISO Arch Linux на флешке. Загружайся с него в том же режиме, в котором стоит система: UEFI для UEFI, BIOS для BIOS. Проверить режим легко — если в live-окружении существует каталог `/sys/firmware/efi`, ты загрузился в UEFI.

### Монтируем разделы

Сначала посмотри, как размечены диски:

```
lsblk
```

В выводе найди корневой раздел и ESP. В примерах ниже корень — `/dev/nvme0n1p2`, ESP — `/dev/nvme0n1p1`. Подставь свои из lsblk.

```
mount /dev/nvme0n1p2 /mnt
mount --mkdir /dev/nvme0n1p1 /mnt/efi
```

Для BIOS-системы вместо ESP монтируй раздел `/boot`:

```
mount /dev/sda2 /mnt
mount /dev/sda1 /mnt/boot
```

Если у тебя отдельные разделы для `/home` или `/var`, смонтируй и их — иначе arch-chroot не увидит данные. Если корень зашифрован LUKS, сначала открой его: `cryptsetup open /dev/nvme0n1p2 cryptroot`, а потом монтируй `/dev/mapper/cryptroot`.

### Заходим в систему через arch-chroot

```
arch-chroot /mnt
```

После этой команды ты внутри своей системы: пакетный менеджер, конфиги, всё на месте. Дальше работаем как обычно, только от root. Последовательность монтирования такая же, как при установке, только без форматирования. Свежий порядок действий — в [«Установка Arch Linux 2026: пошагово»](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya).

## Как переустановить GRUB на UEFI

Внутри chroot убедись, что пакеты на месте:

```
pacman -S grub efibootmgr
```

Если они уже установлены, pacman просто обновит их до актуальной версии. Теперь ставь загрузчик:

```
grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id=GRUB
```

`--efi-directory=/efi` указывает на смонтированную ESP (внутри chroot это `/mnt/efi`). `--bootloader-id=GRUB` — имя записи в меню UEFI. После установки сгенерируй конфиг:

```
grub-mkconfig -o /boot/grub/grub.cfg
```

Это стандартный путь. Если у тебя нестандартная схема, где grub.cfg лежит на ESP, пиши `-o /efi/GRUB/grub.cfg` — но для большинства систем подходит именно `/boot/grub/grub.cfg`.

### Дублирующиеся записи в efibootmgr

После повторных установок в NVRAM копятся одинаковые записи GRUB. Посмотри список:

```
efibootmgr
```

Лишние записи удаляются по номеру:

```
efibootmgr -b 0001 -B
```

Где `0001` — номер записи из вывода efibootmgr. Если efibootmgr ругается на переменные — почитай [«efi variables not supported: efibootmgr»](https://ordanax.github.io/efi-variables-not-supported-efibootmgr).

## Как переустановить GRUB на BIOS/MBR

Для BIOS-системы команда другая — GRUB пишется прямо в MBR диска:

```
grub-install --target=i386-pc /dev/sda
```

Обрати внимание: указывается диск целиком (`/dev/sda`), а не раздел (`/dev/sda1`). Подставь свой диск из lsblk. Потом тот же grub-mkconfig:

```
grub-mkconfig -o /boot/grub/grub.cfg
```

## Как обновить конфиг GRUB

grub-mkconfig пересобирает grub.cfg из скриптов `/etc/grub.d/` и настроек `/etc/default/grub`. Запускай его после каждого изменения этих файлов, после установки или удаления ядра, а также после переустановки самого GRUB.

Чтобы GRUB находил другие ОС (Windows, второй Linux), нужен пакет os-prober и строка в `/etc/default/grub`:

```
GRUB_DISABLE_OS_PROBER=false
```

После этого снова `grub-mkconfig -o /boot/grub/grub.cfg`. Нюансы поиска Windows описаны в [«os-prober и GRUB: Windows»](https://ordanax.github.io/os-prober-grub-windows).

## Частые вопросы

**Что делать, если после grub-install система всё равно не грузится?**

Проверь, что ты загрузился с live-USB в том же режиме (UEFI/BIOS), что и система. Для UEFI попробуй установку в fallback-путь: `grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id=GRUB --removable` — тогда GRUB появится в `/efi/EFI/BOOT/BOOTX64.EFI`, и прошивка найдёт его даже без записи в NVRAM.

**Нужно ли переустанавливать GRUB после каждого обновления ядра?**

Нет. После обновления ядра достаточно перегенерировать конфиг: `grub-mkconfig -o /boot/grub/grub.cfg`. Сама переустановка нужна только при поломке или смене диска.

**Как понять, UEFI у меня или BIOS?**

В загруженной системе проверь наличие каталога: `ls /sys/firmware/efi`. Если он есть — UEFI, если нет — BIOS (или UEFI с включённым CSM).

**Можно ли переустановить GRUB без live-USB?**

Если система грузится в rescue-режиме, иногда хватает команд `set root=`, `insmod`, `linux`, `initrd`, `boot` — но это временный запуск. Для надёжного ремонта всё равно нужен chroot из live-окружения.

## Заключение

Переустановить GRUB после поломки — простая процедура: live-USB, монтирование разделов, arch-chroot, grub-install и grub-mkconfig. Главное — не перепутать режим (UEFI или BIOS) и правильно указать ESP. Запомни две команды — и любой сломанный загрузчик чинится за десять минут. Подробности о том, как устроен запуск системы, — в [ArchWiki: Arch boot process](https://wiki.archlinux.org/title/Arch_boot_process).

## Полезные ресурсы

- [ArchWiki: GRUB](https://wiki.archlinux.org/title/GRUB) — полная документация по установке и настройке
- [Dualboot: Windows пропала из GRUB](https://ordanax.github.io/dualboot-windows-propala-iz-grub) — если Windows исчезла из меню