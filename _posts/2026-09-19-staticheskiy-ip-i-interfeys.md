---
layout: post
title: "Статический IP: определение интерфейса и ручная настройка"
description: "Как узнать имя сетевого интерфейса в Arch Linux и настроить статический IP-адрес через systemd-networkd: пошаговая инструкция."
date: 2026-09-19 00:00:00 +0300
permalink: /staticheskiy-ip-i-interfeys
categories:
- linux
- arch linux
- network
tags:
- systemd-networkd
- static-ip
- networkctl
- ip-route
- arch-linux
edit: true
---

Чтобы определить имя сетевого интерфейса в Arch Linux, выполни `ip link` или `ip -br addr` — в выводе увидишь имена вроде `enp1s0`, `enp3s0` или `wlp2s0`. После этого статический IP прописывается одной конфигурацией в `/etc/systemd/network/`: указываешь адрес, шлюз и DNS — и всё. Весь процесс занимает пару минут.

## Как узнать имя сетевого интерфейса

Прежде чем настраивать что-либо, нужно понять, как система называет твой сетевой адаптер. Имена формируются автоматически: `en` — проводные, `wl` — беспроводные, `ww` — мобильные, дальше буквы и цифры описывают шину и слот (`p1s0` — PCI, слот 1, порт 0).

### Через ip link и ip -br addr

Самый быстрый способ:

```bash
ip link
```

В выводе тебя интересуют строки вида `2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP>`. Интерфейс `lo` — это петля (loopback), её не трогаем. Остальные — кандидаты.

Компактный вариант — `ip -br addr`: одна строка на интерфейс с именем, состоянием (UP/DOWN) и назначенными IP. Удобно проверить, какой интерфейс активен и получил ли он адрес по DHCP.

### Через networkctl

Если в системе запущен `systemd-networkd`:

```bash
networkctl
```

Таблица покажет имя, тип (ether/wlan), статус и способ настройки. `routable` — интерфейс подключён и имеет рабочий IP. `unmanaged` — конфигурации для него ещё нет.

### Как выбрать нужный интерфейс

