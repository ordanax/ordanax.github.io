---
layout: post
title: "Английская раскладка при установке и русская после"
description: "Почему Arch Linux ставится на английской раскладке и как включить русскую: vconsole.conf, setxkbmap, X11, Wayland и исправление кракозябр"
date: 2026-09-18 00:00:00 +0300
permalink: /raskladka-pri-ustanovke-i-posle
categories:
- linux
- arch linux
- xorg
tags:
- keyboard
- keymap
- vconsole
- setxkbmap
- locale
- xkb
edit: true
---

При установке Arch Linux раскладка по умолчанию — английская (us). Это нормально: все команды установки печатаются на английском, а поддержка кириллицы в live-окружении не гарантирована. Русскую раскладку подключают после входа в систему — для консоли через `vconsole.conf`, для графики через `setxkbmap` или настройки DE. Всё занимает пару команд.

## Почему установка проходит на английской раскладке

Arch ISO загружается с минимальным набором утилит. Раскладка — `us`, и это осознанный выбор. Все команды установки (`pacstrap`, `arch-chroot`, `grub-install`) печатаются на английском, а шрифты для кириллицы могут быть не подгружены. Если попробовать переключиться на русскую в ISO, скорее всего получишь пустые квадратики вместо букв. Настоящая необходимость в русской раскладке появляется, когда нужно набрать текст — пароль, имя файла, комментарий.

## Как переключиться на русскую в консоли после установки

Консоль (TTY) и графическое окружение — два разных мира, раскладка настраивается отдельно для каждого.

### Переключаем на русскую для текущей сессии

```bash
sudo loadkeys ru
```

Раскладка применится до перезагрузки. У клавиатуры со 105 клавишами (стандарт ISO) попробуй `loadkeys ru105` — это вариант с правильным положением клавиш `/` и `\`.

### Делаем настройку постоянной

```bash
sudo localectl set-keymap ru
```

Эта команда пропишет `KEYMAP=ru` в `/etc/vconsole.conf`. Альтернатива — отредактировать файл вручную:

```
# /etc/vconsole.conf
KEYMAP=ru
```

После перезагрузки консоль будет загружаться с русской раскладкой. Важный момент: в консоли полноценное переключение через `Alt+Shift` не работает так же удобно, как в графическом окружении. Подробнее — в статье про [setlocale и кракозябры](https://ordanax.github.io/setlocale-karakuli).

Если хочешь тренировать слепую печать на русской раскладке, посмотри [настройку Klavaro для русской раскладки](https://ordanax.github.io/klavaro-russkaya-raskladka).

## Как настроить русскую раскладку в X11/Wayland

Графические окружения управляют раскладкой отдельно от консоли. Способ зависит от среды.

### X11 (Xorg)

Быстрый способ — команда `setxkbmap` для текущего X-сеанса:

```bash
setxkbmap -layout us,ru -option grp:alt_shift_toggle
```

`us,ru` — две раскладки, первая по умолчанию. `grp:alt_shift_toggle` — переключение через `Alt+Shift`.

Чтобы настройка пережила перезагрузку, создай конфиг:

```bash
sudo mkdir -p /etc/X11/xorg.conf.d
```

```
# /etc/X11/xorg.conf.d/00-keyboard.conf
Section "InputClass"
    Identifier "system-keyboard"
    MatchIsKeyboard "on"
    Option "XkbLayout" "us,ru"
    Option "XkbOptions" "grp:alt_shift_toggle"
EndSection
```

Этот конфиг работает для Xorg напрямую — i3, Openbox,bspwm, LightDM. Настройка терминала Ghostty — в отдельной статье — [конфигурация Ghostty](https://ordanax.github.io/ghostty-terminal-konfiguraciya).

### GNOME

GNOME проигнорирует `xorg.conf.d`. Настраивай через `gsettings`:

```bash
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'ru')]"
gsettings set org.gnome.desktop.input-sources xkb-options "['grp:alt_shift_toggle']"
```

Или через интерфейс: «Настройки» → «Клавиатура» → «Источники ввода» → «+» → «Русский».

### KDE Plasma

System Settings → Input Devices → Keyboard → Layouts. Добавь русскую раскладку и выбери комбинацию переключения. KDE, как и GNOME, не зависит от `xorg.conf.d`.

### Wayland (Hyprland, Sway)

В standalone WM на Wayland раскладка настраивается через конфиг. Например, в Hyprland:

```
input {
    kb_layout = us,ru
    kb_options = grp:alt_shift_toggle
}
```

## Почему видны кракозябры вместо русских букв

Если вместо русских букв — квадратики или пустые знаки, проблема в одном из двух: локаль не поддерживает UTF-8 или не установлены шрифты для кириллицы.

### Проверяем локаль

```bash
locale
```

Ищи строку `LANG=ru_RU.UTF-8`. Если там `C` или `POSIX`:

```bash
sudo sed -i 's/^#ru_RU.UTF-8/ru_RU.UTF-8/' /etc/locale.gen
sudo locale-gen
echo "LANG=ru_RU.UTF-8" | sudo tee /etc/locale.conf
```

Подробности — в статье про [setlocale и кракозябры](https://ordanax.github.io/setlocale-karakuli).

### Устанавливаем шрифты

Без подходящих шрифтов кириллица не появится даже с правильной локалью:

```bash
sudo pacman -S terminus-font ttf-dejavu ttf-liberation
```

`terminus-font` — моноширинный шрифт для консоли, `ttf-dejavu` и `ttf-liberation` — для графических приложений.

## Частые вопросы

**Почему раскладка сбрасывается после перезагрузки?**
Ты переключил через `loadkeys`, но не сохранил. Для консоли — `sudo localectl set-keymap ru`, для X11 — пропиши `setxkbmap` в автозапуск или создай `/etc/X11/xorg.conf.d/00-keyboard.conf`.

**`loadkeys ru` не работает.**
Проверь, что пакет `kbd` установлен: `sudo pacman -S kbd`. На минималистичной системе его может не быть.

**Alt+Shift не переключает раскладку в терминале.**
Это нормально. В консоли полноценное переключение через `Alt+Shift` не поддерживается — работает только в графическом окружении.

**Кракозябры только в одной программе.**
Проверь шрифты в настройках этой программы. Часто помогает установка `ttf-fira-code` или `ttf-jetbrains-mono`.

## Заключение

Английская раскладка при установке — не баг, а особенность Arch. Русскую подключают после: `localectl set-keymap ru` для консоли, `setxkbmap` для X11, `gsettings` для GNOME, настройки DE для KDE. Кракозябры лечатся локалью `ru_RU.UTF-8` и установкой шрифтов. На всё — пять минут.

## Полезные ресурсы

- [ArchWiki: Linux console — Keyboard configuration](https://wiki.archlinux.org/title/Linux_console/Keyboard_configuration)
- [ArchWiki: Xorg — Keyboard configuration](https://wiki.archlinux.org/title/Xorg/Keyboard_configuration)
- [Первый час после установки Arch](https://ordanax.github.io/pervyi-chas-posle-ustanovki-arch) — локали, часы и базовые пакеты после установки
