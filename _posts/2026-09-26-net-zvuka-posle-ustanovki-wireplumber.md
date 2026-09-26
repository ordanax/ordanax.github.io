---
layout: post
title: "Нет звука после установки: PipeWire и WirePlumber"
description: "Почему после установки Arch или pacman -Syu пропал звук: PipeWire и WirePlumber, проверка сервера, откат пакета, профили карты и ALSA."
date: 2026-09-26 00:00:00 +0300
permalink: /net-zvuka-posle-ustanovki-wireplumber
categories:
  - linux
  - arch linux
  - pipewire
  - audio
tags:
  - pipewire
  - wireplumber
  - alsa
  - audio
  - arch-linux
  - troubleshooting
edit: true
---

После установки Arch или после `pacman -Syu` колонки молчат, хотя в трее висит микшер и всё вроде подключено. Дело почти всегда не в железе: Arch давно перешёл с PulseAudio на PipeWire, а роль менеджера сессии забрал WirePlumber. Ниже — путь от быстрой проверки сервера до отката пакета, после которого звук исчез. Проверять всё подряд не нужно: шаги в статье идут от самого частого к редкому, и в 8 случаях из 10 хватает первых трёх команд.

## Почему после установки Arch пропал звук?

Ещё недавно установка тянула `pulseaudio`, и звук появлялся сам. Сейчас базовый стек другой: `pipewire` — сам сервер, `wireplumber` — менеджер сессии, `pipewire-pulse` — слой совместимости, отвечающий на запросы старых программ.

Проверь, что стоит в системе:

```bash
pacman -Q pipewire wireplumber pipewire-pulse
```

Если `pipewire-pulse` в списке нет, привычные инструменты (`pactl`, `pavucontrol`) не увидят ничего. Общая картина по всем пакетам звука:

```bash
pacman -Q | grep -E 'pipewire|wireplumber|pulseaudio'
```

Старый `pulseaudio` в системе больше не нужен и мешает, если стоит рядом с `pipewire-pulse`. Вторая по частоте причина — само обновление: `pacman -Syu` поднимает версии pipewire и wireplumber одновременно, и если демон после этого не стартовал, звук пропадает целиком, хотя ядро и карта на месте.

## Как проверить, что звуковой сервер запустился?

Первое действие — посмотреть, кто отвечает на запросы:

```bash
pactl info | grep "Server Name"
```

В норме строка выглядит так:

```bash
Server Name: PulseAudio (on PipeWire 1.2.7)
```

Голое `Server Name: PulseAudio` без приписки означает, что в системе живёт старый сервер, а PipeWire в работе не участвует. Заодно посмотри, какой вывод считается основным — пустая строка здесь тоже повод разбираться дальше:

```bash
pactl info | grep -E "Server Name|Default Sink"
```

Дальше состояние юнитов:

```bash
systemctl --user status pipewire wireplumber pipewire-pulse
```

Три строки `active (running)` — всё хорошо. Если юнита нет вовсе, включи и стартуй его:

```bash
systemctl --user enable --now pipewire wireplumber pipewire-pulse
```

После этого перезайди в сессию: переменные `XDG_RUNTIME_DIR` и `DBUS_SESSION_BUS_ADDRESS` выставляются только на входе, и до перелогина демон поднимается с ошибкой.

## Почему pactl показывает пустые sinks?

Сервер есть, устройств нет — самая частая картина. Список выходов:

```bash
pactl list sinks short
wpctl status
```

Пусто означает, что WirePlumber не смог опознать карту. Три причины по убыванию частоты.

### Перекрытый конфиг

Пользовательский `~/.config/pipewire/pipewire.conf` заменяет системный `pipewire.conf` целиком, а не дополняет его. Частая беда — файл, оставшийся от прошлой настройки. Отключи его и перезапусти стек:

