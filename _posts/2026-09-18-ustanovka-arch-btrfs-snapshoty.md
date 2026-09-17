---
layout: post
title: "Установка Arch с Btrfs-снапшотами с самого начала"
description: "Ставим Arch Linux на btrfs: подтома @, @home, @snapshots, @log, сжатие zstd, snapper и snap-pac — откат системы за минуты."
date: 2026-09-18 00:00:00 +0300
permalink: /ustanovka-arch-btrfs-snapshoty
categories:
- linux
- arch linux
- storage
tags:
- btrfs
- snapper
- snapshots
- subvolumes
- zstd
- installation
edit: true
---

Btrfs-снапшоты — это мгновенные копии системы, которые почти не занимают места и позволяют откатиться после неудачного обновления за пару минут. Чтобы получить их с самого начала, достаточно при установке Arch Linux создать файловую систему btrfs, разбить её на подтома и поставить snapper. Ниже — полная последовательность команд: от разметки до первого автоматического снапшота.

## Зачем btrfs-снапшоты при установке

Снапшот — это не копия файлов, а «слепок» состояния файловой системы. Btrfs работает по принципу copy-on-write: пока данные не меняются, снапшот и оригинал ссылаются на одни и те же блоки. Изменился файл — btrfs записывает новую версию, а старая остаётся в снапшоте. Поэтому сотня снапшотов занимает столько же места, сколько сами изменения.

Что это даёт на практике:

- **Откат после `pacman -Syu`.** Обновился и сломал систему — загрузился в снапшот и вернулся к рабочему состоянию.
- **Страховка перед экспериментами.** Поставил пакет из AUR, сломал конфиг — откатился.
- **Сжатие zstd.** Btrfs сжимает данные на лету, экономия места на системном разделе — 20–40%.

Снапшоты надо настроить на этапе установки: разбили диск на подтома сразу — откат будет чистым и быстрым. Отложили — придётся переустанавливать или переносить систему.

## Как разметить диск под btrfs с подтомами

