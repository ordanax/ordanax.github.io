---
layout: post
title: Получение красивых коротких ссылок на git.io
description: Получение красивых коротких ссылок на git.io
date: 2019-02-03 21:50:09 +0500
permalink: /poluchenie-krasivyh-korotkih-ssylok-na-gitio
edit: true
categories: 
- scripts
- useful
tags:
- archlinux
- git
- github

---
![Получение красивых коротких ссылок на git.io](../img/poluchenie-krasivyh-korotkih-ssylok-na-gitio.png){:style="float: left;margin-right: 25px;margin-top: 10px;"} На гитхабе можно получить короткие ссылки при помощи git.io, НО! Сокращая таким образом мы получаем ссылку наподобе git.io/djAVq , что очень не удобно особенно если нужна постоянно и легко запоменающаяся ссылка.

В этой статье я расскажу, как получить ссылку, где вместо кракозябер будет то, что вы сами напишите при генерации ссылки.

Например у меня есть скрипт по установке Arch Linux https://github.com/ordanax/arch2018.git Но она неудобно длинная и сложно запоминаемая. Такая git.io/djAVq нам тоже не подойдет. 

Рассмотрим как, получить вот такую ссылку git.io/arch1.sh

### Шаги:
 1) Переходим на страницу гитхаба с вашим скриптом.  
 2) Получаем исходный код, нажав на "row"  
![Первичная настройка i3wm](https://i.imgur.com/MpSbSMN.png)  
 3) В строке ниже, меняем SSILKA_NA_SCRIPT на свою, которую получили в предыдущем шаге  
 4) Вместо SHORT_LINK пишем желаемую короткую ссылку с .sh наконце.  
 5) Подготовленную команду вбиваем в терминале и получаем короткую ссылку.  


```sh
curl -i https://git.io -F "url=SSILKA_NA_SCRIPT" -F "code=SHORT_LINK.sh"
```


Вот пример подготовленной команды:

```sh
curl -i https://git.io -F "url=https://raw.githubusercontent.com/ordanax/arch2018/master/arch1.sh" -F "соde=arch1.sh"
```


И результат ее выполнения:

```sh
git.io/arch1.sh
```


В этом нет ничего сложного, но об этой возможности мало кто знает, а использование таких ссылок решает многие пролемы. Я например использую подобные ссылки для своих скриптов, например в скрипте для установки Arch Linux.

## Способ не сработает, если:  
1) Ссылка уже была сокращена до этого  
2) Короткая ссылка уже занята

Решение это изменить либо название сокращаемого файла или название короткой ссылки.

Если кому нужен наглядный пример, как это делается, то смотрите это видео:
<iframe width="560" height="315" src="https://www.youtube.com/embed/vh5rbx3QuvQ" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