```bash
mv ~/.config/pipewire/pipewire.conf ~/.config/pipewire/pipewire.conf.bak
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### Не задано XDG_RUNTIME_DIR

Каталог должен существовать и принадлежать тебе:

```bash
echo "$XDG_RUNTIME_DIR"
systemctl --user import-environment XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS
```

### Демон падает при старте

Логи WirePlumber:

```bash
journalctl --user -u wireplumber -b --no-pager | tail -30
journalctl --user -b --no-pager | grep -iE 'pipewire|wireplumber' | tail -40
```

Строки с `ALSA lib` или `snd_pcm` укажут на проблему с драйвером, `Cannot connect` — на отсутствие D-Bus.

## Что делать, если звук пропал именно после pacman -Syu?

Сначала перезагрузись: половина таких случаев лечится новым ядром и пересозданием устройств. Если не помогло, откатывай wireplumber. Pacman держит в кэше несколько последних сборок:

```bash
pacman -Q wireplumber
ls -1t /var/cache/pacman/pkg/wireplumber-*.pkg.tar.zst | head -3
```

Ставишь предыдущую версию:

```bash
sudo pacman -U /var/cache/pacman/pkg/wireplumber-1.0.13-1-x86_64.pkg.tar.zst
systemctl --user restart wireplumber
```

Механизм отката подробно разобран в статье про [откат одного пакета](https://ordanax.github.io/otkat-odnogo-paketa-primery).

Вторая по частоте причина — старый менеджер сессии. `pipewire-media-session` устарел и заменён на WirePlumber; если он остался в системе, два менеджера дерутся за один граф, и устройства пропадают. Проверь и удали:

```bash
pacman -Q | grep -E 'pipewire-media-session|wireplumber'
sudo pacman -Rns pipewire-media-session
systemctl --user restart wireplumber
```

Когда ломает не один пакет, а обновление целиком, порядок работы другой — об этом в статье [что делать, если после обновления сломалось](https://ordanax.github.io/slomalos-posle-obnovleniya-otkat).

## Как проверить автозапуск pipewire в systemd --user?

Сервер запускается не init-системой, а юнитом пользователя, поэтому ищи его именно там:

```bash
systemctl --user is-enabled pipewire.socket wireplumber
systemctl --user cat pipewire.service
ls ~/.config/systemd/user/
```

Файл `pipewire.service` в домашнем каталоге перекрывает системный целиком — как и конфиг в `~/.config/pipewire`. Если после правки в `~/.config/systemd/user/` демон не подхватился, нужен сброс кэша юнитов и перелогин:

```bash
systemctl --user daemon-reload
systemctl --user restart pipewire.socket pipewire.service pipewire-pulse.service wireplumber
```

## Почему устройство есть, а звука всё равно нет?

Карта видна, но в списке sinks пусто — или наоборот, есть и молчит. Начни с профиля: у встроенной звуковой карты часто стоит HDMI, к которому физически ничего не подключено.

```bash
pactl list short cards
pactl get-card-profile alsa_card.pci-0000_00_1f.3
pactl set-card-profile alsa_card.pci-0000_00_1f.3 output:analog-stereo
```

Тот же список профилей показывает WirePlumber, а переключается он по идентификатору из вывода:

```bash
wpctl status
wpctl set-profile @DEFAULT_AUDIO_SINK@ pro-audio
```

Профиль с большим числом каналов (`pro-audio`, 5.1) гоняет поток через JACK, обычные плееры с ним не дружат.

Если карта пропала совсем, пересоздай её:

```bash
udevadm trigger --subsystem-match=sound
sudo modprobe -r snd_hda_intel && sudo modprobe snd_hda_intel
systemctl --user restart pipewire pipewire-pulse wireplumber
```

На ноутбуках с двумя аудиокодеками (встроенный плюс HDMI) номера карт после обновления иногда меняются местами, и активным становится не тот выход. Порядок задаётся параметром модуля:

```bash
cat /proc/asound/cards
printf 'options snd_hda_intel index=1\n' | sudo tee /etc/modprobe.d/sound.conf
sudo mkinitcpio -P
```

После `mkinitcpio` нужен перезапуск: параметр читается при загрузке ядра.

## Что делать, если всё равно тишина?

Проверь mute на уровне ALSA — у `alsamixer` есть колонка mute, которую трей не показывает:

```bash
alsamixer
pactl get-sink-mute @DEFAULT_SINK@
pactl set-sink-mute @DEFAULT_SINK@ 0
```

Потом переустанови весь стек и перезайди в сессию:

```bash
sudo pacman -Syu pipewire wireplumber pipewire-pulse
```

Если пакетов в системе нет вообще, установка с нуля даёт тот же результат, что и свежий Arch:

```bash
sudo pacman -S pipewire wireplumber pipewire-pulse libpulse
```

`libpulse` нужен для программ, которые продолжают ходить в старую PulseAudio-библиотеку напрямую.

Если в системе остался JACK, ему нужен модуль `pipewire-jack`:

```bash
pacman -Q pipewire-jack || sudo pacman -S pipewire-jack
```

Отдельная боль — звук с HDMI на карте NVIDIA: там нужно правильно выбрать вывод на стороне PulseAudio-слоя, об этом в статье [PipeWire и HDMI на NVIDIA](https://ordanax.github.io/nvidia-pipewire-hdmi-zvuk).

## Частые вопросы

### Нужен ли pulseaudio, если стоит pipewire-pulse?

Нет. `pipewire-pulse` и есть слой совместимости: старые программы зовут PulseAudio, отвечает PipeWire. Ставить поверх `pulseaudio` не нужно.

### Почему после перезагрузки звук есть, а после -Syu пропадает?

Потому что демоны звука полноценно поднимаются только на входе в сессию. Обновился пакет — а `wireplumber` не смог перезапуститься на лету из-за конфликта версий. Лечится перезагрузкой или откатом пакета.

### Можно вернуть PulseAudio?

Технически да: `sudo pacman -Rdd pipewire-pulse && sudo pacman -S pulseaudio`, затем `systemctl --user disable --now pipewire.socket`. Смысла в этом мало: весь софт давно рассчитан на PipeWire.

### Как понять, что виноват WirePlumber, а не карта?

Сравни `pactl list cards` с тем, что было до обновления, и посмотри логи: `journalctl --user -b | grep -iE 'card|alsa'`. Карта видна в ALSA, но её нет в `wpctl status` — значит, дело в сессии, а не в железе.

### Почему звук идёт только в наушники или только в колонки?

Активный вывод переключается мгновенно, и трей об этом не предупреждает:

```bash
pactl get-default-sink
wpctl set-default @SINK_NAME@
```

### Как понять, что сервер поднялся, но звука нет из-за прав?

PipeWire запускается от твоего пользователя, поэтому громкость выше 100% и смену профиля он разрешит, а вот монтирование без `sudo` — нет. Если в логах есть `Permission denied`, проверь права на каталог состояния:

```bash
ls -ld "$XDG_RUNTIME_DIR" "$XDG_RUNTIME_DIR/pipewire"
```

## Полезные ресурсы

- [PipeWire — ArchWiki](https://wiki.archlinux.org/title/PipeWire)
- [WirePlumber — ArchWiki](https://wiki.archlinux.org/title/WirePlumber)
- [PulseAudio — ArchWiki](https://wiki.archlinux.org/title/PulseAudio)

## Заключение

Почти всегда «пропал звук после обновления» — это PipeWire, который не поднялся, а не сгоревшая карта. Начинай с `pactl info` и `systemctl --user status`, дальше смотри логи WirePlumber, конфиг в `~/.config/pipewire` и остатки `pipewire-media-session`. Если не помогло, откатывай версию из кэша pacman — это самый быстрый путь к работающему звуку.
