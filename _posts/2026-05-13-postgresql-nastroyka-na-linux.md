---
layout: post
title: PostgreSQL настройка на Linux — полное руководство
description: Практический гайд по установке, настройке и управлению PostgreSQL на Linux для начинающих
date: 2026-05-13 08:00:00 +0300
categories:
- linux
- database
- postgresql
- server
tags:
- postgresql
- database
- linux
- server
- configuration
---

![PostgreSQL](../img/postgresql.png){:style="float: left;margin-right: 25px;margin-top: 10px;"} PostgreSQL — мощная объектно-реляционная СУБД с открытым исходным кодом. Этот гайд поможет установить и настроить PostgreSQL на Linux.

## Установка PostgreSQL

### Arch Linux

```bash
sudo pacman -S postgresql
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### Fedora

```bash
sudo dnf install postgresql postgresql-server
sudo postgresql-setup initdb
```

## Инициализация базы данных

### Arch Linux

```bash
sudo -u postgres initdb -D /var/lib/postgres/data
```

### Запуск службы

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

## Настройка пользователя

### Смена пароля пользователя postgres

```bash
sudo -u postgres psql
```

Внутри psql:
```sql
\password postgres
```

Введите новый пароль дважды.

### Создание нового пользователя

```bash
sudo -u postgres createuser --interactive
```

Следуйте инструкциям.

## Создание базы данных

### Через psql

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE mydb;
CREATE USER myuser WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
\q
```

### Через командную строку

```bash
sudo -u postgres createdb mydb
sudo -u postgres createuser myuser
```

## Подключение к базе данных

### Через psql

```bash
sudo -u postgres psql
```

### Подключение к конкретной базе

```bash
sudo -u postgres psql -d mydb
```

### Подключение с конкретным пользователем

```bash
psql -U myuser -d mydb
```

## Основные команды psql

```sql
-- Список баз данных
\l

-- Подключение к базе
\c database_name

-- Список таблиц
\dt

-- Описание таблицы
\d table_name

-- Выход
\q

-- Помощь
\?
```

## Конфигурация PostgreSQL

### Файлы конфигурации

- `/var/lib/postgres/data/postgresql.conf` — основные настройки
- `/var/lib/postgres/data/pg_hba.conf` — аутентификация

### Разрешение удалённых подключений

Отредактируйте `postgresql.conf`:
```bash
sudo nano /var/lib/postgres/data/postgresql.conf
```

Найдите и измените:
```
listen_addresses = '*'
```

Отредактируйте `pg_hba.conf`:
```bash
sudo nano /var/lib/postgres/data/pg_hba.conf
```

Добавьте:
```
host    all             all             0.0.0.0/0               md5
```

Перезапустите службу:
```bash
sudo systemctl restart postgresql
```

## Резервное копирование

### Резервное копирование базы данных

```bash
sudo -u postgres pg_dump mydb > backup.sql
```

### Восстановление из резервной копии

```bash
sudo -u postgres psql mydb < backup.sql
```

### Резервное копирование всех баз

```bash
sudo -u postgres pg_dumpall > all_backup.sql
```

## Управление службой

```bash
# Статус службы
sudo systemctl status postgresql

# Запуск
sudo systemctl start postgresql

# Остановка
sudo systemctl stop postgresql

# Перезапуск
sudo systemctl restart postgresql

# Включение автозапуска
sudo systemctl enable postgresql
```

## Решение проблем

### Проблема: Не удаётся подключиться

Проверьте статус службы:
```bash
sudo systemctl status postgresql
```

Проверьте логи:
```bash
sudo journalctl -xe | grep postgres
```

### Проблема: Ошибка аутентификации

Проверьте `pg_hba.conf`:
```bash
sudo nano /var/lib/postgres/data/pg_hba.conf
```

Убедитесь, что метод аутентификации правильный.

### Проблема: Порт занят

Проверьте, что порт 5432 свободен:
```bash
sudo netstat -tlnp | grep 5432
```

## Полезные команды

```bash
# Проверка версии PostgreSQL
psql --version

# Проверка активных подключений
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Удаление базы данных
sudo -u postgres dropdb mydb

# Удаление пользователя
sudo -u postgres dropuser myuser

# Размер базы данных
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('mydb'));"
```

## Рекомендации

1. **Используйте сильные пароли** для пользователей PostgreSQL
2. **Делайте регулярные резервные копии** баз данных
3. **Ограничьте удалённые подключения** в pg_hba.conf
4. **Обновляйте PostgreSQL** регулярно
5. **Мониторьте логи** при проблемах

## Полезные ресурсы

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ArchWiki: PostgreSQL](https://wiki.archlinux.org/title/PostgreSQL)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)

---

**Автор:** [ordanax.github.io](https://ordanax.github.io/)  
**Telegram:** [@linux4at](https://t.me/linux4at)  
**MAX:** [Присоединиться](https://max.ru/join/b4GtiNvbjYqeboq-nddswKQJ-cvWiJGoaZdIoV1EUMk)
