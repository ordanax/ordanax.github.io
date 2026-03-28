---
layout: post
title: Исправление ошибки picom при перезагрузке Arch Linux
description: Решение проблемы с устаревшими опциями GLX в compositor picom
---

## Ошибка picom при запуске i3wm

После обновления пакетов Arch Linux при перезагрузке компьютера может появиться ошибка запуска compositor **picom**:

```
picom: invalid option -- 'glx-no-rebind-pixmap'
```

или

```
[ WARN ] "glx-no-stencil" has been removed.
```

Эта ошибка возникает из-за того, что в новых версиях picom устаревшие опции GLX были удалены, но они всё ещё указаны в вашей конфигурации.

![Ошибка picom](/img/picom.png)

## Причина ошибки

Опции `--glx-no-rebind-pixmap` и `--glx-no-stencil` являются **устаревшими (deprecated)** и были удалены в версии picom 10+.

Эти опции могут находиться в:

1. **Конфигурации i3wm** (`~/.config/i3/config` или `~/.i3/config`)
2. **Конфигурационном файле picom** (`~/.config/picom/picom.conf` или `~/.config/picom.conf`)
3. **Автозапуске через .xinitrc или другие скрипты**

## Способ 1: Исправление через конфиг i3wm

Откройте файл конфигурации i3:

```bash
nano ~/.config/i3/config
```

Найдите строку запуска picom:

```bash
# Старый вариант (вызывает ошибку)
exec_always --no-startup-id picom --experimental-backends --glx-no-rebind-pixmap --glx-no-stencil
```

Удалите устаревшие опции:

```bash
# Исправленный вариант
exec_always --no-startup-id picom --experimental-backends
```

Сохраните файл (`Ctrl+O`, `Enter`, `Ctrl+X`) и перезагрузите i3:

```bash
$mod+Shift+r
```

## Способ 2: Исправление через конфиг picom

Если опции указаны в `picom.conf`:

```bash
nano ~/.config/picom/picom.conf
```

Найдите и закомментируйте или удалите строки:

```bash
# Удалить или закомментировать:
# glx-no-rebind-pixmap = true;
# glx-no-stencil = true;
```

## Способ 3: Автоматическое исправление скриптом

Создайте скрипт для автоматического исправления:

```bash
#!/bin/bash
# fix-picom.sh

echo "Исправление ошибки picom..."

# Исправление в i3 config
if [ -f "$HOME/.config/i3/config" ]; then
    sed -i 's/--glx-no-rebind-pixmap//g' "$HOME/.config/i3/config"
    sed -i 's/--glx-no-stencil//g' "$HOME/.config/i3/config"
    echo "✓ Исправлен ~/.config/i3/config"
fi

# Исправление в picom.conf
if [ -f "$HOME/.config/picom/picom.conf" ]; then
    sed -i 's/glx-no-rebind-pixmap/#glx-no-rebind-pixmap/g' "$HOME/.config/picom/picom.conf"
    sed -i 's/glx-no-stencil/#glx-no-stencil/g' "$HOME/.config/picom/picom.conf"
    echo "✓ Исправлен ~/.config/picom/picom.conf"
fi

echo "Готово! Перезагрузите i3wm (Mod+Shift+r)"
```

Запустите скрипт:

```bash
chmod +x fix-picom.sh
./fix-picom.sh
```

## Проверка работы picom

После исправления проверьте, что picom запускается без ошибок:

```bash
picom --experimental-backends
```

Если compositor работает корректно, перезагрузите систему или перезапустите i3wm.

## Альтернативные опции (если нужна оптимизация GLX)

Если вы использовали `--glx-no-rebind-pixmap` для оптимизации, в новых версиях picom эта опция не требуется — backend GLX был значительно улучшен.

Для тонкой настройки производительности используйте файл `picom.conf`:

```bash
backend = "glx";
vsync = true;
```

## Полезные ссылки

- [Arch Wiki — Picom](https://wiki.archlinux.org/title/Picom)
- [Репозиторий picom на GitHub](https://github.com/yshui/picom)
- [История изменений picom (Changelog)](https://github.com/yshui/picom/blob/master/CHANGELOG.md)

---

*Статья актуальна для: picom 10+ | Arch Linux 2024-2026*
