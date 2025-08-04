use async_trait::async_trait;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use crate::config::ExchangeConfig;
use reqwest::Client;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use hex;
use chrono::Utc;
use tokio_tungstenite::{connect_async, WebSocketStream, MaybeTlsStream};
use tokio::net::TcpStream;
use futures_util::{SinkExt, StreamExt};
use serde_json::json;
use base64::Engine;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;

trait RoundToStep {
    fn floor_to_step(self, step: f64) -> Self;
}

impl RoundToStep for f64 {
    fn floor_to_step(self, step: f64) -> Self {
        (self / step).floor() * step
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub bid: f64,
    pub ask: f64,
    pub last: f64,
    pub volume: f64,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSocketMarketData {
    pub symbol: String,
    pub bid: f64,
    pub ask: f64,
    pub last: f64,
    pub volume: f64,
    pub timestamp: i64,
}

pub struct WebSocketManager {
    market_data: Arc<Mutex<HashMap<String, WebSocketMarketData>>>,
}

impl WebSocketManager {
    pub fn new() -> Self {
        Self {
            market_data: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn get_market_data(&self, symbol: &str) -> Option<WebSocketMarketData> {
        let data = self.market_data.lock().await;
        data.get(symbol).cloned()
    }

    pub async fn update_market_data(&self, data: WebSocketMarketData) {
        let mut market_data = self.market_data.lock().await;
        market_data.insert(data.symbol.clone(), data);
    }
}

#[async_trait]
pub trait Exchange: Send + Sync {
    async fn connect(&self) -> Result<()>;
    async fn check_balance(&self) -> Result<f64>;
    async fn validate_pair(&self, pair: &str) -> Result<bool>;
    async fn get_market_data(&self, pair: &str) -> Result<MarketData>;
    async fn get_websocket_market_data(&self, pair: &str) -> Result<Option<WebSocketMarketData>>;
    async fn start_websocket(&self, pairs: Vec<String>) -> Result<()>;
    async fn place_order(&self, pair: &str, side: &str, price: f64, size: f64) -> Result<String>;
    async fn place_market_order(&self, pair: &str, side: &str, size: f64) -> Result<String>;
    async fn set_leverage(&self, pair: &str, leverage: f64) -> Result<()>;
    async fn get_open_positions(&self) -> Result<Vec<Position>>;
    async fn cancel_order(&self, pair: &str, order_id: &str) -> Result<()>;
    async fn get_order_status(&self, pair: &str, order_id: &str) -> Result<String>;
    async fn get_lot_size(&self, pair: &str) -> Result<f64>;
    fn name(&self) -> &str;
    fn config(&self) -> &ExchangeConfig;
}

#[derive(Debug, Clone)]
pub struct Position {
    pub id: String,
    pub pair: String,
    pub side: String, // "LONG" or "SHORT"
    pub size: f64,
    pub entry_price: f64,
    pub current_price: f64,
    pub pnl: f64,
    pub pnl_percent: f64,
    pub leverage: f64,
}

#[derive(Debug, Clone)]
pub struct SymbolInfo {
    pub step_size: f64,
    pub tick_size: f64,
    pub min_notional: f64,
    pub min_qty: f64,
}

pub struct Binance {
    config: ExchangeConfig,
    client: Client,
}

impl Binance {
    pub fn new(config: ExchangeConfig) -> Self {
        Self { 
            config,
            client: Client::new(),
        }
    }

    fn generate_signature(&self, query_string: &str) -> String {
        let mut mac = Hmac::<Sha256>::new_from_slice(self.config.secret_key.as_bytes())
            .expect("HMAC can take key of any size");
        mac.update(query_string.as_bytes());
        hex::encode(mac.finalize().into_bytes())
    }
    
    async fn get_symbol_info(&self, pair: &str) -> Result<SymbolInfo> {
        let url = "https://fapi.binance.com/fapi/v1/exchangeInfo";
        let response = self.client.get(url).send().await?;
        let data: serde_json::Value = response.json().await?;
        
        if let Some(symbols) = data["symbols"].as_array() {
            for symbol in symbols {
                if symbol["symbol"] == pair {
                    let filters = symbol["filters"].as_array().unwrap();
                    
                    let lot_size = filters.iter()
                        .find(|f| f["filterType"] == "LOT_SIZE")
                        .unwrap();
                    let price_filter = filters.iter()
                        .find(|f| f["filterType"] == "PRICE_FILTER")
                        .unwrap();
                    let notional_filter = filters.iter()
                        .find(|f| f["filterType"] == "MIN_NOTIONAL")
                        .unwrap();
                    
                    return Ok(SymbolInfo {
                        step_size: lot_size["stepSize"].as_str().unwrap().parse::<f64>().unwrap_or(0.001),
                        tick_size: price_filter["tickSize"].as_str().unwrap().parse::<f64>().unwrap_or(0.01),
                        min_notional: notional_filter["notional"].as_str().unwrap().parse::<f64>().unwrap_or(5.0),
                        min_qty: lot_size["minQty"].as_str().unwrap().parse::<f64>().unwrap_or(0.001),
                    });
                }
            }
        }
        
        // Default values if symbol not found
        Ok(SymbolInfo {
            step_size: 0.001,
            tick_size: 0.01,
            min_notional: 5.0,
            min_qty: 0.001,
        })
    }
}

#[async_trait]
impl Exchange for Binance {
    async fn connect(&self) -> Result<()> {
        // Test connection by checking account info
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!("timestamp={}", timestamp);
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v2/account?{}&signature={}", query_string, signature);
        
        let response = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        if response.status().is_success() {
            println!("✅ Binance connection successful");
            Ok(())
        } else {
            Err(anyhow::anyhow!("Binance connection failed: {}", response.status()))
        }
    }

    async fn check_balance(&self) -> Result<f64> {
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!("timestamp={}", timestamp);
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v2/account?{}&signature={}", query_string, signature);
        
        let response = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        // Find USDT balance
        if let Some(assets) = data["assets"].as_array() {
            for asset in assets {
                if asset["asset"] == "USDT" {
                    let balance = asset["walletBalance"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                    return Ok(balance);
                }
            }
        }
        
        Ok(0.0)
    }

    async fn validate_pair(&self, pair: &str) -> Result<bool> {
        let url = format!("https://fapi.binance.com/fapi/v1/exchangeInfo");
        let response = self.client.get(&url).send().await?;
        let data: serde_json::Value = response.json().await?;
        
        if let Some(symbols) = data["symbols"].as_array() {
            for symbol in symbols {
                if symbol["symbol"] == pair && symbol["status"] == "TRADING" {
                    return Ok(true);
                }
            }
        }
        
        Ok(false)
    }

    async fn get_market_data(&self, pair: &str) -> Result<MarketData> {
        let url = format!("https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={}", pair);
        let response = self.client.get(&url).send().await?;
        let data: serde_json::Value = response.json().await?;
        
        // 🔥 ИСПРАВЛЕНИЕ: Более надежный парсинг цен с проверками
        let bid = data["bidPrice"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&p| p > 0.0)
            .unwrap_or_else(|| {
                println!("⚠️ Invalid bid price for {}, using lastPrice", pair);
                data["lastPrice"].as_str()
                    .and_then(|s| s.parse::<f64>().ok())
                    .unwrap_or(0.0)
            });
        
        let ask = data["askPrice"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&p| p > 0.0)
            .unwrap_or_else(|| {
                println!("⚠️ Invalid ask price for {}, using lastPrice", pair);
                data["lastPrice"].as_str()
                    .and_then(|s| s.parse::<f64>().ok())
                    .unwrap_or(0.0)
            });
        
        let last = data["lastPrice"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&p| p > 0.0)
            .unwrap_or(0.0);
        
        let volume = data["volume"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(0.0);
        
        // 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА: Если все цены 0.0, это фатальная ошибка
        if bid <= 0.0 && ask <= 0.0 && last <= 0.0 {
            println!("[FATAL] All prices are zero for {}! API response: {:?}", pair, data);
            return Err(anyhow::anyhow!("All market prices are zero for {}", pair));
        }
        
        // 🔥 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Если bid или ask 0.0, используем last
        let final_bid = if bid > 0.0 { bid } else { last };
        let final_ask = if ask > 0.0 { ask } else { last };
        
        println!("🔍 {} market data: bid={:.4}, ask={:.4}, last={:.4}", pair, final_bid, final_ask, last);
        
        Ok(MarketData {
            bid: final_bid,
            ask: final_ask,
            last,
            volume,
            timestamp: Utc::now().timestamp(),
        })
    }

    async fn get_websocket_market_data(&self, pair: &str) -> Result<Option<WebSocketMarketData>> {
        // Binance WebSocket does not provide 24hr ticker data directly.
        // This method is kept for compatibility with the trait, but will return None.
        Ok(None)
    }

    async fn start_websocket(&self, pairs: Vec<String>) -> Result<()> {
        // Binance WebSocket does not support starting a general WebSocket stream.
        // This method is kept for compatibility with the trait, but will return an error.
        Err(anyhow::anyhow!("Binance WebSocket not supported"))
    }

    async fn place_order(&self, pair: &str, side: &str, price: f64, size: f64) -> Result<String> {
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!(
            "symbol={}&side={}&type=LIMIT&timeInForce=GTC&quantity={}&price={}&timestamp={}",
            pair, side, size, price, timestamp
        );
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v1/order?{}&signature={}", query_string, signature);
        
        let response = self.client
            .post(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        // 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА: Проверяем код ответа
        if let Some(code) = data["code"].as_i64() {
            if code != 0 {
                let msg = data["msg"].as_str().unwrap_or("Unknown error");
                return Err(anyhow::anyhow!("Binance API error {}: {}", code, msg));
            }
        }
        
        // 🔥 ПРОВЕРЯЕМ ЧТО ОРДЕР ДЕЙСТВИТЕЛЬНО РАЗМЕЩЕН
        if let Some(order_id) = data["orderId"].as_i64() {
            if order_id > 0 {
                println!("✅ Binance order placed successfully: {} {} @ {} (size: {})", 
                    pair, side, price, size);
                Ok(order_id.to_string())
            } else {
                Err(anyhow::anyhow!("Invalid order ID returned from Binance"))
            }
        } else {
            Err(anyhow::anyhow!("Failed to get order ID from Binance response: {}", data))
        }
    }

    async fn place_market_order(&self, pair: &str, side: &str, size: f64) -> Result<String> {
        // Get symbol info for proper precision
        let symbol_info = self.get_symbol_info(pair).await?;
        
        // Debug: print original size and symbol info
        println!("🔍 {} {}: original_size={:.6}, step_size={:.6}, min_qty={:.6}, min_notional={:.2}", 
            pair, side, size, symbol_info.step_size, symbol_info.min_qty, symbol_info.min_notional);
        
        // Round quantity to step size
        let adjusted_size = size.floor_to_step(symbol_info.step_size);
        
        // Debug: print adjusted size
        println!("🔍 {} {}: adjusted_size={:.6}", pair, side, adjusted_size);
        
        // Check minimum quantity
        if adjusted_size < symbol_info.min_qty {
            return Err(anyhow::anyhow!("Quantity {} too small, minimum is {}", adjusted_size, symbol_info.min_qty));
        }
        
        // Get current price for notional check
        let market_data = self.get_market_data(pair).await?;
        let price = if side.to_uppercase() == "BUY" { market_data.ask } else { market_data.bid };
        
        // 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА: Цена не должна быть 0.0
        if price <= 0.0 {
            println!("[FATAL] Order price is zero! Market data: bid={:.4}, ask={:.4}, last={:.4}", 
                     market_data.bid, market_data.ask, market_data.last);
            return Err(anyhow::anyhow!("Order price is zero for {} {}", pair, side));
        }
        
        // Check minimum notional
        let notional = adjusted_size * price;
        println!("🔍 {} {}: notional={:.2} (size={:.6} * price={:.4})", pair, side, notional, adjusted_size, price);
        
        if notional < symbol_info.min_notional {
            return Err(anyhow::anyhow!("Order notional {} too small, minimum is {}", notional, symbol_info.min_notional));
        }
        
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!(
            "symbol={}&side={}&type=MARKET&quantity={}&positionSide={}&timestamp={}",
            pair, 
            side, 
            adjusted_size, 
            if side.to_uppercase() == "BUY" { "LONG" } else { "SHORT" },
            timestamp
        );
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v1/order?{}&signature={}", query_string, signature);
        
        println!("🚀 Placing Binance order: {} {} {} @ market (notional: {:.2})", 
            pair, side, adjusted_size, notional);
        
        let response = self.client
            .post(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        if let Some(order_id) = data["orderId"].as_i64() {
            Ok(order_id.to_string())
        } else {
            Err(anyhow::anyhow!("Failed to place market order: {}", data))
        }
    }

    async fn set_leverage(&self, pair: &str, leverage: f64) -> Result<()> {
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!(
            "symbol={}&leverage={}&timestamp={}",
            pair, leverage as i32, timestamp
        );
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v1/leverage?{}&signature={}", query_string, signature);
        
        let response = self.client
            .post(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        if response.status().is_success() {
            println!("✅ Leverage set to {}x for {}", leverage, pair);
            Ok(())
        } else {
            let error_text = response.text().await.unwrap_or_default();
            Err(anyhow::anyhow!("Failed to set leverage: {}", error_text))
        }
    }

    fn name(&self) -> &str {
        &self.config.name
    }

    fn config(&self) -> &ExchangeConfig {
        &self.config
    }
    
    async fn get_lot_size(&self, pair: &str) -> Result<f64> {
        // For Binance futures, lot size is typically 0.001 for most pairs
        Ok(0.001)
    }

    async fn cancel_order(&self, pair: &str, order_id: &str) -> Result<()> {
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!(
            "symbol={}&orderId={}&timestamp={}",
            pair, order_id, timestamp
        );
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v1/order?{}&signature={}", query_string, signature);
        
        let response = self.client
            .delete(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        if response.status().is_success() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("Failed to cancel order: {}", response.status()))
        }
    }

    async fn get_order_status(&self, pair: &str, order_id: &str) -> Result<String> {
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!(
            "symbol={}&orderId={}&timestamp={}",
            pair, order_id, timestamp
        );
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v1/order?{}&signature={}", query_string, signature);
        
        let response = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        if let Some(status) = data["status"].as_str() {
            Ok(status.to_string())
        } else {
            Err(anyhow::anyhow!("Failed to get order status: {}", data))
        }
    }

    async fn get_open_positions(&self) -> Result<Vec<Position>> {
        let timestamp = Utc::now().timestamp_millis().to_string();
        let query_string = format!("timestamp={}", timestamp);
        let signature = self.generate_signature(&query_string);
        
        let url = format!("https://fapi.binance.com/fapi/v2/positionRisk?{}&signature={}", query_string, signature);
        
        let response = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        let mut positions: Vec<Position> = Vec::new();
        if let Some(positions_data) = data["positions"].as_array() {
            for pos in positions_data {
                let id = pos["symbol"].as_str().unwrap_or("").to_string();
                let pair = id.clone();
                let side = pos["positionSide"].as_str().unwrap_or("").to_string();
                let size = pos["positionAmt"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let entry_price = pos["entryPrice"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let current_price = pos["lastPrice"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let pnl = pos["unRealizedProfit"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let pnl_percent = pos["unRealizedProfitRate"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let leverage = pos["leverage"].as_i64().unwrap_or(1) as f64; // Default to 1 if not found
                
                positions.push(Position {
                    id,
                    pair,
                    side,
                    size,
                    entry_price,
                    current_price,
                    pnl,
                    pnl_percent,
                    leverage,
                });
            }
        }
        
        Ok(positions)
    }
}

pub struct Okx {
    config: ExchangeConfig,
    client: Client,
}

impl Okx {
    pub fn new(config: ExchangeConfig) -> Self {
        Self { 
            config,
            client: Client::new(),
        }
    }

    // 🔥 ЗАГРУЗКА РЕАЛЬНЫХ ТИКЕРОВ С OKX
    pub async fn fetch_allowed_pairs(&self) -> Result<Vec<String>> {
        let url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP";
        
        println!("🔍 Fetching allowed pairs from OKX...");
        
        let response = reqwest::get(url).await?;
        let json: serde_json::Value = response.json().await?;
        
        if let Some(data) = json["data"].as_array() {
            let mut allowed_pairs = Vec::new();
            
            for instrument in data {
                if let Some(inst_id) = instrument["instId"].as_str() {
                    if let Some(state) = instrument["state"].as_str() {
                        if state == "live" { // только активные инструменты
                            allowed_pairs.push(inst_id.to_string());
                        }
                    }
                }
            }
            
            println!("✅ Found {} allowed pairs on OKX SWAP", allowed_pairs.len());
            println!("📋 First 10 pairs: {:?}", &allowed_pairs[..allowed_pairs.len().min(10)]);
            
            Ok(allowed_pairs)
        } else {
            Err(anyhow::anyhow!("Failed to parse OKX instruments response"))
        }
    }

    fn generate_signature(&self, method: &str, request_path: &str, body: &str, timestamp: &str) -> String {
        let message = format!("{}{}{}{}", timestamp, method, request_path, body);
        let mut mac = Hmac::<Sha256>::new_from_slice(self.config.secret_key.as_bytes())
            .expect("HMAC can take key of any size");
        mac.update(message.as_bytes());
        base64::engine::general_purpose::STANDARD.encode(mac.finalize().into_bytes())
    }
}

#[async_trait]
impl Exchange for Okx {
    async fn connect(&self) -> Result<()> {
        // Test connection by checking account info
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/account/balance";
        let signature = self.generate_signature("GET", request_path, "", &timestamp);
        
        let response = self.client
            .get("https://www.okx.com/api/v5/account/balance")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&"".to_string()))
            .send()
            .await?;
        
        if response.status().is_success() {
            println!("✅ OKX connection successful");
            Ok(())
        } else {
            Err(anyhow::anyhow!("OKX connection failed: {}", response.status()))
        }
    }

    async fn check_balance(&self) -> Result<f64> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/account/balance";
        let signature = self.generate_signature("GET", request_path, "", &timestamp);
        
        let response = self.client
            .get("https://www.okx.com/api/v5/account/balance")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&"".to_string()))
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        // Find USDT balance
        if let Some(accounts) = data["data"][0]["details"].as_array() {
            for account in accounts {
                if account["ccy"] == "USDT" {
                    let balance = account["availBal"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                    return Ok(balance);
                }
            }
        }
        
        Ok(0.0)
    }

    async fn validate_pair(&self, pair: &str) -> Result<bool> {
        let url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP";
        let response = self.client.get(url).send().await?;
        let data: serde_json::Value = response.json().await?;
        
        if let Some(instruments) = data["data"].as_array() {
            for instrument in instruments {
                if instrument["instId"] == pair && instrument["state"] == "live" {
                    return Ok(true);
                }
            }
        }
        
        Ok(false)
    }

    async fn get_market_data(&self, pair: &str) -> Result<MarketData> {
        let url = format!("https://www.okx.com/api/v5/market/ticker?instId={}", pair);
        let response = self.client.get(&url).send().await?;
        let data: serde_json::Value = response.json().await?;
        
        // 🔥 ИСПРАВЛЕНИЕ: Проверяем что data["data"] существует и не пустой
        if data["data"].is_null() || data["data"].as_array().map(|arr| arr.is_empty()).unwrap_or(true) {
            println!("[FATAL] No market data received for {}! API response: {:?}", pair, data);
            return Err(anyhow::anyhow!("No market data received for {}", pair));
        }
        
        let ticker = &data["data"][0];
        
        // 🔥 ИСПРАВЛЕНИЕ: Более надежный парсинг цен с проверками
        let bid = ticker["bidPx"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&p| p > 0.0)
            .unwrap_or_else(|| {
                println!("⚠️ Invalid bid price for {}, using last", pair);
                ticker["last"].as_str()
                    .and_then(|s| s.parse::<f64>().ok())
                    .unwrap_or(0.0)
            });
        
        let ask = ticker["askPx"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&p| p > 0.0)
            .unwrap_or_else(|| {
                println!("⚠️ Invalid ask price for {}, using last", pair);
                ticker["last"].as_str()
                    .and_then(|s| s.parse::<f64>().ok())
                    .unwrap_or(0.0)
            });
        
        let last = ticker["last"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&p| p > 0.0)
            .unwrap_or(0.0);
        
        let volume = ticker["vol24h"].as_str()
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(0.0);
        
        // 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА: Если все цены 0.0, это фатальная ошибка
        if bid <= 0.0 && ask <= 0.0 && last <= 0.0 {
            println!("[FATAL] All prices are zero for {}! API response: {:?}", pair, data);
            return Err(anyhow::anyhow!("All market prices are zero for {}", pair));
        }
        
        // 🔥 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Если bid или ask 0.0, используем last
        let final_bid = if bid > 0.0 { bid } else { last };
        let final_ask = if ask > 0.0 { ask } else { last };
        
        println!("🔍 {} market data: bid={:.4}, ask={:.4}, last={:.4}", pair, final_bid, final_ask, last);
        
        Ok(MarketData {
            bid: final_bid,
            ask: final_ask,
            last,
            volume,
            timestamp: Utc::now().timestamp(),
        })
    }

    async fn get_websocket_market_data(&self, pair: &str) -> Result<Option<WebSocketMarketData>> {
        // OKX WebSocket does not provide 24hr ticker data directly.
        // This method is kept for compatibility with the trait, but will return None.
        Ok(None)
    }

    async fn start_websocket(&self, pairs: Vec<String>) -> Result<()> {
        // OKX WebSocket does not support starting a general WebSocket stream.
        // This method is kept for compatibility with the trait, but will return an error.
        Err(anyhow::anyhow!("OKX WebSocket not supported"))
    }

    async fn place_order(&self, pair: &str, side: &str, price: f64, size: f64) -> Result<String> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/trade/order";
        
        // Get lot size info for the pair
        let lot_size = self.get_lot_size(pair).await.unwrap_or(0.01);
        let adjusted_size = if size < lot_size {
            lot_size // Use minimum lot size if calculated size is too small
        } else {
            (size / lot_size).floor_to_step(lot_size)
        };
        
        let body = json!({
            "instId": pair,
            "tdMode": "cross",
            "side": side.to_lowercase(),
            "posSide": if side.to_lowercase() == "buy" { "long" } else { "short" }, // 🔥 ДОБАВЛЯЕМ posSide ДЛЯ FUTURES
            "ordType": "limit",
            "sz": adjusted_size.to_string(),
            "px": price.to_string()
        });
        
        let body_str = body.to_string();
        let signature = self.generate_signature("POST", request_path, &body_str, &timestamp);
        
        let response = self.client
            .post("https://www.okx.com/api/v5/trade/order")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&"".to_string()))
            .header("Content-Type", "application/json")
            .body(body_str)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        // 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОТВЕТА OKX
        println!("🔍 OKX API Response for {} {} @ {} (size: {}):", pair, side, price, adjusted_size);
        println!("   Full response: {}", serde_json::to_string_pretty(&data).unwrap_or_else(|_| "Failed to serialize".to_string()));
        
        // 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА: Проверяем код ответа
        if let Some(code) = data["code"].as_str() {
            if code != "0" {
                let msg = data["msg"].as_str().unwrap_or("Unknown error");
                let detailed_error = format!("OKX API error {}: {} | Full response: {}", code, msg, data);
                println!("❌ {}", detailed_error);
                return Err(anyhow::anyhow!("OKX API error {}: {}", code, msg));
            }
        }
        
        // 🔥 ПРОВЕРЯЕМ ЧТО ОРДЕР ДЕЙСТВИТЕЛЬНО РАЗМЕЩЕН
        if let Some(order_id) = data["data"][0]["ordId"].as_str() {
            if !order_id.is_empty() {
                println!("✅ OKX order placed successfully: {} {} @ {} (size: {})", 
                    pair, side, price, adjusted_size);
                Ok(order_id.to_string())
            } else {
                let error_msg = format!("Empty order ID returned from OKX. Full response: {}", data);
                println!("❌ {}", error_msg);
                Err(anyhow::anyhow!("Empty order ID returned from OKX"))
            }
        } else {
            let error_msg = format!("Failed to get order ID from OKX response: {}", data);
            println!("❌ {}", error_msg);
            Err(anyhow::anyhow!("Failed to get order ID from OKX response: {}", data))
        }
    }

    async fn place_market_order(&self, pair: &str, side: &str, size: f64) -> Result<String> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/trade/order";
        
        // Get lot size info for the pair
        let lot_size = self.get_lot_size(pair).await.unwrap_or(0.01);
        let adjusted_size = if size < lot_size {
            lot_size // Use minimum lot size if calculated size is too small
        } else {
            size.floor_to_step(lot_size)
        };
        
        // Check minimum notional (5 USDT for OKX)
        let market_data = self.get_market_data(pair).await?;
        let price = if side.to_lowercase() == "buy" { market_data.ask } else { market_data.bid };
        
        // �� КРИТИЧЕСКАЯ ПРОВЕРКА: Цена не должна быть 0.0
        if price <= 0.0 {
            println!("[FATAL] Order price is zero! Market data: bid={:.4}, ask={:.4}, last={:.4}", 
                     market_data.bid, market_data.ask, market_data.last);
            return Err(anyhow::anyhow!("Order price is zero for {} {}", pair, side));
        }
        
        let notional = adjusted_size * price;
        
        if notional < 5.0 {
            return Err(anyhow::anyhow!("Order notional {} too small, minimum is 5.0", notional));
        }
        
        let body = json!({
            "instId": pair,
            "tdMode": "cross",
            "side": side.to_lowercase(),
            "posSide": if side.to_lowercase() == "buy" { "long" } else { "short" },
            "ordType": "market",
            "sz": adjusted_size.to_string()
        });
        
        let body_str = body.to_string();
        let signature = self.generate_signature("POST", request_path, &body_str, &timestamp);
        
        println!("🚀 Placing OKX order: {} {} {} @ market (notional: {:.2})", 
            pair, side, adjusted_size, notional);
        
        let response = self.client
            .post("https://www.okx.com/api/v5/trade/order")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&String::new()))
            .header("Content-Type", "application/json")
            .body(body_str)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        if data["code"] == "0" {
            if let Some(order_id) = data["data"][0]["ordId"].as_str() {
                Ok(order_id.to_string())
            } else {
                Err(anyhow::anyhow!("No order ID in response: {}", data))
            }
        } else {
            Err(anyhow::anyhow!("Failed to place market order: {}", data))
        }
    }

    async fn set_leverage(&self, pair: &str, leverage: f64) -> Result<()> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/account/set-leverage";
        
        let body = json!({
            "instId": pair,
            "lever": leverage.to_string(),
            "mgnMode": "cross"
        });
        
        let body_str = body.to_string();
        let signature = self.generate_signature("POST", request_path, &body_str, &timestamp);
        
        let response = self.client
            .post("https://www.okx.com/api/v5/account/set-leverage")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&String::new()))
            .header("Content-Type", "application/json")
            .body(body_str)
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        if data["code"] == "0" {
            println!("✅ Leverage set to {}x for {}", leverage, pair);
            Ok(())
        } else {
            Err(anyhow::anyhow!("Failed to set leverage: {}", data))
        }
    }
    
