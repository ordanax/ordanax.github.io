---
layout: post
title: "Внешние звуковые карты (USB DAC): как заставить работать"
description: "USB DAC обычно работает сразу, но бывает не виден, шумит или не регулируется. Разбираем lsusb, aplay, профили WirePlumber и программную громкость."
date: 2026-09-26 00:00:00 +0300
permalink: /usb-dac-vneshnyaya-zvukovaya-karta
categories:
  - linux
  - arch linux
  - audio
  - pipewire
tags:
  - usb-dac
  - alsa
  - pipewire
  - wireplumber
  - sound
edit: true
---

Подключил внешнюю звуковую карту, а звука нет — в девяти случаях из десяти дело не в железе, а в одном из четырёх слоёв: USB-подсистема, модуль `snd_usb_audio`, карта в ALSA или профиль в PipeWire. Поскольку класс USB Audio Class ядро поддерживает из коробки, DAC чаще всего взлетает без единой настройки, а вот сломанный — требует пройти слои сверху вниз. Проверки занимают минуту и сразу показывают, на каком шаге всё встало.

## С чего начать: видит ли система USB-карту?

Прогони четыре команды по порядку — вывод каждой сужает круг подозреваемых:

```bash
lsusb | grep -iE 'audio|sound'
aplay -l
wpctl status
dmesg | grep -iE 'usb|audio|snd' | tail -20
cat /proc/asound/cards
```

- `lsusb` молчит — до ALSA дело не дошло. Проверь порт, кабель, хаб, а в `dmesg` поищи `error -71` и `device descriptor read`.
- `lsusb` видит устройство, `aplay -l` пуст — не загрузился модуль `snd_usb_audio`.
- `aplay -l` показывает карту, а в `wpctl status` её нет — сбой на уровне пользователя: PipeWire не подхватил ALSA-карту. Проверь, что пользователь в группах `audio` и `video`, и посмотри [разбор конфликта PipeWire и PulseAudio](/pipewire-ne-zapuskaetsya-konflikt-pulseaudio).
- `/proc/asound/cards` показывает карту с именем вроде `USB-Audio` — ядро её увидело, дальше работаешь с профилями.

Полезная привычка: обращаться к карте не через `hw:0,0`, а через `hw:CARD=USB,DEV=0`. Имя по буквам не путается, когда после перезагрузки индексы съезжают.

## Почему карта есть в lsusb, но не появилась в списке?

```bash
lsmod | grep snd_usb
sudo modprobe snd_usb_audio
```

В Arch модуль уже собран в ядре, поэтому ручной `modprobe` нужен только когда карта «залипла» после горячего отключения. Тогда сначала выгружаем, потом перевтыкаем:

```bash
sudo modprobe -r snd_usb_audio
# вытащи карту и воткни обратно
sudo modprobe snd_usb_audio
dmesg | tail -20
```

Из сообщений ядра видно типовые причины:

- `cannot submit URB: -28` — не хватает питания или пропускной способности, пересади карту на порт USB 2.0 напрямую, без хаба.
- `Failed to submit URB` и `error -71` — кабель или разваливающийся хаб.
- `reset SuperSpeed USB device` при смене трека — питания и полосы не хватает, см. раздел про шум.

Часть дешёвых DAC не умеет отдавать нужный USB-интерфейс, и ядру подсказывают это параметром `quirk`. Значение берётся из `lsusb -v` — строки `idVendor`, `idProduct` и `bInterfaceNumber`:

```bash
lsusb -v -d 1234:5678 | grep -E 'idVendor|idProduct|bInterfaceNumber'

# /etc/modprobe.d/usb-audio.conf
options snd-usb-audio quirk=0x1234x5678x00

sudo modprobe -r snd_usb_audio && sudo modprobe snd_usb_audio
```

Второй рычаг — энергосбережение. Карта, ушедшая в autosuspend, просыпается щелчком в колонках:

```bash
cat /sys/module/usbcore/parameters/autosuspend
```

Если там `2` (таймаут в секундах) или `0` для отдельных устройств, выключи приостановку глобально:

```bash
echo 'options usbcore autosuspend=-1' | sudo tee /etc/modprobe.d/usb-no-autosuspend.conf
```

И последний крайний приём — «чёрный список USB» для конфликтующих хабов и устройств в `/etc/modprobe.d/blacklist.conf`, плюс `usbcore.quirks=vvvv:pppp:x` в том же каталоге, где буква `x` в конце отключает устройство целиком.

