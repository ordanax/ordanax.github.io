---
title: Чек-лист по установке и настройке Arch Linux Xfce
permalink: checklist/
layout: post
---

## Вопросы, поддержка

Если у вас возникли вопросы, вступите в группу по Arch Linux для получения бесплатной поддержки:
- [Линукс Телеграм Чат](https://t.me/linux4at)

## Предложения и коррекция чек-листа
Если вы заметили неточность в чек-листе или у вас есть лучшее предложение, то [присылайте свой коммит в github](https://github.com/ordanax/ordanax.github.io/blob/master/checklist.md) 

---

> **Актуальность:** 2026 г. | **Основан на:** [Arch Wiki Installation Guide](https://wiki.archlinux.org/title/Installation_guide)

---

## Подготовка к установке

### Загрузка образа
1. Скачать ISO с [archlinux.org/download](https://archlinux.org/download/)
2. **Проверить подпись** (рекомендуется):
   ```bash
   gpg --keyserver-options auto-key-retrieve --verify archlinux-version-x86_64.iso.sig
   ```
3. Записать на флешку:
   ```bash
   sudo dd if=archlinux-YYYY.MM.DD-x86_64.iso of=/dev/sdX bs=4M status=progress && sync
   ```
   В Windows можно использовать [Rufus](https://rufus.ie) или [Ventoy](https://www.ventoy.net).

### Загрузка с флешки
- **UEFI:** Если ошибка "Security Boot Fail" — отключить Secure Boot в BIOS (установить пароль супервизора, затем отключить Secure Boot)
- **BIOS:** Убедиться, что загрузка с USB включена в Boot Menu

---

## Установка системы

### 1. Начальная настройка консоли
```bash
# Русская раскладка (опционально)
loadkeys ru
setfont cyr-sun16
```

### 2. Подключение к интернету

**Проводное (Ethernet):**
```bash
dhcpcd
```

**Wi-Fi (iwd):**
```bash
iwctl
[iwd]# station wlan0 connect "SSID"
[iwd]# exit
```

**Проверка соединения:**
```bash
ping -c 3 archlinux.org
```

### 3. Синхронизация времени
```bash
timedatectl set-ntp true
```

### 4. Разметка дисков

**Просмотр дисков:**
```bash
fdisk -l
lsblk
```

**Разметка для BIOS (MBR) через cfdisk:**
```bash
cfdisk /dev/sda
```
Выбрать `dos` (MBR) → создать разделы:
- `/dev/sda1` — 1G `/boot` (тип: Linux, флаг: Bootable)
- `/dev/sda2` — 30G `/` (тип: Linux)
- `/dev/sda3` — 4G+ `swap` (тип: Linux swap)
- `/dev/sda4` — остаток `/home` (тип: Linux)

**Разметка для UEFI (GPT) через cfdisk:**
```bash
cfdisk /dev/sda
```
Выбрать `gpt` → создать разделы:
- `/dev/sda1` — 512M-1G `EFI` (тип: EFI System)
- `/dev/sda2` — 30G+ `/` (тип: Linux Filesystem)
- `/dev/sda3` — 4G+ `swap` (тип: Linux swap)
- `/dev/sda4` — остаток `/home` (тип: Linux Filesystem)

### 5. Форматирование разделов

**BIOS (MBR):**
```bash
mkfs.ext4 /dev/sda1 -L boot
mkfs.ext4 /dev/sda2 -L root
mkswap /dev/sda3 -L swap
mkfs.ext4 /dev/sda4 -L home
```

**UEFI (GPT):**
```bash
mkfs.fat -F32 /dev/sda1
mkfs.ext4 /dev/sda2 -L root
mkswap /dev/sda3 -L swap
mkfs.ext4 /dev/sda4 -L home
```

### 6. Монтирование разделов

**BIOS:**
```bash
mount /dev/sda2 /mnt
mkdir /mnt/boot /mnt/home
mount /dev/sda1 /mnt/boot
mount /dev/sda4 /mnt/home
swapon /dev/sda3
```

**UEFI:**
```bash
mount /dev/sda2 /mnt
mkdir -p /mnt/boot/efi /mnt/home
mount /dev/sda1 /mnt/boot/efi
mount /dev/sda4 /mnt/home
swapon /dev/sda3
```

### 7. Настройка зеркал (опционально)
```bash
# Автоматический выбор быстрых зеркал
reflector --country Russia --latest 5 --sort rate --save /etc/pacman.d/mirrorlist

# Или вручную:
nano /etc/pacman.d/mirrorlist
# Переместить нужное зеркало наверх (Ctrl+K, Ctrl+U)
```

### 8. Установка базовой системы

> **Важно:** Флаг `-K` инициализирует pacman keyring (обязательно!)

**Для Intel CPU:**
```bash
pacstrap -K /mnt base linux linux-firmware intel-ucode nano vim
```

**Для AMD CPU:**
```bash
pacstrap -K /mnt base linux linux-firmware amd-ucode nano vim
```

**Расширенная установка (рекомендуется):**
```bash
pacstrap -K /mnt base base-devel linux linux-firmware intel-ucode nano vim networkmanager iwd
# или для AMD:
pacstrap -K /mnt base base-devel linux linux-firmware amd-ucode nano vim networkmanager iwd
```

### 9. Генерация fstab
```bash
genfstab -U /mnt >> /mnt/etc/fstab
cat /mnt/etc/fstab  # Проверка
```

### 10. Вход в установленную систему
```bash
arch-chroot /mnt
```

### 11. Настройка системы внутри chroot

**Имя компьютера:**
```bash
echo "myarch" > /etc/hostname
```

**Часовой пояс:**
```bash
# Москва:
ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime

# Екатеринбург:
ln -sf /usr/share/zoneinfo/Asia/Yekaterinburg /etc/localtime

hwclock --systohc
```

**Локализация:**
```bash
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen

echo 'LANG=ru_RU.UTF-8' > /etc/locale.conf
echo 'KEYMAP=ru' > /etc/vconsole.conf
echo 'FONT=cyr-sun16' >> /etc/vconsole.conf
```

**Пароль root:**
```bash
passwd
```

### 12. Установка загрузчика

**Для BIOS:**
```bash
pacman -S grub
grub-install /dev/sda
grub-mkconfig -o /boot/grub/grub.cfg
```

**Для UEFI:**
```bash
pacman -S grub efibootmgr
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
```

**Если несколько ОС (os-prober):**
```bash
pacman -S os-prober
# Раскомментировать в /etc/default/grub: GRUB_DISABLE_OS_PROBER=false
nano /etc/default/grub
grub-mkconfig -o /boot/grub/grub.cfg
```

### 13. Сетевые инструменты (если не установили в pacstrap)
```bash
pacman -S networkmanager iwd
systemctl enable NetworkManager
```

### 14. Выход и перезагрузка
```bash
exit
umount -R /mnt
reboot
```

---

## Настройка после установки

### 1. Подключение Wi-Fi через NetworkManager
```bash
# Просмотр доступных сетей
nmcli device wifi list

# Подключение
nmcli device wifi connect "SSID" password "пароль"

# Или через nmtui (TUI интерфейс)
nmtui
```

### 2. Создание пользователя
```bash
useradd -m -g users -G wheel,power,storage,audio,video -s /bin/bash username
passwd username
```

### 3. Настройка sudo
```bash
EDITOR=nano visudo
# Раскомментировать строку: %wheel ALL=(ALL:ALL) ALL
```

### 4. Настройка pacman (multilib для 32-бит)
```bash
nano /etc/pacman.conf
# Раскомментировать:
[multilib]
Include = /etc/pacman.d/mirrorlist

# Обновление баз данных
pacman -Syy
```

---

## Установка графического окружения Xfce

### 1. Xorg и драйверы
```bash
sudo pacman -S xorg-server xorg-xinit

# Автоопределение (рекомендуется для большинства систем):
sudo pacman -S xf86-video-fbdev xf86-video-vesa

# Или конкретные драйверы:
# Intel (modesetting предпочтительнее старого xf86-video-intel):
# sudo pacman -S xf86-video-intel

# AMD:
# sudo pacman -S xf86-video-amdgpu xf86-video-ati

# NVIDIA (проприетарный):
# sudo pacman -S nvidia nvidia-utils
```

### 2. Xfce и менеджер входа
```bash
# Xfce + LightDM (рекомендуется)
sudo pacman -S xfce4 xfce4-goodies lightdm lightdm-gtk-greeter

# Альтернативно SDDM:
# sudo pacman -S sddm
```

### 3. Шрифты
```bash
sudo pacman -S ttf-liberation ttf-dejavu ttf-droid
```

### 4. PipeWire (звук) — заменяет PulseAudio
```bash
sudo pacman -S pipewire pipewire-pulse pipewire-alsa pavucontrol
systemctl --user enable pipewire pipewire-pulse
```

### 5. Включение автозагрузки
```bash
sudo systemctl enable lightdm
# или для SDDM:
# sudo systemctl enable sddm
```

### 6. Перезагрузка
```bash
reboot
```

**При первом входе:** Выбрать "Xfce Session" в меню сессий.

---

## Установка AUR helper (yay)

```bash
sudo pacman -S --needed git base-devel
git clone https://aur.archlinux.org/yay.git /tmp/yay
cd /tmp/yay
makepkg -si
cd ~
rm -rf /tmp/yay
```

---

## Рекомендуемые программы

### Базовый набор
```bash
sudo pacman -S firefox thunderbird file-roller \
    p7zip unrar gvfs ntfs-3g dosfstools \
    man-db man-pages texinfo \
    ufw gufw
```

### Мультимедиа
```bash
sudo pacman -S vlc mpv ffmpeg firefox-i18n-ru
```

### Офис и графика
```bash
sudo pacman -S libreoffice-fresh libreoffice-fresh-ru \
    gimp inkscape
```

### Инструменты
```bash
sudo pacman -S htop btop neofetch \
    qbittorrent veracrypt \
    flameshot obs-studio
```

### Разработка
```bash
sudo pacman -S git code
```

### Из AUR (через yay)
```bash
yay -S google-chrome visual-studio-code-bin \
    telegram-desktop spotify-launcher \
    timeshift papirus-icon-theme
```

---

## Настройка Xfce

### Горячие клавиши
**Настройки → Клавиатура → Комбинации клавиш:**

| Действие | Команда | Клавиши |
|----------|---------|---------|
| Терминал | `xfce4-terminal` | Ctrl+Alt+T |
| Скриншот (весь экран) | `xfce4-screenshooter -f` | Ctrl+Print |
| Скриншот (область) | `flameshot gui` | Print |
| Системный монитор | `xfce4-taskmanager` | Ctrl+Alt+M |
| Блокировка экрана | `xflock4` | Ctrl+Alt+L |

### Раскладка клавиатуры
**Настройки → Клавиатура → Раскладка:**
- Добавить: English (US), Russian
- Переключение: Alt+Shift или Win+Space

### Темы и иконки
```bash
yay -S papirus-maia-icon-theme-git capitaine-cursors
```

**Настройки → Внешний вид:**
- Стиль: Adwaita или Arc
- Иконки: Papirus или Papirus-Maia
- Курсор: Capitaine

---

## Безопасность

### Файрвол UFW
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
sudo systemctl enable ufw
```

---

## Обновление системы

```bash
# Простое обновление:
yay -Syu

# С очисткой:
yay -Syu && sudo pacman -Sc && sudo pacman -Rns $(pacman -Qdtq) 2>/dev/null

# С обновлением зеркал:
sudo reflector --country Russia --latest 5 --sort rate --save /etc/pacman.d/mirrorlist && yay -Syu
```

---

## Ускорение загрузки (убрать меню GRUB)

Если нет других ОС:
```bash
sudo nano /etc/default/grub
# Изменить: GRUB_TIMEOUT=5 → GRUB_TIMEOUT=0
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

---

## Полезные ссылки

- [Arch Wiki — Installation Guide](https://wiki.archlinux.org/title/Installation_guide)
- [Arch Wiki — Xfce](https://wiki.archlinux.org/title/Xfce)
- [Arch Wiki — GRUB](https://wiki.archlinux.org/title/GRUB)
- [Arch Wiki — NetworkManager](https://wiki.archlinux.org/title/NetworkManager)
- [Arch Wiki — PipeWire](https://wiki.archlinux.org/title/PipeWire)

---

*Чек-лист актуализирован: 2026 г. | Все изменения проверены по Arch Wiki*
