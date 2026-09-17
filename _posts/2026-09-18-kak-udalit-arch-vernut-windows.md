---
layout: post
title: "Как удалить Arch и вернуть Windows"
description: "Удалил Arch, а Windows не грузится? Восстанови загрузчик через bcdboot, удали разделы и GRUB — пошаговый чек-лист с командами."
date: 2026-09-18 00:00:00 +0300
permalink: /kak-udalit-arch-vernut-windows
categories:
- linux
- arch linux
- windows
tags:
- dualboot
- bcdboot
- grub
- windows
- efibootmgr
- partitioning
edit: true
---

Чтобы удалить Arch и вернуть Windows как единственную систему, действуй в правильном порядке: сначала восстанови загрузчик Windows, пока Arch ещё грузится, а только потом удаляй разделы. Если начать с удаления — останешься без загрузчика обеих систем.

## Что удалить, чтобы избавиться от Arch

В дуалбуте Arch и Windows обычно на одном диске есть минимум три «чужих» раздела: корневой (`/`), домашний (`/home`) и записи GRUB на EFI-разделе. Удалять их надо только после того, как Windows грузится сама.

Если Arch стоял на отдельном диске — проще. Отключи его, загрузись в Windows, и в «Управлении дисками» (`diskmgmt.msc`) удали ненужные разделы. Но правило то же: сначала убедись, что Windows-раздел активен.

