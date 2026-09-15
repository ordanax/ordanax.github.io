---
layout: post
title: "Контент-план блога (внутренний черновик, не публиковать)"
description: Внутренний контент-план блога «Все об Arch Linux». Не для публикации.
search: exclude
sitemap: false
noindex: true
---

# Контент-план блога «Все об Arch Linux» — максимальный вариант

> Внутренний документ. Файл лежит в `_drafts/` и НЕ собирается Jekyll на GitHub Pages,
> поэтому страницы не существует: её нет в sitemap, в поиске по сайту и в индексе поисковиков.
> `search: exclude`/`sitemap: false`/`noindex: true` — страховка на случай локальной сборки с `--drafts`.

**Источники:** 75 тредов bbs.archlinux.org / Unix StackExchange / r/archlinux (2024–2026),
тренды экосистемы 2025–2026, `TROUBLESHOOTER.md` (15 кейсов), карта текущего покрытия блога,
кастомная сборка `klavaro-custom` (`/mnt/hdd/YandexDisk/AI/Klavaro`).

**Приоритеты:** В — высокий (свежая боль, пробел в блоге, трафиковый запрос), С — средний, Н — низкий.

**Формат по умолчанию:** «Симптом → Диагностика → Решение → Нюансы» (как в TROUBLESHOOTER.md),
структура с H2/H3 для SEO. Все статьи на русском.

---

## 0. Спецпункт: Klavaro (кастомная сборка)

> Собственная модификация Klavaro 3.14 в `/mnt/hdd/YandexDisk/AI/Klavaro/klavaro-custom`.
> По git-логу форка: режим «работа над ошибками» (error-practice) с генерацией текста
> из реального словаря языка, Pareto-анализ частых ошибок, цель 100% в статистике
> (вместо заглушки `-1%`), логирование ошибок, `setlocale` для локали через gettext,
> фикс краша при отсутствии intro-файла, фиксы компиляции, двуязычный README,
> история «ё → е → ё» в русских текстах.

- **В | «Klavaro — тренажёр слепой печати в Arch: как поставить и начать»** — `pacman -S klavaro`,
  интерфейс, упражнения (базовый курс, адаптивность, скорость), русская и английская раскладки, статистика.
- **В | «Мой форк Klavaro: режим “работа над ошибками” (error-practice) с анализом Парето»** —
  уникальная тема: что сделано в форке, как собрать из исходников (`./configure && make`),
  чем `data/`/`src/` отличаются от апстрима, что даёт Pareto-режим на практике.
- **С | «Слепая печать на русской раскладке: раскладка vs клавиатура ЙЦУКЕН»** —
  сопутствующая тема (`setxkbmap`/`localectl`), перекликается с форком.

---

## 1. Установка и загрузка

