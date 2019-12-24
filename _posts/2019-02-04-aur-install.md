---
layout: post
title: Какой AUR helper выбрать?
description: Не знаете какой AUR helper выбрать? Давайте разберемся!
date: 2019-02-04 00:34:09 +0500
permalink: /aur-install
edit: true
categories: 
- install
- scripts
- video
tags:
- scripts
- install
- video
- aur
- yay
- опрос
---
<p><img alt="Какой AUR helper выбрать?" class="post-image rounded" src="https://ordanax.github.io/img/aur-install.png" />
Если вы посмотрите таблицу <noindex><a href="https://vk.cc/88yr8q" target="_blank" rel="nofollow">https://vk.cc/88yr8q</a></noindex> из нее можно увидеть что yaourt и aurman помечен, как более не поддерживаемые.
Большинство пользователей склоняются к yay. 
Чтобы установить yay вы можете вопрользоваться скриптом ниже. Достаточно вбить всего 1 троку. Синтаксис точно такй-же как и в pacmam.</p>

Чтобы установить программу пишем

```bash
yay -S nazvanie_paketa
```

Для поиска по AUR можно не писать -Ss

```bash
yay nazvanie_paketa
```

Чтобы обновить всю систему включая AUR пакеты

```bash
yay -Syu
```

## Как установить AUR
Простой способ установить yay

```bash
wget git.io/yay-install.sh && sh yay-install.sh
```

<h2>Результаты опроса</h2>
<div class="text-center">
	<table width="100%" cellspacing="0">
		<tr> 
			<td>
				<div id="vk_poll"></div>
				<script type="text/javascript">
					VK.Widgets.Poll("vk_poll", {}, "320990931_a910f4b472d3a23482");
				</script>
			</td>
		</tr>
	</table>
</div>
