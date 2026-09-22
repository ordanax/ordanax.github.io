---
layout: post
title: "Как собрать Klavaro из форка: PKGBUILD для личного AUR"
description: "Собираем кастомный Klavaro в Arch Linux через PKGBUILD и makepkg: полный гайд по личной сборке без публикации в AUR"
date: 2026-09-16 00:00:00 +0300
permalink: /klavaro-pkgbuild-aur
categories:
  - linux
  - arch linux
  - packages
tags:
  - pkgbuild
  - makepkg
  - aur
  - klavaro
  - custom-build
  - autotools
edit: true
---



Чтобы автоматически собрать форк Klavaro в устанавливаемый пакет Arch Linux, нужен PKGBUILD и команда `makepkg -si`. Скрипт сам скачает исходники, скомпилирует и упакует в `.pkg.tar.zst`, который ставится через `pacman -U`. Никакой публикации в AUR, никакого хостинга, всё локально.

## Зачем свой PKGBUILD, если есть AUR

В AUR полно готовых PKGBUILD, и для стандартного Klavaro пакет там есть. Но если вы форкнули проект и внесли правки, AUR-пакет вам не поможет. Каждое обновление апстрима не подхватит ваш код, а ваш форк не попадёт в чужой PKGBUILD без отдельной договорённости.

Личный PKGBUILD решает задачу чисто. Вы описали сборку один раз, запускаете `makepkg -si` после каждого `git pull`, и пакет обновляется. pacman видит, что пакет установлен, следит за зависимостями, позволяет откатить через `pacman -U`. По сути, это мини-AUR без сервера и голосования.

## Подготовка: что установить и где взять исходники

Нужен набор `base-devel` и утилита `git`. Если ставите Arch недавно, проверьте [чек-лист после установки](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019), там есть все базовые пакеты.

```bash
sudo pacman -S base-devel git
```

Теперь клонируем форк. Подставьте свой URL репозитория:

```bash
git clone https://github.com/ordanax/klavaro-custom.git
cd klavaro-custom
```

Создайте отдельную папку для сборки. makepkg не любит работать в корне репозитория, так он засоряет дерево файлами компиляции:

```bash
mkdir ~/pkgbuild && cd ~/pkgbuild
```

## Полный PKGBUILD

Создайте файл `PKGBUILD` без расширения:

```bash
nano PKGBUILD
```

Вставьте содержимое. Все переменные и функции здесь реальные, синтаксис проверен для Arch 2026:

```bash
# Maintainer: Вы <ваш-email>
pkgname=klavaro-custom
pkgver=3.14
pkgrel=1
pkgdesc="Адаптивный тренажёр слепой печати (кастомная сборка)"
arch=('x86_64')
url="https://github.com/ordanax/klavaro-custom"
license=('GPL-3.0-or-later')
depends=('gtk3' 'gtkdatabox' 'curl')
makedepends=('autoconf' 'automake' 'libtool' 'intltool')
source=("${url}/archive/refs/heads/main.tar.gz")
sha256sums=('SKIP')

build() {
  cd "${srcdir}/klavaro-custom-main"
  autoreconf -fi
  ./configure --prefix=/usr
  make
}

package() {
  cd "${srcdir}/klavaro-custom-main"
  make DESTDIR="${pkgdir}" install
}
```

Разберём по пунктам. `pkgname` не должен совпадать с именем пакета из официального репозитория, иначе pacman запутается. `source` ссылается на архив с GitHub, `sha256sums=('SKIP')` отключает проверку хеша для личного пакета. Функции `build()` и `package()` обязательно строчные, это требование makepkg.

## Сборка: makepkg -si пошагово

Вернитесь в папку с `PKGBUILD` и запустите:

```bash
cd ~/pkgbuild
makepkg -si
```

Флаг `-s` подтянет зависимости через pacman перед сборкой. Флаг `-i` установит пакет сразу после создания. Скрипт выведет лог компиляции, и если ошибок нет, вы увидите финальное сообщение об установке.

