---
layout: post
title: "Как полностью удалить драйвер NVIDIA на Arch Linux"
description: "Пошаговое удаление драйвера NVIDIA в Arch: пакеты, модули ядра, initramfs, blacklist nouveau, конфиг Xorg и проверка отката на nouveau."
date: 2026-09-26 12:00:00 +0300
permalink: /polnoe-udalenie-drajvera-nvidia
categories:
  - linux
  - arch linux
  - nvidia
tags:
  - nvidia
  - nouveau
  - pacman
  - xorg
  - arch linux
edit: true
---

Снести драйвер NVIDIA в Arch проще, чем кажется: `pacman -Rsn` снимает пакеты, `rm` убирает модуль из `/usr/lib/modules/*/updates/`, `mkinitcpio -P` пересобирает initramfs, а удалённый `/etc/modprobe.d/nvidia.conf` возвращает nouveau в blacklist-чистую среду. Пропустишь хотя бы один шаг — получишь чёрный экран или карту, которая грузится вообще без 3D. Разбираю полный порядок, чтобы откат занимал минут десять и заканчивался рабочим nouveau.

## Когда нужно полностью удалять драйвер NVIDIA?

Полное удаление нужно в трёх случаях. Первый — драйвер или ядро ломают систему: после `pacman -Syu` не совпадает версия модуля с новым ядром, графика не поднимается, а tty с `nomodeset` остаётся единственным входом. Второй — переход на другую видеокарту: nouveau, AMD через `amdgpu` или Intel через `i915`, где проприетарный модуль в списке загрузки только мешает. Третий — карта уезжает на продажу или в другую машину, и держать на диске модули под неё незачем.