Разметка как при обычной установке: GPT, ESP на 1 ГБ, корневой раздел. Подробно про выбор схемы — в статье [«Разметка диска с нуля: GPT vs MBR»](https://ordanax.github.io/razmetka-diska-gpt-mbr). Дальше вместо ext4 создаём btrfs:

```bash
mkfs.fat -F 32 /dev/sda1
mkfs.btrfs -L arch /dev/sda2
```

Подтома — это не разделы. Раздел один, а внутри него логические «разделы»: `@` для корня, `@home` для домашних папок, `@log` для журналов, `@snapshots` для снапшотов. Снапшот корня не захватывает `/home` и `/var/log` — при откате данные и логи остаются нетронутыми.

## Как настроить subvol=@, @home, @snapshots, @log

Монтируем раздел без опций и создаём подтома:

```bash
mount /dev/sda2 /mnt
btrfs subvolume create /mnt/@
btrfs subvolume create /mnt/@home
btrfs subvolume create /mnt/@log
btrfs subvolume create /mnt/@snapshots
umount /mnt
```

Теперь монтируем каждый подтом в свою точку. Опции `compress=zstd,noatime` задаём один раз — они применяются ко всей файловой системе:

```bash
mount -o compress=zstd,noatime,subvol=@ /dev/sda2 /mnt
mount --mkdir -o subvol=@home /dev/sda2 /mnt/home
mount --mkdir -o subvol=@log /dev/sda2 /mnt/var/log
mount --mkdir -o subvol=@snapshots /dev/sda2 /mnt/.snapshots
mount --mkdir /dev/sda1 /mnt/boot
```

ESP монтируется в `/boot` как обычно — он вне btrfs, и это нормально. Дальше установка:

```bash
pacstrap -K /mnt base linux linux-firmware btrfs-progs snapper snap-pac grub-btrfs grub efibootmgr
genfstab -U /mnt >> /mnt/etc/fstab
```

`genfstab` сам подхватит опции `subvol=@` и `compress=zstd` из текущих монтирований. Проверь `/mnt/etc/fstab` — каждая строка btrfs должна содержать `subvol=/@` или `subvol=/@home`. Если где-то `subvolid` вместо пути — замени на путь: при откате ID подтома меняется, а путь остаётся.

Для одного btrfs-раздела хуки в mkinitcpio не нужны — `btrfs` хук только для пулов из нескольких устройств, а GRUB сам передаст ядру `rootflags=subvol=@`. Для надёжности можно добавить `btrfs` в `MODULES` в `mkinitcpio.conf` — ArchWiki рекомендует, хотя на практике это не обязательно. Дальше chroot, загрузчик, locale — всё как в [пошаговом руководстве по установке Arch 2026](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya).

## Как поставить snapper и настроить снапшоты

После первой загрузки создаём конфигурацию snapper для корня:

```bash
sudo snapper -c root create-config /
```

Snapper создаст подтом `/.snapshots` внутри `@` — он не нужен, у нас уже есть `@snapshots`. Удаляем и монтируем наш:

```bash
sudo btrfs subvolume delete /.snapshots
sudo mkdir /.snapshots
sudo mount -o subvol=@snapshots /dev/sda2 /.snapshots
```

Добавь строку в `/etc/fstab`, чтобы `/.snapshots` монтировался при загрузке. Включаем снапшоты по расписанию:

```bash
sudo systemctl enable --now snapper-timeline.timer snapper-cleanup.timer
```

`snap-pac` уже установлен — он делает pre/post-снапшоты при каждом `pacman`. Проверить: `sudo pacman -Syu` — и в списке снапшотов появятся пары до/после обновления.

Чтобы снапшоты появлялись в меню GRUB, включи демон grub-btrfs:

```bash
sudo systemctl enable --now grub-btrfsd
```

В GRUB появится пункт «snapshots» — загрузиться в любой снапшот можно прямо из меню.

## Как откатиться

Самый простой путь — загрузиться в снапшот из GRUB и проверить, что система рабочая. Но это read-only состояние: изменения не сохранятся. Для полноценного отката загружаемся с live-USB:

```bash
mount /dev/sda2 /mnt
btrfs subvolume list /mnt
```

Находим нужный снапшот в `/mnt/@snapshots/N/snapshot` (N — номер). Переименовываем текущий корень и восстанавливаем снапшот:

```bash
mv /mnt/@ /mnt/@.broken
btrfs subvolume snapshot /mnt/@snapshots/N/snapshot /mnt/@
```

Перезагружаемся. Если всё работает — удаляем сломанный корень: `btrfs subvolume delete /mnt/@.broken`. Данные в `/home` и логи в `/var/log` не тронуты — они в своих подтомах.

## Частые вопросы

**Подтома — это то же самое, что разделы?**

Нет. Раздел — это часть диска с собственной файловой системой. Подтом — это именованное пространство внутри одной btrfs-файловой системы. Разделы нельзя быстро «откатить», подтома — можно, через снапшоты.

**Сколько места съедают снапшоты?**

Почти ничего, пока данные не меняются. Снапшот хранит только разницу между состояниями. Десятки снапшотов на десктопе — это обычно единицы гигабайт.

**Нужен ли отдельный раздел под /home?**

Нет. При схеме с подтомами `/home` живёт в `@home` внутри того же раздела. Откат корня не трогает домашние файлы — это и есть главный плюс.

**Что делать, если корневой раздел заполнился?**

Сначала почисти снапшоты: `sudo snapper -c root list` и `sudo snapper -c root delete N`. Потом pacman-кэш. Про переполнение корня — в статье [«Корневой раздел заполняется»](https://ordanax.github.io/kornevoy-razdel-zapolnyaetsya).

## Заключение

Btrfs-снапшоты с самого начала — это дешёвая страховка, которая окупается при первом же сломанном обновлении. Схема простая: один раздел btrfs, подтома `@`, `@home`, `@log`, `@snapshots`, snapper с snap-pac для автоматических снапшотов и grub-btrfs для загрузки в них. Настроил один раз — и откат системы занимает минуты, а не переустановку на полдня.

## Полезные ресурсы

- [Btrfs — ArchWiki](https://wiki.archlinux.org/title/Btrfs) — подтома, сжатие, снапшоты, известные проблемы
- [Snapper — ArchWiki](https://wiki.archlinux.org/title/Snapper) — конфигурации, расписания, восстановление
- [Установка Arch с LVM](https://ordanax.github.io/ustanovka-arch-s-lvm) — сравнение: LVM-снапшоты против Btrfs