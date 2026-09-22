---
layout: post
title: "Установка Arch Linux ARM на Raspberry Pi"
description: "Пошаговая установка Arch Linux ARM на Raspberry Pi 4 и 5: скачивание, разметка SD-карты, первый вход, настройка пакетов и драйверов."
date: 2026-09-17 00:00:00 +0300
permalink: /arch-linux-arm-raspberry-pi
categories:
- linux
- arch linux
- arm
- setup
tags:
- arch-linux-arm
- raspberry-pi
- aarch64
- alarm
- embedded
edit: true
---


Arch Linux ARM на Raspberry Pi ставится через скачивание tarball-архива с [сайта проекта](https://archlinuxarm.org), ручную разметку SD-карты через fdisk, распаковку корневой файловой системы bsdtar и настройку после первого входа. Весь процесс занимает минут 20, если карта под рукой, а железо — Raspberry Pi 4 или 5.

## Что такое Arch Linux ARM и чем отличается от обычного Arch

Arch Linux ARM (сокращённо ALARM) — отдельный порт Arch Linux для ARM-устройств. Его поддерживает команда archlinuxarm.org, а не основной проект Arch Linux. Пакеты, репозитории и процесс установки другие. Взять ISO с archlinux.org и запихнуть на Pi не получится — архитектура aarch64 вместо x86_64.

Чем ещё отличается? В ALARM свои зеркала, ключи подписи и репозиторий `alarm`. В нём лежат пакеты, собранные под ARM: ядро с патчами для Broadcom (SoC BCM2711 на Pi 4, BCM2712 на Pi 5), драйверы GPU v3d, firmware для Wi-Fi и Bluetooth.

Если ставил обычный Arch на ПК, концепции знакомы: тот же pacman, подход «поставил — настроил сам». Но пакеты, ядро и процесс установки другие. Подробнее об устройстве Arch Linux — в [обзоре Arch Linux](https://ordanax.github.io/obzor-linux-arch).

## Как скачать и подготовить образ для Raspberry Pi

Идём на [archlinuxarm.org/platforms](https://archlinuxarm.org/platforms/armv8/broadcom/raspberry-pi-4). Для Raspberry Pi 4 и 5 доступны два варианта:

- **AArch64 (рекомендуется)** — образ с mainline-ядром и U-Boot. Полная поддержка железа, включая графику VC4.
- **ARMv7** — образ с закрытым vendor-ядром от Broadcom. Нужен, если зависим от оверлеев или проприетарных GPU-блобов.

Для большинства задач берём AArch64. Архив называется `ArchLinuxARM-rpi-aarch64-latest.tar.gz` и лежит на странице загрузок. Скачиваем на машину, где вставлена SD-карта.

Важно: это **не образ для записи dd**, а tarball с корневой файловой системой.

## Разметка SD-карты и установка системы

Подставь вместо `sdX` имя своей SD-карты (`lsblk` покажет):

```bash
fdisk /dev/sdX
```

В fdisk по порядку: **o** (стереть разделы), **n**, **p**, **1**, ENTER, **+1G** (boot, 1 ГБ), **t**, **c** (тип W95 FAT32), **n**, **p**, **2**, ENTER, ENTER (root на всё остальное), **w** (записать и выйти).

Создаём файловые системы:

```bash
mkfs.vfat /dev/sdX1
mkfs.ext4 /dev/sdX2
```

Монтируем, распаковываем архив и переносим загрузочные файлы:

```bash
mkdir boot root
mount /dev/sdX1 boot
mount /dev/sdX2 root
bsdtar -xpf ArchLinuxARM-rpi-aarch64-latest.tar.gz -C root
mv root/boot/* boot
```

Важный момент для Pi 4: если `fstab` ссылается на `mmcblk0`, а у тебя Pi 4 (где SD-карта — `mmcblk1`), поправь перед извлечением:

```bash
sed -i 's/mmcblk0/mmcblk1/g' root/etc/fstab
```

Размонтируем, вытаскиваем карту:

```bash
umount boot root
```

Вставляем SD-карту в Pi, подключаем Ethernet, подаём питание. Для Pi 4 нужен блок на 3A через USB-C — слабое питание даёт случайные ошибки и портит файловую систему.

## Первый вход и базовая настройка

Подключись по SSH или через консоль:

```bash
ssh root@alarmpi
```

Логин: `root`, пароль: `root`. Есть и пользователь `alarm` с паролем `alarm`. IP-адрес покажет роутер (DHCP по умолчанию через Ethernet).

Первым делом — сменить пароли и инициализировать ключи подписи:

```bash
passwd
pacman-key --init
pacman-key --populate archlinuxarm
```

Без этого pacman будет ругаться на подпись пакетов и не даст ничего установить.

## Что настроить сразу после установки

Базовый набор действий после первого входа:

**Обновление системы:**

```bash
pacman -Syu
```

Rolling release — обновляйся сразу.

**Сеть и Wi-Fi:**

Если нужен Wi-Fi вместо Ethernet:

```bash
iwctl station wlan0 connect "SSID"
```

Для постоянного подключения — `wpa_supplicant` или `NetworkManager`.

**Создание пользователя:**

```bash
useradd -m -G wheel -s /bin/bash myuser
passwd myuser
```

Потом поставь sudo и настрой `/etc/sudoers`.

**Часовой пояс и локаль:**

```bash
timedatectl set-timezone Europe/Moscow
localectl set-locale LANG=en_US.UTF-8
```

## Какие пакеты и драйверы доступны на ARM

Пакетный менеджер — обычный pacman с репозиториями `alarm` и `archlinuxarm`. Многие пакеты из основного Arch пересобраны под ARM. AUR доступен, но не все PKGBUILDы работают на ARM.

Что из коробки работает на Raspberry Pi 4/5:

- **GPU**: open-source драйверы v3d для Videocore VI/VII, KMS для modesetting
- **Wi-Fi/Bluetooth**: firmware на борту, работает через wpa_supplicant и NetworkManager
- **GPIO**: пакет `raspberrypi-gpio` или sysfs
- **Аудио**: HDMI-аудио через ALSA, 3.5mm jack через `bcm2835`

Чего не стоит ожидать: аппаратного ускорения видео через VPU (пока не интегрирован в mainline) и закрытых GPU-блобов в AArch64-образе.

## Частые вопросы

### Что лучше для Raspberry Pi 5: ARMv7 или AArch64?

Однозначно AArch64. ARMv7-образ заточен под старые модели и использует vendor-ядро. На Pi 5 (BCM2712) mainline-ядро через AArch64-образ даёт полную поддержку железа.

### Можно ли запустить Graphical Desktop на Pi с Arch Linux ARM?

Да. Поставь Xorg или Wayland, GNOME/KDE/Sway — что угодно. Pi 4 с 4 ГБ RAM тянет GNOME нормально. Для серверных задач десктоп не нужен.

### Как обновить систему на ALARM?

Так же как на обычном Arch: `pacman -Syu`. Никаких специальных скриптов — rolling release работает одинаково.

### Почему pacman ругается на подпись пакетов?

Не выполнен `pacman-key --populate archlinuxarm`. Этот шаг обязателен после первой установки. Ключи подписи ALARM отличаются от ключей основного Arch.

### Как расширить корневой раздел после увеличения SD-карты?

Если SD-карта заменена на бо́льшую, а раздел root остался прежним:

```bash
fdisk /dev/mmcblk1  # удалить и создать раздел 2 заново, не трогая данные
resize2fs /dev/mmcblk1p2
```

## Заключение

Установка Arch Linux ARM на Raspberry Pi — это не «поставить Arch на ARM в обход», а отдельный зрелый проект со своей инфраструктурой. Процесс не сложнее установки на ПК: скачал tarball, разметил карту, распаковал, вошёл, настроил. Raspberry Pi 4 и 5 работают с AArch64-образом из коробки, Wi-Fi, графика и пакеты доступны сразу. Если знаком с [чек-листом установки Arch](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019) на ПК — логика та же, отличия в пакетах и распаковке вместо pacstrap.

## Полезные ресурсы

- Raspberry Pi — официальный сайт: https://www.raspberrypi.com
- Пошаговая установка Arch Linux 2026: https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya
