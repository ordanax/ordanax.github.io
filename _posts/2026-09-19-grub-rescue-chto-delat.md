---
layout: post
title: "grub rescue: что делать, когда «grub rescue>»"
description: "grub rescue> — не паникуй: загрузись с live-USB, сделай chroot и переустанови GRUB. Пошаговое восстановление загрузчика Arch Linux."
date: 2026-09-19 00:00:00 +0300
permalink: /grub-rescue-chto-delat
categories:
  - linux
  - arch linux
  - configs
  - kernel-boot
tags:
  - grub
  - rescue
  - bootloader
  - recovery
  - live-usb
edit: true
---



Приглашение `grub rescue>` значит, что GRUB-загрузчик не нашёл свои файлы конфигурации. Система загружается через live-USB, монтируешь корневой раздел и ESP, делаешь `arch-chroot` и переустанавливаешь GRUB — после этого загрузка восстанавливается. Вся процедура занимает минут пятнадцать.

## Что значит grub rescue>

Приглашение `grub rescue>` появляется, когда GRUB установлен на диск, но не может найти каталог `/boot/grub` (или `/boot/grub/x86_64-efi` на UEFI-системах) со своим конфигом. Базовые модули уже вшиты в boot-сектор, поэтому ты попадаешь не в чёрный экран, а в мини-оболочку с командной строкой — но дальше загрузчик продвинуться не может.

### Типичные причины

