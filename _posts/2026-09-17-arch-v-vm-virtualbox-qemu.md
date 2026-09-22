---
layout: post
title: "Arch в виртуальной машине: VirtualBox, VMware и QEMU"
description: "Как запустить Arch Linux в виртуальной машине: QEMU/KVM, VirtualBox и VMware, общие папки, 3D-ускорение, virtio-драйверы и UEFI."
date: 2026-09-17 00:00:00 +0300
permalink: /arch-v-vm-virtualbox-qemu
categories:
- linux
- arch linux
- virtual
- setup
tags:
- virtualbox
- qemu
- kvm
- vmware
- virt-manager
- virtio
edit: true
---


Arch Linux отлично живёт в виртуальной машине — подойдёт любой гипервизор, но лучший опыт даёт QEMU/KVM с virt-manager: он быстрее, ближе к железу и полностью открытый. VirtualBox проще для новичка и работает на любом хосте, VMware — вариант для тех, кто привык к её экосистеме. Внутри гостя всё сводится к паре пакетов: гостевые утилиты, virtio-драйверы и агент.

## Какая виртуальная машина лучше для Arch

Честный ответ: для Arch на Linux-хосте лучший выбор — QEMU/KVM. Это не эмуляция, а аппаратная виртуализация: гость исполняется прямо на CPU через модуль ядра `kvm`. Отсюда почти нативная скорость диска и сети, если включить virtio-драйверы.

VirtualBox — компромисс. У него удобный GUI, снапшоты, общие папки из коробки. Но модули `vboxdrv` собираются через DKMS, а после каждого обновления ядра их пересобирает pacman-хук. На Wayland бывают приколы с захватом клавиатуры.

VMware Workstation ставится из AUR, проприетарная, но с ноября 2024 бесплатна для личного использования. Если ты уже работал с ней на Windows — привычная среда, ничего менять не надо.

## QEMU/KVM — быстрый старт

Ставим всё разом: сам QEMU, демон libvirt и графическую обёртку virt-manager.

```bash
sudo pacman -S qemu-full libvirt virt-manager
sudo usermod -aG libvirt $USER
sudo systemctl enable --now libvirtd
```

После `usermod` выйди из сессии и зайди заново — группа подхватится. Проверь, что аппаратная виртуализация доступна:

```bash
ls /dev/kvm
grep -E 'vmx|svm' /proc/cpuinfo
```

