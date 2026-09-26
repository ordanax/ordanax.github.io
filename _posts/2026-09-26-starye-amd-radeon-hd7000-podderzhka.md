---
layout: post
title: "Старые AMD Radeon в 2026 году: radeon или amdgpu?"
description: "Что реально работает на AMD Radeon HD 7000 и ниже: radeon против amdgpu, граница GCN1 и TeraScale, Vulkan RADV, VA-API, Wayland и проверки."
date: 2026-09-26 00:00:00 +0300
permalink: /starye-amd-radeon-hd7000-podderzhka
categories:
  - linux
  - arch linux
  - hardware
tags:
  - radeon
  - amdgpu
  - radv
  - mesa
  - tera-scale
edit: true
---

Если у тебя в корпусе AMD Radeon из поколения 2011–2013 годов, менять карту прямо сейчас не обязательно: под Linux она работает, просто на разных уровнях. HD 7950, R9 270X, R7 265 — это GCN1 и GCN2, они сидят на amdgpu и получают полноценный OpenGL 4.5, Vulkan и VA-API. А вот HD 4000, HD 5000 и HD 6000 — это TeraScale, и там остаётся только драйвер radeon с потолком OpenGL 3.3 и без Vulkan вообще. Где именно проходит эта граница, какой драйвер выбрать и стоит ли экспериментировать — разбираю ниже.

## Какие Radeon считать старыми и где проходит граница?

Под «старыми» удобно понимать всё, что старше GCN3, и разбить это на два лагеря с разными судьбами.

**TeraScale** (ядро r600): RV670 и RV780 из серий HD 2000/3000, а также Evergreen — HD 4000 (RV730), HD 5000 и HD 6000 (Cedar, Redwood, Juniper, Cypress, Hemlock). Эти чипы проектировались для DirectX 9 и 10.1, и Linux-сообщество для них так и не сделало OpenGL 4.

**GCN1 (Southern Islands)** — HD 7750/7770/7850/7950/7970, R7 250, R9 270 и 270X, HD 6970/6970M. **GCN2 (Sea Islands)** — R7 265, R9 280/280X, R9 290/290X, HD 7790, R7 360X, R9 360X. Это уже GCN: DirectX 11, OpenGL 4.5, нормальный VA-API и Vulkan.

Ориентир по названию: R9 380/380X и выше — уже GCN3 (Tonga), там amdgpu работает без штрихов. То есть граница проходит между R9 360X и R9 380X. Точную архитектуру покажет device ID:

```bash
lspci -nn | grep -Ei 'vga|3d controller|display controller'
```

Из найденного ID (например, `1002:67df` — Turks/HD 7970, `1002:67b0` — Bonaire/R7 260) уже видно семейство. Универсальный признак: если модель называется R7 2xx, R9 2xx или HD 6xxx/7xxx — это GCN1/2.

## Какой драйвер выбрать: radeon, amdgpu или nouveau?

Правило простое и жёсткое. GCN1 и GCN2 — только amdgpu, он в ядре с 4.2 и с тех пор идёт драйвером по умолчанию. TeraScale — только radeon, потому что amdgpu на этих чипах официально не поддерживается: архитектура dGPU не та и стек регистров другой. nouveau остаётся запасным вариантом на случай сломанной системы: с ним хуже и X11, и видео-декодирование.

Проверяем, что реально загрузилось:

```bash
lspci -nnk | grep -A3 -Ei 'vga|3d controller|display controller'
dmesg | grep -iE 'amdgpu|radeon|drm' | tail -20
```

