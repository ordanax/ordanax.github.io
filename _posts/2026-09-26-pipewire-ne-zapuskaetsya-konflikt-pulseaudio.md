---
layout: post
title: "PipeWire не запускается: конфликт с PulseAudio"
description: "Can't connect to server: Connection refused — почему PipeWire не стартует, какие пакеты проверить и как замаскировать старый pulseaudio."
date: 2026-09-26 00:00:00 +0300
permalink: /pipewire-ne-zapuskaetsya-konflikt-pulseaudio
categories:
  - linux
  - arch linux
  - pipewire
tags:
  - pipewire
  - pulseaudio
  - wireplumber
  - systemd
  - troubleshooting
edit: true
---

PipeWire не стартует, а `pactl info` отвечает `Connection refused`? Почти всегда виноват не PipeWire, а старый PulseAudio: он держит сокет и свои юниты, а свежий демон умирает на `EADDRINUSE`. Разбираю по шагам, какие пакеты должны стоять, что покажет `systemctl --user`, как замаскировать `pulseaudio` и что делать, если дело не в нём.

## Как выглядит нормальное состояние PipeWire?

В системе с PipeWire работают три пользовательских юнита: `pipewire.service` (графический сервер), `wireplumber.service` (маршрутизация потоков) и `pipewire-pulse.service` (мост совместимости с PulseAudio API). Проверяешь их одной командой:

```bash
systemctl --user status pipewire wireplumber pipewire-pulse
```

Норма — три строки `Active: active (running)`. Если в выводе `Loaded: not found`, проблема не в конфиге, а в том, что пакеты не установлены. Если `active (exited)` — демон умер, смотри логи. Если рядом с `wireplumber` написано `Job for wireplumber.service failed`, скорее всего, упал `pipewire`: wireplumber требует живой сокет и не умеет ждать.

