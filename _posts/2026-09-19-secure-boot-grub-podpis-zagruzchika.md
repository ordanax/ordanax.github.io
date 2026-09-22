---
layout: post
title: "Secure Boot + GRUB: подпись загрузчика"
description: "Secure Boot блокирует GRUB без подписи. Разбор цепочки shim → GRUB, подпись ключами sbctl и MOK через MokManager. Пошагово для Arch Linux."
date: 2026-09-19 00:00:00 +0300
permalink: /secure-boot-grub-podpis-zagruzchika
categories:
  - linux
  - arch linux
  - configs
  - kernel-boot
tags:
  - secure-boot
  - grub
  - shim
  - mokmanager
  - sbctl
  - uefi
edit: true
---



Суть: Secure Boot блокирует GRUB, потому что загрузчик не подписан ключами, которым доверяет прошивка. Решение — цепочка shim → GRUB: shim подписан Microsoft, а GRUB проверяется через MOK (Machine Owner Key). На Arch самый простой путь — sbctl: создаёшь свои ключи, вносишь их в прошивку и подписываешь GRUB и ядро. Ниже оба способа, с командами и разбором подводных камней.

## Почему Secure Boot блокирует GRUB?

Secure Boot — механизм защиты UEFI. При каждой загрузке прошивка проверяет цифровую подпись загружаемого файла и запускает его, только если подпись совпадает с доверенными ключами. Эти ключи лежат в переменных прошивки: db (подписанные файлы), KEK (ключи, обновляющие db) и PK (главный ключ платформы). Если подпись не совпадает — загрузка останавливается с ошибкой «Security Violation» или «Verification failed: 0x1A Security Violation».

GRUB из репозиториев Arch не подписан ключами Microsoft, поэтому при включённом Secure Boot прошивка отказывается его запускать. Это не баг, а защита: без проверки подписи любой файл на ESP можно подменить и получить контроль над загрузкой системы.

Обойти проверку можно двумя путями. Первый — подписать GRUB своими ключами через sbctl. Второй — использовать shim: маленький загрузчик, подписанный Microsoft, который сам проверяет GRUB по твоим ключам MOK. Оба пути рабочие, разница в удобстве.

Secure Boot защищает от bootkit'ов — вредоносных программ, которые прописываются в загрузчик и перехватывают управление раньше антивируса. Подпись гарантирует, что загружается именно тот код, который ты установил.

Проверить, включён ли Secure Boot, можно прямо из Arch: `mokutil --sb-state` покажет SecureBoot enabled или disabled. Утилита входит в пакет mokutil, при необходимости ставь её: `sudo pacman -S mokutil`.

## Как устроена цепочка shim → GRUB?

shim — первый этап загрузки. Прошивка проверяет подпись shim (она от Microsoft) и запускает его. Дальше shim проверяет подпись GRUB, но уже не по ключам прошивки, а по MokList — собственному хранилищу ключей в NVRAM. Ключи туда добавляешь ты сам, и Microsoft на них не влияет.

MOK расшифровывается как Machine Owner Key — «ключ владельца машины». Это твои личные ключи. Управлять MokList можно двумя инструментами: mokutil (команда из Linux) и MokManager (графическая утилита, которая запускается при загрузке, когда shim находит неподписанный файл).

Как выглядит включение: shim видит, что GRUB не подписан ключами из MokList, и запускает MokManager. На экране появляется меню с пунктом «Enroll key from disk» — добавить ключ с диска. Ты указываешь файл ключа, подтверждаешь, и после перезагрузки GRUB загружается. Один раз, дальше ключ уже в MokList.

Технически MokList делится на две части: MokList (ключи, ожидающие подтверждения) и MokListRT (активные ключи). Пока ключ не подтверждён в MokManager, он лежит в MokList и не работает. После подтверждения он переезжает в MokListRT и начинает действовать.

