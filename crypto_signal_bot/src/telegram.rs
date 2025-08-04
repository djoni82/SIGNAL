use crate::config::Config;

pub struct TelegramNotifier {
    config: Config,
}

impl TelegramNotifier {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub async fn send(&self, message: &str) {
        if self.config.telegram_token.is_empty() {
            return;
        }
        
        // Telegram sending logic here
        println!("📱 Telegram: {}", message);
    }

    pub async fn start(&self) {
        // Telegram bot start logic here
        println!("🤖 Telegram bot started");
    }
} 