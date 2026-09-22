---
layout: post
title: "systemd-boot vs GRUB: второе ядро linux-lts в загрузчике"
description: "systemd-boot или GRUB для Arch: когда хватает минимализма, а когда нужен GRUB, и как добавить linux-lts в меню загрузчика."
date: 2026-09-19 00:00:00 +0300
permalink: /systemd-boot-vs-grub-vtoroe-yadro
categories:
- linux
- arch linux
- configs
- kernel-boot
tags:
- systemd-boot
- grub
- linux-lts
- bootloader
- uki
edit: true
---


Для Arch на UEFI-системе с ESP в `/boot` или `/efi` бери **systemd-boot**: он уже входит в пакет `systemd`, ставится одной командой и находит ядра по простым текстовым файлам. GRUB оставь для сложных сценариев — dualboot с Windows, шифрование, кастомизация меню. Второе ядро `linux-lts` в systemd-boot добавляется одним файлом `/boot/loader/entries/arch-lts.conf`, и через минуту в меню два Arch.

## Чем systemd-boot отличается от GRUB

systemd-boot — это не загрузчик в классическом смысле, а UEFI boot manager. Он умеет одно: показать меню и запустить EFI-приложение — ядро или другой загрузчик. Никаких модулей, тем и скриптов. Зато он крошечный, стартует мгновенно и настраивается тремя файлами.

GRUB — полноценный загрузчик с модульной архитектурой. Он сам читает файловые системы, грузит ядро из LVM и btrfs, расшифровывает `/boot`, рисует темы, выполняет скрипты в конфиге и находит другие ОС через `os-prober`. За гибкость платишь сложностью: конфиг генерируется из `/etc/default/grub` командой `grub-mkconfig`, и любая правка — это перегенерация.

Коротко: systemd-boot — минимализм и предсказуемость, GRUB — фичи и гибкость.

## Кому подходит systemd-boot

Бери systemd-boot, если:

- ESP смонтирована в `/boot` или `/efi` — стандартная схема установки Arch;
- один Linux на диске, без сложных сценариев;
- используешь стандартные ядра или UKI;
- хочешь минимум конфигов и быстрый старт.

GRUB нужен, когда:

- dualboot с Windows и другими ОС на разных дисках (простой Windows systemd-boot находит сам — по пути `/EFI/Microsoft/Boot/Bootmgfw.efi`);
- шифрование `/boot` или разметка с LVM/btrfs;
- кастомизация: темы, фоновые картинки, скрипты в меню;
- BIOS-системы без UEFI — тут systemd-boot не работает.

## Как установить systemd-boot

Сначала убедись, что система загружена в UEFI-режиме:

```bash
ls /sys/firmware/efi/efivars
```

Каталог существует — всё в порядке. Дальше установка:

```bash
bootctl install
```

Команда скопирует `systemd-bootx64.efi` в ESP, создаст запись «Linux Boot Manager» и поставит её первой в порядке загрузки. Отдельный пакет не нужен — systemd-boot входит в `systemd`, а он в базовой системе. Подробности — на [странице ArchWiki](https://wiki.archlinux.org/title/Systemd-boot).

### loader.conf

Главный конфиг лежит в `/boot/loader/loader.conf`:

```
default  arch.conf
timeout  4
console-mode max
```

- `default` — запись по умолчанию;
- `timeout` — секунды ожидания в меню;
- `console-mode` — разрешение меню (`max`, `auto`, `keep`).

### Файл записи

Каждая запись меню — отдельный файл в `/boot/loader/entries/`. Пример для основного ядра:

```
title   Arch Linux
linux   /vmlinuz-linux
initrd  /initramfs-linux.img
options root=UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx rw
```

Пути в `linux` и `initrd` относительные — от корня ESP. Проверить записи можно командой `bootctl list`. Обновление самого загрузчика — `bootctl update` (после обновления systemd оно срабатывает автоматически).

## Как добавить linux-lts в меню

Ставим второе ядро:

```bash
pacman -S linux-lts linux-lts-headers
```

Пересобираем initramfs для всех ядер:

```bash
mkinitcpio -P
```

И создаём файл `/boot/loader/entries/arch-lts.conf`:

```
title   Arch Linux (LTS)
linux   /vmlinuz-linux-lts
initrd  /initramfs-linux-lts.img
options root=UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx rw
```

UUID бери тот же, что в `arch.conf`, — проверить можно через `blkid`. Готово: `bootctl list` покажет обе записи.

### Как сделать LTS ядром по умолчанию

Поменяй `default` в `loader.conf`:

```
default  arch-lts.conf
```

### UKI вместо entries

Если собираешь unified kernel image (ядро + initramfs + параметры в одном файле), клади его в `/boot/EFI/Linux/` — systemd-boot найдёт его сам, без файлов в `entries`. Про сборку UKI и подпись под Secure Boot — в статьях про [разрешение экрана и UKI](https://ordanax.github.io/gop-simpledrm-uki-razreshenie) и [Secure Boot через sbctl](https://ordanax.github.io/secure-boot-arch-sbctl).

## Как вернуться на GRUB

Если systemd-boot не зашёл — вернуться просто:

```bash
pacman -S grub
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
```

Потом отредактируй `/etc/default/grub` и сгенерируй конфиг:

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

Для Windows в dualboot поставь `os-prober` и включи его в `/etc/default/grub` — [отдельная статья](https://ordanax.github.io/os-prober-grub-windows). А если GRUB сломался после обновления — [переустановка GRUB](https://ordanax.github.io/pereustanovka-grub-posle-polomki).

## Частые вопросы

**systemd-boot быстрее GRUB?**
Да, меню появляется почти мгновенно — загрузчик крошечный и не сканирует диски. Разница в секунды, но ощущается.

**Нужно ли ставить systemd-boot отдельно?**
Нет. Он входит в пакет `systemd`, который стоит в любой базовой системе Arch.

**Можно ли держать оба загрузчика?**
Можно, но незачем. Оба будут висеть в UEFI boot order, и проще оставить один. Если решил убрать GRUB — удали его запись через `efibootmgr`.

**linux-lts конфликтует с обычным ядром?**
Нет. Ядра живут рядом, у каждого свои `vmlinuz` и initramfs. После установки просто запусти `mkinitcpio -P`.

**Что делать, если после обновления systemd-boot не обновился?**
Запусти `bootctl update` вручную. Обычно автоматически, но при нестандартном пути ESP — только вручную.

## Заключение

Для большинства установок Arch на UEFI systemd-boot — правильный выбор: он проще, быстрее и уже в системе. GRUB бери осознанно — под dualboot, шифрование или кастомизацию. А второе ядро linux-lts — это один файл в `/boot/loader/entries/`, и запасной вариант всегда под рукой. Если только начинаешь — сначала пройди [пошаговую установку Arch](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya), а загрузчик выбирай на работающей системе.

## Полезные ресурсы

- [ArchWiki: Unified kernel image](https://wiki.archlinux.org/title/Unified_kernel_image) — сборка UKI и интеграция с systemd-boot
- [Boot Loader Specification](https://systemd.io/BOOT/) — формат записей, который понимает systemd-boot