`vmx` — Intel, `svm` — AMD. Модуль `kvm_intel` или `kvm_amd` ядро подгружает сам, если в BIOS включена виртуализация. Дальше открываешь virt-manager, жмёшь «Создать новую виртуальную машину», указываешь ISO Arch и следуешь обычной установке — она ничем не отличается от установки на железо. Если только начинаешь, держи под рукой [пошаговую установку Arch Linux 2026](https://ordanax.github.io/ustanovka-archlinux-2026-poshagovaya) и [чек-лист](https://ordanax.github.io/chek-list-po-ustanovke-archlinux-2019).

## Установка Arch в VirtualBox

На хосте:

```bash
sudo pacman -S virtualbox virtualbox-host-dkms linux-headers
sudo modprobe vboxdrv
sudo usermod -aG vboxusers $USER
```

Модуль `vboxdrv` обязателен, без него ни одна машина не стартует. Для bridged-сети понадобятся ещё `vboxnetadp` и `vboxnetflt` — они подгружаются автоматически.

Внутри гостя Arch ставится как обычно, а после первого входа:

```bash
sudo pacman -S virtualbox-guest-utils
sudo systemctl enable --now vboxservice
```

Это даёт общий буфер обмена, drag-and-drop и нормальное разрешение экрана. Для USB 3.0 и 3D-ускорения нужен Extension Pack — пакет `virtualbox-ext-oracle` из AUR.

## VMware Workstation: что нужно знать

`vmware-workstation` собирается из AUR, модули `vmmon` и `vmw_vmci` пересобираются через DKMS. После установки запусти `vmware-networks-configuration.service`, иначе гость не получит сеть.

В гостевой Arch вместо проприетарных VMware Tools ставь открытые:

```bash
sudo pacman -S open-vm-tools
sudo systemctl enable --now vmtoolsd
```

Для скорости можно переключить виртуальные адаптеры на паравиртуальные: SCSI на `pvscsi` (модуль `vmw_pvscsi`), сеть на `vmxnet3`. Оба есть в стандартном ядре Arch.

## Как настроить общую папку

В VirtualBox общая папка монтируется одной командой. Создаёшь папку в настройках машины (например, `Shared`), затем в госте:

```bash
sudo mount -t vboxsf Shared ~/shared
```

Чтобы монтировалась при старте, добавь строку в `/etc/fstab`:

```
Shared  /home/пользователь/shared  vboxsf  defaults,uid=1000,gid=1000  0  0
```

В QEMU/KVM общая папка делается через virtiofsd — это быстрее, чем vboxsf, но настраивается в XML-конфиге машины. Для большинства задач проще поднять SSH и ходить по файлам через `scp` или `rsync`.

## Как включить 3D-ускорение

В QEMU/KVM 3D работает через virtio-gpu с virgl. В virt-manager: «Видео» → модель `virtio`, галочка «3D-ускорение». В госте поставь `virgl` и `spice-vdagent`:

```bash
sudo pacman -S virgl spice-vdagent
sudo systemctl enable --now spice-vdagent
```

`spice-vdagent` заодно даёт общий буфер обмена и динамическое разрешение. В VirtualBox 3D включается в настройках машины, но только при установленном Extension Pack, и работает заметно хуже, чем virgl.

## UEFI и Secure Boot в виртуальной машине

По умолчанию QEMU грузит гость в legacy BIOS. Чтобы проверить установку в UEFI-режиме, поставь прошивку OVMF:

```bash
sudo pacman -S edk2-ovmf
```

В virt-manager при создании машины выбери «Прошивка: UEFI». Secure Boot в гостевой Arch включается через `sbctl` — в виртуалке это безопасная песочница, чтобы потренироваться перед реальным железом. Сеть по умолчанию — NAT через `virbr0`, для доступа к гостью снаружи переключайся на bridge.

## Частые вопросы

### Нужен ли Secure Boot в виртуальной машине?

Не обязателен. В VM он нужен только как тренировка перед включением на реальном железе или для тестов подписанных загрузчиков.

### Почему гость тормозит?

Чаще всего виноваты эмулированные устройства. В QEMU включи virtio для диска и сети, в VirtualBox поставь гостевые утилиты, в VMware — open-vm-tools. И проверь, что в BIOS хоста включена виртуализация.

### Можно ли перенести машину между гипервизорами?

Да. Образы конвертируются через `qemu-img convert`: VDI/VMDK в qcow2 и обратно. Внутри гостя поменяй драйверы диска и сети на универсальные, и машина заведётся где угодно.

### Чем virtio лучше эмулированных устройств?

Virtio — паравиртуализация: гость и гипервизор договариваются напрямую, без эмуляции железа. Диск и сеть работают в разы быстрее, нагрузка на CPU ниже.

## Заключение

Для Arch на Linux-хосте бери QEMU/KVM с virt-manager — это самый быстрый и честный вариант. VirtualBox выручит, если нужен простой GUI или ты на Windows-хосте. VMware — рабочий, но проприетарный выбор. В любом случае внутри гостя поставь гостевые утилиты и virtio-драйверы: именно они превращают «тормозящую виртуалку» в полноценную систему. Установка Arch в VM ничем не отличается от установки на железо — если хочешь повторить её быстро, вот [установка Arch за 15 минут](https://ordanax.github.io/ustanovka-archlinux-2019-za-15-minut).

## Полезные ресурсы

- [QEMU — ArchWiki](https://wiki.archlinux.org/title/QEMU) — полный гайд по QEMU, virtio и сети
- [VirtualBox — ArchWiki](https://wiki.archlinux.org/title/VirtualBox) — установка, модули, гостевые утилиты