---
layout: post
title: Hyprland на Arch Linux — полный гайд по установке и настройке
description: Hyprland — современный динамический тайлинговый WM на Wayland. Полный гайд по установке на Arch Linux с нуля
---

![Hyprland](../img/hyprland.png){:style="float: left;margin-right: 25px;margin-top: 10px;"} Hyprland — один из самых популярных динамических тайлинговых оконных менеджеров на Wayland в 2026 году. Он сочетает в себе производительность i3wm, красоту Wayland и гибкость, которую ценят пользователи Arch Linux.

## Почему Hyprland?

- **Wayland из коробки** — нет проблем с масштабированием, плавная анимация
- **Динамический тайлинг** — окна автоматически располагаются, но можно менять layout
- **Высокая производительность** — написан на C++, использует wlroots
- **Активное развитие** — регулярные обновления и новые функции
- **Гибкая настройка** — конфигурация через YAML, поддержка плагинов

## Установка Hyprland на Arch Linux

### 1. Подготовка системы

Убедитесь, что система обновлена:
```bash
sudo pacman -Syu
```

### 2. Установка Hyprland

Hyprland доступен в официальных репозиториях Arch Linux:
```bash
sudo pacman -S hyprland
```

### 3. Установка зависимостей

Для полноценной работы понадобятся дополнительные пакеты:
```bash
sudo pacman -S waybar xdg-desktop-portal-hyprland polkit-kde-agent
```

### 4. Установка шрифтов и тем

```bash
sudo pacman -S noto-fonts noto-fonts-cjk ttf-font-awesome
```

## Настройка Hyprland

### Конфигурационный файл

Конфигурация Hyprland находится в `~/.config/hypr/hyprland.conf`. Создайте его:
```bash
mkdir -p ~/.config/hypr
nano ~/.config/hypr/hyprland.conf
```

### Базовая конфигурация

```conf
# Монитор
monitor=eDP-1,1920x1080@60,0x0,1

# Ввод
input {
    kb_layout = us,ru
    kb_variant = ,
    kb_model = ,
    kb_options = grp:win_switch
    kb_rules = 
    follow_mouse = 1
    touchpad {
        natural_scroll = no
    }
}

# Общие настройки
general {
    gaps_in = 5
    gaps_out = 20
    border_size = 2
    col.active_border = rgba(33ccffee) rgb(003344)
    col.inactive_border = rgba(595959aa)
    layout = dwindle
}

# Декорации
decoration {
    rounding = 10
    blur {
        enabled = yes
        size = 3
        passes = 2
    }
    drop_shadow = yes
    shadow_range = 4
    shadow_render_power = 3
}

# Анимации
animations {
    enabled = yes
    bezier = myBezier,0.05,0.9,0.1,1.05
    animation = windows,1,7,myBezier
    animation = windowsOut,1,7,default,popin 80%
    animation = border,1,10,default
    animation = borderangle,1,8,default
    animation = fade,1,7,default
    animation = workspaces,1,6,default
}
```

## Установка Waybar

Waybar — популярная панель для Hyprland:

```bash
sudo pacman -S waybar
```

Конфигурация Waybar:
```bash
mkdir -p ~/.config/waybar
nano ~/.config/waybar/config
```

Пример конфигурации:
```json
{
    "layer": "top",
    "position": "top",
    "height": 30,
    "modules-left": ["hyprland/workspaces", "hyprland/window"],
    "modules-center": ["clock"],
    "modules-right": ["cpu", "memory", "tray"],
    "hyprland/workspaces": {
        "format": "{name}"
    },
    "clock": {
        "format": "{:%H:%M}"
    },
    "cpu": {
        "format": "CPU {}%"
    },
    "memory": {
        "format": "RAM {}%"
    }
}
```

## Горячие клавиши

Добавьте в `hyprland.conf`:

```conf
# Горячие клавиши
$mainMod = SUPER

# Запуск терминала
bind = $mainMod, Return, exec, kitty

# Запуск меню
bind = $mainMod, D, exec, rofi -show drun

# Закрытие окна
bind = $mainMod, Q, killactive

# Переключение layout
bind = $mainMod, SPACE, togglesplit

# Перемещение фокуса
bind = $mainMod, left, movefocus, l
bind = $mainMod, right, movefocus, r
bind = $mainMod, up, movefocus, u
bind = $mainMod, down, movefocus, d

# Перемещение окон
bind = $mainMod SHIFT, left, movewindow, l
bind = $mainMod SHIFT, right, movewindow, r
bind = $mainMod SHIFT, up, movewindow, u
bind = $mainMod SHIFT, down, movewindow, d

# Workspace
bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod, 4, workspace, 4

# Перемещение окон между workspace
bind = $mainMod SHIFT, 1, movetoworkspace, 1
bind = $mainMod SHIFT, 2, movetoworkspace, 2
bind = $mainMod SHIFT, 3, movetoworkspace, 3
bind = $mainMod SHIFT, 4, movetoworkspace, 4
```

## Автозапуск приложений

```conf
# Автозапуск
exec-once = waybar &
exec-once = dunst &
exec-once = /usr/lib/polkit-kde-authentication-agent-1 &
```

## Решение типичных проблем

### Проблема: Нет звука

Установите PipeWire:
```bash
sudo pacman -S pipewire pipewire-pulse wireplumber
```

### Проблема: Не работают уведомления

Установите dunst:
```bash
sudo pacman -S dunst libnotify
```

### Проблема: Не работает копирование между X11 и Wayland

Установите wl-clipboard:
```bash
sudo pacman -S wl-clipboard
```

## Рекомендации

1. **Сделайте бэкап** перед установкой Hyprland
2. **Используйте Timeshift** для резервного копирования системы
3. **Начните с базовой конфигурации** и постепенно добавляйте функции
4. **Изучите документацию** на [Hyprland Wiki](https://wiki.hypr.land/)
5. **Присоединяйтесь к сообществу** для получения помощи

## Полезные ресурсы

- [Официальная документация Hyprland](https://wiki.hypr.land/)
- [Hyprland на ArchWiki](https://wiki.archlinux.org/title/Hyprland)
- [Автоматический скрипт установки](https://github.com/JaKooLit/Arch-Hyprland)

---

**Автор:** [ordanax.github.io](https://ordanax.github.io/)  
**Telegram:** [@linux4at](https://t.me/linux4at)  
**MAX:** [Присоединиться](https://max.ru/join/b4GtiNvbjYqeboq-nddswKQJ-cvWiJGoaZdIoV1EUMk)
