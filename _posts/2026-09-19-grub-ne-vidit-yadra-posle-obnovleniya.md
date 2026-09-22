---
layout: post
title: "GRUB не видит ядра после обновления: что делать"
description: "Ядра пропали из меню GRUB после обновления Arch? Чиним: grub-mkconfig, проверка /boot и ESP, переустановка ядра и GRUB."
date: 2026-09-19 00:00:00 +0300
permalink: /grub-ne-vidit-yadra-posle-obnovleniya
categories:
- linux
- arch linux
- configs
- kernel-boot
tags:
- grub
- kernel
- bootloader
- update
- troubleshooting
edit: true
---


Ядра пропали из меню GRUB после обновления — виноват не сам загрузчик, а grub.cfg, который перестал соответствовать содержимому /boot: записи ссылаются на файлы, которых там нет. Чинится одной командой — grub-mkconfig -o /boot/grub/grub.cfg, а если и она не помогла — переустановкой ядра или самого GRUB.

## Почему ядра исчезают из меню после обновления

GRUB не сканирует диск при каждой загрузке — он читает готовый файл /boot/grub/grub.cfg. Пока файлы ядра на месте, записи работают даже после обновления: они ссылаются на стабильные пути /vmlinuz-linux и /initramfs-linux.img. Проблема появляется, когда обновление не доехало до /boot — ESP переполнена, раздел не смонтирован, файлы не записались. Тогда записи ведут в пустоту, и меню становится пустым. Пересборка конфига — первый шаг диагностики.

### grub.cfg не пересобрался после pacman -Syu

Типичный случай. mkinitcpio пересобирает initramfs автоматически через хук pacman, а вот grub-mkconfig никто за тебя не запустит. Конфиг остался от прошлой сборки и не видит текущее содержимое /boot — пересобери его и проверь, что записи появились.

### ESP смонтирован не туда

В Arch два популярных расклада: ESP в /boot или ESP в /efi с отдельным /boot. Если в fstab прописано одно, а смонтировано другое — ядра и grub.cfg разъезжаются по разным файловым системам. GRUB ищет vmlinuz рядом с grub.cfg, не находит и рисует пустое меню. Проверь fstab и findmnt /boot.

### os-prober отключён