Главное: не трогай EFI-раздел (ESP) целиком. На нём лежит Windows Boot Manager, и если его стереть, ни одна ОС не загрузится. Подробнее — в статье про [один EFI-раздел в дуалбуте](https://ordanax.github.io/odin-efi-razdel-dualboot).

## Как восстановить загрузчик Windows

### Вариант 1: из Arch, пока грузится

Определи номера разделов через `lsblk`. Обычно Windows на `/dev/nvme0n1p3`, а EFI-раздел на `/dev/nvme0n1p1`:

```bash
lsblk
sudo mkdir -p /mnt/windows /mnt/efi
sudo mount /dev/nvme0n1p3 /mnt/windows
sudo mount /dev/nvme0n1p1 /mnt/efi
```

`bcdboot` — утилита Windows, из Arch её не запустишь. Вместо нее скопируй загрузочный файл Windows на EFI-раздел и добавь запись через `efibootmgr`:

```bash
sudo mkdir -p /mnt/efi/EFI/Microsoft/Boot
sudo cp /mnt/windows/Windows/Boot/EFI/bootmgfw.efi /mnt/efi/EFI/Microsoft/Boot/bootmgfw.efi
sudo efibootmgr --create --disk /dev/nvme0n1 --part 1 --label "Windows Boot Manager" --loader "\EFI\Microsoft\Boot\bootmgfw.efi"
```

Числа после `--disk` и `--part` — из `lsblk`: диск и номер EFI-раздела. Команда копирует `bootmgfw.efi` в ESP и регистрирует запись в NVRAM.

### Вариант 2: с установочной флешки Windows

Если Arch уже не грузится — загрузись с флешки Windows, выбери «Восстановление системы» → «Командная строка» и выполни:

```cmd
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd
```

Этот способ больше подходит для BIOS/MBR. Для UEFI используй `bcdboot` из варианта 1. Также можно через `diskpart` пометить раздел Windows активным:

```cmd
diskpart
list volume
select volume 1
active
exit
```

## Как удалить GRUB и разделы Arch

Когда Windows грузится без проблем — пора убирать Arch.

### Удаление разделов

Открой «Управление дисками» (`Win+R` → `diskmgmt.msc`). Разделы Arch обычно отформатированы в ext4 и выглядят как «Неизвестный раздел». Удали их все и расширь диск `C:` на освободившееся место.

Если Arch на отдельном диске — через `diskpart`:

```cmd
diskpart
list disk
select disk 1
clean
exit
```

`select disk 1` — подставь номер диска с Arch. `clean` сотрёт всю разметку.

### Удаление записей GRUB

В UEFI после удаления разделов в NVRAM остаются записи GRUB. Из Windows (от администратора):

```cmd
bcdedit /enum firmware
```

Найди запись с GRUB и удали:

```cmd
bcdedit /delete {GUID-записи}
```

Или из Arch до удаления:

```bash
efibootmgr
sudo efibootmgr -b XXXX -B
```

Подробнее — в статье про [EFI variables not supported](https://ordanax.github.io/efi-variables-not-supported-efibootmgr).

## А что если Windows вообще не грузится

**Удалил разделы Arch до восстановления загрузчика Windows.** Без Arch GRUB больше не грузится, а Windows Boot Manager ты ещё не пересоздал. Решение — установочная флешка Windows и `bcdboot` по инструкции выше.

**Удалил ESP-раздел целиком.** Серьёзнее. Без ESP ни одна система не грузится. Восстановление через флешку: в `diskpart` создай новый ESP и выполни `bcdboot`:

```cmd
diskpart
select disk 0
create partition efi size=100
format quick fs=fat32
assign letter=S
exit
bcdboot C:\Windows /s S: /f UEFI
```

Главное правило: не удаляй GRUB, пока не убедился, что `bcdboot` отработал и Windows грузится.

## Как удалить Arch полностью: чек-лист

1. Из Arch или с флешки — восстановить Windows Boot Manager через `bcdboot`.
2. Перезагрузиться в Windows, убедиться что грузится.
3. Открыть `diskmgmt.msc`, удалить разделы Arch.
4. Расширить `C:` на освободившееся место.
5. Убрать записи GRUB из NVRAM (`bcdedit` или `efibootmgr`).
6. НЕ удалять ESP-раздел.
7. Проверить перезагрузкой.

## Частые вопросы

**Можно ли просто удалить раздел Arch?**

Нет. Если Arch был загрузчиком (GRUB), после удаления Windows не загрузится. Сначала восстанови Windows Boot Manager через `bcdboot`.

**Как узнать, какие разделы принадлежат Arch?**

В `diskmgmt.msc` посмотри на файловую систему. Arch обычно использует ext4 или btrfs — Windows покажет их как «Неизвестный раздел». Не трогай разделы с NTFS и FAT32.

**Безопасно ли удалять GRUB из NVRAM?**

Да, если Windows Boot Manager уже на месте. Проверь перед удалением: перезагрузись и выбери Windows в меню прошивки (F12 или аналог).

**Windows Boot Manager не появился в NVRAM после bcdboot. Что делать?**

Убедись, что ESP смонтирована и команда отработала без ошибок. Проверь через `bcdedit /enum firmware`. Если запись не появилась — обнови BIOS.

## Заключение

Удалить Arch и вернуть Windows получится, если соблюдать порядок: сначала восстановить загрузчик Windows через `bcdboot`, убедиться, что Windows грузится, и только потом удалять разделы Arch и чистить NVRAM. Главная ошибка — начинать с удаления, теряя загрузчик обеих систем. Весь процесс занимает десять минут, если знаешь последовательность.

## Полезные ресурсы

- [ArchWiki: Dual boot with Windows](https://wiki.archlinux.org/title/Dual_boot_with_Windows): официальная документация по сосуществованию Arch и Windows
- [ArchWiki: GRUB](https://wiki.archlinux.org/title/GRUB): настройка и восстановление загрузчика
- [Дуалбут: Windows пропал из GRUB](https://ordanax.github.io/dualboot-windows-propala-iz-grub): как вернуть Windows в меню, если она просто пропала
- [Разметка диска: GPT и MBR](https://ordanax.github.io/razmetka-diska-gpt-mbr): как понять, какие разделы занимает Arch, и что можно удалить
- [Клонирование Arch на похожее железо](https://ordanax.github.io/klonirovanie-arch-na-podobnoe-zhelezo): если перед удалением нужно оставить резервную копию
