---
layout: post
title: Установка и настройка i3wm c polybar
description: Ман по установке и настройке i3wm с polybar
date: 2020-08-14 17:43:09 +0500
permalink: /i3wm_polybar
categories: 
- install
- configs
- i3wm
- video
tags:
- checklists
edit: true
---
![Тайлинг i3wm](../img/i3wm_polybar.jpg){:style="float: left;margin-right: 25px;margin-top: 10px;"} В [прошлой статье](https://ordanax.github.io/i3wm) я рассказывал об минимальной установке и настройка i3wm с i3status.
В этой статье мы копнем немного глубже, установим и на строим i3wm c polybar. Так же установим необходимые скрипты. Заменим привычный pamac на упрощенный индикатор обновлений.


# Установка и настройка i3wm + polybar

## Ссылки
[Официальная документация по i3wm](https://i3wm.org/docs/userguide.html)<br>
[i3wm в ArchWiki](https://wiki.archlinux.org/index.php/i3_%28%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9%29)<br>
[Wiki по Polybar](https://github.com/polybar/polybar/wiki)<br>
[Мой конфиг с пояснениями внутри](https://github.com/ordanax/dots/tree/master/3wm_v_3)<br>


**Нам понадобится:** <br>
    1. **i3wm** — оконный менеджер или его форк (ответвление) i3-gaps <br>
    2. **Polybar** — наша панелька<br>
    3. **dmenu** — утилита для запуска программ <br>
    4. **ttf-font-awesome** — шрифтовые иконки <br>
    5. **feh** — установка обоины на рабочий стол <br>
    6. **pcmanfm** — файловый менеджер <br>
    7. **gvfs** и **udiskie** — для авто монтирования внешних дисков <br>
    8. **xorg-xbacklight** — для управлением яркостью экрана <br>
    9. **geeqie** — для просмотра фото <br>
    10. **tumbler** — для отображения миниатюр фото <br>
    11. **sakura** — терминал <br>
    12. **picom** — для прозрачности окон и для устранения тиринга (вместо compton)<br>
    13. **ttf-weather-icons** — Иконнки для скрипта погоды<br>
    14. **jq** — этот пакет также нужен для скрипта для отображения погоды<br>
    15. **tlp** — для скрипта отображения количества обновлении<br>
    16. **ttf-clear-sans** — хороший шрифт<br>
    17. **pacman-contrib** — зависимость для скрипта по обновлениям<br>
    18. **playerctl** — для управления горячими клавишами аудиоплеера<br>
    19. **speedtest-cli** - для полибар скрипта, который отображает скорость интернета<br>
   
    
## Ставим необходимые пакеты.

```
#pacman -S i3-wm dmenu pcmanfm ttf-font-awesome feh gvfs udiskie xorg-xbacklight ristretto tumbler picom jq pacman-contrib sakura speedtest-cli
```
```
$yay -S polybar ttf-weather-icons ttf-clear-sans tlp playerctl
```

**Настройки тем делаем правкой файлов настройки GTK:**
1. [~/.gtkrc-2.0](https://github.com/ordanax/dots/blob/master/3wm_v_3/gtkrc-2.0.tar.gz) и <br>
2. [~/.config/gtk-3.0/settings.ini](https://github.com/ordanax/dots/blob/master/3wm_v_3/gtk-3.0/settings.ini)<br>

Я использовал ручную настройку, если вам больше нарвится настройка с GUI то используйте для этих целей пакет **lxappearance**


## Горячие клавиши для аудиоплеера
Чтобы работли клавиши ⏮ ⏵ ⏭ нужно не забыть поставить пакет **playerctl** и добавить в конфиг следующий код:

```
# Media player controls
bindsym XF86AudioPlay exec playerctl play
bindsym XF86AudioPause exec playerctl pause
bindsym XF86AudioNext exec playerctl next
bindsym XF86AudioPrev exec playerctl previous
```
## Подключение скриптов

В своей настройке я использовал следующие скрипты:<br>
1) Скрипт погоды<br>
![скрипт погоды](../img/wheather.png)<br>
2) Скрипт для отображения количества обновлений в системе вместо pamac. <br>
![скрипт погоды](../img/update.png)<br>
3) Отображения заряда батареи<br>
4) Отображение скорости интернета
5) Отображение курса валют

Эти скрипты и инструкцию к ним смотрите тут [https://github.com/x70b1/polybar-scripts.git](https://github.com/x70b1/polybar-scripts.git)<br>
Там большое кол-во скриптов, найдете все, что вам по душе.
Скрипт по скороси интернет [https://github.com/ShiroUsagi-san/speedtest-polybar-module](https://github.com/ShiroUsagi-san/speedtest-polybar-module)
Скрипт корса валют в моем конфиге [https://github.com/ordanax/dots/blob/master/polybar/scripts/btc](https://github.com/ordanax/dots/blob/master/polybar/scripts/btc)

## Видео демонстрация
<iframe width="560" height="315" src="https://www.youtube.com/embed/uh_WeYrjCOY" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

