---
layout: post
title: Ghostty терминал — установка и конфигурация
description: Практический гайд по установке и настройке Ghostty — современного терминала для Linux с поддержкой GPU
date: 2026-05-12 09:00:00 +0300
permalink: /ghostty-terminal-konfiguraciya
categories:
- linux
- terminal
- configuration
tags:
- ghostty
- terminal
- linux
- configuration
- gpu
edit: true
---

![Ghostty Terminal](/img/ghostty.png){:style="float: left;margin-right: 25px;margin-top: 10px;"} Ghostty — современный терминал с поддержкой GPU ускорения, написанный на Zig. Отличается высокой производительностью и гибкой конфигурацией.

## Установка Ghostty

### Arch Linux

```bash
sudo pacman -S ghostty
```

### Ubuntu/Debian

```bash
sudo apt install ghostty
```

### Fedora

```bash
sudo dnf install ghostty
```

### Из исходников

```bash
git clone https://github.com/mitchellh/ghostty
cd ghostty
zig build
sudo cp ghostty /usr/local/bin/
```

## Конфигурация Ghostty

### Расположение конфигурационного файла

Конфигурация Ghostty находится в:
```
~/.config/ghostty/config
```

### Создание конфигурации

```bash
mkdir -p ~/.config/ghostty
nano ~/.config/ghostty/config
```

## Базовая конфигурация

```conf
# Шрифт
font-family = JetBrains Mono
font-size = 12

# Тема
theme = dark

# Прозрачность
background-opacity = 0.9

# Курсор
cursor-style = block
cursor-color = #ff0000

# Скроллбар
scrollbar-width = thin

# Горячие клавиши
keybind = ctrl+shift+c copy_to_clipboard
keybind = ctrl+shift+v paste_from_clipboard
keybind = ctrl+shift+n new_window
keybind = ctrl+shift+t new_tab
```

## Настройка шрифтов

### Изменение шрифта

```conf
font-family = "JetBrains Mono"
font-size = 12
```

### Поддержка Nerd Font

```bash
sudo pacman -S ttf-jetbrains-mono-nerd
```

```conf
font-family = "JetBrainsMono Nerd Font"
font-size = 12
```

## Настройка темы

### Тёмная тема

```conf
theme = dark
```

### Светлая тема

```conf
theme = light
```

### Кастомная тема

```conf
background = #1e1e1e
foreground = #d4d4d4
cursor-color = #ffffff
selection-background = #264f78
selection-foreground = #ffffff
```

## Горячие клавиши

### Копирование и вставка

```conf
keybind = ctrl+shift+c copy_to_clipboard
keybind = ctrl+shift+v paste_from_clipboard
```

### Управление вкладками

```conf
keybind = ctrl+shift+t new_tab
keybind = ctrl+shift+w close_tab
keybind = ctrl+shift+1 switch_to_tab 1
keybind = ctrl+shift+2 switch_to_tab 2
keybind = ctrl+shift+3 switch_to_tab 3
```

### Управление окнами

```conf
keybind = ctrl+shift+n new_window
keybind = ctrl+shift+q close_window
```

## Настройка профилей

### Создание профиля для SSH

```conf
[profile-ssh]
command = ssh user@server
working-directory = ~/
```

Запуск профиля:
```bash
ghostty --profile=ssh
```

### Профиль для конкретного каталога

```conf
[profile-projects]
working-directory = ~/projects
```

## Интеграция с shell

### Zsh интеграция

Добавьте в `~/.zshrc`:
```bash
export GHOSTTY_RESOURCES_DIR=/usr/share/ghostty
```

### Bash интеграция

Добавьте в `~/.bashrc`:
```bash
export GHOSTTY_RESOURCES_DIR=/usr/share/ghostty
```

## Решение проблем

### Проблема: Конфигурация не применяется

1. Закройте все окна Ghostty
2. Проверьте путь к конфигурационному файлу
3. Перезапустите Ghostty

### Проблема: Шрифт не отображается

1. Установите шрифт в системе
2. Проверьте название шрифта в конфиге
3. Попробуйте другой шрифт

### Проблема: Прозрачность не работает

Проверьте поддержку композитора в вашей системе:
```bash
echo $XDG_SESSION_TYPE
```

Должно быть `wayland` или `x11`.

## Полезные команды

```bash
# Запуск Ghostty с конкретным профилем
ghostty --profile=myprofile

# Запуск с конкретной командой
ghostty --command="htop"

# Запуск в конкретном каталоге
ghostty --directory=~/projects

# Проверка версии
ghostty --version
```

## Рекомендации

1. **Используйте Nerd Font** для иконок в терминале
2. **Настройте горячие клавиши** для быстрой работы
3. **Создайте профили** для разных задач
4. **Используйте GPU ускорение** для лучшей производительности
5. **Делайте бэкап конфигурации** перед изменениями

## Полезные ресурсы

- [Ghostty GitHub](https://github.com/mitchellh/ghostty)
- [Ghostty Documentation](https://ghostty.org/docs)
- [Nerd Fonts](https://www.nerdfonts.com/)

---

**Автор:** [ordanax.github.io](https://ordanax.github.io/)  
**Telegram:** [@linux4at](https://t.me/linux4at)  
**MAX:** [Присоединиться](https://max.ru/join/b4GtiNvbjYqeboq-nddswKQJ-cvWiJGoaZdIoV1EUMk)
