---
layout: post
title: "Температуры и частоты GPU в /sys/class/drm"
description: "Где драйвер отдаёт температуру, частоты и мощность GPU, как читать /sys/class/drm/cardN/device и как ограничить аппетит видеокарты средствами sysfs."
date: 2026-09-26 00:00:00 +0300
permalink: /temperatura-chastota-sys-class-drm
categories:
  - linux
  - arch linux
  - gpu
  - overclocking
tags:
  - drm
  - amdgpu
  - sysfs
  - hwmon
  - power-management
edit: true
---

Температуру ядра, реальную частоту и загрузку видеокарты в Linux можно посмотреть без единой сторонней программы: драйвер выкладывает телеметрию обычными файлами в `/sys/class/drm/cardN/device/`. Через `cat` ты получишь текущие значения, а через `power_dpm_force_performance_level` или `pp_power_profile_mode` заставишь карту работать тише. Разберём, что лежит в этих каталогах у amdgpu и i915, как ограничить частоты и как закрепить профиль при загрузке.

## Где драйвер отдаёт телеметрию?

`/sys/class/drm/` — class-каталог подсистемы DRM. Каждый видеодрайвер создаёт там карточку `card0`, `card1` и интерфейс рендеринга `renderD128`. Сам каталог `cardN` почти пустой, поэтому всё интересное лежит по симлинку `device/`, который указывает на PCI-устройство:

```bash
ls /sys/class/drm/
ls -l /sys/class/drm/card0/device/
```

