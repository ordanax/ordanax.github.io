---
layout: post
title: "Не грузится после установки: чёрный экран, emergency shell"
description: "Arch не грузится после установки: чёрный экран, emergency shell, triggering uevents. Пошаговая диагностика и восстановление через live-USB."
date: 2026-09-17 00:00:00 +0300
permalink: /ne-gruzitsya-posle-ustanovki-chernyi-ekran
categories:
- linux
- arch linux
- update-recovery
tags:
- troubleshooting
- boot
- emergency-shell
- grub
- arch-linux
edit: true
---


Установка Arch Linux прошла успешно, но после перезагрузки вместо рабочего стола — чёрный экран, emergency shell или зависание на "triggering uevents". Три симптома, три разных корня, но один алгоритм диагностики: fstab, загрузчик, ядро/initramfs, видеодрайвер. Разбираю каждый случай с командами.

## Почему после установки появляется чёрный экран

Самая частая причина — видеодрайвер. Установка шла через tty, без графики, и ядро использовало простой framebuffer. После первого входа в графическое окружение запускается модуль DRM, и если драйвер несовместим с железом — экран тухнет.

Вторая причина — неправильный `fstab`: система не может смонтировать корень или `/home` и падает в emergency shell. Третья — повреждённый initramfs: ядро не находит модули для дисков, загрузка зависает на "triggering uevents".

## Как исправить чёрный экран после первого входа

### Параметр nomodeset — быстрый способ вернуть экран

Если экран погас сразу после первого входа в графику — добавь `nomodeset` в строку ядра. Это отключит Kernel Mode Setting и позволит загрузиться с базовым framebuffer'ом.

В меню GRUB нажми `e`. Найди строку, начинающуюся с `linux`, допиши в конец `nomodeset` и нажми `Ctrl+x`. Система загрузилась? Проблема в драйвере. Сделай параметр постоянным:

```bash
sudo nano /etc/default/grub
```

В строке `GRUB_CMDLINE_LINUX_DEFAULT` допиши `nomodeset`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="quiet nomodeset"
```

Примени изменения:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

`nomodeset` — временная мера. Постоянное решение — установить правильный драйвер. Для NVIDIA:

```bash
sudo pacman -S nvidia nvidia-utils
```

Проверь, что DRM включён:

```bash
cat /sys/module/nvidia_drm/parameters/modeset
```

Вывод `Y` — всё в порядке. Если `N`, добавь `nvidia_drm.modeset=1` в параметры ядра. Подробнее — в статье [драйвер NVIDIA для Arch Linux](https://ordanax.github.io/nvidia-drayver-arch-linux).

## Что такое emergency shell и как из него выйти

Emergency shell — интерактивная оболочка, в которую systemd опускает при критической ошибке загрузки. Типичное сообщение: "You are now being dropped into an emergency shell". Выйти можно командой `exit`, но без решения проблемы система снова упадёт.

### Как проверить fstab из emergency shell

Смонтируй корневой раздел и открой `fstab`:

```bash
mount /dev/sdXn /mnt
cat /mnt/etc/fstab
```

Типичные ошибки: неправильный UUID, опечатка в точке монтирования, несуществующий swap. Сверь UUID с реальными:

```bash
blkid
```

Не совпадают? Исправь `fstab`:

```bash
nano /mnt/etc/fstab
```

Закомментируй проблемную строку (поставь `#` в начале) и проверь:

```bash
mount -a
```

Ошибок нет — система загрузится.

### Как посмотреть лог ошибок

В emergency shell с busybox initramfs journal недоступен — используй `dmesg`:

```bash
dmesg | tail -30
```

С хуком `systemd` в mkinitcpio доступен полный журнал:

```bash
journalctl -xb
```

Флаг `-xb` показывает ошибки текущей загрузки с развёрнутым выводом.

## Что значит "triggering uevents" и почему система зависает

"Triggering uevents" — этап работы udev: ядро отправляет события об оборудовании, udev создаёт файлы устройств в `/dev`. Зависание здесь — проблема initramfs: в образ не попали модули для файловой системы (btrfs, ext4, lvm2) или дискового контроллера (nvme, ahci).

### Пересборка initramfs

Загрузись с live-USB, войди в chroot (см. ниже) и пересобери образы для всех ядер:

```bash
mkinitcpio -P
```

Для одного ядра — `mkinitcpio -p linux`. Проверь `/etc/mkinitcpio.conf`: в `MODULES` — нужные модули, в `HOOKS` — хуки (`lvm2`, `btrfs`, `encrypt`). Подробности — на [ArchWiki: mkinitcpio](https://wiki.archlinux.org/title/Mkinitcpio).

## Как починить загрузчик с live-USB

GRUB повреждён или не установлен — система падает сразу после POST с "no bootable device". Лечится через live-USB.

1. Загрузись с live-USB Arch.
2. Смонтируй корень:

```bash
mount /dev/sdXn /mnt
```

3. Смонтируй ESP (для UEFI) или `/boot`:

```bash
mount /dev/sdXn /mnt/boot
```

4. Войди в chroot:

```bash
arch-chroot /mnt
```

5. Переустанови GRUB (UEFI):

```bash
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
```

Для Legacy BIOS: `grub-install --target=i386-pc /dev/sdX`.

6. Сгенерируй конфигурацию:

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

7. Выходи и перезагружайся:

```bash
exit
umount -R /mnt
reboot
```

## Личный алгоритм: что проверять по порядку

Проверенная последовательность, которая экономит часы:

1. **fstab** — UUID и точки монтирования. Частая ошибка: UUID swap не совпадает с реальным.
2. **Загрузчик** — GRUB установлен? Конфигурация сгенерирована?
3. **Ядро и initramfs** — модули для файловой системы и контроллера на месте? mkinitcpio пересобран?
4. **Видеодрайвер** — `nomodeset` решает временно, правильный пакет — постоянно.

В девяти случаях из десяти проблема в первых двух пунктах. Ничего не помогло? Сверь каждый шаг с [чек-листом установки Arch Linux](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019).

## Частые вопросы

### fstab выглядит нормально, но система падает в emergency shell

Проверь `journalctl -xb` или `dmesg`. Часто дело в повреждённой файловой системе: запусти `fsck /dev/sdXn` (раздел должен быть не смонтирован).

### Чёрный экран после обновления, а не после установки

Загрузись с предыдущим ядром (в GRUB — "Advanced options"), затем откати пакет:

```bash
sudo pacman -U /var/cache/pacman/pkg/nvidia-utils-<старая_версия>.pkg.tar.zst
```

### Нужно ли всегда использовать nomodeset?

Нет. Это временная мера для диагностики. После установки правильного драйвера убери параметр из `/etc/default/grub` и пересобери конфигурацию — иначе отключено аппаратное ускорение графики.

## Заключение

Не грузится Arch после установки — не повод переустанавливать. Большинство проблем решаются за минуты: добавил `nomodeset`, поправил `fstab`, пересобрал `mkinitcpio` или переустановил GRUB через live-USB. Проверяй по порядку: fstab, загрузчик, ядро, драйвер.

## Полезные ресурсы

- [ArchWiki: General troubleshooting](https://wiki.archlinux.org/title/General_troubleshooting) — общие методы диагностики
- [Полная установка Arch Linux 2026: пошаговое руководство](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya)
- [Установка Arch Linux за 15 минут](https://ordanax.github.io/ustanovka-archlinux-2019-za-15-minut)