До сноса стоит убедиться, что проблема не лечится точечно. Если драйвер работает, а сломалось только разрешение или звук по HDMI, чинить нужно HDMI, а не драйвер — иначе потеряешь рабочее 3D на ровном месте. Отдельный случай — карта, на которой свежий драйвер уже не запускается и ты держишься за старую ветку: про legacy-версии 340-390 на новом ядре я писал [отдельно](https://ordanax.github.io/legacy-nvidia-340-390-na-novom-yadre). Там решение — точечный откат версии, а не демонтаж.

Полезно заранее посмотреть, какая версия драйвера соответствует твоему ядру: [эта статья](https://ordanax.github.io/nvidia-drayver-na-arch-linux) пригодится и для обратного возврата. А чтобы понять, грузится ли проприетарный модуль вообще, проверь `lspci -k | grep -A2 'VGA compatible controller'` — строка `Kernel driver in use: nvidia` означает, что активен именно он.

## Какие пакеты удалять, а какие оставить?

Сначала инвентаризация — смотри, что вообще стоит:

```bash
pacman -Q | grep -E 'nvidia|libglvnd'
pacman -Qs nvidia | grep -E '^nvidia|^libnvidia'
```

Целить нужно в этот набор: `nvidia` (userspace-библиотеки и модуль под конкретное ядро), `nvidia-dkms` (то же, но через DKMS — модуль пересобирается при установке нового ядра), `nvidia-open` (открытый модуль для Turing и новее; он ставится вместо `nvidia`, а не вместе с ним), `nvidia-utils` (`nvidia-smi`, `nvidia-settings`, утилиты конфигурации) и `nvidia-settings` — GUI. Иногда в списке есть ещё `nvidia-vdpauinfo` и `lib32-nvidia-*`; их сносит pacman по зависимостям вместе с `nvidia`, отдельно трогать не нужно.

Не трогай `mesa`, `lib32-mesa`, `mesa-vanilla-drivers` и любые vulkan-пакеты. Они не принадлежат NVIDIA: именно из них nouveau берёт 3D-ускорение, и после удаления проприетарного драйвера они остаются единственным графическим стеком. Снеси mesa — получишь систему без 3D вообще, и никакого nouveau взамен не появится.

Порядок важен из-за конфликта `nvidia-utils` с GL-стеком mesa. Пакет тянет за собой libGL/EGL/Vulkan-библиотеки NVIDIA, которые не уживаются с `mesa-libgl`, и pacman при неверной последовательности ругается на конфликт либо оставляет mesa в удалённом состоянии. Сначала производные, потом утилиты, потом модуль:

```bash
sudo pacman -Rsn nvidia-settings
sudo pacman -Rsn nvidia-utils
sudo pacman -Rsn nvidia nvidia-dkms
```

Строки можно объединить в один вызов — pacman разберёт зависимости сам. Но списком нужных пакетов универсальнее, потому что не спотыкается об отсутствующий `nvidia-dkms` или `nvidia-open`:

```bash
sudo pacman -Rsn $(pacman -Qq | grep -E '^nvidia|^lib32-nvidia')
```

## Как убрать модуль ядра и пересобрать initramfs?

`pacman -Rsn` удаляет модуль не всегда: uninstall-скрипт может не отработать при сбое, при ручной установке через `.run`-файл файлы остаются, а после смены ядра в дереве `/usr/lib/modules` копятся осиротевшие копии. Проверь:

```bash
ls -l /usr/lib/modules/$(uname -r)/updates/ | grep nvidia
```

Если `nvidia.ko`, `nvidia-drm.ko`, `nvidia-modeset.ko` или `nvidia-uvm.ko` на месте — сноси их:

```bash
sudo rm -f /usr/lib/modules/*/updates/nvidia*
```

Флаг `-P` у `mkinitcpio` пересобирает initramfs для всех ядер в `/boot`, а не только для текущего. Пропустишь этот шаг — старый модуль продолжит ехать в ramdisk и ускорение старта. После любой правки modprobe-конфигов повторяй сборку:

```bash
sudo mkinitcpio -P
```

Контроль после сборки:

```bash
modinfo -F version nvidia
```

Ответ `modinfo: ERROR: Module nvidia not found` означает, что в дереве модулей текущего ядра NVIDIA больше нет.

## Почему после удаления не загружается nouveau?

Драйвер nvidia при установке создаёт `/etc/modprobe.d/nvidia.conf` с blacklist nouveau. Пока файл на месте, nouveau не загрузится никогда — даже при полностью снесённом проприетарном модуле, потому что запрет действует на уровне modprobe, а не на уровне пакетов.

```bash
ls /etc/modprobe.d/
sudo rm -f /etc/modprobe.d/nvidia.conf
```

Проверь ещё три места, где nouveau может быть заблокирован:

```bash
grep -R nouveau /etc/modprobe.d/
grep -n 'nouveau\|nvidia' /etc/mkinitcpio.conf
grep -n 'rd.driver.blacklist\|nouveau' /etc/default/grub
```

Строку `MODULES=(nouveau)` в `/etc/mkinitcpio.conf` нужно убрать: это включение nouveau в initramfs, а не то, что требуется для обычной загрузки. Если в `/etc/default/grub` указан `rd.driver.blacklist=nouveau`, правь `GRUB_CMDLINE_LINUX_DEFAULT` и пересобери конфиг загрузчика: `grub-mkconfig -o /boot/grub/grub.cfg`. Если система грузится через systemd-boot, правь соответствующий файл в `/boot/loader/entries/`.

Когда графика не поднимается, а tty доступен, выход — загрузка с `nomodeset`; [как это сделать и как вернуть параметр обратно](https://ordanax.github.io/nvidia-chernyj-ekran-nomodeset), разбирал в отдельной статье.

## Что удалить из конфигурации Xorg?

`nvidia-xconfig` при установке драйвера генерирует собственный фрагмент конфига, и он остаётся лежать после удаления пакетов:

```bash
ls /etc/X11/xorg.conf.d/
sudo rm -f /etc/X11/xorg.conf.d/20-nvidia.conf
```

Файл с блоком `Section "Device"` и строкой `Driver "nvidia"` заставляет Xorg искать проприетарный модуль. Если он остался, сервер не переключится ни на modesetting с nouveau, ни на `amdgpu`/`i915`, а в логе появится `Failed to load module "nvidia"`. В некоторых установках рядом лежит `10-nvidia.conf` — его тоже снеси.

Основной `/etc/X11/xorg.conf` трогать не нужно: в свежих системах его вообще нет, а Xorg отлично работает в режиме modesetting с nouveau. Косметику от прошлой конфигурации — prime-run обёртки и переменные в `~/.config/environment.d` — можно удалить попутно, на работоспособность это не влияет.

## Как проверить, что драйвер удалён полностью?

Пять проверок после перезагрузки:

```bash
lsmod | grep nvidia
lspci -k | grep -A3 'VGA compatible controller'
glxinfo -B | grep -Ei 'vendor|renderer'
which nvidia-smi
pacman -Q | grep -E 'nvidia|libglvnd'
```

Что ожидаемо:

- `lsmod | grep nvidia` — пусто. Непустой вывод означает, что модуль где-то остался.
- `lspci -k` — в строке `Kernel driver in use` стоит `nouveau`, либо `amdgpu`/`i915`, если карта сменилась.
- `glxinfo -B` — `vendor: mesa` и renderer со словом `nouveau`. Если утилиты нет, поставь пакет: `sudo pacman -S mesa-utils`.
- `which nvidia-smi` — пусто, команда не найдена.
- `pacman -Q` — остались только `libglvnd` и mesa-пакеты, ни одного `nvidia*`.

## Как откатиться на nouveau, если карта старая?

Отдельного пакета «nouveau» в Arch нет. 3D-ускорение берётся из mesa: модуль ядра `nouveau` загружается штатно, а userspace-часть — это `nouveau_dri.so` из пакета `mesa` вместе с `libGL` и `libEGL`. Xorg в режиме modesetting или Wayland-композитор подхватывают её автоматически, ручная настройка не нужна.

Сценарий после перезагрузки простой: `lsmod | grep nouveau` показывает модуль, `glxinfo -B` показывает renderer nouveau. Дальше сравнивай ощущения с проприетарным драйвером — на бюджетных картах разница в играх обычно заметна, на рабочем столе с видео почти незаметна.

Если после перезагрузки nouveau не загрузился или карта настолько старая, что KMS на ней не заводится, система покажет чёрный экран. Тогда загрузись с `nomodeset` и сними диагностику:

```bash
dmesg | grep -i nouveau
```

Нет сообщений про nouveau — блокировка в modprobe или initramfs, возвращайся к предыдущим разделам. Сообщения есть, а картинки нет — это ограничение железа: на части карт про Nvidia рабочий KMS отсутствует, и остаётся только базовый framebuffer. Дальше решай по ситуации: смириться с nouveau без 3D, попробовать параметр ядра `nouveau_modeset=0`, собрать более свежий `nouveau-dkms` из AUR или поменять карту на ту, которую nouveau понимает по-настоящему.

## Частые вопросы

### Нужно ли удалять mesa и lib32-mesa?

Нет. Это главная ошибка при сносе драйвера. Mesa обслуживает nouveau, встроенную графику Intel и AMD, а также Vulkan на встроенных картах. После удаления NVIDIA mesa становится основным графическим стеком, а не мусором. Удаляй только пакеты, в имени которых есть `nvidia`.

### Что делать, если pacman ругается при удалении?

Почти всегда виноват порядок: конфликт `nvidia-utils` с GL-библиотеками mesa. Удаляй пакетами по одному — сначала `nvidia-settings`, потом `nvidia-utils`, потом `nvidia` или `nvidia-dkms`. Если mesa осталась в странном состоянии, проверь целостность файлов командой `pacman -Qkk mesa` и переустанови пакет, если найдутся расхождения.

### Как вернуть драйвер NVIDIA обратно?

Убедись, что `/etc/modprobe.d/nvidia.conf` удалён и nouveau больше не заблокирован, затем поставь версию драйвера, подходящую твоему ядру, через `pacman -S`. Подбор версии описан в статье про драйвер NVIDIA на Arch Linux, а порядок проверки совпадения модуля с ядром — в разделах выше. Если карта старая, сначала прочитай про ветку 340-390, иначе новая версия просто не заведётся.

### Нужно ли удалять libglvnd?

Нет, если он остался в системе. `libglvnd` — это прослойка выбора GL-вендора, её использует в том числе mesa. Удалять имеет смысл только пакеты, которые ставились вместе с проприетарным драйвером.

## Полезные ресурсы

- [NVIDIA (ArchWiki), раздел Uninstallation](https://wiki.archlinux.org/title/NVIDIA#Uninstallation) — официальная процедура сноса, включая проверку зависимостей.
- [Nouveau (ArchWiki)](https://wiki.archlinux.org/title/Nouveau) — параметры ядра, известные ограничения и способы диагностики.

## Заключение

Полное удаление драйвера NVIDIA в Arch — это четыре слоя: пакеты pacman, модули в `/usr/lib/modules/*/updates/`, initramfs и конфигурация modprobe вместе с Xorg. Пройди их по порядку, перезагрузись и проверь себя через `lsmod`, `lspci -k` и `glxinfo -B`. Если всё сходится на nouveau — mesa на месте, карта работает, а лишних файлов от NVIDIA в системе не осталось.
