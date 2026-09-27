---
layout: post
title: "ALSA из-под root: правильный порядок настройки"
description: "Пошагово: alsamixer из-под root, снятие mute, проверка speaker-test и сохранение состояния через alsactl store, чтобы звук не слетал."
date: 2026-09-26 00:00:00 +0300
permalink: /alsa-iz-pod-root-nastrojka
categories:
  - linux
  - arch linux
  - alsa
tags:
  - alsa
  - alsamixer
  - pipewire
  - sound
  - troubleshooting
  - arch-linux
edit: true
---

Звук молчит, хотя колонки подключены, драйверы стоят, а в системном микшере всё выглядит нормально? Почти всегда виноват один заглушенный контрол микшера и один забытый `alsactl store`. Тебе нужен короткий порядок действий: открыть `alsamixer` из-под root, снять mute с нужных контролов, проверить результат через `speaker-test` и только после этого сохранить состояние. Ниже — каждый шаг с командами, плюс разбор того, что меняется, если у тебя PipeWire.

## Почему ALSA приходится настраивать из-под root?

`alsamixer` — не обёртка над PulseAudio или PipeWire. Он открывает напрямую control-устройства `/dev/snd/controlC*` и пишет туда значения микшеров. Тот же низкоуровневый доступ нужен PCM-устройствам `/dev/snd/pcmC0D0p`, через которые ядро отдаёт поток на DMA-контроллер. Ни PipeWire, ни WirePlumber такой доступ тебе не подменяют: их громкости живут в их собственных базах, а железо продолжает хранить свои значения.

Поэтому привилегии нужны разные:

- `alsamixer` хватает членства в группе `audio` или запуска через `sudo alsamixer`;
- `alsactl store` пишет системный файл состояния — ему нужен настоящий root.

Проверь свою группу:

```bash
groups | grep -o '\baudio\b'
```

Если пусто, а запускать микшер без `sudo` не хочется:

```bash
sudo usermod -aG audio "$USER"
```

Новые группы подхватываются только после повторного входа в систему. Учти, что `audio` даёт прямой доступ ко всем звуковым устройствам, включая микрофон: на личном ноутбуке это нормально, на общем сервере — спорно.

## Какие пакеты поставить перед настройкой?

```bash
sudo pacman -S --needed alsa-utils alsa-lib alsa-plugins
```

- `alsa-utils` — сами утилиты: `alsamixer`, `alsactl`, `speaker-test`, `aplay`, `amixer`, `arecord`;
- `alsa-lib` — библиотека, без неё не запустится ни одна ALSA-программа;
- `alsa-plugins` — конвертеры форматов и мосты к внешним устройствам.

Проверка после установки:

```bash
which alsamixer alsactl speaker-test
```

Если `alsamixer: command not found` — пакет не установлен, а не «сломан». Для Bluetooth-гарнитуры, которую подхватывает сама ALSA, дополнительно нужны `bluez` (библиотека libbluez) и плагин `libasound_module_pcm_bluez` из `alsa-plugins`.

## Как включить звук в alsamixer и выставить громкость?

```bash
sudo alsamixer
```

1. **F6** — открыть список звуковых карт и выбрать нужную. Обычно `hw:0` — встроенная карта, `hw:1` — USB-гарнитура или вебкамера.
2. **F5** («All») — показать все контролы, включая скрытые. Без этой кнопки в списке будет одно-два пункта, и покажется, что сломан весь звук.
3. **Стрелки ↑/↓** — громкость выбранного контрола. Доведи до 80–100%.
4. **m** — снять mute. Пока рядом с названием стоит `MM`, канал заглушен, как бы громкость ни была выставлена.
5. Пройдись по списку и сними mute с `Master`, `Headphone`, `Front`, `Speaker`, `PCM` — у разных карт они называются по-разному.

Про `Auto-Mute` стоит знать отдельно: у HDA-карт он умеет глушить аналоговый выход при подключённых наушниках. Если звук пропал из колонок ровно в момент вставки наушников — это он. Похожие симптомы разбираю в статье [почему звук уходит только в наушники и как его переключать](/zvuk-tolko-naushniki-pereklyuchenie).

На HDMI и DisplayPort отдельный контрол `LOOPBACK` (он же «Digital Matrix»): если звук в приложениях идёт, а в `alsamixer` ползунка нет или он зажат — сними mute с него. У HDMI-карт уровень выхода вообще не регулируется на уровне ALSA, поэтому в микшере там может не быть ничего при живом звуке.

## Как сохранить настройки, чтобы они не слетели после перезагрузки?

Снимок состояния делается только от root:

```bash
sudo alsactl store
```

По умолчанию файл кладётся в `/etc/asound.state`. Проверь, что он появился и не пустой:

```bash
ls -l /etc/asound.state
grep -c '^\s*control\.' /etc/asound.state
```

А вот systemd на Arch читает другой путь — `/var/lib/alsa/asound.state`. Юнит `alsa-restore.service` при загрузке вызывает `alsactl restore` с этим файлом, а `alsa-store.service` при завершении работы сохраняет текущее состояние. Поэтому надёжнее писать сразу в оба места:

```bash
sudo alsactl store -f /var/lib/alsa/asound.state
```

Проверка, что механизм работает:

```bash
systemctl status alsa-restore.service
systemctl cat alsa-restore.service
```

Если ты решил хранить состояние в своём файле, юнит придётся переопределить:

```bash
sudo systemctl edit alsa-restore.service
```

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/alsactl restore -f /etc/asound.state
```

Затем `sudo systemctl daemon-reload` и `sudo systemctl restart alsa-restore.service`.

Про udev-альтернативу: карты, которые появляются только когда ты воткнул HDMI-кабель, при загрузке просто отсутствуют — восстанавливать им нечего. Для таких случаев нужен хук, применяющий сохранённое состояние к карте в момент подключения:

```bash
sudo tee /etc/udev/rules.d/70-alsa-restore.rules >/dev/null <<'EOF'
ACTION=="add", SUBSYSTEM=="sound", KERNEL=="controlC[0-9]*", RUN+="/usr/bin/alsactl restore -f /var/lib/alsa/asound.state"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Помни, что `alsactl restore` раздаёт одно и то же состояние каждой подошедшей карте — для систем с несколькими картами это иногда мешает больше, чем помогает.

## Как проверить, что звук пошёл в нужную карту?

```bash
aplay -l
aplay -L | head -20
speaker-test -c 2 -t wav
speaker-test -D plughw:0,0 -c 2 -t wav
```

Первая команда покажет карты и их индексы, вторая — доступные PCM. `speaker-test` без `-D` играет через маршрут по умолчанию, а с `-D plughw:0,0` идёт прямо в железо, минуя dmix и плагин `pulse`. Разница существенна: дефолтный маршрут может вести в PipeWire, и звук в наушниках окажется не тем, что уходит в колонки.

`amixer` покажет состояние текстом — удобно, когда сомневаешься:

```bash
amixer -c 0 scontents
amixer -c 1 scontents
```

Любое `MM` вместо числа в выводе — это заглушенный канал.

## Что делать, если у тебя PipeWire: нужна ли настройка ALSA вообще?

Коротко: обычно не нужна. PipeWire сам открывает `/dev/snd/*`, раздаёт звук между приложениями и хранит свои громкости в базе WirePlumber, а не в `/etc/asound.state`. Если в системе уже всё слышно, трогать ALSA-конфиг незачем. С чего начинать настройку звука целиком — в статье [PipeWire в KDE Plasma вместо PulseAudio](/pipewire-kde-plasma-pulseaudio).

ALSA всё-таки пригодится в четырёх случаях: PipeWire не видит карту; приложение умеет только ALSA; используется JACK или другая низкоуровневая схема, где нужен `plughw`; старая программа требует default-устройство из `/etc/asound.conf`.

```bash
sudo nano /etc/asound.conf
```

```conf
pcm.!default {
    type plug
    slave.pcm "hw:0,0"
}
ctl.!default {
    type hw
    card 0
}
```

Проверка после правки:

```bash
speaker-test -c 2 -t wav
aplay -D default /usr/share/sounds/alsa/Front_Center.wav
```

Два предостережения. Пока играет PipeWire, `type plug` с `slave.pcm hw:0,0` заставит ALSA-приложения идти мимо него прямо в железо — это источник `Device or resource busy` и странных конфликтов. И если в `/etc/asound.conf` остался `slave.pcm "pulse"` от времен PulseAudio, а сам PulseAudio удалён, приложения получат `no such file or directory` или `Connection refused`. Про это подробнее в статье [про конфликт PipeWire и PulseAudio](/pipewire-ne-zapuskaetsya-konflikt-pulseaudio).

## Какие ошибки встречаются чаще всего?

1. **`MM` вместо числа.** Громкость 100% не значит, что звук идёт. Найди `MM` и нажми `m`.
2. **Не тот индекс карты.** После перезагрузки или подключения USB порядок меняется: то, что было `hw:0`, становится `hw:1`. Всегда начинай с `aplay -l`.
3. **Карта выбрана, канал — нет.** У аналогового выхода это `plughw:0,0`, у HDMI обычно `plughw:0,3`. Ошибка даёт `Invalid argument` или тишину.
4. **Сохранено до проверки.** `sudo alsactl store` с заглушенным каналом запишет именно mute. Правильный порядок: настроил → проверил `speaker-test` → сохранил.
5. **Упал `sudo` в конвейере.** `alsamixer | alsactl store` без `sudo` завершится `Permission denied`, и ошибка легко теряется в выводе.
6. **Полоса ALSA занята.** Если приложение держит карту, `alsamixer` может показать её как недоступную. Закрой плеер и повтори.

## Частые вопросы

### Нужно ли что-то делать, если звук уже работает?

Нет. Если в системном микшере слышно, ALSA-уровень не трогай. Настройку начинай только после реальной проблемы — она уйдёт сама, как только найдёшь заглушенный контрол.

### Почему после перезагрузки всё снова заглушено, хотя я сохранял?

Три частые причины: `alsactl store` запускался без `sudo`; ты сохранил до того, как снял mute; снимок записался в `/etc/asound.state`, а systemd читает `/var/lib/alsa/asound.state`. Проверь `ls -l /var/lib/alsa/asound.state` и повтори команду с `sudo`.

### Можно ли запустить `alsamixer` без root?

Да, если ты в группе `audio`: `sudo usermod -aG audio "$USER"` и повторный вход в систему. Иначе — `sudo alsamixer`. Помни, что группа `audio` даёт доступ ко всем звуковым устройствам, включая микрофон.

### `alsamixer` не запускается, что делать?

`command not found` — поставь `alsa-utils`. Другие сообщения: `Mixer attach default error: No such file or directory` значит, что не выбрана карта (жми F6); `Cannot access card` — не хватает прав на `/dev/snd/controlC*`; пустой список карт — в системе нет работающего звукового драйвера, проверь `cat /proc/asound/cards`.

### Почему в `alsamixer` нет ни одного ползунка?

Нажми F5 — по умолчанию видна лишь малая часть контролов. Если и после F5 пусто, карта не выбрана: жми F6. У HDMI-карт уровень выхода в `alsamixer` не регулируется вовсе, громкость живёт в приложении или в PipeWire.

## Полезные ресурсы

- [Advanced Linux Sound Architecture — ArchWiki](https://wiki.archlinux.org/title/Advanced_Linux_Sound_Architecture) — устройства, драйверы, mixer и отладка ALSA.
- [PipeWire — ArchWiki](https://wiki.archlinux.org/title/PipeWire) — если у тебя именно PipeWire, а не голый ALSA.
- [Нет звука после установки WirePlumber](/net-zvuka-posle-ustanovki-wireplumber) — что проверять, когда PipeWire запускается, а звука нет.

## Заключение

Настройка ALSA сводится к трём действиям: снять mute в `alsamixer` из-под root, проверить результат через `speaker-test` и сохранить состояние через `alsactl store` в тот файл, который читает systemd. С PipeWire этот уровень обычно не нужен — сначала убедись, что звук вообще есть, и настраивай ALSA только когда проблема осталась. Порядок действий важнее отдельных команд: проверка до сохранения экономит отладку на следующей загрузке.
