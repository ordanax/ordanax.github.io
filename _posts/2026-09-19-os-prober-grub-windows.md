---
layout: post
title: "os-prober: как GRUB увидит Windows и другие ОС"
description: "Настройка os-prober в Arch Linux для dual boot: установка, включение GRUB_DISABLE_OS_PROBER, пересборка grub.cfg и решение проблем."
date: 2026-09-19 00:00:00 +0300
permalink: /os-prober-grub-windows
categories:
- linux
- arch linux
- configs
tags:
- os-prober
- grub
- dualboot
- windows
- bootloader
edit: true
---

Чтобы GRUB показывал Windows (или любую другую ОС) в меню загрузки, нужно три действия: поставить `os-prober`, добавить в `/etc/default/grub` строку `GRUB_DISABLE_OS_PROBER=false` и пересобрать конфиг. С 2023 года `os-prober` по умолчанию отключён — это главная причина, почему Windows «пропадает» из меню.

## Почему GRUB не видит Windows из коробки

GRUB — гибкий загрузчик, но из коробки он знает только те ядра и ОС, которые нашёл при установке. Если ты ставишь Arch на чистый диск — GRUB видит только Linux. А вот Windows, Fedora или FreeBSD — нет.

С 2023 года разработчики GRUB по соображениям безопасности отключили автосканирование. Раньше достаточно было поставить `os-prober`, и он работал молча. Теперь нужно явно разрешить его в конфиге. Без этой строчки `grub-mkconfig` выдаст предупреждение:

```
Warning: os-prober will not be executed to detect other bootable partitions.
```

Именно это видят те, кто после обновления системы обнаруживает, что Windows пропала из меню.

## Как установить и включить os-prober

### Установка пакета

Начни с установки:

```
sudo pacman -S os-prober
```

Пакет небольшой, зависимости минимальные. После установки он готов к работе, но пока не активен — GRUB его игнорирует.

### Включение в конфиге GRUB

Отредактируй файл `/etc/default/grub`:

```
sudo nano /etc/default/grub
```

Добавь (или раскомментируй, если строка уже есть):

```
GRUB_DISABLE_OS_PROBER=false
```

Именно `false` — значит «не отключай os-prober». Запутанная логика, но работает так: переменная называется «отключить», а тебе нужно значение «нет, не отключай».

### Проверка ntfs-3g

`os-prober` сканирует разделы и определяет ОС по содержимому. Для NTFS-разделов (где живёт Windows) ему нужен пакет `ntfs-3g`:

```
sudo pacman -S ntfs-3g
```

Без него `os-prober` не сможет прочитать файловую систему Windows и пропустит раздел.

## Как пересобрать конфиг GRUB

После всех изменений пересобери `grub.cfg`:

```
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Если всё настроено правильно, в выводе увидишь что-то вроде:

```
Found Windows Boot Manager on /dev/sda1@/EFI/Microsoft/Boot/bootmgfw.efi
```

После перезагрузки Windows появится в меню GRUB.

### Скрытые разделы и точки монтирования

`os-prober` читает `mtab` (список смонтированных файловых систем) и ищет загрузочные записи там. Обычно раздел Windows монтировать не нужно — `os-prober` увидит его сам. Но если раздел не определяется, смонтируй его перед пересборкой:

```
sudo mount /dev/sda2 /mnt/windows
```

Точка монтирования может быть любой — `os-prober` смотрит на сам раздел, а не на путь.

## Почему os-prober не находит системы

### Несколько ESP (EFI System Partition)

Если Windows и Arch живут на разных дисках и у каждого свой EFI-раздел — это классическая проблема. `os-prober` ищет загрузчик Windows на разделах текущего ESP. Если Windows boot-менеджер лежит на другом диске, он не будет найден.

Решение: убедись, что оба загрузчика используют один ESP, либо добавь запись Windows вручную через `/etc/grub.d/40_custom`. Подробнее — в статье [Один EFI-раздел для dual boot](https://ordanax.github.io/odin-efi-razdel-dualboot).

### Windows на отдельном диске

Если Windows установлена на отдельный физический диск, убедись, что:

1. `GRUB_DISABLE_OS_PROBER=false` в **правильном** файле `/etc/default/grub`.
2. Второй диск виден в Arch (`lsblk`).
3. Windows Fast Startup отключён — иначе NTFS-раздел в «гибернации», и `ntfs-3g` откажется его читать.

### Ошибка в chroot

`os-prober` может работать некорректно, если запускать `grub-mkconfig` из chroot (например, при установке Arch). Если Windows не видна — перезагрузись в установленную систему и запусти команду оттуда.

## Как добавить другие ОС вручную

Если `os-prober` не помогает или ты хочешь точечный контроль, добавь запись вручную. Отредактируй `/etc/grub.d/40_custom`:

```
menuentry "Windows 11" --class windows {
    insmod part_gpt
    insmod fat
    search --fs-uuid --no-floppy --set=root XXXX-XXXX
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}
```

Замени `XXXX-XXXX` на UUID EFI-раздела — его покажет `blkid /dev/sda1`. После редактирования пересобери конфиг: `sudo grub-mkconfig -o /boot/grub/grub.cfg`.

### systemd-boot и os-prober

Если ты используешь `systemd-boot` вместо GRUB, `os-prober` не нужен — systemd-boot автоматически подхватывает Windows Boot Manager через ESP. А вот если GRUB после обновления перестал видеть ядра — смотри [GRUB не видит ядра после обновления](https://ordanax.github.io/grub-ne-vidit-yadra-posle-obnovleniya).

## Частые вопросы

### Windows пропала после обновления GRUB — что делать?

Пересобери конфиг: `sudo grub-mkconfig -o /boot/grub/grub.cfg`. Если не помогло — проверь, что `GRUB_DISABLE_OS_PROBER=false` на месте. После крупных обновлений GRUB строка иногда сбрасывается.

### os-prober не видит Windows на втором диске

Убедись, что раздел NTFS виден через `lsblk`, и проверь наличие `ntfs-3g`. Если Windows на отдельном диске с отдельным ESP — в этом случае лучше добавить запись вручную через `40_custom`. Также смотри статью [Dualboot: Windows пропала из GRUB](https://ordanax.github.io/dualboot-windows-propala-iz-grub).

### Нужен ли os-prober, если в меню только Arch и Windows?

Да, `os-prober` — самый простой способ. Без него GRUB не знает о Windows автоматически. Альтернатива — ручная запись в `40_custom`, но это требует больше настройки.

### grub-mkconfig ругается на os-prober

Убедись, что пакет установлен (`pacman -Qi os-prober`). Если пакет есть, а предупреждение остаётся — проверь синтаксис: нужна строка `GRUB_DISABLE_OS_PROBER=false` без лишних пробелов и кавычек.

### Где посмотреть, какие ОС нашёл os-prober?

Запусти сканирование вручную:

```
sudo os-prober
```

Вывод покажет разделы и обнаруженные ОС. Если команда ничего не возвращает — система не нашла загрузчиков.

## Полезные ресурсы

- [GRUB — ArchWiki](https://wiki.archlinux.org/title/GRUB): полная документация по настройке GRUB.
- [Dual boot with Windows — ArchWiki](https://wiki.archlinux.org/title/Dual_boot_with_Windows): пошаговое руководство по dual boot.
- [Разметка диска GPT/MBR](https://ordanax.github.io/razmetka-diska-gpt-mbr): как правильно разметить диск перед установкой.
- [Переустановка GRUB после поломки](https://ordanax.github.io/pereustanovka-grub-posle-polomki): если GRUB потерялся целиком.

## Заключение

`os-prober` — маленький пакет, но без него dual boot с GRUB превращается в ручную настройку. С 2023 года он отключён по умолчанию, и это первое, что стоит проверить, если Windows исчезла из меню загрузки. Установка занимает минуту: `pacman -S os-prober`, одна строчка в конфиге и пересборка. Если что-то пошло не так — начни с ручного запуска `os-prober` и проверь, видит ли система NTFS-раздел.