Отдельный признак успеха — `pactl info`, где в поле `Server Name` стоит `PulseAudio (on PipeWire 1.2.x)`. Если wireplumber уже установлен и настроен, начни с [этой статьи](https://ordanax.github.io/net-zvuka-posle-ustanovki-wireplumber) — там разобран нормальный рабочий вариант.

## Почему systemctl --user не находит юнит pipewire?

Отсутствие юнита почти всегда означает отсутствие пакета. Arch разбивает PipeWire на несколько пакетов, и базовый `pipewire` не тянет за собой ни `pipewire-pulse`, ни ALIA-часть:

```bash
pacman -Q pipewire wireplumber pipewire-pulse pipewire-alsa pipewire-jack wireplumber-pulse
```

Пустые строки в ответе — твой список к установке. Ставить нужно комплектом, иначе `pulseaudio`-совместимые программы продолжат получать `Connection refused`:

```bash
sudo pacman -S --needed pipewire wireplumber pipewire-pulse pipewire-jack \
  wireplumber-pulse pipewire-alsa wireplumber-alsa alsa-utils
```

Перед этим обнови систему: в репозитории может лежать устаревший `wireplumber`, несовместимый по ABI с новым `pipewire`. После установки перечитай юниты и проверь, что демон поднялся:

```bash
systemctl --user daemon-reload
systemctl --user enable --now pipewire-pulse wireplumber
```

Если в системе включён `linger` для твоего пользователя (`loginctl show-user $(id -u) -p Linger`), демоны стартуют без твоего входа в сессию. Проверить:

```bash
loginctl show-user $(id -u) -p Linger
```

Значение `Linger=yes` означает, что звук работает даже на экране входа GDM. Если `no` и звук нужен всегда — включи:

```bash
sudo loginctl enable-linger $USER
```

## Почему PipeWire не стартует, пока живёт PulseAudio?

Классический сценарий: в системе стоял PulseAudio, потом поставили PipeWire, но не убрали старый сервер. Демон запускается, видит занятый сокет ALSA или свой сокет в `/run/user/1000`, падает и уходит в перезапуск. Проверь, кто ещё жив:

```bash
systemctl --user list-units 'pulseaudio*' 'pipewire*'
ps -ef | grep -E 'pulseaudio|pipewire|wireplumber'
```

Останавливаешь и отключаешь старые юниты, потом маскируешь их, чтобы они не поднялись после релогина:

```bash
systemctl --user disable --now pulseaudio.socket pulseaudio.service
systemctl --user mask pulseaudio.socket pulseaudio.service
```

Маска нужна для `socket`-юнита: он активируется по требованию, поэтому без неё `pulseaudio` воскреснет при первом же обращении программы. Затем удали пакеты — после этого в твоей системе останется только PipeWire:

```bash
pacman -Qq | grep '^pulseaudio' | grep -v pulseaudio-utils
sudo pacman -Rns pulseaudio pulseaudio-alsa pulseaudio-jack
```

`pulseaudio-utils` (`pactl`, `pacmd`) оставь: PipeWire их полностью заменяет по поведению. Заодно посмотри, не остался ли старый сокет: папка `/run/user/$(id -u)/pulse` после выхода из сессии исчезает сама, но если ты ничего не перезаходил, её лучше убрать руками. Конфиг PulseAudio можно сохранить для отката, просто переименовав:

```bash
mv ~/.config/pulse ~/.config/pulse.bak
```

## Что делать, если XDG_RUNTIME_DIR или dbus-session пустые?

PipeWire живёт в пользовательской шине systemd и общается с `dbus`, поэтому в окружении без session bus он не поднимется в принципе. Проверяй три вещи:

```bash
echo "$XDG_RUNTIME_DIR"
ls -ld "/run/user/$(id -u)"
systemctl --user is-active dbus.socket
```

Пустой `XDG_RUNTIME_DIR` или отсутствующий каталог — причина отказа запускать сокет. Отсутствующий `dbus.socket` — вторая причина. Для быстрой проверки запусти сессию с отдельной шиной:

```bash
dbus-run-session -- bash -lc 'systemctl --user start pipewire pipewire-pulse; pactl info'
```

Если внутри всё работает, значит проблема в твоей сессии — в менеджере входа, а не в пакетах. Отдельно про `sudo`: команда `sudo systemctl --user start pipewire` не делает ничего полезного, потому что под root у другой пользовательской шины и другого `XDG_RUNTIME_DIR`. Хуже — если ты так запускал демон руками, в `/etc/systemd/system` остаются симлинки на юниты. Их надо убрать:

```bash
sudo rm -f /etc/systemd/system/pipewire.service \
  /etc/systemd/system/wireplumber.service \
  /etc/systemd/system/pipewire-pulse.service
sudo systemctl daemon-reload
```

Про AppArmor и SELinux забудь: в Arch из коробки нет мандатной системы, политики контекста тут проверять не нужно.

## Как найти причину в логах и strace?

Когда статус показал `failed`, смотри журнал. Первое, что нужно, — последние строки юнита:

```bash
journalctl --user -u pipewire -b --no-pager | tail -50
journalctl --user -u wireplumber -b --no-pager | tail -30
```

Читай сообщения так:

- `EADDRINUSE: Address already in use` — сокет занят старым демоном, вернись к маске `pulseaudio`.
- `Failed to connect to session bus` — нет `dbus`, проверяй session bus.
- `No such file or directory` при обращении к сокету — кривой `XDG_RUNTIME_DIR`.
- `Failed to open ALSA device` / `snd_pcm_open failed` — аудиоустройство занято другим сервером или его видит только один из демонов.

Проверить, создался ли сокет вообще, и кому он принадлежит:

```bash
ls -l "/run/user/$(id -u)/pipewire-0"
```

Если файла нет после нескольких попыток запуска, запусти демон вручную с отладкой в текущем терминале:

```bash
pipewire -v
pw-cli info 0
```

Для последнего шага есть `strace` — он покажет, на каком именно системном вызове демон упал:

```bash
strace -f -o /tmp/pipewire.log pipewire
grep -E 'ENOENT|EACCES|EADDRINUSE|EPERM' /tmp/pipewire.log | tail -20
```

Мусорный лог потом можно убрать: `rm -f /tmp/pipewire.log`.

## Что делать, если конфиг PipeWire сломан?

Arch из коробки не требует никакого конфига. Если ты копировал рецепты из интернета или правил `~/.config/pipewire/pipewire.conf`, сломанная секция `context.properties` даёт падение на старте с `Failed to load config`. Разбираться с каждой строкой долго — надёжнее откатиться на дефолт:

```bash
mv ~/.config/pipewire ~/.config/pipewire.bak
mv ~/.config/wireplumber ~/.config/wireplumber.bak
systemctl --user daemon-reload
systemctl --user restart pipewire wireplumber pipewire-pulse
```

Если после отката всё ожило — дело было в конфиге. Настройки WirePlumber лежат в `~/.config/wireplumber/wireplumber.conf` и там же создаются сегменты для карт и устройств. Не забудь, что сбросили и правила маршрутизации, если ты их настраивал.

Единственный конфиг, который реально нужен, — минимальный `pipewire.conf` с sane-частотами:

```bash
mkdir -p ~/.config/pipewire
cat > ~/.config/pipewire/pipewire.conf <<'EOF'
context.properties = {
    default.clock.rate       = 48000
    default.clock.quantum    = 1024
    default.clock.min-quantum = 32
    default.clock.max-quantum = 8192
}
node.properties = {
    audio.rate = 48000
}
EOF
systemctl --user restart pipewire wireplumber pipewire-pulse
```

## Как проверить, что PipeWire ожил?

Финальная проверка из трёх шагов. Состояние юнитов:

```bash
systemctl --user is-active pipewire pipewire-pulse wireplumber
```

Ожидается три раза `active`. Клиентская проверка:

```bash
pactl info | head -20
```

Ошибки, которые всё ещё означают «не запустился»:

- `Connection refused` — демона нет, клиент не достучался до сокета.
- `Can't connect to server: Connection refused` после установки пакетов — не поднялся `pipewire-pulse`.
- `No such file or directory` — нет `XDG_RUNTIME_DIR`.

Список устройств и потоков:

```bash
wpctl status
pw-cli ls Node
```

В `wpctl status` должны быть реальные устройства. Если в списке только `Dummy Output`, демон работает, но не видит звуковых карт — это уже про уровни громкости и переключение между наушниками и колонками, и тут поможет [отдельный разбор](https://ordanax.github.io/zvuk-tolko-naushniki-pereklyuchenie).

## Частые вопросы

### Нужно ли добавлять себя в группу audio?

Нет. PipeWire запускается от твоего пользователя, а доступ к `/dev/snd/*` udev раздаёт по правилу `TAG+="uaccess"` активной сессии. Группа `audio` нужна для прямой работы с ALSA вне звукового сервера. Если ты добавил себя в неё во время настройки — вернись назад: лишнее членство иногда даёт доступ к устройству, который конфликтует с uaccess-меткой.

### Почему после удаления pulseaudio юнит pipewire не появился в списке?

Файлы юнитов читаются при старте systemd, а список пакетов обновился раньше. Помогает `systemctl --user daemon-reload`, а если и это не сработало — полный выход из сессии и вход заново. Плюс проверь, что в `/usr/lib/systemd/user/` реально лежат `pipewire.service` и `wireplumber.service`.

### Зачем маскировать, если pulseaudio уже удалён?

Юниты `pulseaudio.socket` и `pulseaudio.service` могли остаться в `/etc/systemd/user/` от прошлой установки или в виде симлинков в `/usr/lib/systemd/user/`. Удаление пакета их не убирает. `systemctl --user mask` перекрывает путь в `/dev/null`, и старый сервер уже не поднимется ни при каких условиях. Проверить текущую маску:

```bash
systemctl --user is-enabled pulseaudio.socket pulseaudio.service
```

### У меня в .bashrc есть alias на pipewire — это важно?

Нет, и лучше его убрать. Демон запускает systemd, алиас на это не влияет, но мешает отладке: команда `pipewire -v` из терминала и та же команда, подставленная в юнит, — разные вещи. Посмотри свой rc-файл на всякий случай:

```bash
grep -n 'pipewire' ~/.bashrc ~/.zshrc ~/.profile 2>/dev/null
```

### Как откатить маску, если PipeWire так и не понадобился?

Сними маску и верни пакеты на место:

```bash
systemctl --user unmask pulseaudio.socket pulseaudio.service
sudo pacman -S pulseaudio pulseaudio-alsa
systemctl --user enable --now pulseaudio.socket
```

Перед этим обязательно верни `~/.config/pulse` из `~/.config/pulse.bak`, иначе настройки устройств и раскладки сокетов потеряются.

## Полезные ресурсы

- [ArchWiki: PipeWire](https://wiki.archlinux.org/title/PipeWire) — устройства, маршруты, split-моно и прочие тонкости поверх работающего демона.
- [ArchWiki: PulseAudio](https://wiki.archlinux.org/title/PulseAudio) — почему coexistence с PipeWire ломает звук и какие файлы конфига читает старый сервер.
- [Pacman от А до Я: команды](https://ordanax.github.io/pacman-ot-a-do-ya-komandy) — установка комплекта пакетов, поиск владельца файла, безопасное удаление с зависимостями.

## Заключение

В девяти случаях из десяти PipeWire не запускается по двум причинам: не установлен `pipewire-pulse` или не замаскирован старый `pulseaudio`. Начни с `pacman -Q pipewire wireplumber pipewire-pulse`, затем `systemctl --user disable --now pulseaudio.socket` и `mask`, и проверь `pactl info`. Если после этого всё ещё `Connection refused`, смотри `journalctl --user -u pipewire -b` и проверяй `XDG_RUNTIME_DIR` с `dbus-run-session` — дальше останется только сбросить конфиг.