У amdgpu температуры и энергия лежат в hwmon, частота ядра и памяти — в списках `pp_dpm_sclk` и `pp_dpm_mclk`, где текущая строка помечена звёздочкой, а загрузка и видеопамять — в `gpu_busy_percent` и `mem_info_vram_used`. У i915 скуднее: `hwmon/hwmon*/temp1_input` есть, а частоты ядра лежат не в `device/`, а уровнем выше — `gt_cur_freq_mhz` и `gt_max_freq_mhz`. Проприетарный NVIDIA телеметрию в sysfs не отдаёт вообще, только через `nvidia-smi`, поэтому про вентиляторы и лимиты — отдельная история про [coolbits и перегрев](https://ordanax.github.io/nvidia-peregrev-ventilyatory-coolbits).

## Как прочитать температуру и частоты?

Температура записана в миллинградусах, поэтому дели на 1000:

```bash
cat /sys/class/drm/card0/device/hwmon/hwmon*/temp1_input
awk '{printf "%.1f °C\n", $1/1000}' /sys/class/drm/card0/device/hwmon/hwmon*/temp1_input
cat /sys/class/drm/card0/device/hwmon/hwmon*/temp1_crit
```

Рядом лежат `temp1_max` и `temp1_label` — метка подсказывает, это датчик кристалла, памяти или горячей точки.

Частоты и загрузка:

```bash
cat /sys/class/drm/card0/device/pp_dpm_sclk
cat /sys/class/drm/card0/device/gpu_busy_percent
cat /sys/class/drm/card0/device/mem_info_vram_used
```

Значения удобно свернуть в одну строку и обновлять её на лету:

```bash
D=/sys/class/drm/card0/device
watch -n1 "awk '{printf \"%.1f C, GPU %s%%, VRAM %d MB\\n\", \$1/1000, \"\$(cat $D/gpu_busy_percent)\", \"\$(cat $D/mem_info_vram_used/1048576)\"}' $D/hwmon/hwmon*/temp1_input"
```

Для наблюдения в реальном времени хватает `watch` без всяких демонов:

```bash
watch -n1 'cat /sys/class/drm/card0/device/gpu_busy_percent; cat /sys/class/drm/card0/device/hwmon/hwmon*/temp1_input'
```

Если поставишь `lm_sensors`, то hwmon подхватится сам и температуры покажутся в привычном виде вместе с процессорами и вентиляторами:

```bash
sudo pacman -S lm_sensors
sudo sensors-detect
sensors
```

Учти, что `sensors` печатает температуру в градусах, а `sensors -u` — в микро градусах, то есть в тысячу раз больше, чем цифра в `temp1_input`. Полезная привычка: сначала посмотреть сырые файлы и только потом искать причину, если значение кажется странным.

Для игр удобнее оверлей: как настроить MangoHud поверх Vulkan, разбирал в статье про [слой и MangoHud](https://ordanax.github.io/vulkan-sloi-lakt-mangohud). А для терминала есть `radeontop` (запусти с `radeontop -d 1`, покажет частоту, температуру и занятость VRAM) и `nvtop` для карт NVIDIA.

## Почему часть файлов пропадает?

Набор файлов зависит от драйвера, и это нормально. У встроенной графики Ryzen есть только hwmon с температурой и энергией: никаких `pp_dpm_sclk`, `ppfeaturemask` и `power_dpm_force_performance_level` там не будет, частоту ядра iGPU задают через `gt_max_freq_mhz`. У карт AMD разных поколений отличается поддержка OverDrive, у Intel свой набор файлов, у NVIDIA — ноль sysfs-интерфейсов.

Перед записью всегда делай `ls` и проверяй, что файл вообще есть, а перед первой записью — что у тебя root. На ноутбуках с гибридной графикой в `card0` может оказаться встроенная карта, а дискретная получит `card1`:

```bash
lspci -nnk | grep -A3 'VGA compatible controller'
cat /sys/class/drm/card0/device/uevent
```

## Как ограничить частоты и потребление на amdgpu?

Самый грубый и самый надёжный переключатель — `power_dpm_force_performance_level`:

```bash
cat /sys/class/drm/card0/device/power_dpm_force_performance_level
echo low  | sudo tee /sys/class/drm/card0/device/power_dpm_force_performance_level
echo auto | sudo tee /sys/class/drm/card0/device/power_dpm_force_performance_level
```

Допустимые значения — строки `auto`, `low`, `high` и `manual`. `low` прижимает карту к самым низким частотам: шум вентиляторов и нагрев падают, но падают и кадры. Если после такой настройки в играх появились подёргивания, сначала верни `auto` — про [низкую частоту кадров на Ryzen iGPU](https://ordanax.github.io/nizkaya-chastota-kadrov-ryzen-igpu) я писал отдельно.

Более тонкий вариант для игровых сценариев — профиль мощности, где `2` обычно отвечает за 3D_FULL_SCREEN:

```bash
cat /sys/class/drm/card0/device/pp_power_profile_mode
echo 2 | sudo tee /sys/class/drm/card0/device/pp_power_profile_mode
```

Набор числовых режимов отличается от поколения к поколению, поэтому сначала посмотри текущее значение, а потом записывай. Отдельный `power_dpm_state` со значением `battery` просит драйвер держать карту на экономном бюджете — удобно на ноутбуке от батареи.

В ручном режиме появляется список уровней, где `1` — минимальный, а последняя строка — максимальный:

```bash
cat /sys/class/drm/card0/device/pp_dpm_performance_level
cat /sys/class/drm/card0/device/pp_dpm_performance_level_manual
echo 2 | sudo tee /sys/class/drm/card0/device/pp_dpm_performance_level_manual
```

Запись в эти файлы требует root и иногда вызывает короткое мигание экрана, будто сбрасывается композитор. Для энергосбережения хватает `low` или `battery`, а `high` и ручной уровень стоит ставить осознанно: карта не даст тебе сэкономить счёт за электричество, зато нагреет ноутбук.

## Как поднять частоты и что делать с бюджетом мощности?

За верхние частоты отвечает OverDrive, а сам он выключен по умолчанию. Включается битом в маске возможностей:

```bash
cat /sys/class/drm/card0/device/ppfeaturemask
sudo sh -c 'echo 0xfff7bfff > /sys/class/drm/card0/device/ppfeaturemask'
```

Значение `0xfff7bfff` снимает бит OverDrive, после чего появляется `pp_od_clk_voltage`. На APU там же включают OverDriveVoltage — бит 14, значение `0x4000`; проще сначала прочитать текущую маску и аккуратно скомбинировать биты, чем затирать её всю.

Дальше — сам OverDrive:

```bash
cat /sys/class/drm/card0/device/pp_od_clk_voltage
echo "s 2100 1200" | sudo tee /sys/class/drm/card0/device/pp_od_clk_voltage
echo "r" | sudo tee /sys/class/drm/card0/device/pp_od_clk_voltage
```

Команда `s` задаёт частоту и напряжение, `r` возвращает штатные значения. Бюджет мощности настраивают через TDC/EDC: на дискретных картах это делают `CoreCtrl` и `LACT`, оба запускаются как обычные консольные утилиты (`corectrl`, `lact`, параметры — в `man` и `--help`). На APU общий TDP делится между ядром и встроенной графикой: поднял частоты iGPU — урежь бюджет CPU, иначе упрешься в троттлинг всей системы. И не запускай два менеджера разгона одновременно: они пишут в одни и те же файлы и будут драться.

## Как закрепить профиль при загрузке и по расписанию?

Все значения в sysfs живут до перезагрузки, сна или перезагрузки драйвера — после этого всё возвращается к заводским значениям. Поэтому профиль удобно закреплять через systemd-юнит, а не вручную. Сервис для экономного режима:

```ini
# /etc/systemd/system/gpu-power-low.service
[Unit]
Description=GPU: экономный режим
[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo low > /sys/class/drm/card0/device/power_dpm_force_performance_level'
```

И таймер, который периодически возвращает карту в нужное состояние:

```ini
# /etc/systemd/system/gpu-power-low.timer
[Unit]
Description=Включить экономный режим GPU
[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-power-low.timer
```

По времени суток вместо интервала удобнее `OnCalendar=*-*-* 09,17:00:00`. Если правка sysfs нужна без `sudo`, добавь правило в `/etc/udev/rules.d/`, а повторное применение после подключения горячего картоданных повесь на `systemd` через тег `TAG+="systemd"`. Крон тоже годится, но юнит надёжнее: он переживает загрузку и виден в `systemctl list-timers`.

## Частые вопросы

### Почему `echo 0` в power_dpm_force_performance_level не работает?

Интерфейс принимает только строки `auto`, `low`, `high` и `manual`, число `0` драйвер отвергает с ошибкой ввода. Чтобы снять принудительный режим, пиши `auto`, а `manual` переключает управление на `pp_dpm_performance_level_manual`, где доступен список уровней.

### Как узнать, какой cardN — моя дискретная карта?

Посмотри `uevent` или связку `lspci -nnk`: в выводе будет пара «vendor device» с классом VGA/3D. Если в ноутбуке две графики, встроенная обычно получает `card0`, дискретная — `card1`, но порядок не гарантирован, поэтому проверяй по вендору, а не по номеру.

### Почему после сна карта снова на максимуме?

Драйвер переинициализирует карту и сбрасывает все значения в sysfs. Чтобы профиль вернулся после пробуждения, добавь в сервис `After=suspend.target` и выполнение по событию пробуждения либо перезапусти таймер из hook в `/usr/lib/systemd/system-sleep/`.

### Чем power_dpm_state отличается от power_dpm_force_performance_level?

`power_dpm_state` переключает режим энергопотребления целиком: `battery` ограничивает и частоты, и напряжения, `performance` снимает ограничения. `power_dpm_force_performance_level` действует грубее — `low` просто прижимает карту к нижней частоте, а `auto` возвращает штатное поведение. На практике `battery` полезнее для автономной работы, а `low` удобен как грубый аварийный способ унять шум вентиляторов.

### Можно ли следить за GPU без lm_sensors?

Да, всё то же самое лежит в raw-файлах: пара `cat` в цикле или `watch -n1` покажет температуру и загрузку, а `radeontop` и `nvtop` соберут всё в одну таблицу без установки дополнительных библиотек.

## Полезные ресурсы

- [AMDGPU — ArchWiki](https://wiki.archlinux.org/title/AMDGPU) — разбор sysfs-интерфейсов amdgpu и OverDrive.
- [Lm sensors — ArchWiki](https://wiki.archlinux.org/title/Lm_sensors) — настройка мониторинга через hwmon.
- [Systemd timer — ArchWiki](https://wiki.archlinux.org/title/Systemd_timer) — как оформить периодическое применение профиля.

## Заключение

Температура, частоты и загрузка видеокарты читаются из `/sys/class/drm/cardN/device/` без сторонних программ, а `power_dpm_force_performance_level` и `pp_power_profile_mode` позволяют ограничить аппетит карты без перезагрузки. Помни, что набор файлов зависит от драйвера, значения сбрасываются после сна и перезагрузки, поэтому надёжный профиль удобнее закрепить через systemd-юнит с таймером.
