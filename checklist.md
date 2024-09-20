---
title: Чек лист по установке и настройке Arch Linux Xfce
permalink: archlinux-xfce/
layout: post
---

# Чек лист по установке и настройке Arch Linux Xfce

## Вопросы и поддержка

Если у вас возникли вопросы, вступите в группу по Arch Linux для получения бесплатной поддержки:
- [Линукс Телеграм Чат](https://t.me/linux4at)

## Удаленная установка по SSH

1. Запускаем службу на компьютере, на который ставим Arch Linux:
   systemctl start sshd.service

2. Узнаем IP-адрес компьютера, на который будем устанавливать Arch Linux:
   ip a

3. На компьютере, на который будем производить установку, подключаем Wi-Fi: [Инструкции по подключению](https://docs.google.com/document/d/1IsTwkhYvYde9y3zTD1EscqockzdtdUYcItnAglYfZdU/edit#heading=h.l46257y8p7ek).

4. Устанавливаем пароль для root командой:
   passwd

5. Заходим на компьютер по SSH командой:
   ssh root@000.000.0.000  
   Вместо нулей подставляем IP-адрес компьютера.

# 1. Загрузка

## Скачиваем дистрибутив с офф сайта
[https://www.archlinux.org/download/](https://www.archlinux.org/download/)

## Проверяем целостность образа
1. Открываем папку со скаченным архивом.
2. Жмем правой кнопкой мыши и выбираем “Открыть в терминале”.
3. Вбиваем в терминале команду md5sum + название файла.

   Пример: md5sum archlinux-2019.06.01-dual.iso

   Контрольная сумма 97537db63e61d20a5cb71d29145b2937 должна совпадать. См. видео [https://vk.cc/7S7N3o](https://vk.cc/7S7N3o).

   Актуальную контрольную сумму смотрите на официальном сайте [https://www.archlinux.org/download/](https://www.archlinux.org/download/).

   Для Windows можно воспользоваться программой для проверки суммы [http://hashtab.ru](http://hashtab.ru).

## Записываем его на флешку

sudo dd if=X of=/dev/sdY

Где X — это название ISO файла, Y — буква диска.

Пример: 

sudo dd if=archlinux-2019.06.01-dual.iso of=/dev/sdb && sync

В Windows лучше записывать программой [Rufus](https://rufus.ie). Чтобы избежать ошибок при разметке диска, предварительно перезапишите его нулями, например, программой Disks, загрузившись с USB в любом дистрибутиве Linux.

## Загружаемся с флешки

ВАЖНО!  
Если вы ставите с UEFI и при загрузке получаете ошибку “Security Boot Fail”, то нужно зайти в BIOS, в разделе установить пароль в разделе Set Supervisor Password и в вкладке Boot отключить Security Boot. См. [https://i.imgur.com/jFLlrm0.png](https://i.imgur.com/jFLlrm0.png).

# Перед установкой

## Установка раскладки клавиатуры
После загрузки настроим русский язык для удобства работы:

loadkeys ru

Изменим консольный шрифт на тот, который поддерживает кириллицу:

setfont cyr-sun16

## Соединение с Интернетом
### Подключаем проводной интернет

dhcpcd

Если не знаете название вашего устройства (device), то пишем:

ip link

### Подключение через Wi-Fi

iwctl

station device connect SSID

Где SSID = название вашей сети  
Где device = wlp5s0 или wlan0 (у вас будет свое)  

После этого вам будет предложено ввести пароль.  
Подробнее: [https://wiki.archlinux.org/index.php/Iwd#iwctl](https://wiki.archlinux.org/index.php/Iwd#iwctl)

## Синхронизация системных часов

timedatectl set-ntp true

## Создание разделов
### Смотрим какие диски есть

fdisk -l

### Разбиваем диски 
(для ручной разметки используем fdisk, для псевдографической разбивки можно использовать команду cfdisk)

fdisk /dev/sda

Можно вызвать подсказки нажатием на клавишу “m”.

### Разделяем диски (подробно в видео)
Видео, которые могут вам помочь: [https://www.youtube.com/watch?v=PemucgRrdPk](https://www.youtube.com/watch?v=PemucgRrdPk)  
Ручная разметка дисков начинается на 5:14.  
Если есть желание использовать файловую систему Btrfs, то ставим вот так: [https://vk.com/@arch4u-ustanovka-arch-linux-na-btrfs](https://vk.com/@arch4u-ustanovka-arch-linux-na-btrfs)

### Создание разделов с BIOS
- /boot - 100M - выставить флаг boot командой a
- / - 20G
- swap - 1024M
- /home - весь остаток

### Создание разделов с UEFI

cfdisk /dev/sda

- /dev/sda1 - 500M EFI - выставить флаг EFI командой t
- /dev/sda2 - 30G root Linux File System
- /dev/sda3 - Весь остаток home Linux file System

### Процесс разбивки диска по шагам
См. видео: [https://vk.cc/7S7OMg](https://vk.cc/7S7OMg)

1. Создаем MBR таблицу (Для UEFI - GPT командой g):

   o

2. Создаем новый диск:

   n

   Жмем enter.
3. Выбираем primary (основной) или extended (расширенный).
   По умолчанию стоит primary (основной), поэтому просто жмем enter.
4. Выбор номера диска, по умолчанию подставляется следующий номер:
   Жмем enter.
5. Запрос на первый сектор диска:
   Жмем enter.
6. Запрос на последний сектор диска (ставим + и объем памяти. Пример: +100M):

   +100M

Повторяем все шаги снова для всех нужных разделов диска.  

(LEGACY) Для /boot не забываем указать a и поставить 1 для установки его загрузочным.  
(UEFI) Для EFI не забываем указать, что это EFI раздел t и поставить 1.  

Как все разметили, не забываем все записать командой:

w

В итоге можете проверить, что у вас получилось командой:

fdisk -l

Должно получиться примерно так:  
Legacy разметка: [http://i.imgur.com/pgej0Nt.png](http://i.imgur.com/pgej0Nt.png)  
UEFI разметка: [https://i.imgur.com/O7Yn0MK.png](https://i.imgur.com/O7Yn0MK.png)  

## Форматирование и монтирование разделов
### Разделы с BIOS

mkfs.ext2  /dev/sda1 -L boot
mkfs.ext4  /dev/sda2 -L root
mkswap /dev/sda3 -L swap
mkfs.ext4  /dev/sda4 -L home

#### Монтируем /

mount /dev/sda2 /mnt

# Перейдём в установленную систему

arch-chroot /mnt

## Прописываем имя компьютера
Вместо ArchLinux впишите свое название:

echo "ArchLinux" > /etc/hostname

## Настроим часы
- Для Москвы:

  ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime

- Для Екатеринбурга:

  ln -sf /usr/share/zoneinfo/Asia/Yekaterinburg /etc/localtime

## Добавляем русскую локаль системы
Добавим русскую локаль в систему:

echo -e "en_US.UTF-8 UTF-8\nru_RU.UTF-8 UTF-8" >> /etc/locale.gen

Обновим текущую локаль системы:

locale-gen

Указываем язык системы:

echo 'LANG="ru_RU.UTF-8"' > /etc/locale.conf

Указываем keymap для console и прописываем шрифт:

echo 'KEYMAP=ru' >> /etc/vconsole.conf
echo 'FONT=cyr-sun16' >> /etc/vconsole.conf

## Создадим загрузочный RAM диск

mkinitcpio -p linux

## Изменим пароль root

passwd

# Установка загрузчика

## Обновляем базы данных пакетов:

pacman -Syy

## Устанавливаем загрузчик (для BIOS)

pacman -S grub
grub-install /dev/sda

## Устанавливаем загрузчик (для UEFI)

pacman -S grub efibootmgr
grub-install /dev/sda

Если в системе будут несколько ОС, то устанавливаем:

pacman -S os-prober mtools fuse

## Обновляем grub.cfg

grub-mkconfig -o /boot/grub/grub.cfg

## Ставим программу для Wi-Fi

pacman -S dialog wpa_supplicant

## Выходим

exit

# Перезагрузка

reboot

# После установки

## Логинимся
- Логин: root  
- Пароль: тот, что установили

## Подключаем Wi-Fi

wifi-menu

Или если у вас проводной интернет, то подключаем его:

dhcpcd

## Добавляем пользователя
Добавим нового пользователя. Вместо MYUSERNAME пишем имя пользователя без спец символов, только маленькие лат. буквы:

useradd -m -g users -G wheel -s /bin/bash MYUSERNAME

## Устанавливаем пароль пользователя
Установим пароль для нового пользователя. Вместо MYUSERNAME пишем имя пользователя:

passwd MYUSERNAME

## Устанавливаем SUDO
Заходим в файл sudoers:

nano /etc/sudoers

В файле /etc/sudoers находим строчку:

# %wheel ALL=(ALL) ALL

и раскомментируем её, убрав символ #.

Так было:

## Uncomment to allow members of group wheel to execute any command
#%wheel ALL=(ALL) ALL

Так должно быть:

## Uncomment to allow members of group wheel to execute any command
%wheel ALL=(ALL) ALL

## Сохраняем
Ctrl+O (Enter)  
Выходим  
Ctrl+X

Теперь мы можем использовать sudo для выполнения команд администратора.

## Настройка pacman
Настроим pacman (только для x86_64):

nano /etc/pacman.conf

Для работы 32-битных приложений в 64-битной системе необходимо раскомментировать репозиторий multilib:

[multilib]
Include = /etc/pacman.d/mirrorlist

## Сохраняем
Ctrl+O (Enter)  
Выходим  
Ctrl+X

## Обновляем базы данных пакетов:

pacman -Syy

# Ставим иксы и драйвера
Установим Х (Иксы) и свободные драйвера + читаем зависимости при необходимости, ставим их тоже:

pacman -S xorg-server xorg-drivers

# Ставим Xfce, LXDM и сеть 
Ставим Xfce + менеджер входа lxdm (или sddm):

pacman -S xfce4 xfce4-goodies lxdm

Ставим шрифты, чтобы можно было читать, что написано. Иначе будут просто квадратики:

pacman -S ttf-liberation ttf-dejavu

Ставим менеджер сети:

pacman -S networkmanager network-manager-applet ppp

## Подключаем автозагрузку менеджера входа и интернет
(с соблюдением регистра для NetworkManager):

systemctl enable lxdm NetworkManager

# Перезагрузка
Выбираем Xfce Session или просто “Сеанс”! Это важно, иначе не войдете!

# Дополнительные настройки

## Проприетарные драйвера для видеокарт (Условный пункт)
Если все работает нормально, то можете этот пункт пропустить.

### Установим драйвер для видеокарты:
Пакеты lib32-* нужно устанавливать только на x86_64 системы.

- Intel:

  sudo pacman -S xf86-video-intel lib32-intel-dri

- Nvidia:

  sudo pacman -S nvidia nvidia-utils lib32-nvidia-utils

- AMD:

  sudo pacman -S xf86-video-ati lib32-ati-dri

- Если вы устанавливаете систему на виртуальную машину:

  sudo pacman -S xf86-video-vesa

## Подключаем Wi-Fi
1. Идём в меню - настройки - сетевые соединения. Сюда: [http://i.imgur.com/9fIT56r.png](http://i.imgur.com/9fIT56r.png)
2. Если Wi-Fi нет, то жмем сюда: [http://i.imgur.com/GUwknhy.png](http://i.imgur.com/GUwknhy.png) и добавляем Wi-Fi.
3. Выбираем сеть, жмем изменить, вводим пароль.

## Установка AUR
yaourt и aurman более не обновляются разработчиками, поэтому рекомендую к использованию именно yay. (См. таблицу [https://vk.cc/88yr8q](https://vk.cc/88yr8q) и голосование [https://vk.cc/8YQdqI](https://vk.cc/8YQdqI))

### Обновляем систему

sudo pacman -Syu

### Создаём yay_install директорию и переходим в неё

mkdir -p /tmp/yay_install
cd /tmp/yay_install

### Установка "yay" из AUR

sudo pacman -S git
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -sir --needed --noconfirm --skippgpcheck
rm -rf yay_install

Если вы предпочитаете работать с графическим интерфейсом, а не с терминалом, то как альтернативу yay можно использовать pamac (установщик пакетов из AUR c GUI).

### Обновляем систему

sudo pacman -Syu

### Создаём pamac-aur_install директорию и переходим в неё

mkdir -p /tmp/pamac-aur_install
cd /tmp/pamac-aur_install

### Установка "pamac-aur" из AUR

sudo pacman -S git
git clone https://aur.archlinux.org/pamac-aur.git
cd pamac-aur
makepkg -si --needed --noconfirm --skippgpcheck
rm -rf pamac-aur_install

## Установка программ
### Установка пакетов, которые решают большинство проблем

sudo pacman -S f2fs-tools dosfstools ntfs-3g alsa-lib alsa-utils file-roller p7zip unrar gvfs aspell-ru pulseaudio

### Установка программ

sudo pacman -S firefox doublecmd-gtk2 filezilla gimp gnome-calculator libreoffice libreoffice-fresh-ru kdenlive screenfetch vlc ufw qbittorrent obs-studio veracrypt freemind flameshot

Если нужно русифицировать Firefox, добавляем еще и firefox-i18n-ru. Если русификация не вступила в силу, тогда сбросьте настройки Firefox: [https://vk.cc/9n7uLx](https://vk.cc/9n7uLx).

### Установка AUR программ

yay -S sublime-text-dev cherrytree timeshift google-talkplugin hunspell-ru pamac-aur xflux xflux-gui-git osx-arc-shadow papirus-maia-icon-theme-git breeze-obsidian-cursor-theme flameshot-git megasync

Рекомендуемые и используемые мной программы можете посмотреть здесь: [https://vk.cc/5XjUqt](https://vk.cc/5XjUqt).

## Установка тем
### Темы Gtk+ для Xfce

yay -S x-arc-shadow

или

yay -S vertex-themes

### Темы иконок 
- papirus-maia-icon-theme-git
- Faenza: [https://goo.gl/rE1rMi](https://goo.gl/rE1rMi) 
- Paper Icons: [https://www.xfce-look.org/p/1099618/](https://www.xfce-look.org/p/1099618/) 
- Revival Icon Theme: [https://www.xfce-look.org/p/1099769/](https://www.xfce-look.org/p/1099769/) 
- Moka Icon Theme: [https://www.xfce-look.org/p/1012513/](https://www.xfce-look.org/p/1012513/) 

### Темы курсора 

sudo pacman -S capitaine-cursors
yay -S xcursor-breeze-serie-obsidian
yay -S breeze-obsidian-cursor-theme

Теперь можно менять тему для курсора в настройках. Для этого открываем «Меню» -> «Настройки» -> «Мышь и тачпад».

## Ставим тему на LXDM

yay -S lxdm-themes

### Меняем тему в настройках 

sudo nano /etc/lxdm/lxdm.conf

Находим строку с theme=Industrial и заменяем на название нашей темы:

theme=ArchlinuxTop

## Настройки Xfce
Смотрите видео по настройке Xfce: [https://vk.cc/7qwQ8L](https://vk.cc/7qwQ8L)  
Настройка прозрачного терминала см. в видео: [https://vk.cc/9afFih](https://vk.cc/9afFih) (Время в видео 39:36)

Настройки моих горячих клавиш по ссылке: [https://github.com/ordanax/dots/blob/master/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml](https://github.com/ordanax/dots/blob/master/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml) 

### Настраиваем горячие клавиши на запуск терминала
Перейдите в Settings (Настройки) > Keyboard (Клавиатура) > Application Shortcuts (Комбинации клавиш)

Команда:

xfce4-terminal

Клавиши: Ctrl+Alt+T

### Настраиваем горячие клавиши на скриншот
Назначьте команду:

xfce4-screenshooter -f

на клавишу Ctrl + Print Screen, которая будет делать скриншоты всего экрана.

# Убираем меню GRUB для выбора системы
Если у вас нет второй системы, как у меня, то вы можете ускорить загрузку системы и убрать это GRUB меню. Делается это следующим образом:

sudo nano /etc/default/grub 

Измените строку:

GRUB_TIMEOUT=5

на

GRUB_TIMEOUT=0

## Обновляем grub.cfg

sudo grub-mkconfig -o /boot/grub/grub.cfg

# Обновление системы
Обновление всей системы (ядра, окружения рабочего стола, программ из pacman и из AUR) производится одной командой:

yay -Syu

## Альтернативная команда для обновления и очистки системы

yay -Syu && sudo pacman -Scc && sudo pacman -Rsn $(pacman -Qdtq) && sudo rm -rf ~/.cache/thumbnails/*

### Пояснения:
- yay -Syu - обновляет ядро, программы в pacman и в AUR.
- sudo pacman -Scc - очищает кэш пакетов, высвобождая место на диске.
- sudo pacman -Rsn $(pacman -Qdtq) - удаляет пакеты-сироты (которые не используются ни одной программой).
- sudo rm -rf ~/.cache/thumbnails/* - удаляет миниатюры фото, которые накапливаются в системе.

## Обновление системы вместе с проверкой зеркал (должен стоять рефлектор)

sudo reflector --verbose -l 5 -p https --sort rate --save /etc/pacman.d/mirrorlist && sudo pacman -Syyu && yay -Syu --noconfirm && sudo pacman -Rsn $(pacman -Qdtq)

# Устанавливаем Conky

sudo pacman -S conky conky-manager

Конфиги можно скачать в группе и добавить свои: [https://vk.cc/89e28X](https://vk.cc/89e28X).

## Ставим курсор по умолчанию
Откройте файл:

sudo nano /usr/share/icons/default/index.theme

Меняем тему курсоров на нужную, например Breeze Obsidian.

Oxygen Neon: [http://vk.cc/5AcWC7](http://vk.cc/5AcWC7)
