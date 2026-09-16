---
layout: post
title: "Дуалбут: Windows пропал из GRUB — как вернуть"
description: "Windows пропал из меню GRUB? Разбираем, почему os-prober отключён, как вернуть пункт Windows Boot Manager и починить порядок загрузки через efibootmgr."
date: 2026-09-17 00:00:00 +0300
permalink: /dualboot-windows-propala-iz-grub
categories:
- linux
- arch linux
- boot
tags:
- grub
- os-prober
- dualboot
- windows
- efibootmgr
- uefi
edit: true
---

Windows пропал из меню GRUB не потому, что система сломалась. С 2022 года GRUB по умолчанию не сканирует другие операционные системы: os-prober отключён, и пункт Windows Boot Manager просто не генерируется. Лечится это тремя командами: поставить os-prober, включить его в `/etc/default/grub` и пересобрать конфиг. Ниже разберу весь путь — от простого случая до восстановления загрузчика из live-USB.

## Почему Windows пропал из меню GRUB

Раньше `grub-mkconfig` сам искал соседние системы через скрипт os-prober. В 2022 году разработчики GRUB отключили его по умолчанию: os-prober слишком часто падал на кривых разметках и выдавал ложные пункты меню. Теперь при пересборке конфига ты увидишь предупреждение:

```
Warning: os-prober will not be executed to detect other bootable partitions
```

Это не ошибка. Это штатное поведение: GRUB честно говорит, что не искал другие ОС. Windows никуда не делась, её загрузчик лежит на EFI-разделе. Просто GRUB про него не знает, пока ты явно не попросишь.

## Как установить os-prober

Пакет os-prober есть в официальных репозиториях, ставится одной командой:

```bash
sudo pacman -S os-prober
```

После установки открой `/etc/default/grub` любым редактором и найди строку:

```
#GRUB_DISABLE_OS_PROBER=false
```

Раскомментируй её — убери решётку в начале:

```
GRUB_DISABLE_OS_PROBER=false
```

Сохрани файл. Эта строка разрешает `grub-mkconfig` запускать os-prober. Без неё предупреждение останется, и Windows в меню не появится.

## Как обновить конфиг GRUB

Теперь пересобери главный конфиг:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

В выводе должно появиться что-то вроде:

```
Found Windows Boot Manager on /dev/nvme0n1p1@/EFI/Microsoft/Boot/bootmgfw.efi
```

Перезагружайся — в меню GRUB теперь есть пункт Windows Boot Manager. Это решение проверено практикой: в чате сообщества на вопрос «Windows пропал из GRUB» первым делом отвечают «ос-пробер установи», дальше `pacman -S os-prober` и `grub-mkconfig`. Работает.

## Что делать, если os-prober не находит Windows

Если пункт не появился, проверяй по порядку.

**Windows установлен после Arch.** Тогда Windows перезаписала загрузочные записи, и GRUB может вообще не грузиться. Решение — переустановить GRUB заново, чтобы он вернул себя в NVRAM:

```bash
sudo grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Путь `--efi-directory` подставь свой: если ESP смонтирована в `/efi`, будет `/efi`.

**os-prober не читает NTFS.** Для сканирования Windows-раздела os-prober нужен доступ к NTFS. Поставь ntfs-3g:

```bash
sudo pacman -S ntfs-3g
```

**Windows в режиме BIOS/MBR, а Arch в UEFI.** GRUB из UEFI не умеет цеплять загрузчик из BIOS/MBR и наоборот. Проверь режим Windows через `msinfo32` (строка «BIOS mode»). Если режимы разные — это не баг, а ограничение, пункт меню не появится никак.

**Secure Boot.** Если включён Secure Boot, GRUB может не видеть Windows Boot Manager. Временное решение — отключить Secure Boot в прошивке, постоянное — настроить его через sbctl.

## Как восстановить запись Windows в NVRAM

Бывает и так: Windows в меню GRUB есть, но при выборе ничего не грузится, или система сразу уходит в GRUB, минуя BIOS. Это значит, что в NVRAM сбился порядок загрузки. Смотри текущее состояние:

```bash
efibootmgr
```

Вывод покажет список записей вроде `Boot0000* GRUB`, `Boot0001* Windows Boot Manager` и строку `BootOrder`. Если Windows стоит после GRUB или вообще не в списке, верни порядок:

```bash
sudo efibootmgr -o 0000,0001
```

Подставь свои номера: сначала GRUB, потом Windows. BIOS снова увидит обе системы. Если `efibootmgr` ругается на `EFI variables are not supported` — это отдельная история про кривые прошивки, разобрана в статье про [EFI variables not supported](https://ordanax.github.io/efi-variables-not-supported-efibootmgr).

## Если GRUB вообще не грузится

Когда после установки Windows загрузчик пропал целиком и машина уходит в Windows или в чёрный экран, лечим из live-USB:

1. Загрузись с установочной флешки Arch.
2. Смонтируй корневой раздел и ESP:

```bash
mount /dev/nvme0n1p2 /mnt
mount /dev/nvme0n1p1 /mnt/boot
```

3. Войди в систему:

```bash
arch-chroot /mnt
```

4. Переустанови GRUB и пересобери конфиг:

```bash
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
```

Имена разделов подставь свои — проверь их через `lsblk`. После перезагрузки GRUB снова на месте, а с включённым os-prober вернётся и Windows.

## Частые вопросы

**Windows пропал из GRUB после обновления системы. Это из-за pacman -Syu?**

Нет. Обновление не трогает записи Windows. Скорее всего, при обновлении пересобрался `grub.cfg`, а os-prober отключён. Поставь os-prober, включи `GRUB_DISABLE_OS_PROBER=false` и пересобери конфиг.

**os-prober установлен, а Windows всё равно не находится. Что ещё проверить?**

Проверь, что Windows-раздел доступен: поставь ntfs-3g, убедись, что режимы загрузки совпадают (UEFI с UEFI, BIOS с BIOS), и отключи Secure Boot для проверки. Если Windows стоит на втором диске — убедись, что диск подключён и виден в `lsblk`.

**Можно ли добавить Windows в GRUB вручную, без os-prober?**

Можно. Добавь в `/etc/grub.d/40_custom` пункт с chainload:

```
menuentry "Windows Boot Manager" {
    search --fs-uuid --no-floppy --set=root <UUID_ESP>
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}
```

UUID ESP найдёшь через `blkid`. Но проще один раз настроить os-prober — он сам найдёт Windows.

**Почему после установки Windows пропал GRUB?**

Windows при установке перезаписывает загрузочные записи в NVRAM и ставит себя первой. GRUB не удаляется, он просто выпадает из порядка загрузки. Восстанови порядок через `efibootmgr -o` или переустанови GRUB из live-USB.

## Заключение

Windows пропала из GRUB почти всегда по одной причине: os-prober отключён по умолчанию, и `grub-mkconfig` не ищет соседние системы. Решение простое — `pacman -S os-prober`, строка `GRUB_DISABLE_OS_PROBER=false` в `/etc/default/grub` и пересборка конфига. Если загрузчик пропал целиком — live-USB, chroot и `grub-install`. Порядок загрузки чинится через `efibootmgr`. Все три сценария закрываются за десять минут.

## Полезные ресурсы

- [ArchWiki: GRUB](https://wiki.archlinux.org/title/GRUB): официальная документация по установке и настройке загрузчика
- [ArchWiki: Dual boot with Windows](https://wiki.archlinux.org/title/Dual_boot_with_Windows): тонкости сосуществования Arch и Windows
- [Установка Arch Linux за 15 минут](https://ordanax.github.io/ustanovka-archlinux-2019-za-15-minut): если загрузчик сломался, а переустановить систему проще, чем чинить
- [Чек-лист по установке Arch Linux](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019): порядок шагов, включая установку GRUB