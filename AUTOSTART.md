# Автозапуск бота при включении Mac

## Проблема
Когда ноутбук выключается или засыпает, все процессы останавливаются. Бот не запускается автоматически при следующем включении.

## Решение
Используем macOS LaunchAgent для автоматического запуска бота при входе в систему.

## Установка

### Быстрая установка (рекомендуется)
```bash
cd /Users/zhakhongirkuliboev/SIGNAL
./setup_autostart.sh
```

Скрипт автоматически:
- Создаст LaunchAgent файл
- Настроит автозапуск
- Запустит бота немедленно

### Ручная установка
Если нужно настроить вручную:

1. Создайте файл `~/Library/LaunchAgents/com.signalpro.bot.plist`
2. Скопируйте содержимое из `setup_autostart.sh`
3. Загрузите агент:
```bash
launchctl load ~/Library/LaunchAgents/com.signalpro.bot.plist
```

## Управление

### Проверить статус
```bash
launchctl list | grep signalpro
```

### Остановить автозапуск
```bash
launchctl unload ~/Library/LaunchAgents/com.signalpro.bot.plist
```

### Включить автозапуск обратно
```bash
launchctl load ~/Library/LaunchAgents/com.signalpro.bot.plist
```

### Перезапустить бота
```bash
launchctl stop com.signalpro.bot
launchctl start com.signalpro.bot
```

## Логи

LaunchAgent создает отдельные логи:
- **Основной лог**: `/Users/zhakhongirkuliboev/SIGNAL/launchd.log`
- **Ошибки**: `/Users/zhakhongirkuliboev/SIGNAL/launchd_error.log`
- **Watchdog**: `/Users/zhakhongirkuliboev/SIGNAL/watchdog.log`
- **Бот**: `/Users/zhakhongirkuliboev/SIGNAL/bot.log`

## Как это работает

1. **При входе в систему**: macOS автоматически запускает LaunchAgent
2. **LaunchAgent запускает**: `persistent_bot.sh`
3. **Watchdog следит**: Если бот упадет, watchdog перезапустит его
4. **KeepAlive**: Если watchdog упадет, LaunchAgent перезапустит его

## Преимущества

✅ Бот работает 24/7, даже после перезагрузки  
✅ Автоматический перезапуск при сбоях  
✅ Не нужно вручную запускать после включения Mac  
✅ Работает в фоне, не мешает другим задачам

## Отключение (если нужно)

Если хотите временно отключить автозапуск (например, для обслуживания):

```bash
# Остановить и отключить
launchctl unload ~/Library/LaunchAgents/com.signalpro.bot.plist

# Удалить файл (полное удаление)
rm ~/Library/LaunchAgents/com.signalpro.bot.plist
```
