use serde::{Deserialize, Serialize};
use std::fs;
use anyhow::Result;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    pub exchanges: Vec<ExchangeConfig>,
    pub min_volatility: f64,
    pub max_volatility: f64,
    pub min_spread: f64,
    pub max_spread: f64,
    pub min_volume: f64,
    pub risk_per_trade: f64,
    pub high_volatility_threshold: f64,
    pub low_leverage: f64,
    pub high_leverage: f64,
    pub min_order_size: f64,
    pub max_order_size: f64,
    pub daily_stop_loss: f64,
    pub telegram_token: String,
    pub telegram_chat_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExchangeConfig {
    pub name: String,
    pub api_key: String,
    pub secret_key: String,
    pub passphrase: Option<String>,
    pub pairs: Vec<String>,
}

pub async fn load_config() -> Result<Config> {
    let config_content = fs::read_to_string("config.toml")?;
    let config: Config = toml::from_str(&config_content)?;
    Ok(config)
} 