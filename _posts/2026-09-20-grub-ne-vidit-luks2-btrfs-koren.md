---
layout: post
title: "GRUB не видит LUKS2-/btrfs-корень: принудительная настройка"
description: "GRUB не находит LUKS2-корень или btrfs-подтом: включи GRUB_ENABLE_CRYPTODISK, добавь модули luks2, lvm, btrfs и перегенерируй grub.cfg."
date: 2026-09-20 00:00:00 +0300
permalink: /grub-ne-vidit-luks2-btrfs-koren
categories:
  - linux
  - arch linux
  - configs
tags:
  - grub
  - luks2
  - btrfs
  - lvm
  - cryptodisk
  - encryption
edit: true
---

GRUB не видит LUKS2-корень или btrfs-подтом из-за нехватки модулей: в core image загрузчика нет cryptodisk, luks2, lvm и btrfs, а в параметрах ядра не указан корень. Включи `GRUB_ENABLE_CRYPTODISK=y` в `/etc/default/grub`, добавь модули в `grub-install`, пропиши `root=/dev/mapper/arch-root` и `rootflags=subvol=@`, перегенерируй `grub.cfg`. После этого загрузка заработает.

## Почему GRUB не видит зашифрованный корень

GRUB работает в два этапа. В ESP вшит компактный core image с базовыми модулями. Дальше загрузчик читает `/boot/grub/grub.cfg` и подгружает остальное. Если `/boot` лежит внутри LUKS2-контейнера, поверх которого развёрнуты LVM и btrfs, для чтения конфига нужны модули cryptodisk, luks2, lvm, btrfs и crypto. В core image по умолчанию их нет. Отсюда симптомы:

- `error: disk 'lvmid/...' not found`: `grub.cfg` ссылается на логический том по lvmid, но том недоступен. LUKS не разблокирован или модуль lvm не загружен.
- `error: unknown filesystem`: GRUB не распознал файловую систему на разделе.
- Зависание на чёрном экране сразу после выбора Arch в меню.

Важный момент: если `/boot` вынесен на отдельный незашифрованный раздел, GRUB справляется без всякого крипто. Проблема появляется только когда `/boot` находится внутри зашифрованного корня. Дальше речь только о таком варианте.

### Как понять, что /boot внутри LUKS

Посмотри на раскладку дисков:

```bash
lsblk -f
```

Цепочка выглядит так: раздел с типом `crypto_LUKS`, поверх него `lvm`, внутри логический том с `btrfs`. Если `/boot` не отдельный раздел, а каталог внутри этого тома, значит, GRUB обязан разблокировать LUKS до чтения конфига. Именно для этого нужен cryptodisk. Если же в выводе виден отдельный раздел с типом `vfat` или `ext4`, смонтированный в `/boot`, то вся настройка ниже не нужна: GRUB читает `/boot` напрямую.

## Как включить поддержку LUKS2 в GRUB

Открой `/etc/default/grub` и добавь строку:

```bash
GRUB_ENABLE_CRYPTODISK=y
```

Эта опция заставляет `grub-mkconfig` добавить в `grub.cfg` поиск зашифрованных дисков. Без неё GRUB даже не попытается разблокировать LUKS. После правки перегенерируй конфиг:

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

Пароль GRUB спросит ещё до появления меню, потому что сам `grub.cfg` лежит на зашифрованном диске. Это отдельный запрос, не путай его с запросом initramfs, который появится позже.

## Как указать корень и подтом btrfs в параметрах ядра

Мало разблокировать диск, ядру нужно сказать, где корень. Пропиши в `/etc/default/grub`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="root=/dev/mapper/arch-root rw"
```

Если корень на btrfs, добавь подтом и тип файловой системы:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="root=/dev/mapper/arch-root rw rootflags=subvol=@ rootfstype=btrfs"
```

Разбор параметров:

- `root=/dev/mapper/arch-root`: путь к логическому тому. `arch-root` значит группа томов `arch`, том `root`. Если имена другие, подставь свои. Раскладка из гайда [установка Arch с LVM](https://ordanax.github.io/ustanovka-arch-s-lvm) использует именно такие имена.
- `rootflags=subvol=@`: имя подтома, на который смонтирован корень. Посмотри строку для `/` в `/etc/fstab`, там будет `subvol=...`. Типовая раскладка подтомов описана в [установке Arch на btrfs со снимками](https://ordanax.github.io/ustanovka-arch-btrfs-snapshoty).
- `rootfstype=btrfs`: страховка, чтобы ядро не гадало по содержимому диска.

Вместо `/dev/mapper/arch-root` можно указать `root=UUID=<uuid логического тома>`. UUID показывает `lsblk -f` в строке тома. Такой вариант переживает переименование группы томов.

Параметры попадут в `grub.cfg` только после перегенерации:

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

## Как вшить модули luks2, lvm и btrfs в GRUB

Обычно `grub-install` сам определяет нужные модули через `grub-probe`. На зашифрованном btrfs он иногда промахивается. Тогда вшей модули принудительно:

```bash
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB --modules="btrfs cryptodisk luks2 lvm"
grub-mkconfig -o /boot/grub/grub.cfg
```

Флаг `--modules` добавляет модули прямо в core image, поэтому они доступны с самого старта. Он дополняет стандартный набор, а не заменяет его. После переустановки обязательно перегенерируй `grub.cfg`, иначе изменения не подхватятся.

Есть и второй способ: прописать модули в `/etc/default/grub`:

```bash
GRUB_PRELOAD_MODULES="btrfs cryptodisk luks2 lvm"
```

Эффект тот же, но модули подгружаются из `/boot/grub/x86_64-efi`, а не вшиваются в core image. Если ESP маленькая, этот вариант удобнее.

Проверь, что GRUB понимает твой `/boot`:

```bash
grub-probe --target=fs /boot
```

Команда должна вернуть `btrfs`. Ошибка значит, что GRUB не умеет читать эту файловую систему.

## Что делать, если initramfs не разблокирует диск

GRUB разблокировал LUKS и передал управление ядру. Дальше ядро должно снова разблокировать корень, теперь уже через initramfs. Если в initramfs нет нужных хуков, загрузка зависнет на этапе ожидания устройства.

Открой `/etc/mkinitcpio.conf`. Для systemd-стиля:

```bash
HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole sd-encrypt lvm2 filesystems fsck)
```

Для классического busybox:

```bash
HOOKS=(base udev autodetect microcode modconf kms keyboard keymap consolefont block encrypt lvm2 filesystems fsck)
```

`sd-encrypt` (или `encrypt`) разблокирует LUKS, `lvm2` активирует логические тома. Без них ядро не найдёт корень, даже если GRUB всё сделал правильно. Стили хуков не смешиваются: если в начале списка стоит `systemd`, используй `sd-encrypt`, если `udev` и `block`, тогда `encrypt`.

После правки пересобери образы:

```bash
mkinitcpio -P
```

Проверь, что хуки попали в образ:

```bash
lsinitcpio /boot/initramfs-linux.img | grep -E "sd-encrypt|lvm2"
```

Если строк нет, хуки не подключились, ищи опечатку в `HOOKS`.

## Как проверить разблокировку прямо из меню GRUB

Если система не грузится, а хочется понять, на каком этапе затык, зайди в командную строку GRUB. В меню нажми `c`. Дальше:

```bash
cryptomount -a
ls
```

`cryptomount -a` пробует разблокировать все зашифрованные диски и спросит пароль. `ls` покажет доступные устройства: `(crypto0)`, `(lv/arch/root)` и другие. Если после `cryptomount` том виден, модули на месте, а проблема в параметрах ядра или конфиге.

Для конкретного диска укажи его UUID:

```bash
cryptomount -u 1234abcd-5678-ef90-1234-5678abcdef90
```

UUID берётся из `lsblk -f` или `cryptsetup luksDump`.

Можно загрузиться вручную, не дожидаясь починки:

```bash
set root=(lv/arch/root)
linux /@/boot/vmlinuz-linux root=/dev/mapper/arch-root rw rootflags=subvol=@
initrd /@/boot/initramfs-linux.img
boot
```

Путь `/@/boot/...` верен, когда `/boot` лежит внутри подтома `@`. При другой раскладке подставь свой путь.

## Почему GRUB не принимает пароль от LUKS2 с Argon2

LUKS2 умеет вырабатывать ключ двумя алгоритмами: PBKDF2 и Argon2. Старые версии GRUB понимали только PBKDF2. Если пароль верный, а GRUB пишет `invalid passphrase`, проверь алгоритм:

```bash
cryptsetup luksDump /dev/nvme0n1p2
```

В секции Keyslots будет видно, какой PBKDF используется. Современный GRUB 2.12 поддерживает Argon2id, поэтому на свежем Arch проблема редкая. Версию загрузчика смотри так:

```bash
grub-install --version
```

При переносе системы на другое железо или в другую ОС имей в виду. Перевести ключ на PBKDF2 можно так:

```bash
cryptsetup luksConvertKey --pbkdf pbkdf2 /dev/nvme0n1p2
```

Команда спросит текущий пароль и перепишет ключ. Про управление ключами и keyfile подробнее в статье [смена паролей LUKS2 и keyfile](https://ordanax.github.io/luks2-keyfile-smena-parolei).

## Частые вопросы

### GRUB просит пароль дважды, это нормально?

Да. Первый запрос от GRUB: загрузчик разблокирует диск, чтобы прочитать `/boot`. Второй от initramfs: ядро монтирует корень. Два независимых механизма, оба обязательны при такой схеме. Убрать второй запрос можно, если вынести `/boot` на отдельный раздел, тогда cryptodisk GRUB не понадобится.

### Ошибка «disk lvmid/... not found»: что делать?

`grub.cfg` ссылается на логический том по lvmid, но на момент чтения конфига том недоступен. Причины две: LUKS не разблокирован или модуль lvm не загружен. Лечится `GRUB_ENABLE_CRYPTODISK=y` и переустановкой GRUB с модулями luks2 и lvm.

### Можно ли загружаться без GRUB, если корень зашифрован?

Да. systemd-boot умеет разблокировать LUKS2 через sd-encrypt, а ядро можно грузить напрямую через EFISTUB или UKI. Переход описан в статье [смена загрузчика с GRUB на systemd-boot](https://ordanax.github.io/smena-zagruzchika-s-grub-na-systemd-boot), а прямая загрузка ядра в [загрузке ядра через EFISTUB и UKI](https://ordanax.github.io/pryamaya-zagruzka-yadra-efistub-uki).

### Нужен ли отдельный /boot при зашифрованном корне?

Не обязателен. GRUB читает `/boot` внутри LUKS2+btrfs, если вшить модули. Но отдельный `/boot` упрощает жизнь: не нужен cryptodisk, нет двойного запроса пароля, проще чинить систему с live-USB. Минус один: обновления ядра требуют перегенерации `grub.cfg`, иначе новый образ не появится в меню.

### Как узнать имя подтома для rootflags?

Посмотри строку для `/` в `/etc/fstab`, там будет `subvol=...`. Либо выполни `btrfs subvolume list /` и найди подтом, смонтированный в корень.

## Полезные ресурсы

- [GRUB (ArchWiki)](https://wiki.archlinux.org/title/GRUB): установка и настройка загрузчика.
- [Dm-crypt/Encrypting an entire system (ArchWiki)](https://wiki.archlinux.org/title/Dm-crypt/Encrypting_an_entire_system): схемы шифрования всего диска.

## Заключение

GRUB не видит LUKS2-корень или btrfs-подтом из-за нехватки модулей и неправильных параметров ядра. Три шага решают проблему: `GRUB_ENABLE_CRYPTODISK=y` в `/etc/default/grub`, модули luks2, lvm и btrfs в `grub-install`, `root=/dev/mapper/arch-root` с `rootflags=subvol=@` в параметрах ядра. Не забудь перегенерировать `grub.cfg` после каждой правки и пересобрать initramfs с хуками sd-encrypt и lvm2. Если сомневаешься, где затык, проверь разблокировку через `cryptomount -a` прямо из меню GRUB.