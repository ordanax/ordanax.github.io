---
layout: post
title: "Установка Arch на ноутбук: Wi-Fi, тачпад и питание"
description: "Как установить Arch Linux на ноутбук: подключение Wi-Fi через iwctl до установки, настройка тачпада через libinput и энергосбережение"
date: 2026-09-17 00:00:00 +0300
permalink: /ustanovka-na-noutbuk-osobennosti
categories:
- linux
- arch linux
- network
- setup
tags:
- laptop
- iwctl
- libinput
- tlp
- touchpad
- power-management
edit: true
---


Установка Arch на ноутбук почти не отличается от установки на стационарный ПК, но три вещи решают всё: Wi-Fi до загрузки системы, тачпад и питание. На этапе установки сеть поднимается через `iwctl` — iwd уже входит в ISO, ничего ставить не нужно. После первого входа остаётся настроить прошивки, тачпад через libinput и энергосбережение. Ниже — по шагам, без воды.

## Как подключить Wi-Fi на этапе установки

В live-окружении Arch ISO Wi-Fi настраивается через iwd и его интерактивный клиент `iwctl`. Запусти интерактивный режим:

```bash
iwctl
```

Дальше по шагам:

```text
[iwd]# device list
[iwd]# station wlan0 scan
[iwd]# station wlan0 get-networks
[iwd]# station wlan0 connect "Название_сети"
[iwd]# exit
```

`device list` покажет имя беспроводного интерфейса — обычно `wlan0` или `wlp2s0`. Если устройство выключено, включи его:

```text
[iwd]# device wlan0 set-property Powered on
```

После `connect` iwd спросит пароль и сохранит профиль сети в `/var/lib/iwd`. Проверь, что интернет реально работает:

```bash
ping archlinux.org
```

Если пинга нет, а сеть подключилась — глянь `ip addr show wlan0`: возможно, DHCP не выдал адрес. В ISO iwd обычно поднимает сеть сам, но на некоторых роутерах приходится подождать пару секунд и повторить `connect`.

## Что делать, если Wi-Fi не виден

Чаще всего проблема в прошивке или в rfkill. Сначала проверь, не заблокирован ли адаптер:

```bash
rfkill list
```

Если устройство в состоянии `soft blocked` или `hard blocked`, разблокируй:

```bash
rfkill unblock wifi
```

Аппаратный переключатель на корпусе тоже никто не отменял — на некоторых ноутбуках он есть до сих пор.

Дальше проверь, какой чипсет стоит в ноутбуке и загрузился ли его драйвер:

```bash
lspci -knnd ::0280
```

В выводе ищи строку `Kernel driver in use`. Для Intel это `iwlwifi`, для Realtek — `rtw88` или `rtw89`, для MediaTek — `mt76`. Прошивки для большинства чипов лежат в пакете `linux-firmware` — он ставится по умолчанию вместе с ядром. Если адаптер не виден вообще, проверь `dmesg | grep firmware` — там будет видно, какую прошивку не удалось загрузить.

## Как настроить Wi-Fi после установки

После первого входа в установленную систему Wi-Fi нужно поднять заново. Самый простой путь — NetworkManager:

```bash
sudo pacman -S networkmanager
sudo systemctl enable --now NetworkManager
```

Подключение через nmcli:

```bash
nmcli device wifi connect "Название_сети" password "Пароль"
```

NetworkManager запомнит сеть и будет подключаться автоматически. Если предпочитаешь iwd без посредников — поставь его и включи службу:

```bash
sudo pacman -S iwd
sudo systemctl enable --now iwd
```