Пропали не только ядра Arch, но и Windows? Тогда дело в os-prober. Начиная с GRUB 2.06 он отключён по умолчанию: в /etc/default/grub стоит GRUB_DISABLE_OS_PROBER=true. Ставишь пакет os-prober, меняешь значение на false, пересобираешь конфиг — и чужие системы возвращаются в меню. Разбор — в статье [«Windows пропала из GRUB»](https://ordanax.github.io/dualboot-windows-propala-iz-grub).

### ESP переполнен

ESP на FAT32 обычно маленький — 100–512 МБ. Старые ядра копятся, места не хватает, pacman падает с ошибкой записи, и свежий vmlinuz-linux не доезжает до /boot. grub-mkconfig честно генерирует записи для файлов, которых нет. Проверка — df -h /boot.

## Как проверить, что ядра на месте

Прежде чем чинить конфиг, убедись, что сами ядра существуют.

### Смотрим /boot

```
ls /boot
```

В выводе должны быть vmlinuz-linux и initramfs-linux.img. Если стоит несколько ядер — по файлу на каждое. Нет файлов — ядро не установилось, и дело не в конфиге.

### Смотрим grub.cfg

```
cat /boot/grub/grub.cfg | grep -A2 menuentry
```

Нашёл записи с vmlinuz-linux — конфиг в порядке, проблема глубже. Пусто или одни заголовки без команд — конфиг старый или битый. Заодно проверь, где лежит grub.cfg: ls /efi/GRUB или ls /boot/grub.

## Как пересобрать конфиг GRUB

Пошагово, без паники:

1. Убедись, что /boot смонтирован: findmnt /boot.
2. Пересобери initramfs: mkinitcpio -P.
3. Пересобери конфиг: grub-mkconfig -o /boot/grub/grub.cfg.
4. Проверь вывод — там должны появиться строки Found linux image: /boot/vmlinuz-linux.
5. Перезагрузись.

### Что делает grub-mkconfig

Утилита проходит по скриптам в /etc/grub.d/. Главный — 10_linux: он ищет ядра в /boot, собирает записи меню и пишет их в grub.cfg. Учитываются и настройки из /etc/default/grub — например, GRUB_PRELOAD_MODULES, модули для подгрузки до чтения файловой системы. Если записи не появляются — смотри вывод grub-mkconfig: он почти всегда называет причину.

## Что делать, если grub-mkconfig не помог

Конфиг пересобрался, записи на месте, а меню всё равно пустое или система не грузится — копаем глубже.

### Переустанови ядро

Если в /boot пусто или файлы битые, верни ядро на место:

```
pacman -S linux
mkinitcpio -P
grub-mkconfig -o /boot/grub/grub.cfg
```

Первая ставит ядро заново, вторая пересобирает initramfs, третья — конфиг. Подробности — на странице [mkinitcpio в ArchWiki](https://wiki.archlinux.org/title/Mkinitcpio).

### Переустанови GRUB

Если конфиг генерируется, а загрузчик всё равно не видит ядра — сломан сам GRUB: битые модули, кривая запись в NVRAM, повреждённый grubx64.efi. Нужна полная переустановка через grub-install и grub-mkconfig. Пошаговый ремонт из live-окружения — в статье [«Переустановка GRUB после поломки»](https://ordanax.github.io/pereustanovka-grub-posle-polomki).

## Как избежать проблемы в будущем

Пара привычек, и меню больше не будет пустеть:

- После каждого обновления ядра запускай grub-mkconfig -o /boot/grub/grub.cfg. Можно повесить это на хук pacman.
- Не делай частичных обновлений — pacman -Syu целиком. Почему это опасно — в статье [«Частичное обновление Arch»](https://ordanax.github.io/pacman-chastichnoe-obnovlenie).
- Следи за местом на ESP: старые ядра чисти через paccache -rk1.
- Если GRUB надоел — присмотрись к systemd-boot: он сам обновляет записи при установке ядра. Сравнение — в статье [«systemd-boot против GRUB»](https://ordanax.github.io/systemd-boot-vs-grub-vtoroe-yadro).

## Частые вопросы

**После обновления в меню только старые ядра, новые не появляются. Что делать?**

Пересобери конфиг: grub-mkconfig -o /boot/grub/grub.cfg. GRUB не добавляет записи сам — он читает готовый файл.

**Пропали и Arch, и Windows из меню.**

Включи os-prober: установи пакет os-prober, поставь GRUB_DISABLE_OS_PROBER=false в /etc/default/grub и пересобери конфиг.

**grub-mkconfig ругается на «failed to get canonical path».**

Запускай команду из загруженной системы, а не из chroot. В live-окружении используй arch-chroot.

**В /boot вообще нет vmlinuz-linux.**

Ядро не установилось. Верни его: pacman -S linux, затем mkinitcpio -P и grub-mkconfig -o /boot/grub/grub.cfg.

**ESP переполнен, pacman не может записать ядро.**

Почисти старые ядра: paccache -rk1 удалит все версии, кроме последней.

## Полезные ресурсы

- [«Первый час после установки Arch»](https://ordanax.github.io/pervyi-chas-posle-ustanovki-arch) — что настроить сразу
- [«Не грузится после установки: чёрный экран»](https://ordanax.github.io/ne-gruzitsya-posle-ustanovki-chernyi-ekran) — если система не стартует
- [GRUB — ArchWiki](https://wiki.archlinux.org/title/GRUB) — официальная документация

## Заключение

Ядра не пропадают бесследно. В девяти случаях из десяти виноват устаревший grub.cfg, который никто не пересобрал после обновления. Три команды — mkinitcpio -P, grub-mkconfig -o /boot/grub/grub.cfg и перезагрузка — решают проблему за пару минут. Не помогло — переустанови ядро, а затем и сам GRUB. Главное правило: обновил ядро — пересобери конфиг.