Обычно нужен проводной адаптер — имя начинается на `en` (например, `enp1s0`). В виртуальной машине интерфейс может называться `ens3` или `eth0` — зависит от гипервизора, подробнее в [статье про Arch в VirtualBox/QEMU](https://ordanax.github.io/arch-v-vm-virtualbox-qemu).

## Как настроить статический IP через systemd-networkd

`systemd-networkd` входит в пакет `systemd`, который уже стоит в системе. Отдельно ничего ставить не нужно.

### Создаём конфигурационный файл

Открой файл `/etc/systemd/network/20-wired.network`:

```bash
sudo mkdir -p /etc/systemd/network
sudo nano /etc/systemd/network/20-wired.network
```

Вставь содержимое:

```ini
[Match]
Name=enp1s0

[Link]
RequiredForOnline=routable

[Network]
Address=192.168.1.50/24
Gateway=192.168.1.1
DNS=192.168.1.1
DNS=8.8.8.8
```

Разберём построчно:

- **`[Match] Name=enp1s0`** — привязка к конкретному интерфейсу. Подставь своё имя.
- **`[Link] RequiredForOnline=routable`** — systemd считает сеть готовой, только когда интерфейс получит routable-адрес.
- **`Address=192.168.1.50/24`** — статический IP. `/24` — маска `255.255.255.0`.
- **`Gateway=192.168.1.1`** — адрес роутера (шлюза).
- **`DNS=192.168.1.1`** — DNS-сервер (обычно тот же роутер). Вторая строка — запасной публичный DNS.

### Временная настройка без файла

Поставить IP «прямо сейчас», для отладки:

```bash
sudo ip addr add 192.168.1.50/24 dev enp1s0
sudo ip route add default via 192.168.1.1
```

Команды действуют до перезагрузки — удобно проверить адрес и шлюз.

### Включаем и запускаем systemd-networkd

```bash
sudo systemctl enable systemd-networkd
sudo systemctl restart systemd-networkd
```

`enable` — сервис стартует при загрузке. `restart` — применить изменения сейчас (или `networkctl reload`, если интерфейс не требует полного перезапуска).

Проверяем результат:

```bash
networkctl status enp1s0
ping -c 3 8.8.8.8
ping -c 3 archlinux.org
```

Первая команда — статус интерфейса (должен быть `routable`), вторая — IP-связность, третья — разрешение DNS.

### Не забудь про systemd-resolved

Для работы DNS-записей из `.network`-файла нужен `systemd-resolved`:

```bash
sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved
```

Проверить резолвер: `resolvectl status`. Если DNS не резолвится — resolved не запущен.

## Как настроить DHCP обратно

Если статический IP не подошёл, замени содержимое файла на:

```ini
[Match]
Name=enp1s0

[Network]
DHCP=yes
```

Перезапусти сервис:

```bash
sudo systemctl restart systemd-networkd
```

## Что делать после изменения конфигурации сети

После правки `.network`-файла перезапусти `systemd-networkd` и проверь: статус (`networkctl status enp1s0`, `ip -br addr`, `ip route`), связность (`ping -c 3 8.8.8.8`) и DNS (`ping -c 3 archlinux.org`). Если пинги по IP работают, а по имени нет — проблема в DNS: проверь, запущен ли `systemd-resolved`, и содержимое `/etc/resolv.conf` (обычно симлинк на resolved).

Логи смотри в отдельном терминале:

```bash
journalctl -u systemd-networkd -f
```

Они покажут, если интерфейс не найден или адрес уже занят. Как читать логи — в [статье про journalctl при первой загрузке](https://ordanax.github.io/chitat-journalctl-b-pervaya-zagruzka).

## Можно ли использовать NetworkManager вместо systemd-networkd

На десктопах с графическим окружением часто стоит NetworkManager. Статический IP через `nmcli`:

```bash
nmcli con mod "Wired connection 1" ipv4.addresses 192.168.1.50/24
nmcli con mod "Wired connection 1" ipv4.gateway 192.168.1.1
nmcli con mod "Wired connection 1" ipv4.dns "192.168.1.1,8.8.8.8"
nmcli con mod "Wired connection 1" ipv4.method manual
nmcli con up "Wired connection 1"
```

Не смешивай `systemd-networkd` и `NetworkManager` на одном интерфейсе — конфликт. Если NetworkManager уже стоит, работай с ним. Для минимальной системы без GUI systemd-networkd — лёгкое и надёжное решение. О настройке после установки — в [«Первом часе после установки Arch»](https://ordanax.github.io/pervyi-chas-posle-ustanovki-arch).

## Частые вопросы

### Почему интерфейс называется enp1s0, а не eth0?

Современные ядра Linux используют Predictable Network Interface Names: `en` — Ethernet, `p1` — PCI-слот 1, `s0` — порт 0. Имена стабильны — даже после добавления нового адаптера старый интерфейс сохранит своё имя.

### Как узнать маску подсети?

Маска — часть после косой черты: `Address=192.168.1.50/24` означает `255.255.255.0`. Для домашних сетей `/24` подходит почти всегда.

### Можно ли добавить несколько IP на один интерфейс?

Да. В секции `[Network]` укажи несколько строк `Address=`:

```ini
[Network]
Address=192.168.1.50/24
Address=10.0.0.5/24
Gateway=192.168.1.1
```

Шлюз по умолчанию обычно один. Для маршрутов к конкретным подсетям — секция `[Route]`.

### Стоит ли использовать статический IP на Wi-Fi?

Обычно нет: роутер стабильно выдаёт один и тот же адрес по DHCP. Статический IP на Wi-Fi нужен, только если ты вещаешь сервисы (медиасервер, принтсервер). Настройка аналогична проводной — только имя интерфейса будет `wlp2s0`. Wi-Fi вручную настраивается через wpa_supplicant — [отдельная статья](https://ordanax.github.io/wifi-nastroyka-wpa-supplicant).

## Полезные ресурсы

- [systemd-networkd — ArchWiki](https://wiki.archlinux.org/title/Systemd-networkd) — полная документация по конфигурационным файлам и сервисам.
- [Network configuration — ArchWiki](https://wiki.archlinux.org/title/Network_configuration) — обзор всех способов настройки сети в Arch Linux.
- [fstab: поля на практике](https://ordanax.github.io/fstab-polya-na-praktike) — ещё одна практичная статья о ручной настройке системы.

## Заключение

Определение имени интерфейса и настройка статического IP в Arch Linux — задача на пять минут. Запустил `ip link`, нашёл интерфейс, создал конфиг в `/etc/systemd/network/`, перезапустил сервис — и всё работает. Не забудь про маску подсети, шлюз и DNS, убедись, что `systemd-resolved` запущен. Если что-то пошло не так — `journalctl -u systemd-networkd` покажет, где именно.