Подключение — тем же `iwctl`, что и на этапе установки. Про классический вариант через wpa_supplicant я писал отдельно — [настройка Wi-Fi через wpa_supplicant](https://ordanax.github.io/wifi-nastroyka-wpa-supplicant).

## Что учесть с тачпадом

Современные тачпады в Arch работают через libinput. Драйвер ставится так:

```bash
sudo pacman -S xf86-input-libinput
```

В большинстве окружений (GNOME, KDE, XFCE) тачпад подхватывается сразу. Если хочется тап по тачпаду вместо клика кнопкой — включи tap-to-click: в GNOME это в настройках мыши, в XFCE — в настройках тачпада. Проверить, что libinput видит устройство, можно так:

```bash
libinput list-devices
```

Скролл двумя пальцами работает из коробки. Трёхпальцевые жесты — через touchegg или встроенные настройки окружения. Если тачпад не определяется вообще, попробуй параметры ядра `i8042.noloop i8042.nomux` — для старых ноутбуков это классика.

## Энергосбережение на ноутбуке

Без настройки питания ноутбук с Arch будет греться и быстро разряжаться. Два основных варианта: TLP и power-profiles-daemon.

TLP — классика для ноутбуков:

```bash
sudo pacman -S tlp
sudo systemctl enable --now tlp
```

TLP сам управляет CPU-частотами, USB-устройствами и диском. power-profiles-daemon — выбор тех, кто сидит в GNOME: профили «Экономия», «Сбалансированный», «Производительность» переключаются прямо из настроек.

Отдельно настрой поведение при закрытии крышки. Файл `/etc/systemd/logind.conf`, параметр `HandleLidSwitch`:

```conf
HandleLidSwitch=suspend
```

После правки — `systemctl restart systemd-logind`. Значение `suspend` усыпляет ноутбук при закрытии крышки, `ignore` — ничего не делает, `poweroff` — выключает.

## Какие пакеты поставить сразу

Минимальный набор для ноутбука после установки:

```bash
sudo pacman -S intel-ucode   # для процессоров Intel
sudo pacman -S amd-ucode     # для процессоров AMD
```

Микрокод ставится до пересборки загрузчика — иначе обновления прошивки CPU не подхватятся. После установки пересобери GRUB:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Про графику: для встроенной Intel и AMD ничего ставить не нужно — драйверы уже в ядре. Для ноутбуков с NVIDIA (в том числе гибридных) есть отдельный гайд — [драйвер NVIDIA в Arch Linux](https://ordanax.github.io/nvidia-drayver-arch-linux).

Полный порядок действий от загрузки ISO до первого входа — в [чек-листе установки Arch Linux](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019), а свежее пошаговое руководство — в статье [установка Arch Linux 2026](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya).

## Частые вопросы

**Почему на этапе установки не работает Wi-Fi?**
Проверь rfkill (`rfkill list`), включи адаптер (`rfkill unblock wifi`) и убедись, что прошивка загрузилась — `dmesg | grep firmware`. Для большинства чипов достаточно пакета `linux-firmware`.

**iwctl не видит сеть, хотя соседи её ловят.**
Сделай `station wlan0 scan` ещё раз и подожди пару секунд перед `get-networks`. Если сеть скрытая — `station wlan0 connect-hidden "SSID"`.

**Тачпад работает, но тап не кликает.**
Включи tap-to-click в настройках окружения. В X11 можно прописать опцию в конфиг libinput, в Wayland — через настройки GNOME или KDE.

**TLP или power-profiles-daemon — что выбрать?**
Не ставь оба сразу — они конфликтуют. TLP для максимальной автономности, power-profiles-daemon — если хочешь переключать профили из GNOME.

**Нужен ли xf86-video-intel для встроенной графики?**
Нет, современный драйвер modesetting в ядре работает лучше. xf86-video-intel ставят только под старые чипы.

## Заключение

Установка Arch на ноутбук сводится к трём вещам: поднять Wi-Fi через `iwctl` до установки, после первого входа настроить тачпад через libinput и включить энергосбережение (TLP или power-profiles-daemon). Плюс не забыть микрокод процессора и драйвер видеокарты. С этим набором ноутбук будет работать стабильно, не греться и не разряжаться за час.

## Полезные ресурсы

- [ArchWiki: Laptop](https://wiki.archlinux.org/title/Laptop)
- [ArchWiki: iwd](https://wiki.archlinux.org/title/Iwd)