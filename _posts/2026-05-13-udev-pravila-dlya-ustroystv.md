---
layout: post
title: Udev правила для устройств в Linux — полное руководство
description: Практический гайд по созданию udev правил для фиксации имён устройств, микрофонов и другого оборудования
date: 2026-05-13 05:00:00 +0300
categories:
- linux
- system
- hardware
- configuration
tags:
- udev
- devices
- rules
- linux
- hardware
---

![Udev Rules](../img/udev-rules.png){:style="float: left;margin-right: 25px;margin-top: 10px;"} Udev — система управления устройствами в Linux, которая позволяет создавать правила для автоматического определения и настройки устройств. Это критически важно для фиксации имён сетевых интерфейсов, микрофонов и других периферийных устройств.

## Что такое udev?

Udev — это менеджер устройств для ядра Linux, который:
- Автоматически создаёт/удаляет файлы устройств в `/dev`
- Управляет именами устройств
- Выполняет скрипты при подключении/отключении устройств
- Применяет правила для настройки устройств

## Структура udev правил

Файлы правил находятся в `/etc/udev/rules.d/`:
```
/etc/udev/rules.d/
├── 10-network.rules
├── 70-persistent-net.rules
└── 99-custom.rules
```

Формат правила:
```
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="00:11:22:33:44:55", NAME="eth0"
```

## Фиксация имён сетевых интерфейсов

### Проблема: wlan0 меняет название на wlan1

Создайте правило:
```bash
sudo nano /etc/udev/rules.d/70-persistent-net.rules
```

Добавьте:
```
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="mac:адрес:интерфейса", NAME="wlan0"
```

### Определение MAC-адреса

```bash
ip link show wlan0
# или
ip addr show wlan0
```

Ищите строку `link/ether 00:11:22:33:44:55`

## Настройка микрофона через udev

### Проблема: Микрофон меняется или не определяется

Создайте правило:
```bash
sudo nano /etc/udev/rules.d/99-microphone.rules
```

Добавьте:
```
SUBSYSTEM=="sound", ATTR{id}=="USB Device 1234:5678", ATTR{index}=="0", SYMLINK+="microphone"
```

### Определение атрибутов устройства

```bash
# Найти все звуковые устройства
ls -la /dev/snd/

# Подробная информация о устройстве
udevadm info -a -p /sys/class/sound/card0
```

## Создание symlink для удобства

### Пример: Создание symlink для микрофона

```bash
sudo nano /etc/udev/rules.d/99-mic-symlink.rules
```

```
KERNEL=="card*", SUBSYSTEM=="sound", ATTR{id}=="USB Device 1234:5678", SYMLINK+="mic"
```

Теперь можно обращаться к `/dev/mic` вместо сложного пути.

## Автоматический запуск скриптов при подключении устройств

### Пример: Автоматическое монтирование USB

```bash
sudo nano /etc/udev/rules.d/99-usb-mount.rules
```

```
ACTION=="add", SUBSYSTEM=="block", ENV{ID_FS_UUID}=="1234-5678", RUN+="/usr/local/bin/mount-usb.sh"
```

Создайте скрипт:
```bash
sudo nano /usr/local/bin/mount-usb.sh
```

```bash
#!/bin/bash
mount /dev/disk/by-uuid/1234-5678 /mnt/usb
```

Сделайте исполняемым:
```bash
sudo chmod +x /usr/local/bin/mount-usb.sh
```

## Полезные команды для работы с udev

### Тестирование правил без перезагрузки

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Проверка информации об устройстве

```bash
# Информация о конкретном устройстве
udevadm info -a -p /sys/class/net/wlan0

# Мониторинг событий udev
udevadm monitor

# Мониторинг только событий устройств
udevadm monitor --environment --udev
```

### Поиск атрибутов устройства

```bash
# Все атрибуты устройства
udevadm info -a -p $(udevadm info -q path -n /dev/sda)

# Только специфические атрибуты
udevadm info -q property -n /dev/sda
```

## Решение проблем

### Проблема: Правило не применяется

1. Проверьте синтаксис:
```bash
sudo udevadm test /sys/class/net/wlan0
```

2. Перезагрузите правила:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

3. Проверьте логи:
```bash
sudo journalctl -xe | grep udev
```

### Проблема: Конфликт правил

Проверьте порядок загрузки правил:
```bash
ls -la /etc/udev/rules.d/
```

Файлы обрабатываются в алфавитном порядке. Используйте числа в начале имён для контроля порядка.

### Проблема: Устройство не определяется

Проверьте, что устройство видно в системе:
```bash
lsusb
lsblk
```

Проверьте, что ядро поддерживает устройство:
```bash
dmesg | grep -i usb
```

## Примеры полезных правил

### Фиксация имени USB диска

```
SUBSYSTEM=="block", ENV{ID_SERIAL}=="USB_DISK_SERIAL", SYMLINK+="backup_drive"
```

### Автоматическое изменение прав доступа

```
KERNEL=="ttyUSB*", MODE="0666"
```

### Отключение конкретного устройства

```
SUBSYSTEM=="usb", ATTR{idVendor}=="1234", ATTR{idProduct}=="5678", OPTIONS+="ignore_device"
```

## Рекомендации

1. **Делайте бэкап** правил перед изменениями
2. **Тестируйте правила** перед применением
3. **Используйте уникальные идентификаторы** (MAC-адреса, серийные номера)
4. **Проверяйте логи** при проблемах
5. **Используйте systemd** для сложных скриптов вместо udev

## Полезные ресурсы

- [ArchWiki: Udev](https://wiki.archlinux.org/title/Udev)
- [Writing udev rules](https://reboot.pro/topic/19286-writing-udev-rules/)
- [Udev documentation](https://www.freedesktop.org/software/systemd/man/udev.html)

---

**Автор:** [ordanax.github.io](https://ordanax.github.io/)  
**Telegram:** [@linux4at](https://t.me/linux4at)  
**MAX:** [Присоединиться](https://max.ru/join/b4GtiNvbjYqeboq-nddswKQJ-cvWiJGoaZdIoV1EUMk)