Почему вообще нужен shim, а не подпись GRUB напрямую? Потому что ключей Microsoft в прошивке нет ни у кого, кроме самой Microsoft. Подписать GRUB ключом Microsoft невозможно — их не выдают. Поэтому Microsoft подписывает shim, а shim уже доверяет твоим ключам. Получается мост между прошивкой и твоей системой.

При первом включении shim может показать синий экран с надписью «Verification failed: (0x1A) Security Violation» — это нормально, так shim сообщает, что GRUB не подписан. Дальше MokManager предложит варианты: Continue boot, Enroll key from disk, Enroll hash from disk. Выбирай Enroll key from disk.

## Как включить Secure Boot с GRUB через sbctl?

sbctl — самый простой способ на Arch. Он сам создаёт ключи, вносит их в прошивку и подписывает файлы. Ставим:

```bash
sudo pacman -S sbctl
```

Проверяем состояние:

```bash
sbctl status
```

Утилита покажет, включён ли Secure Boot и есть ли ключи. В выводе три строки: State (включён ли Secure Boot), Setup Mode (режим настройки) и список ключей. Различай два режима прошивки: Setup Mode и User Mode. В Setup Mode ключи можно менять свободно — именно в этом режиме работает enroll-keys. После внесения ключей прошивка переходит в User Mode, и менять ключи без подтверждения уже нельзя. Если Setup Mode — On, ключи ещё не внесены. Если ключей нет — создаём свои:

```bash
sbctl create-keys
```

Вносим ключи в прошивку. Флаг -m добавляет ключи Microsoft, чтобы продолжали работать Windows и другие подписанные загрузчики:

```bash
sbctl enroll-keys -m
```

Если внести только свои ключи без флага -m, прошивка перестанет доверять ключам Microsoft. Windows и другие загрузчики, подписанные Microsoft, загружаться не будут. Флаг -m оставляет их в силе — используй его, если на машине есть Windows или ты планируешь dualboot.

Теперь подписываем GRUB и ядро. Флаг --save запоминает файлы: при обновлении пакетов sbctl переподписывает их автоматически через свой pacman-хук:

```bash
sbctl sign --save /boot/EFI/GRUB/grubx64.efi
sbctl sign --save /boot/vmlinuz-linux
```

Проверяем результат:

```bash
sbctl verify
```

Команда покажет список подписанных файлов и пометит неподписанные. Если увидишь unsigned — подпиши файл и прогони verify снова. Перезагружайся, включи Secure Boot в настройках прошивки (обычно раздел Boot или Security) и загружайся. После перезагрузки проверь `sbctl status` — строка Secure Boot должна показывать Enabled. Если всё сделано верно — система стартует без ошибок.

Пути в командах подразумевают, что ESP смонтирована в /boot. Если у тебя ESP в /efi или /boot/efi — подставляй свои пути. Точку монтирования ESP покажет `findmnt /boot` или `lsblk -o NAME,MOUNTPOINTS`.

Если подписать только GRUB, а ядро нет — система всё равно загрузится, потому что ядро запускает GRUB, а не прошивка. Но подпись ядра нужна для прямой загрузки (EFISTUB, UKI) и для systemd-boot. Подписывай ядро сразу, чтобы потом не переделывать.

