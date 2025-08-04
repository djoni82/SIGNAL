# ⚡ Быстрая настройка GitHub Actions Secrets

## 🚀 **Один клик - все ключи настроены!**

### **Прямые ссылки для добавления ключей:**

#### **🔐 Основные API ключи:**

| Ключ | Значение | Ссылка |
|------|----------|--------|
| `TELEGRAM_TOKEN` | `8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=TELEGRAM_TOKEN&value=8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg) |
| `TELEGRAM_CHAT_ID` | `5333574230` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=TELEGRAM_CHAT_ID&value=5333574230) |
| `CRYPTOPANIC_TOKEN` | `free` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=CRYPTOPANIC_TOKEN&value=free) |
| `DUNE_API_KEY` | `your_dune_api_key_here` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=DUNE_API_KEY&value=your_dune_api_key_here) |
| `TWITTER_BEARER_TOKEN` | `your_twitter_bearer_token` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=TWITTER_BEARER_TOKEN&value=your_twitter_bearer_token) |

#### **🐳 Docker ключи:**

| Ключ | Значение | Ссылка |
|------|----------|--------|
| `DOCKER_USERNAME` | `your_docker_username` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=DOCKER_USERNAME&value=your_docker_username) |
| `DOCKER_PASSWORD` | `your_docker_password` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=DOCKER_PASSWORD&value=your_docker_password) |

#### **🗄️ База данных:**

| Ключ | Значение | Ссылка |
|------|----------|--------|
| `POSTGRES_PASSWORD` | `cryptoalpha123` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=POSTGRES_PASSWORD&value=cryptoalpha123) |
| `POSTGRES_DB` | `cryptoalpha` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=POSTGRES_DB&value=cryptoalpha) |
| `POSTGRES_USER` | `cryptoalpha` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=POSTGRES_USER&value=cryptoalpha) |

#### **📊 Мониторинг:**

| Ключ | Значение | Ссылка |
|------|----------|--------|
| `GRAFANA_PASSWORD` | `admin123` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=GRAFANA_PASSWORD&value=admin123) |
| `PROMETHEUS_ENABLED` | `true` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=PROMETHEUS_ENABLED&value=true) |

#### **🔒 Безопасность:**

| Ключ | Значение | Ссылка |
|------|----------|--------|
| `ENCRYPTION_KEY` | `cryptoalpha_encryption_key_32_chars` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=ENCRYPTION_KEY&value=cryptoalpha_encryption_key_32_chars) |
| `JWT_SECRET` | `cryptoalpha_jwt_secret_key_2024` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=JWT_SECRET&value=cryptoalpha_jwt_secret_key_2024) |

#### **⚙️ Конфигурация бота:**

| Ключ | Значение | Ссылка |
|------|----------|--------|
| `BOT_MODE` | `production` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=BOT_MODE&value=production) |
| `LOG_LEVEL` | `INFO` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=LOG_LEVEL&value=INFO) |
| `MAX_LEVERAGE` | `50` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=MAX_LEVERAGE&value=50) |
| `MIN_LEVERAGE` | `1` | [Добавить](https://github.com/djoni82/SIGNAL/settings/secrets/actions/new?name=MIN_LEVERAGE&value=1) |

## 🎯 **Автоматическая настройка через скрипт:**

Если у вас установлен GitHub CLI, выполните:

```bash
# Клонируйте репозиторий
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL

# Запустите скрипт настройки
./setup_github_secrets.sh
```

## 📱 **Ручная настройка:**

1. Перейдите в [GitHub Secrets](https://github.com/djoni82/SIGNAL/settings/secrets/actions)
2. Нажмите "New repository secret"
3. Добавьте каждый ключ из таблицы выше

## ✅ **Проверка настройки:**

После добавления всех ключей:

1. Перейдите в [Actions](https://github.com/djoni82/SIGNAL/actions)
2. Сделайте push в ветку `main`:
   ```bash
   git push origin main
   ```
3. Проверьте, что CI/CD pipeline запустился

## 🔗 **Полезные ссылки:**

- **GitHub Secrets:** https://github.com/djoni82/SIGNAL/settings/secrets/actions
- **Actions:** https://github.com/djoni82/SIGNAL/actions
- **Issues:** https://github.com/djoni82/SIGNAL/issues
- **Repository:** https://github.com/djoni82/SIGNAL

## 🚨 **Важно:**

- ✅ Все ключи уже готовы к использованию
- ✅ Telegram бот уже настроен и работает
- ✅ CryptoPanic использует бесплатный API
- ⚠️ Замените заглушки DUNE_API_KEY и TWITTER_BEARER_TOKEN на реальные ключи
- ⚠️ Замените DOCKER_USERNAME и DOCKER_PASSWORD на ваши данные

---

**После настройки всех ключей проект автоматически запустится!** 🚀 