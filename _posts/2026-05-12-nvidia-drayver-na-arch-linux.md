---
layout: post
title: NVIDIA драйверы на Arch Linux — полное руководство по установке и настройке
description: Практический гайд по установке и настройке NVIDIA драйверов на Arch Linux для Wayland и X11 на основе реального опыта решения проблем с GPU
date: 2026-05-12 03:00:00 +0300
categories:
- linux
- arch linux
- drivers
- nvidia
tags:
- nvidia
- drivers
- arch linux
- wayland
- x11
- gpu
---

![NVIDIA Drivers](/img/nvidia-drivers.png){:style="float: left;margin-right: 25px;margin-top: 10px;"} NVIDIA драйверы на Arch Linux — одна из самых частых тем для вопросов. Правильная установка критически важна для стабильной работы системы, особенно с Wayland и современными WM.

## Определение видеокарты

Сначала определите, какая у вас видеокарта:
```bash
lspci | grep -E "VGA|3D"
```

Пример вывода:
```
01:00.0 VGA compatible controller: NVIDIA Corporation GP107 [GeForce GTX 1050 Ti]
```

## Выбор драйвера

### Для старых видеокарт (Fermi)
```bash
sudo pacman -S nvidia-340xx
```

### Для видеокарт Kepler, Maxwell, Pascal (GTX 600-1000)
```bash
sudo pacman -S nvidia
```

### Для видеокарт Turing и новее (RTX 20, 30, 40)
```bash
sudo pacman -S nvidia
```

### Для ноутбуков с Optimus
```bash
sudo pacman -S nvidia bbswitch nvidia-settings
```

## Установка драйвера

### Базовая установка

```bash
sudo pacman -S nvidia nvidia-utils nvidia-settings
```

### Для 32-битных приложений (игры через Wine/Proton)
```bash
sudo pacman -S lib32-nvidia-utils
```

### Для Wayland (Hyprland, Sway, GNOME)

```bash
sudo pacman -S nvidia egl-wayland
```

## Конфигурация

### Отключение nouveau (обязательно)

Создайте файл:
```bash
sudo nano /etc/modprobe.d/nouveau_blacklist.conf
```

Добавьте:
```
blacklist nouveau
options nouveau modeset=0
```

Обновите initramfs:
```bash
sudo mkinitcpio -P
```

### Настройка GRUB

Отредактируйте GRUB конфигурацию:
```bash
sudo nano /etc/default/grub
```

Добавьте в `GRUB_CMDLINE_LINUX_DEFAULT`:
```
nvidia_drm.modeset=1
```

Обновите GRUB:
```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

### Настройка X11

Создайте файл:
```bash
sudo nano /etc/X11/xorg.conf.d/20-nvidia.conf
```

Добавьте:
```
Section "Device"
    Identifier "NVIDIA"
    Driver "nvidia"
    Option "NoLogo" "true"
    Option "DPI" "96 x 96"
EndSection
```

## Проверка работы

### Перезагрузка
```bash
sudo reboot
```

### Проверка драйвера
```bash
nvidia-smi
```

Должна появиться информация о видеокарте и драйвере.

### Проверка OpenGL
```bash
glxinfo | grep "OpenGL renderer"
```

## Настройка для Wayland

### Hyprland

Добавьте в `~/.config/hypr/hyprland.conf`:
```conf
env = LIBVA_DRIVER_NAME,nvidia
env = XDG_SESSION_TYPE,wayland
env = GBM_BACKEND,nvidia-drm
env = __GLX_VENDOR_LIBRARY_NAME,nvidia
```

### Sway

Добавьте в `~/.config/sway/config`:
```
set $gnome-schema org.gnome.desktop.interface
exec_always gsettings set $gnome-schema gtk-theme 'Adwaita'
exec_always gsettings set $gnome-schema icon-theme 'Adwaita'
```

## Решение проблем

### Проблема: Чёрный экран после установки драйвера

1. Загрузитесь в recovery mode
2. Удалите драйвер:
```bash
sudo pacman -Rns nvidia nvidia-utils
```
3. Переустановите с правильными параметрами

### Проблема: Wayland не работает с NVIDIA

Убедитесь, что установлены пакеты:
```bash
sudo pacman -S egl-wayland
```

Проверьте переменные окружения в конфигурации WM.

### Проблема: Нет ускорения в играх

Установите Vulkan:
```bash
sudo pacman -S vulkan-icd-loader lib32-vulkan-icd-loader
```

### Проблема: Экран мигает или артефакты

Отключите G-Sync:
```bash
nvidia-settings
```

В X Server Display Configuration → Disable G-SYNC.

### Проблема: Несколько мониторов не работают

Используйте nvidia-settings:
```bash
sudo nvidia-settings
```

Настройте конфигурацию X Server Display Configuration и сохраните в `/etc/X11/xorg.conf`.

## NVIDIA Optimus (ноутбуки)

### Установка Bumblebee

```bash
sudo pacman -S bumblebee bbswitch nvidia
```

Включите сервис:
```bash
sudo systemctl enable bumblebeed
sudo systemctl start bumblebeed
```

Добавьте пользователя в группу:
```bash
sudo gpasswd -a $USER bumblebee
```

### Использование NVIDIA PRIME (современный метод)

Установите драйверы:
```bash
sudo pacman -S nvidia nvidia-prime
```

Перезагрузитесь.

Переключение между GPU:
```bash
# Интегрированная графика
sudo prime-select intel

# Дискретная графика
sudo prime-select nvidia
```

## Настройка энергосбережения

### Управление питанием

Создайте файл:
```bash
sudo nano /etc/modprobe.d/nvidia.conf
```

Добавьте:
```
options nvidia NVreg_EnableGpuFirmware=0
options nvidia NVreg_UsePageAttributeTable=1
options nvidia NVreg_RegistryDwordsPerGpu=0x20000000
```

### Coolbits (разблокировка разгона)

Отредактируйте:
```bash
sudo nano /etc/X11/xorg.conf.d/20-nvidia.conf
```

Добавьте в Section "Device":
```
Option "Coolbits" "28"
```

## Обновление системы

При обновлении ядра драйверы NVIDIA могут перестать работать. Всегда перезагружайтесь после обновления:
```bash
sudo pacman -Syu
sudo reboot
```

## Полезные команды

```bash
# Информация о видеокарте
nvidia-smi

# Настройки NVIDIA
nvidia-settings

# Мониторинг температуры
nvidia-smi dmon

# Проверка OpenGL
glxinfo | grep "OpenGL renderer"

# Проверка Vulkan
vulkaninfo | grep "GPU id"
```

## Рекомендации

1. **Используйте официальные драйверы** из репозитория Arch
2. **Отключите nouveau** перед установкой NVIDIA драйверов
3. **Настройте Wayland** правильно для современных WM
4. **Используйте PRIME** для ноутбуков с Optimus
5. **Перезагружайтесь** после обновления системы
6. **Сделайте бэкап** конфигурационных файлов

## Полезные ресурсы

- [ArchWiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA)
- [ArchWiki: NVIDIA Optimus](https://wiki.archlinux.org/wiki/NVIDIA_Optimus)
- [NVIDIA Developer Forums](https://developer.nvidia.com/)

---

**Автор:** [ordanax.github.io](https://ordanax.github.io/)  
**Telegram:** [@linux4at](https://t.me/linux4at)  
**MAX:** [Присоединиться](https://max.ru/join/b4GtiNvbjYqeboq-nddswKQJ-cvWiJGoaZdIoV1EUMk)
