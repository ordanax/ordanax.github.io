---
layout: post
title: "Тема GRUB: ставим красивый фон в Arch Linux"
description: "Как поставить тему GRUB и красивый фон в Arch Linux: готовые темы, GRUB_THEME, GRUB_BACKGROUND, GRUB_GFXMODE и пересборка grub.cfg."
date: 2026-09-19 00:00:00 +0300
permalink: /tema-oformleniya-grub-fon
categories:
- linux
- arch linux
- configs
- kernel-boot
tags:
- grub
- theme
- customization
- bootloader
- background
edit: true
---


Тема GRUB ставится в три шага: кладёшь папку темы в /boot/grub/themes, прописываешь путь к theme.txt в переменной GRUB_THEME в /etc/default/grub и пересобираешь конфиг командой grub-mkconfig -o /boot/grub/grub.cfg. После перезагрузки вместо чёрного экрана с белым списком пунктов увидишь меню с картинкой. Пять минут работы — и загрузчик перестаёт пугать.

Если ты только что поставил Arch, загляни в статью про [первый час после установки](https://ordanax.github.io/pervyi-chas-posle-ustanovki-arch). Здесь разберём косметику: как сделать загрузчик красивым.

## Какие темы есть для GRUB

### Готовые наборы

Самый известный проект — vinceliuice/grub2-themes с GitHub: варианты Tela, Vimix, Stylish и WhiteSur, современные иконки и шрифты. Ставится скриптом install.sh.

В AUR лежит grub2-theme-archlinux — тема в стиле Arch с фирменным логотипом, ставится через yay. Есть и экзотика: minegrub в стиле Minecraft, arch-silence-grub-theme-git.

Не забывай про встроенную тему Starfield — она идёт в пакете grub и лежит в /usr/share/grub/themes/starfield/.

### Как устроена тема

Тема — обычная папка с файлами. Главный файл — theme.txt: цвета, шрифты, позиции элементов меню и фон. Рядом лежат картинки (обычно background.png), шрифты .pf2 и иконки. GRUB читает theme.txt и рисует меню по его описанию.

## Как установить готовую тему

### Из AUR

```
yay -S grub2-theme-archlinux
```

После установки найди папку темы — обычно /boot/grub/themes/. Дальше по общему сценарию: пропиши путь к theme.txt в /etc/default/grub и пересобери конфиг.

### Из GitHub

```
git clone https://github.com/vinceliuice/grub2-themes
cd grub2-themes
sudo ./install.sh -b -t tela
```

Флаг -b ставит тему в /boot/grub/themes, -t выбирает вариант (tela, vimix, stylish, whitesur), -s — разрешение, например -s 1080p или -s 2k.

### Вручную

Скачал тему архивом — распакуй в /boot/grub/themes/. Должна получиться структура /boot/grub/themes/`<имя>`/theme.txt. Если GRUB ещё не настроен — например, ты только что поставил систему по [пошаговой инструкции](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya), — сначала убедись, что загрузчик работает.

Открой /etc/default/grub и добавь:

```
GRUB_THEME="/boot/grub/themes/<имя>/theme.txt"
```

Пересобери конфиг:

```
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

В выводе появится Found theme: ... — значит, GRUB увидел тему. Перезагружайся и смотри.

## Как поставить свой фон

### Через GRUB_BACKGROUND

Если тема не нужна, а хочется просто картинку — используй GRUB_BACKGROUND:

```
GRUB_BACKGROUND="/boot/grub/background.png"
```

GRUB понимает PNG, JPEG и TGA. Положи картинку в /boot/grub/, пропиши путь и пересобери конфиг. В выводе grub-mkconfig ищи строку Found background image... — она подтверждает, что фон подхватился.

### Через тему

У каждой темы свой фон — background.png внутри папки темы. Хочешь свою картинку — замени этот файл, сохранив имя и разрешение. Учти: при включённой теме GRUB_BACKGROUND обычно игнорируется — тема перекрывает фон. Выбирай одно.

### Разрешение и GRUB_GFXMODE

Чтобы фон выглядел чётко, разрешение GRUB должно совпадать с разрешением картинки:

```
GRUB_GFXMODE=1920x1080
GRUB_GFXPAYLOAD_LINUX=keep
```

GRUB_GFXMODE задаёт разрешение меню, GRUB_GFXPAYLOAD_LINUX=keep передаёт его ядру — без скачка картинки при загрузке. Можно указать несколько режимов через запятую: GRUB_GFXMODE=1920x1080,1024x768,auto. Подробности — в [GRUB/Tips and tricks](https://wiki.archlinux.org/title/GRUB/Tips_and_tricks) на ArchWiki.

## Почему фон не отображается

### Неправильный путь или имя

Самая частая причина. Проверь путь в GRUB_THEME или GRUB_BACKGROUND до буквы. Имя файла не должно содержать пробелов — grub-mkconfig не экранирует его в grub.cfg. Если в выводе пересборки нет Found theme или Found background image — GRUB не нашёл файл.

### Изображение слишком тяжёлое

GRUB грузит картинку в память до старта системы, поэтому файл должен быть лёгким — до нескольких мегабайт. Формат: PNG, JPEG (8-bit, RGB, не индексированный) или TGA. Фото на 20 МБ в 4K GRUB не потянет.

### Текстовый режим вместо gfxterm

Фон рисует графический терминал gfxterm. Если в /etc/default/grub стоит GRUB_TERMINAL_OUTPUT="console" — увидишь только текст. Проверь:

```
GRUB_TERMINAL_OUTPUT="gfxterm"
```

### initrd и разрешение

Тема влияет только на меню. Чтобы после выбора пункта не было скачка разрешения, нужен GRUB_GFXPAYLOAD_LINUX=keep — тогда ядро и initrd получат то же разрешение, что и GRUB.

Если после обновления ядра пункты меню пропали — это отдельная история, чинится той же командой grub-mkconfig. Подробности в статье [GRUB не видит ядра после обновления](https://ordanax.github.io/grub-ne-vidit-yadra-posle-obnovleniya).

## Как увеличить разрешение в GRUB

Если меню размытое или фон растянут — разрешение GRUB ниже, чем у монитора. Узнай, какие режимы поддерживает видеокарта: в меню GRUB нажми c, введи videoinfo. Или выполни в системе:

```
sudo hwinfo --framebuffer
```

Пропиши нужное разрешение в GRUB_GFXMODE и пересобери конфиг. Для 4K — GRUB_GFXMODE=3840x2160, для ноутбука — 1920x1080. Если режим не поддерживается, GRUB откатится на запасной — добавляй fallback через запятую. Полный список опций — на странице [GRUB](https://wiki.archlinux.org/title/GRUB) в ArchWiki.

## Частые вопросы

**Тема поставилась, но фон чёрный. Что делать?**
Проверь три вещи: путь к theme.txt, GRUB_TERMINAL_OUTPUT="gfxterm" и вывод grub-mkconfig. Если в выводе нет Found theme — GRUB не видит файл. И пересобери конфиг после правок.

**Можно ли использовать GRUB_BACKGROUND вместе с GRUB_THEME?**
Можно, но смысла мало: при включённой теме фон из GRUB_BACKGROUND обычно не показывается — тема перекрывает его. Выбирай один способ.

**После выбора пункта меню разрешение скачет. Как убрать?**
Добавь GRUB_GFXPAYLOAD_LINUX=keep в /etc/default/grub и пересобери конфиг. Ядро получит разрешение GRUB, и переключения не будет.

**Тема не грузится при зашифрованном /boot. Почему?**
GRUB не может читать зашифрованный раздел до ввода пароля. Скопируй тему в /boot/grub/themes/ — этот путь GRUB читает до разблокировки.

**Как вернуть стандартный вид?**
Удали строки GRUB_THEME и GRUB_BACKGROUND из /etc/default/grub и пересобери конфиг.

## Заключение

Красивый GRUB — это пять минут и три строки в конфиге: папка темы в /boot/grub/themes, переменная GRUB_THEME, пересборка grub-mkconfig. Если что-то пошло не так, почти всегда виноват путь или забытая пересборка конфига.

А если в меню пропала Windows при dual boot — смотри [os-prober: как GRUB увидит Windows](https://ordanax.github.io/os-prober-grub-windows) и [Windows пропала из GRUB](https://ordanax.github.io/dualboot-windows-propala-iz-grub).

## Полезные ресурсы

- [GNU GRUB Manual](https://www.gnu.org/software/grub/manual/grub/grub.html) — официальная документация по переменным и командам GRUB.
- [vinceliuice/grub2-themes](https://github.com/vinceliuice/grub2-themes) — репозиторий с темами Tela, Vimix, Stylish и WhiteSur.