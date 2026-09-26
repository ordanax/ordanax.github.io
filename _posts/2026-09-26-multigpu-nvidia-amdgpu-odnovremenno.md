---
layout: post
title: "МультиGPU: nvidia + amdgpu одновременно"
description: "Две карты NVIDIA и AMD в одной системе: amdgpu из ядра плюс nvidia-dkms, xorg.conf с BusID и PrimaryGPU, DRI_PRIME для PRIME, modeset в Wayland, чёрный экран."
date: 2026-09-26 00:00:00 +0300
permalink: /multigpu-nvidia-amdgpu-odnovremenno
categories:
  - linux
  - arch linux
  - nvidia
  - amdgpu
tags:
  - nvidia
  - amdgpu
  - prime
  - xorg
  - wayland
  - multi-gpu
edit: true
---

Две видеокарты от разных производителей в одной системе — рабочая схема, а не экзотика: amdgpu живёт в ядре, драйвер nvidia ставится снаружи, и модули не конфликтуют между собой. Конфликт живёт только в пользовательском стеке — в выборе OpenGL, EGL и Vulkan, и там всё решают PRIME плюс аккуратный xorg.conf. Ниже — настройка, в которой мониторы висят на разных картах, а приложение можно отправить на любую из них. Ты узнаешь, какие пакеты ставить, что писать в конфиг Xorg, чем Wayland отличается от X11 и куда смотреть, если одна из карт даёт чёрный экран.

## Что ставить, чтобы обе карты работали одновременно?

