---
layout: post
title: Какой AUR helper выбрать?
description: Не знаете какой AUR helper выбрать? Давайте разберемся!
date: 2019-02-04 00:34:09 +0500
permalink: /aur-install
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
Если вы посмотрите таблицу <noindex><a href="https://vk.cc/88yr8q" target="_blank" rel="nofollow">https://vk.cc/88yr8q</a></noindex> из нее можно увидеть что yaourt и aurman помечан как более не поддерживаемые.
Большинство пользователей склоняются к yay. 
Чтобы установить yay вы можете вопрользоваться скриптом ниже. Достаточно вбить всего 1 троку. Синтаксис точно такй-же как и в pacmam.</p>

<p>Чтобы установить программу пишем
<br><code>yay -S nazvanie_paketa</code></p>

<p>Для поиска по AUR можно не писать -Ss
<br><code>yay nazvanie_paketa</code></p>

<p>Чтобы обновить всю систему включая AUR пакеты
<br><code>yay -Syu</code>
</p>

<h2>Результаты опроса</h2>
<div class="text-center">
	<table width="50%" cellspacing="0">
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
<br><b>Простой способ установить yay</b>
<code>wget git.io/yay-install.sh && sh yay-install.sh</code>