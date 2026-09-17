---
layout: post
title: "Миграция с другого дистрибутива на Arch: чек-лист"
description: "Как перенести систему с Ubuntu, Fedora или другого дистрибутива на Arch Linux: что переустановить, что перенести и чего ожидать."
date: 2026-09-18 00:00:00 +0300
permalink: /migraciya-s-drugoi-arch
categories:
- linux
- arch linux
tags:
- migration
- dotfiles
- pacman
- arch linux
- ubuntu
edit: true
---

Миграция с другого дистрибутива на Arch — это не конвертация системы, а переустановка приложений с переносом личных настроек. Автоматического способа перевести Ubuntu или Fedora в Arch не существует: берёшь список пакетов, переносишь dotfiles и ставишь всё заново. Зато получаешь систему, которую полностью контролируешь.

## Что перенести, а что переустановить

**Переношу как есть:** личные конфигурации (dotfiles) — `.vimrc`, `.zshrc`, `.gitconfig`, `.ssh/`, `.gnupg/`, скрипты, документы.

**Переустанавливаю заново:** все пакеты — pacman не понимает дистрибутивные базы apt/dnf. DE/WM целиком. Загрузчик — GRUB или systemd-boot ставится с нуля.

**Не переношу вообще:** `/etc/shadow` — пароли создаются заново. Системные сервисы и их конфигурация. Загрузчик.

## Как вытащить список установленных пакетов

Список нужен как шпаргалка, а не для автоматического импорта:

```bash
# Debian/Ubuntu
dpkg --get-selections | awk '{print $1}' > ~/packages-debian.txt

# Fedora
rpm -qa --qf '%{NAME}\n' > ~/packages-fedora.txt

# openSUSE
zypper se -i | awk -F'|' 'NR>2 {gsub(/^[ \t]+|[ \t]+$/, "", $3); print $3}' > ~/opensuse.txt
```

Пакеты с generic-именами (`vim`, `git`, `curl`) перенесутся без проблем. А вот `python3-pip` из apt превратится в `python-pip` из pacman — имена отличаются. Далеко не всё из Ubuntu/Fedora имеет аналог в Arch или в AUR.

## Куда деть dotfiles

Dotfiles — это личные настройки в домашней директории. Большинство переносятся без изменений:

```bash
scp -r user@old-pc:~/.vimrc ~/
scp -r user@old-pc:~/.zshrc ~/
scp -r user@old-pc:~/.ssh ~/
scp -r user@old-pc:~/.gnupg ~/
scp -r user@old-pc:~/.config ~/
```

Терминальные утилиты переносятся спокойно. Конфиги DE (GNOME, KDE, XFCE) лучше не копировать — слишком много скрытых зависимостей. Правило простое: настройки CLI копируй, GUI настраивай заново.

## Что принципиально иначе устроено в Arch

**Нет sudo по умолчанию.** После установки работает только root. Пользователь создаётся вручную, `sudo` ставится отдельно. Подробнее — [«Создание пользователя: useradd vs adduser»](https://ordanax.github.io/sozdanie-polzovatelya-useradd).

**Pacman вместо apt/dnf.** Команды другие, логика другая:

| Действие | apt | dnf | pacman |
|---|---|---|---|
| Установить | `apt install pkg` | `dnf install pkg` | `pacman -S pkg` |
| Обновить | `apt update && apt upgrade` | `dnf upgrade` | `pacman -Syu` |
| Удалить | `apt remove pkg` | `dnf remove pkg` | `pacman -R pkg` |

**Категорически нельзя делать `pacman -Sy`** — это partial update, который ломает зависимости. Обновил индекс — делай `pacman -Syu`. Хочешь один пакет — `pacman -S` без `-y`.

**AUR — второй источник пакетов.** Многих приложений нет в официальных репозиториях. Поставь yay:

```bash
sudo pacman -S --needed git base-devel
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si
```

Подробно — в [«Установке AUR-пакетов»](https://ordanax.github.io/aur-install).

**Зеркала.** В Arch ты сам выбираешь, откуда качать. Файл `/etc/pacman.d/mirrorlist` определяет скорость обновлений. Настройка — в [«Настройке зеркал Arch Linux»](https://ordanax.github.io/arch-linux-mirrorlist-nastroyka).

**Rolling release.** Arch обновляется постоянно. Полное обновление — `sudo pacman -Syu`. Про [частичное обновление](https://ordanax.github.io/pacman-chastichnoe-obnovlenie) и его последствия стоит знать.

## Что проверить после переезда: чек-лист

1. **Создать пользователя и настроить sudo** — root-only система опасна. Статья [«Создание пользователя»](https://ordanax.github.io/sozdanie-polzovatelya-useradd).

2. **Настроить сеть** — Wi-Fi через `iwctl`, проводное подключение обычно работает сразу.

3. **Настроить зеркала** — быстрое зеркало = быстрые обновления. Инструкция в [«Настройке зеркал»](https://ordanax.github.io/arch-linux-mirrorlist-nastroyka).

4. **Установить DE и базовые пакеты:**

```bash
sudo pacman -S sudo vim git curl wget base-devel

# Для GNOME
sudo pacman -S gnome gnome-extra

# Для XFCE
sudo pacman -S xfce4 xfce4-goodies
```

5. **Поставить AUR-хелпер** — без этого половина пакетов недоступна.

6. **Перенести dotfiles** — терминальные конфиги копируй, DE настраивай заново.

7. **Чистка орфанов:**

```bash
pacman -Qdtq | sudo pacman -Rns -
```

## Частые вопросы

**Можно ли перенести систему через rsync или dd?**
Нет. Разные дистрибутивы — разные пакетные базы, структуры и конфигурации. Результат будет нерабочий.

**Как найти аналог пакета из Ubuntu?**
На [archlinux.org/packages](https://archlinux.org/packages/). Имена отличаются: `libfoo-dev` → `libfoo`, `python3-foo` → `python-foo`. В [AUR](https://aur.archlinux.org/) найдётся ещё больше.

**Сколько времени займёт переезд?**
При быстром интернете и готовом списке пакетов — 1–2 часа. Основное время — скачивание и настройка среды.

## Заключение

Миграция на Arch — переустановка приложений с переносом личных настроек. Автоматической конверсии не существует, зато ты получаешь полный контроль над системой. Главное: не конвертируй пакетные базы, переноси dotfiles точечно и настраивай sudo сразу.

## Полезные ресурсы

- [ArchWiki: Mirrors](https://wiki.archlinux.org/title/Mirrors) — документация по зеркалам
- [ArchWiki: AUR helpers](https://wiki.archlinux.org/title/AUR_helpers) — сравнение AUR-хелперов
- [Всё про yay: ошибка EOF/IPv6](https://ordanax.github.io/yay-eof-ipv6-gai-conf) — если AUR-хелпер падает при первом запуске
- [Что делать после установки Arch](https://ordanax.github.io/pervyi-chas-posle-ustanovki-arch) — чек-лист первого часа на новой системе
