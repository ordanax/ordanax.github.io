---
layout: post
title: Получение красивых коротких ссылок на git.io
description: Получение красивых коротких ссылок на git.io
date: 2019-02-03 21:50:09 +0500
permalink: /poluchenie-krasivyh-korotkih-ssylok-na-gitio
categories: 
- scripts
- useful
tags:
- archlinux
- git
- github

---
<p><img alt="Получение красивых коротких ссылок на git.io" class="post-image rounded" src="https://ordanax.github.io/img/poluchenie-krasivyh-korotkih-ssylok-na-gitio.png" /></p>На гитхабе модно получить короткие ссылки при помощи git.io, НО! Сокрщая таким образом мы получаем ссылку наподобе git.io/djAVq , что очень не удобно особенно если нужна постоянно и легко запоменающаяся ссылка.

В этой статье я расскажу, как получить ссылку где вместо кракозябер будет то, что вы сами напишите при генерации ссылки.

Например у меня есть скрипт по установке Arch Linux https://github.com/ordanax/arch2018.git Но она неудобно длинная и сложно запоминаемая. Такая git.io/djAVq нам тоже не подойдет. 

Рассмотрим как, получить вот такую ссылку git.io/arch1.sh


<h3 class="font-weight-bold">Шаги:</h3>
<br>1) Переходим на страницу гитхаба с вашим скриптом.
<br>2) Получаем исходный код нажав на "row" 
<br>3) В строке ниже, меняем SSILKA_NA_SCRIPT на свою, которую получили в предыдущем шаге
<br>4) Вместо SHORT_LINK пишем желаемую короткую ссылку с .sh наконце.
<br>3) Подготовленную команду вбивает в терминале и получаем короткую ссылку.


<code>curl -i https://git.io -F "url=SSILKA_NA_SCRIPT" -F "code=SHORT_LINK.sh"</code>


<p>Вот пример подготовленной команды:</p>

<code>curl -i https://git.io -F "url=https://raw.githubusercontent.com/ordanax/arch2018/master/arch1.sh" -F "code=arch1.sh"</code>


<p>И результат ее выполнения:</p>

<code>git.io/arch1.sh</code>


В этом нет ничего сложного, но об этомй возможности мало кто знает, а использование таких ссылок решает многие пролемы.