### Типичные ошибки и как их чинить

**`autoreconf: command not found`** — не установлены инструменты сборки. Проверьте, что `autoconf`, `automake`, `libtool` и `intltool` стоят. `pacman -S autoconf automake libtool intltool` решает.

**`configure: error: Package requirements (gtk+-3.0) were not met`** — нет GTK3 или gtkdatabox. `sudo pacman -S gtk3 gtkdatabox`.

**`makepkg` ругается на конфликтующие файлы** — добавьте `--cleanbuild` для полной пересборки:

```bash
makepkg -sirc
```

Флаг `-c` удалит предыдущую сборку перед началом новой.

## Установка и обновление

После успешной сборки пакет появится в текущей папке с именем вида `klavaro-custom-3.14-1-x86_64.pkg.tar.zst`. Установка через pacman:

```bash
sudo pacman -U klavaro-custom-3.14-1-x86_64.pkg.tar.zst
```

При обновлении форка порядок действий прост. Заходите в клон репозитория, тяните свежий код, обновляете `pkgver` в PKGBUILD и пересобираете:

```bash
cd ~/klavaro-custom
git pull
cd ~/pkgbuild

# Обновляем версию в PKGBUILD (если она изменилась в upstream)
nano PKGBUILD

makepkg -sirc
sudo pacman -U klavaro-custom-*.pkg.tar.zst
```

Версию можно подставить автоматически из `configure.ac` или git-тега, но для личного пакета ручное обновление проще и надёжнее.

## Альтернативный вариант: source=file://

Если репозиторий не на GitHub, а локально на диске, замените строку `source` в PKGBUILD:

```bash
source=("klavaro-custom::file:///mnt/hdd/YandexDisk/AI/Klavaro/klavaro-custom")
```

Двойное двоеточие задаёт имя папки, в которую makepkg распакует источник. Эта схема удобна, когда код живёт рядом с PKGBUILD и нет смысла тянуть его через сеть.

Для git-варианта (склонировать прямо во время сборки):

```bash
source=("git+https://github.com/ordanax/klavaro-custom.git#branch=main")
```

Тогда уберите `sha256sums` или оставьте `SKIP`. makepkg сам склонирует репозиторий в `$srcdir`.

## Частые вопросы

**Можно ли установить такой пакет на другую машину?** Да. Скопируйте готовый `.pkg.tar.zst` и поставьте через `pacman -U`. Пакет сам подхватит зависимости.

**Чем `makepkg -si` отличается от `yay -S`?** AUR-хелперы делают то же самое, но автоматически. Для личного PKGBUILD makepkg проще и не требует настройки хелпера.

**Пакет конфликтует с `klavaro` из официального репозитория. Что делать?** Если у вас стоит `klavaro` из pacman, удалите его: `sudo pacman -R klavaro`. После этого `klavaro-custom` встанет без конфликтов.

**Как проверить, что пакет установился правильно?** Запустите `klavaro` из терминала или через меню приложений. Проверьте версию: `pacman -Qi klavaro-custom`.

## Заключение

PKGBUILD для личного форка Klavaro — это пять минут на написание и десять секунд на сборку. Вы получаете полноценный pacman-пакет, который ставится, обновляется и удаляется штатными средствами. Если вы уже собирали [Klavaro из исходников](https://ordanax.github.io/klavaro-fork-error-practice), то PKGBUILD лишь обернёт тот же процесс в стандартный формат Arch Linux.

## Полезные ресурсы

- [PKGBUILD — ArchWiki](https://wiki.archlinux.org/title/PKGBUILD) — полная структура файла, все переменные и функции.
- [Makepkg — ArchWiki](https://wiki.archlinux.org/title/Makepkg) — флаги, опции сборки, подсказки.
- [GitHub — как работать с репозиториями](https://ordanax.github.io/github) — клонирование, форки, pull-реквесты.