1. **В | «Не грузится после установки: чёрный экран, emergency shell, “triggering uevents”»** —
   диагностика зависаний, падение в emergency shell, починка fstab. (bbs #314900, r/archlinux)
2. **В | «EFI variables are not supported / efibootmgr failed»** — Secure Boot, кривые прошивки,
   `efibootmgr` не пишет запись, `efivar`. (SE, активность 2024)
3. **С | «Дуалбут: Windows пропал из GRUB / GRUB не грузит Windows / не зайти в BIOS после установки»** —
   `os-prober`, восстановление записи, порядок загрузки. (SE)
4. **С | «Один EFI-раздел для дуалбута: правильное монтирование ESP»** — конфликты с Windows Boot Manager. (SE)
5. **С | «Установка Arch на внешний SSD / с заблокированным USB-boot в BIOS»** — обход ограничений прошивки. (bbs #314891, SE)
6. **Н | «Всё ставится в корень, и корневой раздел заполняется»** — почему не отделён `/home`,
   перенос данных, чистка pacman cache. (bbs #314901)

## 2. GRUB / загрузчики

7. **В | «Как переустановить GRUB после поломки»** — `grub-mkconfig`, `grub-install`, chroot с live-USB. (SE, 367K просмотров)
8. **В | «systemd-boot vs GRUB + второе ядро (linux-lts) в загрузчике»** — сравнение, конфиги systemd-boot,
   добавление ядра в boot entry. (bbs #314850)
9. **С | «GRUB не видит ядра после обновления»** — пропали ядра из меню. (bbs #314878)
10. **С | «mkinitcpio v42 сломал TPM-разблокировку LUKS»** — свежая боль 2026: меняются PCR,
   `systemd-cryptenroll` перестаёт работать. (bbs #314912)
11. **Н | «GRUB installation error “airootfs”»** — ошибка установки из archiso. (SE, 120K просмотров)

## 3. Обновление и восстановление после `pacman -Syu`

12. **В | «Сломалось после обновления: единый гайд по откату»** — downgrade из `/var/cache/pacman/pkg`,
    `pacman -U`, снапшоты, chroot, «почему нельзя частично обновляться». (bbs #314363, #314864, r/archlinux)
13. **В | «pacman: “exists on filesystem” error»** — конфликты файлов, когда `--overwrite` оправдан. (SE, 225K просмотров)
14. **В | «GPG: unknown public key / corrupted GPG keys»** — `pacman-key --refresh-keys`, сброс keyring. (SE, 39 голосов; bbs #314898)
15. **В | «pacman fails to commit transaction (invalid or corrupted package)»** — битые зеркала, повреждённый кэш. (SE, 61K просмотров)
16. **С | «libsystemd/libudev undefined symbol / dynamic linker segfaulting»** — частичное обновление,
    переустановка `glibc`. (bbs #314678, #314419)
17. **С | «Обновление сломало KDE Plasma / Discover / chromium resets»** — после апдейта падают приложения и DE. (bbs #314357, #312291, #314895)
18. **С | «“warning: local is newer than core” / пропал пакет из multilib»** — рассинхрон зеркал. (bbs #314636, #314663)
19. **С | «Как пережить обновление: кэш pacman, офлайн-восстановление»** — `/var/cache/pacman/pkg`,
    kernel-module mismatch + `/boot/efi`. (r/archlinux)
20. **Н | «Pacman fails to downgrade packages»** — нюансы даунгрейда. (bbs #285197)

## 4. AUR и безопасность

21. **В | «AUR-хелпер: yay vs paru, pkg vs pkg-bin vs pkg-git»** — что отличает варианты пакетов,
    какой хелпер безопаснее. (SE, 26 голосов)
22. **В | «AUR connection issues (EOF/TLS errors)»** — sticky-тред, 105 ответов / 65K просмотров:
    почему AUR отдаёт EOF/TLS и что делать. (bbs #309805)
23. **В | «Безопасность AUR: как проверять PKGBUILD»** — после инцидента с вредоносными AUR-пакетами 2026-06-12:
    что смотреть в PKGBUILD, как распознать майнер/сниффер, `makepkg --check`. (bbs #313892, #314865, тренды 2026)
24. **С | «Сборка из AUR падает: missing git submodules, checksum mismatch, слишком новый python»** —
    починка падающих сборок. (bbs #314924, #314852, #314838)
25. **С | «AUR-зависимости ломаются после обновления репо (ffmpeg, jsoncpp, ncurses5)»** —
    ABI-поломки, пересборка AUR после апгрейда библиотек. (bbs #314707, #314836, #314618)
26. **Н | «AUR-пакеты не обновляются без --overwrite»** — конфликты файлов. (SE)

## 5. NVIDIA / AMD

27. **В | «NVIDIA: чёрный экран после обновления, нужен nomodeset»** — nvidia vs nvidia-open, когда nomodeset. (bbs #314888, r/archlinux)
28. **В | «nvidia-open рассинхронизируется с ядром: переходить или нет»** — тренд 2026
    (NVIDIA 590 снимает Pascal, open-kernel-mods). (bbs #314815, тренды)
29. **С | «NVIDIA: DisplayPort/HDMI/второй монитор не работает»** — мультимонитор, link training, eDP. (bbs #314859, #314908, SE)
30. **С | «AMDGPU: поломки после linux-firmware-amdgpu / 4:2:0 HDMI / фризы»** — откат firmware,
    chroma subsampling, фризы при загрузке. (bbs #314887, #314819, #314885)
31. **С | «Гибридная графика: prime-run, screen tearing, выбор GPU для Steam»** — `DRI_PRIME`, переключение GPU. (bbs #314915, #314856, SE)
32. **Н | «Legacy NVIDIA 340/390 на новом ядре»** — старые карты, nouveau vs проприетарный. (bbs #314917, #314732)

## 6. Звук (PipeWire)

33. **В | «Нет звука после свежей установки / после обновления»** — wireplumber, почему после `-Syu` пропал звук. (SE, 38 голосов; bbs #314785, #314799)
34. **В | «Звук только из наушников / не переключаются динамики и гарнитура»** — переключение профилей,
    `hdajackretask`. (SE, 5.8K просмотров; bbs #314186, #314796)
35. **В | «Микрофон не работает: USB-микрофон молчит в PipeWire, постоянный шум»** — wireplumber, права,
    выбор источника. (SE, 20 голосов; bbs #314817) — наложить на кейс «Bluetooth-звук WirePlumber suspend» из TROUBLESHOOTER.
36. **С | «Микрофон гарнитуры не работает, а встроенный — да»** — jack detection, переключение профилей. (bbs #309942, #314906, #299258)
37. **С | «wireplumber обновился и сломал звук»** — откат пакета (Scarlett Solo 4th Gen и т.п.). (bbs #314820)
38. **С | «PipeWire не запускается / Can't get Pipewire started»** — systemd-юниты, конфликт с pulseaudio. (bbs #314640)
39. **С | «Звук по HDMI не работает»** — переключение sink на NVIDIA/AMD. (SE, 41 голос)
40. **Н | «Cannot replace jack2 with pipewire-jack»** — JACK-совместимость. (bbs #314335)

## 7. Bluetooth

41. **В | «Bluetooth-наушники: не подключаются, отваливаются после обновления, тихий звук»** —
    A2DP, кодеки, обрывы (Sony WH-1000XM5 Endpoint unregistered и др.). (bbs #313545, #314728; SE, 22 голоса)
42. **С | «Качественный кодек и микрофон одновременно»** — почему при включении микрофона падает качество,
    mSBC, PipeWire. (SE, 59 голосов)
43. **С | «bluetooth.service запущен, но NotReady»** — rfkill, прошивки. (SE, 142K просмотров)

## 8. Wayland и DE

44. **В | «Приложения размытые/кривые на Wayland (Hyprland), XWayland»** — масштабирование,
    fractional scaling. (SE) — наложить на кейс «KWin-правила» из TROUBLESHOOTER.
45. **С | «Could not find the Qt platform plugin “wayland”»** — qt5/6-wayland. (SE, 72K просмотров)
46. **С | «Какой DE выбрать / как сменить окружение»** — KDE vs GNOME vs Hyprland без переустановки. (r/archlinux, SE)
47. **С | «GDM/SDDM не запускается / “Unit file gdm.service does not exist”»** — display manager, автологин. (SE, 5.2K просмотров)
48. **С | «KDE Plasma крашится / ведёт себя странно после обновления»** — сброс настроек, kwallet. (bbs #314822, #314902, #314561)
49. **Н | «kdeconnect и приложения падают после перехода на Wayland»** — XWayland-фолбэк. (bbs #314883, #314580)

## 9. Гибернация и suspend/resume

50. **В | «Гибернация сломалась (снова): resume=, swapfile vs swap partition»** — почему ломается
    после каждого обновления ядра. (bbs #313116, #314873, #314869)
51. **С | «Systemd suspend не уходит в глубокий сон: s2idle vs S3»** — `mem_sleep` на новых ноутбуках. (bbs #314925, #314876)
52. **С | «Зависания при сне/пробуждении, ноутбук просыпается сам»** — `HandleLidSwitch`, wakeup sources. (bbs #282837, #314814, SE)
53. **Н | «Как отключить автозасыпание при закрытии крышки»** — logind.conf. (SE, 185K просмотров)

## 10. Сеть / VPN / Wi-Fi

54. **В | «Wi-Fi обрывы на MediaTek MT7921e / Realtek RTL8852CE, конфликт BT+Wi-Fi»** —
    обрывы после обновления ядра. (bbs #314406, #302036)
55. **В | «Корпоративные VPN: Fortinet/OpenConnect, L2TP, WireGuard, DNS-утечки»** — kill switch,
    split tunneling. (bbs #314407, #314881, #314387, #314916) — наложить на кейс «гео-блоки РФ» из TROUBLESHOOTER.
56. **С | «NetworkManager: “Secrets were required, but not provided”»** — keyring, nm-applet. (SE, 205K просмотров)
57. **С | «iwctl не подключается / Network is unreachable»** — диагностика IWD. (SE, 34 голоса)
58. **Н | «Своя точка доступа / USB-модем с dhcpcd»** — dhcpcd vs systemd-networkd. (bbs)

## 11. Диски / btrfs / монтирование

59. **В | «NTFS-диск виден в Windows, но не монтируется в Linux»** — ntfs3, Fast Startup. (SE, 2K просмотров)
    — наложить на кейс «монтирование» из TROUBLESHOOTER.
60. **С | «Снапшоты и откат системы: snapper/timeshift/grub-btrfs»** — стратегия после поломки -Syu. (bbs #314900)
61. **С | «btrfs: монтирование сабволюмов, авто-монтирование внешних дисков через udisks»** — `subvol=`, `@home`. (bbs #314848)
62. **Н | «LUKS2: keyfile, добавление/смена паролей, TPM»** — из кейса «LUKS keyfile» из TROUBLESHOOTER.

## 12. Локаль / шрифты / кириллица

63. **В | «Иероглифы и квадраты вместо символов: что за проблема и как вылечить»** —
    noto-fonts, ttf-*, fallback, эмодзи. (SE, 37 голосов)
64. **В | «tmux: need UTF-8 locale / всё жалуется на locale»** — генерация локалей, `ru_RU.UTF-8`,
    кириллица в терминале. (SE, 47 и 30 голосов)
65. **Н | «Как объединить варианты шрифтов для fontconfig»** — семейства и рендеринг. (bbs #314854)

## 13. Gaming

66. **С | «Steam: “bwrap: setting up uid map: Permission denied” / flatpak Steam не видит DISPLAY»** —
    sandbox, `dbus-update-activation-environment`. (bbs #314503, r/archlinux)
67. **С | «Игры крашатся: Elden Ring, звук, рендеринг после обновления Mesa»** — Proton, откат Mesa. (bbs #313754, #314403, #314792)
68. **С | «Геймпады: DualSense/Pro Controller не определяется по Bluetooth»** — xpadneo, hid-playstation. (bbs #313655)
69. **Н | «FPS-просадки и троттлинг (Iris Xe, Core Ultra): power management»** — термонастройка. (bbs #314634, SE)

## 14. Железо и периферия

70. **С | «Тачпад: лагает, дёргается, не работает после обновления ядра»** — libinput, synaptics. (bbs #300749, #314789, #314782)
71. **С | «Веб-камера: чёрное изображение / не определяется (ipu6)»** — v4l2. (bbs #314669, #314884, #314905)
72. **С | «Принтер: CUPS не печатает, тестовая страница падает»** — драйверы, avahi. (bbs #314889, #314800)
73. **С | «Случайные перезагрузки / kernel panic (Ryzen)»** — journalctl, ACPI/PSU. (bbs #314842, #314870)
74. **Н | «ACPI BIOS Error / AE_NOT_FOUND / No handler for Region RAM_»** — безвредно ли, как убрать из логов. (SE, 23 голоса; bbs #222409)
75. **Н | «OOM killer не срабатывает, система зависает»** — earlyoom, systemd-oomd. (SE, 55 голосов)

## 15. Тренды и разборы (категория news)

76. **В | «Вредоносные AUR-пакеты 2026: разбор инцидента и как защититься»** — продолжение темы 23. (тренды)
77. **С | «NVIDIA 590: конец поддержки Pascal, переход на open-kernel-mods»** — что это значит для владельцев старых карт. (тренды)
78. **С | «Что нового: pacman v7 / новый формат ISO / iptables→nft»** — обзор без воды. (тренды)
79. **С | «Plasma 6.4 на X11: что работает из коробки и что чинить руками»** — (тренды)
80. **Н | «HDR на Wayland: когда это станет возможно»** — (тренды)

## 16. Практические кейсы из TROUBLESHOOTER.md (формат «по симптомам»)

81. **В | «yay выдаёт EOF при обновлении AUR: дело в IPv6 (gai.conf)»** — кейс с корневой причиной.
82. **В | «Bluetooth-звук пропадает при блокировке/уходе в сон: WirePlumber suspend»** — кейс.
83. **С | «Реалтек уходит в downshift: почему скорость падает до 100 Мбит»** — кейс.
84. **С | «Гео-блоки от российских IP: что делать на Arch»** — кейс (пересекается с 55).
85. **С | «GOP/simpledrm: чёрный экран на новых картах с UKI»** — кейс.
86. **Н | «Wine-шим powershell: экзотика, но история»** — кейс.
87. **С | «Свободный порт уже занят: как найти и убить процесс»** — общий гайд по `ss`/`lsof`.
88. **Н | «Локальная LLM на Arch (сборка из исходников)»** — кейс.
89. **Н | «Квота: игра не стартует из-за занятого порта»** — мини-кейс.

---

**Итого: ~90 тем.** Из них 28 «В» — ядро квартального плана.
Свежие боли 2026 (mkinitcpio/TPM, AUR-инцидент, nvidia-open), кейсы из TROUBLESHOOTER
и форк Klavaro — уникальный контент, которого нет у других русскоязычных блогов.