## Как дать карте постоянное имя?

`hw:0,0` — привязка к индексу, `CARD=Device` — бесполезный мусор. Устойчивое имя делает udev, читая серийный номер:

```bash
# /etc/udev/rules.d/90-usb-dac.rules
KERNEL=="card[0-9]*", SUBSYSTEM=="sound", ATTRS{serial}=="*", ACTION=="add", \
  RUN+="/bin/sh -c 'echo %k {ATTR{serial}} | /usr/bin/speaker-id $(cat /proc/asound/%k/id)'"
```

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=sound
aplay -l
```

`/usr/bin/speaker-id` приходит с пакетом `alsa-utils`. Через пару перезагрузок `aplay -l` начнёт печатать имя из серийника, а в `wpctl status` появится внятный идентификатор карты вместо `alsa_output.usb-..._DEV_0`.

Почему это принципиально: WirePlumber и PipeWire помнят маршруты по ALSA-имени, а не по позиции в списке. Меняется индекс после ребута — слетают все настройки. Мой подход к устойчивому переключению профилей и карт описан [здесь](/wireplumber-pereklyuchenie-audioprofilej).

## Какие профили выбирать у USB DAC?

Список профилей смотрится на лету:

```bash
wpctl introspect <ID-устройства> | grep -A30 'Profiles'
```

Набор почти всегда один и тот же:

- `output:analog-stereo+input:analog-stereo` — обычный комплектный USB-адаптер с линейным входом и выходом.
- `output:analog-stereo` — только выход, микрофон остаётся на встроенной карте.
- `output:digital-stereo` — S/PDIF по коаксилу или оптике.
- `pro-audio` — «сырая» пара дорожек: без микса, без автоматического подмешивания, ровно то, что отдал плеер.

Для музыки разумно выбирать `pro-audio`: никакого dmix, никаких неожиданных пересчётов. Для S/PDIF нужен `output:digital-stereo` плюс бит-перфектт в самом плеере, иначе ресемплинг 44.1 → 48 кГц гарантирован.

24 бита и 192 кГц отдельным профилем не выглядят — это параметры формата. Что карта реально умеет, покажет:

```bash
cat /proc/asound/card1/stream0
```

Заставить всю систему работать на 192 кГц можно глобально:

```bash
mkdir -p ~/.config/pipewire/pipewire.conf.d
```

```ini
# ~/.config/pipewire/pipewire.conf.d/50-rate.conf
context.properties = {
    default.clock.rate = 192000
}
```

### А задержка?

```bash
pw-cli list-objects Node | grep -E 'node.name|node.latency'
```

Значение по умолчанию (1024 на 48000, около 21 мс) для музыки незаметно, для записи мысленно избыточно. Подкрутить:

```ini
# /etc/pipewire/pipewire.conf.d/20-quantum.conf
context.properties = {
    node.default.clock.quantum = 1024
    node.default.clock.min-quantum = 256
}
```

## Почему громкость не регулируется?

Симптомы знакомые: ползунок есть, но не двигается, либо его нет вовсе; в одном приложении тихо при 100% в системном микшере.

```bash
pactl list sinks | grep -A6 Volume
wpctl get-volume @DEFAULT_SINK@
```

Механика в том, что у внешнего DAC два независимых уровня: аппаратный регулятор в микросхеме карты и программный том в графе PipeWire. Если у DAC регулятора нет, у ALSA-карты не будет элемента управления Volume — но софтверный уровень всё равно считается.

Проверь напрямую, минуя любые графические оболочки:

```bash
wpctl set-default <ID нужного sink>
wpctl set-volume @DEFAULT_SINK@ 50%
wpctl get-volume @DEFAULT_SINK@
```

Громкость изменилась — софт работает, вопрос только в шкале. Не изменилась, потому что регулятор на железе перехватывает уровень: принуди включи программный том отдельным узлом-фильтром.

```ini
# /etc/pipewire/pipewire.conf.d/20-soft-volume.conf
context.objects = [
  {
    factory = filter
    args = {
      node.name = "soft-volume"
      filter.name = "volume"
    }
  }
]
```

```bash
systemctl --user restart pipewire wireplumber
wpctl status
```

Имя узла может немного отличаться от `soft-volume` в зависимости от версии PipeWire, поэтому идентификатор лучше взять из вывода `wpctl status` и сделать его дефолтным.

На большинстве карт с крутилкой задача решается проще: не трогай системный том вообще, крути ручку и держи софт на максимуме.

## Как убрать шум, треск и фон

Сначала посмотри, что пишет ядро:

```bash
dmesg | grep -iE 'reset super|disconnect|snd_usb'
```

- `reset SuperSpeed USB device` — карта теряет связь с хабом. Убери хаб, замени кабель, подведи питание.
- Щелчок на каждом треке — autosuspend, лечится значением `-1` из раздела выше.
- Фон 50/60 Гц и лёгкое шуршание — не софт, а земля и питание.

Железная часть:

- питание карты — отдельным блоком, а не из хаба или удлинителя;
- одна розетка (лучше один удлинитель с фильтром) на компьютер, карту, усилитель;
- экранированный кабель, до полутора метров, без цепочки переходников;
- если комп и усилитель в разных ветках сети — сначала попробуй общий сетевой фильтр, потом уже ищи землю в акустике.

Программная часть: найди источник, который играет громче остальных.

```bash
pactl list sink-inputs | grep -E 'Sink Input|Corked|Volume'
```

Тот поток, у которого свой уровень отличается от системного, и есть источник тихого звука. Если подозрение на WebRTC, сбросить сохранённые громкости приложений помогает перезагрузка модуля:

```bash
pactl unload-module module-stream-restore
pactl load-module module-stream-restore
```

## Как сделать USB DAC картой по умолчанию?

```bash
wpctl status
wpctl set-default <ID нового sink>
wpctl set-default <ID нового source>
```

WirePlumber запоминает выбор и восстанавливает его после перезагрузки, так что настройку не придётся повторять. Проверяется повторным `wpctl status`: у дефолтного устройства стоит звёздочка.

Встроенная карта при этом никуда не денется и может забрать маршрут, если что-то её разбудит. Временно убрать её можно так:

```bash
cat /proc/asound/cards
sudo modprobe -r snd_hda_intel
```

Постоянно:

```bash
# /etc/modprobe.d/blacklist.conf
blacklist snd_hda_intel
```

Плата — микрофон ноутбука и встроенные динамики. Поэтому чаще достаточно снять с неё маршрут по умолчанию, не выгружая драйвер. Если после смены карты звук пропал целиком, у меня есть [гайд по тишине в PipeWire](/net-zvuka-posle-ustanovki-wireplumber) — начни с него, там короче.

## Частые вопросы

### Карта работает в Windows, а в Linux её не видно — в чём разница?

Windows ставит родной драйвер с панелью управления и умеет больше: там есть и MIDI, и многоканальный вывод, и настройки эквалайзера. Linux опирается на USB Audio Class, поэтому функций меньше, но базовая работа из коробки. Если даже она не работает — начинай с четырёх команд диагностики, дальше смотри сообщения `dmesg`. Совсем экзотика — дешёвые карты, у которых весь тракт реализован как vendor-специфичный интерфейс: там спасает `quirk` для `snd-usb-audio`.

### Как узнать серийный номер карты для udev-правила?

```bash
udevadm info --query=all --name=/dev/snd/controlC1 | grep -i ID_SERIAL
```

Если ничего нет, значит карта серийника не сообщает — тогда привязывай правило к `ATTRS{product}=="*"` и вставляй `ATTRS{product}` вместо `ATTRS{serial}`.

### Можно ли вывести звук сразу на две USB-карты?

Да, через совместимость PulseAudio, которая есть в PipeWire:

```bash
pactl list short sinks
pactl load-module module-combine-sink sink_name=dual slaves=sink_name_1,sink_name_2
```

Дальше приложения пишут в `dual`, а он уже раздаёт поток в обе карты. Работает и с наушниками, и с линейным выходом — удобно, когда в комнате два усилителя.

## Полезные ресурсы

- [Advanced Linux Sound Architecture — ArchWiki](https://wiki.archlinux.org/title/Advanced_Linux_Sound_Architecture)
- [PipeWire — ArchWiki](https://wiki.archlinux.org/title/PipeWire)

## Заключение

Большинство «мёртвых» USB-карт чинятся не переустановкой, а последовательной проверкой: `lsusb` → `aplay -l` → `wpctl status` → `dmesg`, а затем модуль, профиль и имя карты. Потраченные пять минут почти всегда дают точный ответ, а стойкое имя от udev избавляет от повторной настройки после каждой перезагрузки.