Драйвер amdgpu уже входит в ядро Arch (CONFIG_DRM_AMDGPU), его достаточно — отдельно ставить нечего. А вот для NVIDIA нужен внешний модуль, и тут есть выбор между nvidia из репозитория и nvidia-dkms: разница в том, пересобирается ли модуль под каждое новое ядро. Почему это важно и чем чреваты ошибки при сборке, разобрано в статье про [dkms и статическое ядро](https://ordanax.github.io/dkms-ili-staticheskoe-yadro).

```bash
sudo pacman -S nvidia-dkms nvidia-utils mesa libglvnd vulkan-icd-loader vulkan-radeon
sudo mkinitcpio -P
```

`nvidia-utils` даёт nvidia-smi, `mesa` обслуживает карту AMD, `vulkan-icd-loader` и два ICD-пакета нужны, чтобы Vulkan увидел обе карты. Для игр в Steam доустанови 32-битные аналоги. Хук dkms в `/etc/mkinitcpio.conf` сам пересоберёт модуль при обновлении ядра, вручную ничего запускать не нужно.

Проверь, что обе карты поднялись:

```bash
lsmod | grep -E 'nvidia|amdgpu'
lspci -Dnnk | grep -A3 -E 'VGA compatible controller|3D controller'
```

Модули не мешают друг другу: у nvidia своё DRM-устройство, у amdgpu своё, имена разные, в списке `/dev/dri/` обе карты живут как `card0` и `card1`. Дальше ты увидишь, где у этой схемы действительно есть узкие места.

## Как прописать две карты в xorg.conf?

Xorg по умолчанию пытается угадать обе карты сам, но с парой NVIDIA + AMD он часто ошибается: запускает сервер без консольного вывода или вешает оба экрана на одну карту. Лечится явным описанием устройств с адресом `BusID`.

Сначала узнай адреса:

```bash
lspci -Dnn | grep -E 'VGA compatible controller|3D controller'
```

```
0000:00:0.0 VGA compatible controller [0300]: Advanced Micro Devices [AMD/ATI] Raphael [1002:164e]
0000:01:0.0 VGA compatible controller [0300]: NVIDIA Corporation GA107 [GeForce RTX 3050] [10de:2520]
```

Xorg ждёт адрес в своём виде — `PCI:bus:device:function`, без домена `0000:`. Создай `/etc/X11/xorg.conf.d/10-gpu.conf`:

```
Section "ServerFlags"
    Option "AllowEmptyInitialConfiguration" "True"
    Option "AutoAddGPU" "off"
EndSection

Section "ServerLayout"
    Identifier "MultiGPU"
    PrimaryGPU "Nvidia0"
EndSection

Section "Device"
    Identifier "Nvidia0"
    Driver "nvidia"
    BusID "PCI:0:1:0"
EndSection

Section "Device"
    Identifier "Amd0"
    Driver "amdgpu"
    BusID "PCI:0:0:0"
EndSection
```

Разберём по строкам. `BusID` берётся из вывода `lspci` — здесь `0000:01:0.0` превращается в `PCI:0:1:0`. `PrimaryGPU` в секции `ServerLayout` выбирает, какая карта владеет консолью; старый `Option "BootDisplay"` в modern Xorg объявлен устаревшим и работает хуже. `AllowEmptyInitialConfiguration` нужен именно для смешанной схемы: если монитор подключён к карте, которая не станет primary, Xserver на старте не находит выхода и отказывается стартовать. `AutoAddGPU "off"` отключает автодетект, чтобы udev не подсунул лишнее устройство поверх твоих секций.

Два замечания по файлам. Установщик NVIDIA может создать свой сниппет `10-nvidia.conf` — если он тоже описывает Device, сведи обе схемы в одну, иначе секции передерутся. Утилиту `nvidia-xconfig` на такой машине лучше не запускать: она перезаписывает `/etc/X11/xorg.conf` целиком и выкидывает описание второй карты.

Про мониторы: дополнительных настроек не требуется. Каждая карта видит только свой кабель, так что в настройках рабочего стола они появятся отдельными пунктами, а `xrandr --listmonitors` покажет, кто что отдаёт.

## Как включить PRIME на смешанной паре?

PRIME работает и для пары NVIDIA + AMD — ограничение только в том, что рендерить можно на карте с выводом или на карте без вывода. Сначала посмотри, кого Xorg считаем первым:

```bash
xrandr --listproviders
```

Если первым идёт NVIDIA, а рисовать ты хочешь на AMD, скажи провайдеру, кто владеет выводом, чтобы тот рисовал:

```bash
xrandr --setprovideroutputsource 0 1
```

Первое число — провайдер-владелец вывода, второе — тот, который рисует. Если поменять карты местами, поменяй и числа: `xrandr --setprovideroutputsource 1 0` для обратного случая. Проверить, что получилось, можно так:

```bash
DRI_PRIME=1 glxinfo -B | grep -E 'OpenGL vendor|OpenGL renderer'
```

`DRI_PRIME` ждёт номера карт в порядке перечисления `lspci`, то есть 1 и 2, а не 0 и 1. На постоянной основе задай переменную в `/etc/environment` или в `~/.profile`, а для отдельных игр удобнее обёртка `prime-run` — как её настроить вместе со Steam, описано в статье о [гибридной графике и prime-run](https://ordanax.github.io/gibridnaya-grafika-prime-run-steam).

Vulkan на двух картах выбирается отдельно, именем ICD-файла:

```bash
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json vulkaninfo --summary
```

В новых версиях загрузчика та же задача решается переменной `VK_DRIVER_FILES`.

## Что меняется в Wayland?

Главное требование — включить modeset у nvidia_drm, иначе Wayland-композитор не сможет получить поверхности. Без этого на NVIDIA обычно чёрный экран, и разбор такой поломки с привязкой к параметрам modeset я делал в статье про [чёрный экран и nomodeset](https://ordanax.github.io/nvidia-chernyj-ekran-nomodeset).

```
# /etc/modprobe.d/nvidia.conf
options nvidia_drm modeset=1 fbdev=1
```

После правки пересобери initramfs (`sudo mkinitcpio -P`). Если встроенный экран проходит через карту NVIDIA ещё до загрузки системы, добавь модули в `/etc/mkinitcpio.conf` в строку `MODULES=`, иначе нужна будет секция `early KMS` — но на смешанной пате это обычно лишнее.

Дальше разница между окружениями. В Plasma выбор ускорителя живёт в «Настройки → Экран и видео → Композитное устройство»: на паре NVIDIA + AMD там обычно только NVIDIA и Automatic, а карта AMD и так дефолтная, так что вмешиваться не нужно. В GNOME выбора нет вообще — Mutter берёт DRM-устройство, определённое при установке драйвера, поэтому поменять дефолт проще через `PrimaryGPU` и перезагрузку, а не через переменные окружения. И в KDE, и в GNOME не лишний раз проверить, не уехало ли окно в XWayland: если в плазменных приложениях у тебя встроенный Wayland, а карта рисует через Xwayland, смена GPU не даст эффекта.

## Почему nvidia-smi не видит карту AMD?

Это нормально: nvidia-smi работает через NVML, который обращается только к картам NVIDIA, и про amdgpu он ничего не знает. Кто реально есть на машине, покажут `lspci -nnk` и `ls -l /dev/dri/`, а что рендерит конкретное приложение — `glxinfo -B` и `vulkaninfo --summary`. Ищи AMD в выводе Vulkan и OpenGL, а не в nvidia-smi.

## Что делать, если одна из карт даёт чёрный экран?

Сначала посмотри логи, а не переустанавливай драйвер:

```bash
journalctl -b | grep -Ei 'drm|nvidia|amdgpu|gbm' | tail -40
```

Дальше по порядку, чаще всего хватает первых двух шагов.

1. Сверь `BusID` в конфиге с выводом `lspci -Dnn` — опечатка в шине, устройстве или функции даёт пустой Xserver с сообщением про отсутствие устройств.
2. Сними modeset, если сломалось именно от его включения: `options nvidia_drm modeset=0` в `/etc/modprobe.d/nvidia.conf` плюс `mkinitcpio -P`. Это осознанный откат к рабочей конфигурации, а не попытка вылечить всё.
3. Отключи проблемную карту в X, оставив вторую: в её секции `Device` добавь `Option "Accel" "off"` и `Option "NoAccel" "True"`.
4. Проверь, что модуль пересобрался после последнего обновления ядра: `dkms status` и лог `/var/log/Xorg.0.log`. Разбор типовых ошибок в этом логе — в статье про [ошибки Xorg и NVIDIA](https://ordanax.github.io/oshibki-xorg-nvidia-smotrim-logi).

## Частые вопросы

**Нужно ли собирать nvidia-dkms вручную?** Нет, хук dkms в initramfs-конфиге делает это на каждом обновлении ядра. Ручная сборка нужна только в двух случаях: Secure Boot с самоподписанным ключом или нестандартное ядро без работающего хука.

**Можно ли поставить nvidia вместо amdgpu?** Нет, драйвера привязаны к Vendor ID: под NVIDIA нет проприетарного драйвера, под AMD нет проприетарного NVIDIA-драйвера. Ядро само подхватит правильный модуль по PCI ID, руками ничего назначать не нужно.

**Нужны ли разные версии Mesa для двух карт?** Нет, один Mesa обслуживает обе карты: AMD через `radeon` или `iris`, NVIDIA через glvnd-прослойку с проприетарной реализацией. Разъезжаются они только при неверном `__GLX_VENDOR_LIBRARY_NAME` или вручную прописанном `LibraryPath`.

**Сломается ли Wayland, если убрать modeset=1?** Да. Без DRM-устройства у nvidia композитор не получает буферы, и сессия либо не стартует, либо показывает чёрный экран. Для X11 отсутствие modeset допустимо, но в 2026 году это архаичный путь.

**Нужно ли что-то делать в UEFI?** Нет. Порядок опроса карт в UEFI не влияет на то, какая станет primary, — это целиком решает `PrimaryGPU` в xorg.conf.

## Полезные ресурсы

- [ArchWiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA) — установка, версии, PRIME, разбор типовых ошибок.
- [ArchWiki: Hybrid graphics](https://wiki.archlinux.org/title/Hybrid_graphics) — провайдеры, `DRI_PRIME`, секции `Device` и `ServerLayout`, переключение с карты на карту.

## Заключение

Схема nvidia + amdgpu работает без борьбы: модули ядра живут параллельно, а всю настройку берёт на себя пользовательский стек. Проверяй результат не словами в интерфейсе, а `glxinfo -B` и `vulkaninfo --summary` — они показывают реальный рендерер. Если сомневаешься, начни с явного xorg.conf и `PrimaryGPU`: почти все мутные симптомы оттуда.