Для amdgpu в выводе dmesg будет строка вида `amdgpu 0000:01:00.0: [drm] card0: ...`, для TeraScale — `radeon 0000:01:00.0: [drm]`. Разница между этими драйверами подробно разобрана в статье про [AMD APU, Radeon и amdgpu](https://ordanax.github.io/amd-apu-radeon-ili-amdgpu) — начни с неё, если только что поставил систему.

Отдельный подводный камень: amdgpu при инициализации дисплея требует, чтобы в BIOS карты был UEFI-модуль GOP. Если после переключения на amdgpu на GCN1 получаешь чёрный экран, дело почти наверняка в прошивке — разбор этого случая в материале про [amdgpu и поломки после linux-firmware](https://ordanax.github.io/amdgpu-polomki-posle-linux-firmware).

## Что делать, если хочется amdgpu на TeraScale?

### Эксперимент с si_support

В ядре есть код поддержки SI (Northern Islands) и CIK (часть мобильных Southern Islands), который включается вручную:

```bash
echo 'options radeon si_support=0' | sudo tee /etc/modprobe.d/radeon.conf
echo 'options amdgpu si_support=1' | sudo tee /etc/modprobe.d/amdgpu.conf
sudo mkinitcpio -P
```

После перезагрузки проверяй `dmesg | grep -i amdgpu`. И сразу считай плюсы и минусы: **плюсов почти нет**. TeraScale и под radeon, и под amdgpu рисует один и тот же драйвер r600 с OpenGL 3.3, Vulkan не появляется ни в одном из двух случаев, VA-API не появляется тоже. **Минусы настоящие**: DPM там кривой, карта греется сильнее, хуже видеодекодирование, а в части случаев инициализация дисплея вообще не проходит. Разве что любопытство, не более того.

### ppfeaturemask и dpm на GCN1/GCN2

А вот тут трюки реально помогают. Типичные симптомы на GCN1: зависание в 3D, чёрный экран при загрузке, сбой при переходе между частотами. Лечится отключением проблемных блоков и динамического управления частотами:

```bash
echo 'options amdgpu dpm=0 ppfeaturemask=0xfff7ffff gpu_recovery=1' | sudo tee /etc/modprobe.d/amdgpu.conf
```

`ppfeaturemask=0xfff7ffff` выключает биты функций, на которых карта сыпется, `dpm=0` запрещает переключение состояний питания, `gpu_recovery=1` позволяет драйверу перезагрузить GPU вместо полного зависания. Маска подбирается экспериментально. Если проблема с изображениями на втором мониторе, добавляй `dc=0`.

### Mesa, LLVM и radeonsi

`mesa` в Arch обновляется вместе с ядром и даёт нужный OpenGL: radeonsi на GCN1/2 выдаёт 4.5, r600 на TeraScale остаётся на 3.3. Ломается это только если Mesa собрана без поддержки r600 — тогда в `glxinfo -B` вместо карты появится llvmpipe. Второй момент — LLVM: слишком свежая версия иногда ломает компиляцию шейдеров для r600, и тогда помогает откат версии Mesa.

## Какой Vulkan и OpenGL ты получишь?

RADV работает только поверх amdgpu и только начиная с GCN1. То есть на TeraScale его нет вообще, а на GCN1/2 он полноценен: gfx8 и gfx9, RADV_PERFTEST, компилятор ACO. Настройку пакетов, проверку того, какой драйвер реально подхватился, и тюнинг шейдеров я разбирал в статье про [AMDGPU-Vulkan и Mesa](https://ordanax.github.io/nastrojka-amdgpu-vulkan-mesa-dlya-igr).

Ловушка на TeraScale выглядит так: ты ставишь `vulkan-tools`, запускаешь `vulkaninfo --summary` и видишь устройство. Оно есть, но оно программное — lavapipe на CPU. Аппаратной поддержки нет и не появится: игра на lavapipe либо не запустится, либо пойдёт считать на процессоре.

```bash
sudo pacman -S vulkan-tools
vulkaninfo --summary
```

Смотри на два поля: `deviceType` должен быть `DISCRETE_GPU`, а `driverName` — `radeon` (это RADV). Значения `CPU` и `llvmpipe` означают, что Vulkan у тебя нет даже в виде картинки.

С OpenGL картина честнее: 4.5 на GCN1/2 — игры 2012–2015 годов идут нормально, 3.3 на TeraScale — только старые проекты, плюс у r600 нет 16-битных текстур, на которых ломается часть движков даже при формальной совместимости. OpenCL на TeraScale отсутствует полностью: Clover вырезали из Mesa ещё в 2020 году, остаётся только программный pocl. На GCN1/2 OpenCL даёт rusticl из Mesa, но ему нужны пользовательские библиотеки ROCm — без них `clinfo` покажет только cpu.

## А как дела с видео и Wayland?

С видео у двух лагерей разный уровень. TeraScale под radeon отдаёт только VDPAU — это отличное декодирование, но API для него отдельное, и VA-API поверх VDPAU моста в Mesa не существует. Проверить и использовать можно так:

```bash
vdpauinfo
mpv --hwdec=vdpau ~/video.mkv
ffmpeg -hwaccel vdpau -i ~/video.mkv -f null -
```

На GCN1/2 с amdgpu доступен VA-API, и для Firefox, mpv и браузерного видео он удобнее:

```bash
mpv --hwdec=vaapi ~/video.mkv
```

VA-API появился в Mesa только недавно, поэтому в некоторых версиях его ещё нет — тогда откатывайся на VDPAU, amdgpu для GCN этот интерфейс тоже умеет. Кодекы ограничены возрастом карты: H.264, MPEG-2, VC-1, в лучшем случае VP9, никакого AV1.

С Wayland на TeraScale всё заметно хуже: VA-API нет, поэтому скринкасты в Firefox и HDR в mpv не работают, атомарный modesetting поддержан не везде, и в играх идёт Xwayland. Практический совет — оставаться на Xorg. На GCN1/2 Wayland работает нормально, и если нужна VA-API для Firefox, это лучшее время переехать.

## Как проверить, что карта жива и какой у неё уровень?

Порядок проверок простой, начинай с драйвера и заканчивай реальной нагрузкой:

```bash
# 1. Какой драйвер загрузился
lspci -nnk | grep -A3 -Ei 'vga|3d controller|display controller'
dmesg | grep -iE 'amdgpu|radeon|drm|gpu_recovery' | tail -20

# 2. OpenGL: имя карты и версия
sudo pacman -S mesa-utils glmark2
glxinfo -B | grep -E 'OpenGL renderer|renderer string|core profile version'

# 3. Vulkan
vulkaninfo --summary

# 4. Видео: оба интерфейса сразу
vdpauinfo
mpv --hwdec=auto ~/video.mkv

# 5. Температура и энергопотребление
sensors
sudo amdgpu_top -d          # для amdgpu
sudo radeontop -d          # для radeon
```

Если в `glxinfo -B` ты видишь llvmpipe, значит 3D-ускорение не заработало. Проверяй `lsmod | grep -E 'radeon|amdgpu'`, смотри Xorg-лог командой `grep -iE 'drm|glx' /var/log/Xorg.0.log | tail -30` и убедись, что в `dmesg` нет failed to init. Типичная причина — nouveau вместо radeon на TeraScale.

## Почему radeon греется и гудит, и что с этим делать?

Драйвер radeon по умолчанию не бережёт старую карту: без динамического управления питанием она сидит на максимальных частотах, греется и раскручивает вентилятор на максимум, а оттуда гул и свист. Включаем DPM:

```bash
echo 'options radeon dynpm=1 dpm=1' | sudo tee /etc/modprobe.d/radeon.conf
sudo mkinitcpio -P
```

После перезагрузки появляется возможность принудительно опустить карту:

```bash
echo low | sudo tee /sys/class/drm/card0/device/pp_dpm_performance_level
watch -n1 'cat /sys/class/drm/card0/device/pp_dpm_state'
```

Для amdgpu всё проще — есть готовые профили питания от 0 (battery) до 2 (performance):

```bash
echo 0 | sudo tee /sys/class/drm/card0/device/power_dpm_state
```

Если температура всё равно выше 80 градусов, дело уже не в драйвере. Эти карты 2011–2013 годов стоят с пыльными радиаторами и высохшей термопастой: чистка, замена пасты и проверка вентилятора дают больше, чем настройки ядра. Ограничить аппетит можно утилитой AMDOverdrive, если она ещё работает с твоей картой.

## Частые вопросы

### Как понять, GCN у меня или TeraScale?

По таблице моделей: R7 2xx, R9 2xx, HD 6xxx и 7xxx — это GCN1/2, драйвер amdgpu. HD 4xxx, 5xxx и 6xxx с буквами HD — TeraScale, драйвер radeon. Если сомневаешься, смотри device ID через `lspci -nn` и строку OpenGL renderer в `glxinfo -B`: на TeraScale в имени карты стоит Turks/Cypress/Barts/BarTS.

### Почему после переключения radeon на amdgpu чёрный экран?

Нет UEFI-модуля GOP в BIOS карты. Проверяй `dmesg | grep -i firmware` — amdgpu пишет про failed to load firmware. Лечится прошивкой либо возвратом к radeon, и для TeraScale второй путь всё равно единственный рабочий.

### Можно ли на TeraScale запустить Vulkan-игру?

Аппаратно — нет. lavapipe из состава Mesa работает через процессор, и на игре ты получишь 1–5 кадров в секунду. Смысл в Vulkan-стеке на TeraScale есть только у редакторов и утилит, которым достаточно программного рендера.

### В radeontop карта молчит, состояние не меняется

Скорее всего, DPM выключен. При `dynpm=1` в sysfs появляется `pp_dpm_state` с состояниями low, middle, high, default, и radeontop начинает их показывать. Проверь `ls /sys/class/drm/card0/device/ | grep pp_dpm`.

### Стоит ли ставить amdgpu на HD 6000?

Не стоит. Уровень OpenGL не изменится, Vulkan не появится, VA-API не появится, а риск получить нестабильную карту с перегревом вместо десктопа — артефакты. Radeon на 4000/5000/6000 в связке с Xorg и VDPAU — куда разумнее.

## Полезные ресурсы

- [AMDGPU — ArchWiki](https://wiki.archlinux.org/title/AMDGPU) — таблица поддерживаемых чипов, параметры модуля, версии и GCN-специфика.
- [Radeon — ArchWiki](https://wiki.archlinux.org/title/Radeon) — всё про драйвер radeon на TeraScale: sysfs, DPM, VDPAU, X11.

## Заключение

Старые Radeon под Linux не мертвы, но живут по разным законам. GCN1 и GCN2 дают почти всё, что нужно, на amdgpu: OpenGL 4.5, Vulkan, VA-API и нормальный Wayland, а dpm=0 и ppfeaturemask чинят самые частые болячки. TeraScale — это radeon, Xorg, OpenGL 3.3 и VDPAU: зато стабильно и холоднее, а Vulkan там не появится ни при каком раскладе. Для офиса, браузера с аппаратным видео и рабочего стола связка radeon + VDPAU закрывает задачу, а вот для игр даже на GCN1 пора менять карту.