Подробный разбор sbctl с примерами — в статье «[Secure Boot в Arch Linux через sbctl](https://ordanax.github.io/secure-boot-arch-sbctl)».

## Как подписать GRUB через shim-signed и MokManager?

Второй путь — пакет shim-signed. Он ставит shim, подписанный Microsoft, и MokManager. GRUB подписывается твоим ключом, а ключ добавляется в MokList.

Когда выбирать shim вместо sbctl? Если нужен ручной контроль над ключами и ты готов разбираться с MokManager. sbctl прячет все детали, shim оставляет их на виду. Для большинства систем хватает sbctl.

Ставим shim и инструменты подписи:

```bash
sudo pacman -S shim-signed sbsigntools mokutil
```

Пакет кладёт файлы shimx64.efi и mmx64.efi (MokManager) в /usr/share/shim-signed. Скопируй их на ESP:

```bash
sudo cp /usr/share/shim-signed/shimx64.efi /usr/share/shim-signed/mmx64.efi /boot/EFI/
```

Если GRUB ещё не установлен — поставь его и установи на ESP:

```bash
sudo pacman -S grub
sudo grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Загрузочная запись должна указывать на shimx64.efi, а не на grubx64.efi. Создать запись и проверить порядок загрузки можно через efibootmgr — разбор в статье «[Порядок загрузки в NVRAM через efibootmgr](https://ordanax.github.io/poryadok-zagruzki-nvram-efibootmgr)».

Пример создания записи: `sudo efibootmgr --create --disk /dev/nvme0n1 --part 1 --label "Arch Linux (shim)" --loader '\EFI\shimx64.efi'`. Номер диска и раздела подставляй свои.

Теперь ключ для подписи GRUB. Создаём его через openssl:

```bash
openssl req -new -x509 -newkey rsa:2048 -keyout MOK.key -out MOK.crt -nodes -days 3650 -subj "/CN=My MOK"
```

Подписываем GRUB:

```bash
sudo sbsign --key MOK.key --cert MOK.crt --output /boot/EFI/GRUB/grubx64.efi /boot/EFI/GRUB/grubx64.efi
```

Если переустанавливаешь GRUB — сначала выполни `grub-install` как обычно, а потом заново подпиши grubx64.efi, иначе shim снова не пропустит загрузчик.

Импортируем ключ в MokList:

```bash
sudo mokutil --import MOK.crt
```

mokutil попросит задать пароль — он понадобится один раз при загрузке. Перезагружайся: shim запустит MokManager, выбери «Enroll key from disk», укажи файл MOK.crt и введи пароль. Управление в MokManager простое: стрелки и Enter. После выбора ключа MokManager спросит подтверждение и перезагрузит систему.

Проверить список внесённых ключей:

```bash
mokutil --list-enrolled
```

## Что делать, если прошивка сбросила ключи?

Сброс настроек UEFI (Reset to defaults, обновление прошивки, замена батарейки CMOS) стирает и ключи Secure Boot. Система перестаёт загружаться с ошибкой проверки подписи.

Лечится повторным внесением ключей. Для sbctl:

```bash
sbctl enroll-keys -m
```

Для shim — повторно импортировать ключ:

```bash
sudo mokutil --import MOK.crt
```

И перезагрузиться, подтвердив добавление в MokManager. Сами ключи при сбросе не теряются — они лежат на диске, теряется только доверие прошивки к ним.

Важно: MokList тоже хранится в NVRAM, поэтому сброс прошивки стирает и его. После сброса `mokutil --list-enrolled` покажет пустой список — первый признак, что ключи пропали.

Если система не загружается вовсе — загрузись с live-USB, сделай arch-chroot и выполни те же команды оттуда.

Чтобы не попадать в такую ситуацию, держи копию ключей в надёжном месте: MOK.key и MOK.crt (или ключи sbctl из /var/lib/sbctl) можно скопировать на флешку. Тогда восстановление займёт пару минут.

## Какие подводные камни есть у Secure Boot с GRUB?

### Обновление ядра

После pacman -Syu новый vmlinuz-linux приходит без подписи. Если не переподписать — загрузка упадёт с «Security Violation». sbctl решает это сам: файлы, подписанные с --save, переподписываются автоматически. Для shim-пути добавь pacman-хук, который после обновления ядра запускает sbsign заново. Ключи положи в /etc/efi-keys (MOK.key и MOK.crt), чтобы хук их находил. Пример хука в /etc/pacman.d/hooks/sign-kernel.hook:

```ini
[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = linux
Target = linux-lts

[Action]
Description = Signing kernel with MOK key
When = PostTransaction
Exec = /usr/bin/sbsign --key /etc/efi-keys/MOK.key --cert /etc/efi-keys/MOK.crt --output /boot/vmlinuz-linux /boot/vmlinuz-linux
```

Если у тебя несколько ядер (linux и linux-lts) — подписывай каждое. Для sbctl: `sbctl sign --save /boot/vmlinuz-linux-lts`.

Если после обновления GRUB не видит новое ядро — смотри «[GRUB не видит ядра после обновления](https://ordanax.github.io/grub-ne-vidit-yadra-posle-obnovleniya)».

### Модули Nvidia

Модули ядра Nvidia подписаны ключом из пакета nvidia. При включённом Secure Boot ядро откажется их загружать, пока ключ не попадёт в MokList:

```bash
sudo mokutil --import /usr/share/nvidia/nvidia-modsign-crt.der
```

Дальше — стандартная процедура с MokManager при перезагрузке. Ключ Nvidia вносится один раз — при обновлениях драйвера он не меняется, так что повторный импорт не нужен.

### Initramfs

С GRUB initramfs загружает сам GRUB, и прошивка её не проверяет. initramfs-linux.img — обычный файл, который GRUB читает с диска. Но если перейдёшь на прямую загрузку ядра (EFISTUB или UKI) — подписывать придётся весь образ целиком. Про разницу способов загрузки — в статье «[Смена загрузчика с GRUB на systemd-boot](https://ordanax.github.io/smena-zagruzchika-s-grub-na-systemd-boot)».

## Частые вопросы

### Нужно ли подписывать initramfs при загрузке через GRUB?

Нет. GRUB загружает initramfs сам, Secure Boot её не проверяет. Подпись нужна только для файлов, которые запускает прошивка: shim, GRUB и ядро при прямой загрузке. Если перейдёшь на UKI — initramfs вшивается в образ, и подписывается весь образ целиком.

### Что делать, если после обновления ядра появилась ошибка подписи?

Переподписать ядро. Для sbctl — `sbctl sign --save /boot/vmlinuz-linux`, для shim — sbsign с твоим ключом. Чтобы не повторять вручную, настрой pacman-хук. После этого перезагрузись — ошибка уйдёт.

### Чем MOK отличается от ключей Secure Boot?

Ключи Secure Boot (db, KEK, PK) хранятся в прошивке и управляются ею. MOK — твои ключи в NVRAM, которые проверяет shim. Прошивка их не знает, зато их можно добавлять и удалять без перепрошивки. Для sbctl MOK не нужен — sbctl работает напрямую с ключами прошивки.

### Можно ли просто отключить Secure Boot?

Можно, и многие так делают. Но тогда теряется защита от подмены загрузчика, ради которой Secure Boot и включают. Подпись через sbctl занимает десять минут — проще один раз настроить, чем потом ловить ошибки при загрузке с чужих носителей.

### Работает ли Secure Boot с видеодрайвером Nvidia?

Да, если внести ключ подписи модулей Nvidia в MokList. Без этого ядро не загрузит модули nvidia при включённом Secure Boot. Процедура та же: mokutil --import и подтверждение в MokManager при перезагрузке.

## Полезные ресурсы

- [Secure Boot — ArchWiki](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Security) — полная документация по Secure Boot, shim и MOK.
- [GRUB — ArchWiki](https://wiki.archlinux.org/title/GRUB) — установка и настройка GRUB, включая раздел про Secure Boot.

## Заключение

Secure Boot с GRUB настраивается за один вечер. Самый надёжный путь — sbctl: создал ключи, внёс в прошивку, подписал GRUB и ядро. Альтернатива — shim-signed с MokManager, если нужен ручной контроль над ключами. Главное после настройки — не забывать про переподпись после обновлений и про ключ Nvidia. Тогда Secure Boot работает тихо и не мешает.