- Перемещение или переименование разделов через `gdisk`/`fdisk`.
- Замена диска без переустановки GRUB.
- Удаление каталога `/boot`.
- Изменение UUID корневого раздела без обновления `grub.cfg`.
- Ошибка при настройке dualboot — подробнее разобрано в статье «[Windows пропала из меню GRUB](https://ordanax.github.io/dualboot-windows-propala-iz-grub)».

## Как загрузиться с live-USB и попасть в chroot

Это основной способ лечения. Нужна загрузочная флешка с Arch Linux (ISO с archlinux.org).

### Загрузись с USB

Перезагрузись, выбери загрузку с флешки через BIOS/UEFI (обычно `F12`, `F2` или `Delete`). Выбери «Boot Arch Linux (x86_64)».

### Подключи интернет (опционально)

Если нужен доступ к репозиториям для переустановки пакетов:

```bash
dhcpcd          # для проводного интернета
iwctl           # для Wi-Fi
```

### Смонтируй разделы

Определи раскладку дисков:

```bash
lsblk
```

Затем смонтируй корневой раздел и (если есть отдельный) ESP:

```bash
mount /dev/nvme0n1p2 /mnt          # корень — подставь свой раздел
mount /dev/nvme0n1p1 /mnt/boot     # ESP (для UEFI)
```

Для BIOS-системы с отдельным `/boot` — аналогично.

### Войди в chroot

```bash
arch-chroot /mnt
```

Теперь ты внутри своей системы — можно работать с GRUB.

## Как починить GRUB из chroot

После `arch-chroot` выполняй команды по порядку.

### Для UEFI-системы

```bash
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
```

### Для BIOS (Legacy)

```bash
grub-install --target=i386-pc /dev/nvme0n1
grub-mkconfig -o /boot/grub/grub.cfg
```

Важно: в команде `grub-install` для BIOS указывай именно диск (`nvme0n1` или `sda`), а не раздел.

После этого выйди из chroot и перезагружайся:

```bash
exit
umount -R /mnt
reboot
```

Перед перезагрузкой проверь `/etc/fstab` — UUID в нём должны совпадать с реальными (команда `lsblk -f` покажет текущие UUID). Если ты перемещал разделы, несовпадение UUID — частая причина повторного падения в rescue. Подробный разбор — в статье «[Переустановка GRUB после поломки](https://ordanax.github.io/pereustanovka-grub-posle-polomki)».

## Можно ли поднять систему прямо из rescue

Да, если знаешь расположение ядра и раздела.

### Быстрая попытка — insmod normal

```bash
insmod normal
normal
```

Запустит обычный режим загрузки. Сработает, если `grub.cfg` лежит на месте, но не нашёлся по умолчанию.

### Ручная загрузка ядра

Если `insmod normal` не помог, загружаем ядро вручную. Пример для UEFI с корнем на `nvme0n1p2`:

```bash
set root=(hd0,gpt2)
linux /vmlinuz-linux root=/dev/nvme0n1p2 rw
initrd /initramfs-linux.img
boot
```

Для BIOS:

```bash
set root=(hd0,msdos2)
linux /vmlinuz-linux root=/dev/sda2 rw
initrd /initramfs-linux.img
boot
```

Номера разделов (`hd0,gpt2`, `hd0,msdos2`) подставляй из вывода команды `ls` — она покажет доступные разделы и файловые системы.

Это способ «скорой помощи»: загрузить систему один раз, чтобы потом починить GRUB изнутри.

## Как предотвратить появление grub rescue>

### Обновляй grub.cfg после любых изменений

Каждый раз, когда меняешь разделы или обновляешь ядро:

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

### Сверяй UUID в fstab

После перемещения разделов:

```bash
lsblk -f
cat /etc/fstab
```

Если UUID не совпадают — правь `fstab` и перегенерируй `grub.cfg`.

### При замене диска — всегда переустанавливай GRUB

Копирование разделов не переносит boot-код. После клонирования диска всегда прогоняй `grub-install` из chroot.

### Используй UUID в конфигурации GRUB

По умолчанию `grub-mkconfig` генерирует конфиг с UUID — это надёжнее, чем имена устройств (`/dev/sda1` может стать `/dev/sdb1` при подключении нового диска).

Общая методика диагностики подобных проблем — в статье «[Методика решения проблем в Arch Linux](https://ordanax.github.io/metodika-resheniya-problem-arch)».

## Частые вопросы

### grub rescue> появился после обновления ядра — что случилось?

Скорее всего, обновление ядра прошло некорректно и `grub.cfg` не был перегенерирован. Загрузись с live-USB и выполни `grub-mkconfig`. Если ядро не видно — смотри «[GRUB не видит ядра после обновления](https://ordanax.github.io/grub-ne-vidit-yadra-posle-obnovleniya)».

### Стоит ли прописывать set root и set prefix в rescue?

Это вариант для «скорой помощи». Если знаешь правильный раздел — попробуй:

```bash
set root=(hd0,gpt2)
set prefix=($root)/boot/grub
insmod normal
normal
```

Если модули и конфиг на месте — система загрузится. Но это костыль. Настоящий ремонт — через `arch-chroot`.

### Часто ли ломается GRUB в Arch Linux?

Нет. GRUB сам по себе стабилен. Чаще всего проблема в действиях пользователя: перемещение разделов без обновления конфига, замена диска, ручные правки `fstab`. Если не трогать раскладку дисков — работает годами.

### После ремонта GRUB система не грузится с другого диска в dualboot?

GRUB мог не увидеть Windows или вторую Linux-установку. Решение — `os-prober` и повторная генерация `grub.cfg`. Подробнее — в статье «Windows пропала из меню GRUB».

## Полезные ресурсы

- [GRUB — ArchWiki](https://wiki.archlinux.org/title/GRUB) — основная страница по установке и настройке загрузчика.
- [GRUB/Tips and tricks — ArchWiki](https://wiki.archlinux.org/title/GRUB/Tips_and_tricks) — продвинутые приёмы работы с GRUB.

## Заключение

`grub rescue>` — не смертельный экран, а подсказка: GRUB не нашёл свой конфиг. Загрузка с live-USB, `arch-chroot` и две команды (`grub-install` + `grub-mkconfig`) решают проблему за пару минут. Если нужно поднять систему прямо сейчас — ручная загрузка ядра из rescue тоже работает. Главное после ремонта — проверь `fstab` и UUID, чтобы не попасть в ту же ловушку снова.