    async fn get_lot_size(&self, pair: &str) -> Result<f64> {
        let url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP";
        let response = self.client.get(url).send().await?;
        let data: serde_json::Value = response.json().await?;
        
        if let Some(instruments) = data["data"].as_array() {
            for instrument in instruments {
                if instrument["instId"] == pair {
                    let lot_size = instrument["lotSz"].as_str().unwrap_or("0.01").parse::<f64>().unwrap_or(0.01);
                    return Ok(lot_size);
                }
            }
        }
        
        Ok(0.01) // Default lot size
    }

    fn name(&self) -> &str {
        &self.config.name
    }

    fn config(&self) -> &ExchangeConfig {
        &self.config
    }
    
    async fn cancel_order(&self, pair: &str, order_id: &str) -> Result<()> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/trade/cancel-order";
        
        let body = json!({
            "instId": pair,
            "ordId": order_id
        });
        
        let body_str = body.to_string();
        let signature = self.generate_signature("POST", request_path, &body_str, &timestamp);
        
        let response = self.client
            .post("https://www.okx.com/api/v5/trade/cancel-order")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&"".to_string()))
            .header("Content-Type", "application/json")
            .body(body_str)
            .send()
            .await?;
        
        if response.status().is_success() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("Failed to cancel order: {}", response.status()))
        }
    }

    async fn get_order_status(&self, pair: &str, order_id: &str) -> Result<String> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let query_string = format!("instId={}&ordId={}", pair, order_id);
        let request_path = format!("/api/v5/trade/order?{}", query_string);
        let signature = self.generate_signature("GET", &request_path, "", &timestamp);
        
        let url = format!("https://www.okx.com{}", request_path);
        
        let response = self.client
            .get(&url)
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&"".to_string()))
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        
        if let Some(status) = data["data"][0]["state"].as_str() {
            Ok(status.to_string())
        } else {
            Err(anyhow::anyhow!("Failed to get order status: {}", data))
        }
    }

    async fn get_open_positions(&self) -> Result<Vec<Position>> {
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%S.%3fZ").to_string();
        let request_path = "/api/v5/account/positions";
        let signature = self.generate_signature("GET", request_path, "", &timestamp);
        
        let response = self.client
            .get("https://www.okx.com/api/v5/account/positions")
            .header("OK-ACCESS-KEY", &self.config.api_key)
            .header("OK-ACCESS-SIGN", signature)
            .header("OK-ACCESS-TIMESTAMP", &timestamp)
            .header("OK-ACCESS-PASSPHRASE", self.config.passphrase.as_ref().unwrap_or(&"".to_string()))
            .send()
            .await?;
        
        let data: serde_json::Value = response.json().await?;
        println!("🔍 [OKX POSITIONS] Raw API response: {:?}", data);
        
        let mut positions: Vec<Position> = Vec::new();
        if let Some(positions_data) = data["data"].as_array() {
            for pos in positions_data {
                let pos_size = pos["pos"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                
                // 🔥 ФИЛЬТРУЕМ ТОЛЬКО АКТИВНЫЕ ПОЗИЦИИ (размер != 0)
                if pos_size.abs() < 0.000001 {
                    continue;
                }
                
                let id = pos["posId"].as_str().unwrap_or("").to_string();
                let pair = pos["instId"].as_str().unwrap_or("").to_string();
                let pos_side = pos["posSide"].as_str().unwrap_or("").to_string();
                
                // 🔥 КОНВЕРТИРУЕМ OKX SIDE В НАШИ ФОРМАТЫ
                let side = match pos_side.as_str() {
                    "long" => "BUY".to_string(),
                    "short" => "SELL".to_string(),
                    _ => {
                        println!("⚠️ Unknown position side: {}", pos_side);
                        continue;
                    }
                };
                
                let entry_price = pos["avgPx"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let current_price = pos["last"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(entry_price);
                let pnl = pos["upl"].as_str().unwrap_or("0").parse::<f64>().unwrap_or(0.0);
                let leverage = pos["lever"].as_str().unwrap_or("1").parse::<f64>().unwrap_or(1.0);
                
                // 🔥 ПРАВИЛЬНЫЙ РАСЧЕТ PnL В ПРОЦЕНТАХ
                let pnl_percent = if entry_price > 0.0 {
                    match side.as_str() {
                        "BUY" => ((current_price - entry_price) / entry_price) * 100.0,
                        "SELL" => ((entry_price - current_price) / entry_price) * 100.0,
                        _ => 0.0
                    }
                } else {
                    0.0
                };
                
                positions.push(Position {
                    id: id.clone(),
                    pair: pair.clone(),
                    side: side.clone(),
                    size: pos_size.abs(), // Используем абсолютное значение
                    entry_price,
                    current_price,
                    pnl,
                    pnl_percent,
                    leverage,
                });
                
                println!("📊 [OKX POSITION] {} {} @ {:.5}, size: {:.4}, PnL: {:.2}% ({:.4} USDT)", 
                         pair, side, entry_price, pos_size.abs(), pnl_percent, pnl);
            }
        } else {
            println!("⚠️ [OKX POSITIONS] No positions data in response");
        }
        
        println!("✅ [OKX POSITIONS] Found {} active positions", positions.len());
        Ok(positions)
    }
} 