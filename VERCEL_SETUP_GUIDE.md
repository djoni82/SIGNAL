# 🚀 Настройка Vercel для CryptoAlphaPro Signal Bot

## 🚨 **Проблема**

Vercel подключен к неправильному репозиторию `djoni82/maker` вместо `djoni82/SIGNAL`.

## ✅ **Решение: Создать новый Vercel проект**

### **Шаг 1: Перейти в Vercel Dashboard**
1. Откройте https://vercel.com/dashboard
2. Нажмите "Add New..." → "Project"

### **Шаг 2: Подключить правильный репозиторий**
1. В списке репозиториев найдите `djoni82/SIGNAL`
2. Если репозитория нет в списке:
   - Нажмите "Import Git Repository"
   - Введите: `https://github.com/djoni82/SIGNAL`
   - Нажмите "Continue"

### **Шаг 3: Настроить проект**
1. **Project Name:** `cryptoalpha-signal-bot`
2. **Framework Preset:** `Other`
3. **Root Directory:** `./` (оставьте пустым)
4. **Build Command:** оставьте пустым
5. **Output Directory:** оставьте пустым
6. **Install Command:** оставьте пустым

### **Шаг 4: Настроить переменные окружения**
Добавьте следующие переменные:
```
NODE_ENV=production
```

### **Шаг 5: Развернуть**
1. Нажмите "Deploy"
2. Дождитесь завершения деплоя

## 🔧 **Альтернативный способ через CLI**

### **Установить Vercel CLI:**
```bash
npm install -g vercel
```

### **Войти в Vercel:**
```bash
vercel login
```

### **Создать проект:**
```bash
cd "/Users/zhakhongirkuliboev/Desktop/Crypto_signal_bot Pro"
vercel
```

### **Следовать инструкциям:**
- Выберите "Create new project"
- Выберите репозиторий `djoni82/SIGNAL`
- Название проекта: `cryptoalpha-signal-bot`
- Framework: `Other`
- Root Directory: `./`

## 📋 **Проверка конфигурации**

Убедитесь, что в проекте есть файлы:
- ✅ `index.html` - landing page
- ✅ `vercel.json` - конфигурация
- ✅ `package.json` - метаданные
- ✅ `.vercelignore` - исключения

## 🎯 **Ожидаемый результат**

После правильной настройки:
1. Vercel будет деплоить из `djoni82/SIGNAL`
2. Сайт будет доступен по адресу: `https://cryptoalpha-signal-bot.vercel.app`
3. На странице будет информация о CryptoAlphaPro Signal Bot

## 🔗 **Полезные ссылки**

- **Vercel Dashboard:** https://vercel.com/dashboard
- **GitHub Repository:** https://github.com/djoni82/SIGNAL
- **GitHub Actions:** https://github.com/djoni82/SIGNAL/actions

## 📱 **Telegram Bot данные**

- **Bot Token:** `8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg`
- **Chat ID:** `5333574230`

## 🚀 **После настройки**

1. Проверьте, что деплой прошел успешно
2. Откройте сайт - должна показаться landing page
3. Проверьте, что GitHub Actions работают
4. Протестируйте Telegram бота

**🎉 После правильной настройки Vercel будет работать!** 🚀 