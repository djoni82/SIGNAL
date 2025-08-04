# 🔑 Настройка GitHub Actions Secrets для CryptoAlphaPro Signal Bot

## 📋 **Пошаговая инструкция по добавлению API ключей**

### **1. Перейдите в настройки репозитория**
```
https://github.com/djoni82/SIGNAL/settings/secrets/actions
```

### **2. Добавьте следующие Secrets:**

#### **🔐 Основные API ключи:**

| Secret Name | Описание | Пример значения |
|-------------|----------|-----------------|
| `TELEGRAM_TOKEN` | Токен Telegram бота | `8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg` |
| `TELEGRAM_CHAT_ID` | ID вашего чата | `5333574230` |
| `CRYPTOPANIC_TOKEN` | API ключ CryptoPanic | `free` (или ваш платный ключ) |
| `DUNE_API_KEY` | API ключ Dune Analytics | `your_dune_api_key_here` |
| `TWITTER_BEARER_TOKEN` | Twitter API Bearer Token | `your_twitter_bearer_token` |

#### **🐳 Docker ключи:**

| Secret Name | Описание | Пример значения |
|-------------|----------|-----------------|
| `DOCKER_USERNAME` | Ваш Docker Hub логин | `your_docker_username` |
| `DOCKER_PASSWORD` | Ваш Docker Hub пароль | `your_docker_password` |

#### **🗄️ База данных:**

| Secret Name | Описание | Пример значения |
|-------------|----------|-----------------|
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `cryptoalpha123` |
| `POSTGRES_DB` | Имя базы данных | `cryptoalpha` |
| `POSTGRES_USER` | Пользователь БД | `cryptoalpha` |

#### **📊 Мониторинг:**

| Secret Name | Описание | Пример значения |
|-------------|----------|-----------------|
| `GRAFANA_PASSWORD` | Пароль Grafana | `admin123` |
| `PROMETHEUS_ENABLED` | Включить Prometheus | `true` |

#### **🔒 Безопасность:**

| Secret Name | Описание | Пример значения |
|-------------|----------|-----------------|
| `ENCRYPTION_KEY` | Ключ шифрования | `your_32_character_encryption_key` |
| `JWT_SECRET` | JWT секрет | `your_jwt_secret_key` |

#### **⚙️ Конфигурация бота:**

| Secret Name | Описание | Пример значения |
|-------------|----------|-----------------|
| `BOT_MODE` | Режим работы | `production` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `MAX_LEVERAGE` | Максимальное плечо | `50` |
| `MIN_LEVERAGE` | Минимальное плечо | `1` |

## 🚀 **Быстрая настройка через GitHub CLI**

Если у вас установлен GitHub CLI, можете использовать команды:

```bash
# Основные API ключи
gh secret set TELEGRAM_TOKEN --body "8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg"
gh secret set TELEGRAM_CHAT_ID --body "5333574230"
gh secret set CRYPTOPANIC_TOKEN --body "free"
gh secret set DUNE_API_KEY --body "your_dune_api_key"
gh secret set TWITTER_BEARER_TOKEN --body "your_twitter_token"

# Docker ключи
gh secret set DOCKER_USERNAME --body "your_docker_username"
gh secret set DOCKER_PASSWORD --body "your_docker_password"

# База данных
gh secret set POSTGRES_PASSWORD --body "cryptoalpha123"
gh secret set POSTGRES_DB --body "cryptoalpha"
gh secret set POSTGRES_USER --body "cryptoalpha"

# Мониторинг
gh secret set GRAFANA_PASSWORD --body "admin123"
gh secret set PROMETHEUS_ENABLED --body "true"

# Безопасность
gh secret set ENCRYPTION_KEY --body "your_32_character_encryption_key"
gh secret set JWT_SECRET --body "your_jwt_secret_key"

# Конфигурация
gh secret set BOT_MODE --body "production"
gh secret set LOG_LEVEL --body "INFO"
gh secret set MAX_LEVERAGE --body "50"
gh secret set MIN_LEVERAGE --body "1"
```

## 📱 **Получение API ключей**

### **Telegram Bot Token:**
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

### **Telegram Chat ID:**
1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте любое сообщение
3. Скопируйте ваш Chat ID

### **CryptoPanic API:**
1. Перейдите на [cryptopanic.com](https://cryptopanic.com)
2. Зарегистрируйтесь
3. Получите API ключ в настройках

### **Dune Analytics API:**
1. Перейдите на [dune.com](https://dune.com)
2. Зарегистрируйтесь
3. Получите API ключ в настройках

### **Twitter API:**
1. Перейдите на [developer.twitter.com](https://developer.twitter.com)
2. Создайте приложение
3. Получите Bearer Token

### **Docker Hub:**
1. Перейдите на [hub.docker.com](https://hub.docker.com)
2. Зарегистрируйтесь
3. Создайте Access Token

## 🔧 **Проверка настройки**

После добавления всех ключей:

1. Перейдите в [Actions](https://github.com/djoni82/SIGNAL/actions)
2. Сделайте push в ветку `main` или `develop`
3. Проверьте, что CI/CD pipeline запустился
4. Убедитесь, что все шаги прошли успешно

## 🚨 **Важные замечания:**

- ✅ **Никогда не коммитьте API ключи** в код
- ✅ **Используйте только GitHub Secrets** для хранения ключей
- ✅ **Регулярно обновляйте ключи** для безопасности
- ✅ **Проверяйте права доступа** к API ключам

## 📞 **Поддержка:**

Если возникли проблемы с настройкой:
- Создайте [Issue](https://github.com/djoni82/SIGNAL/issues)
- Опишите проблему подробно
- Приложите скриншоты (без ключей!)

---

**После настройки всех ключей проект будет готов к автоматическому деплою!** 🚀 