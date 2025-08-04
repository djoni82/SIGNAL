use tokio_tungstenite::{WebSocketStream, MaybeTlsStream};
use tokio::net::TcpStream;
use futures_util::{SinkExt, StreamExt};
use serde_json::{json, Value};
use anyhow::Result;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;
use crate::exchange::WebSocketMarketData;
use tokio_tungstenite::tungstenite::protocol::Message;
use tokio_native_tls::TlsConnector;
use native_tls;
use url::Url;

pub struct WebSocketClient {
    market_data: Arc<Mutex<HashMap<String, WebSocketMarketData>>>,
}

impl WebSocketClient {
    pub fn new() -> Self {
        Self {
            market_data: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn start_binance_websocket(&self, pairs: Vec<String>) -> Result<()> {
        let market_data = self.market_data.clone();
        
        tokio::spawn(async move {
            // Create WebSocket URL for Binance futures
            let streams: String = pairs
                .iter()
                .map(|pair| format!("{}@ticker", pair.to_lowercase()))
                .collect::<Vec<_>>()
                .join("/");
            
            let url = format!("wss://fstream.binance.com/stream?streams={}", streams);
            println!("🔌 Connecting to Binance WebSocket: {}", url);
            
            match Self::connect_with_tls(&url).await {
                Ok((ws_stream, _)) => {
                    println!("✅ Binance WebSocket connected successfully");
                    Self::handle_binance_stream(ws_stream, market_data).await;
                }
                Err(e) => {
                    println!("❌ Failed to connect to Binance WebSocket: {}", e);
                }
            }
        });
        
        Ok(())
    }

    pub async fn start_okx_websocket(&self, pairs: Vec<String>) -> Result<()> {
        let market_data = self.market_data.clone();
        
        tokio::spawn(async move {
            let url = "wss://ws.okx.com:8443/ws/v5/public";
            println!("🔗 Connecting to OKX WebSocket: {}", url);
            
            match Self::connect_with_tls(url).await {
                Ok((ws_stream, _)) => {
                    println!("✅ OKX WebSocket connected successfully");
                    
                    // Subscribe to tickers
                    let subscribe_msg = json!({
                        "op": "subscribe",
                        "args": pairs.iter().map(|pair| {
                            json!({
                                "channel": "tickers",
                                "instId": pair
                            })
                        }).collect::<Vec<_>>()
                    });
                    
                    println!("📡 Subscribing to OKX channels: {}", subscribe_msg);
                    
                    let (mut write, mut read) = ws_stream.split();
                    
                    // Send subscription
                    match write.send(Message::Text(subscribe_msg.to_string().into())).await {
                        Ok(_) => {
                            println!("✅ OKX WebSocket subscription sent successfully");
                            Self::handle_okx_stream(read, market_data).await;
                        }
                        Err(e) => {
                            println!("❌ Failed to subscribe to OKX WebSocket: {:?}", e);
                        }
                    }
                }
                Err(e) => {
                    println!("❌ Failed to connect to OKX WebSocket: {:?}", e);
                }
            }
        });
        
        Ok(())
    }

    async fn connect_with_tls(url: &str) -> Result<(WebSocketStream<MaybeTlsStream<TcpStream>>, tokio_tungstenite::tungstenite::handshake::client::Response), tokio_tungstenite::tungstenite::Error> {
        let (ws_stream, response) = tokio_tungstenite::connect_async(url).await?;
        Ok((ws_stream, response))
    }

    async fn handle_binance_stream(
        mut ws_stream: WebSocketStream<MaybeTlsStream<TcpStream>>,
        market_data: Arc<Mutex<HashMap<String, WebSocketMarketData>>>,
    ) {
        println!("📊 Binance WebSocket stream handler started");
        let mut message_count = 0;
        
        while let Some(msg) = ws_stream.next().await {
            match msg {
                Ok(msg) => {
                    if let Message::Text(text) = msg {
                        message_count += 1;
                        if message_count % 100 == 0 {
                            println!("📈 Binance WebSocket received {} messages", message_count);
                        }
                        
                        // Debug: print first few messages
                        if message_count <= 5 {
                            println!("🔍 Binance message {}: {}", message_count, text);
                        }
                        
                        if let Ok(data) = serde_json::from_str::<Value>(&text) {
                            // Debug: print data structure
                            if message_count <= 3 {
                                println!("🔍 Binance data structure: {:?}", data);
                            }
                            
                            // Handle both single stream and combined stream formats
                            if let Some(stream) = data["stream"].as_str() {
                                if stream.ends_with("@ticker") {
                                    if let Some(ticker_data) = data["data"].as_object() {
                                        let symbol = stream.replace("@ticker", "").to_uppercase();
                                        
                                        // Safe parsing with defaults - using correct Binance WebSocket fields
                                        let last_str = ticker_data["c"].as_str().unwrap_or("0");
                                        let high_str = ticker_data["h"].as_str().unwrap_or("0");
                                        let low_str = ticker_data["l"].as_str().unwrap_or("0");
                                        let volume_str = ticker_data["v"].as_str().unwrap_or("0");
                                        
                                        // Parse with error handling
                                        let last = last_str.parse::<f64>().unwrap_or(0.0);
                                        let high = high_str.parse::<f64>().unwrap_or(0.0);
                                        let low = low_str.parse::<f64>().unwrap_or(0.0);
                                        let volume = volume_str.parse::<f64>().unwrap_or(0.0);
                                        
                                        // Calculate bid/ask from high/low (approximation)
                                        let spread = (high - low) * 0.001; // 0.1% spread
                                        let bid = last - spread / 2.0;
                                        let ask = last + spread / 2.0;
                                        
                                        // Only update if we have valid data
                                        if bid > 0.0 && ask > 0.0 {
                                            let ws_data = WebSocketMarketData {
                                                symbol: symbol.clone(),
                                                bid,
                                                ask,
                                                last,
                                                volume,
                                                timestamp: chrono::Utc::now().timestamp_millis(),
                                            };
                                            
                                            let mut data_guard = market_data.lock().await;
                                            data_guard.insert(symbol.clone(), ws_data);
                                            
                                            // Debug: print when data is saved
                                            if message_count <= 10 {
                                                println!("💾 Binance data saved for {}: bid={:.4}, ask={:.4}, last={:.4}", symbol, bid, ask, last);
                                            }
                                            
                                            if message_count % 100 == 0 {
                                                println!("📊 Binance {}: bid={:.4}, ask={:.4}, last={:.4}", symbol, bid, ask, last);
                                            }
                                        }
                                    }
                                }
                            }
                        } else {
                            if message_count <= 5 {
                                println!("❌ Failed to parse Binance message: {}", text);
                            }
                        }
                    }
                }
                Err(e) => {
                    println!("❌ Binance WebSocket error: {:?}", e);
                    break;
                }
            }
        }
        println!("❌ Binance WebSocket stream ended");
    }

    async fn handle_okx_stream(
        mut read: futures_util::stream::SplitStream<WebSocketStream<MaybeTlsStream<TcpStream>>>,
        market_data: Arc<Mutex<HashMap<String, WebSocketMarketData>>>,
    ) {
        println!("📊 OKX WebSocket stream handler started");
        let mut message_count = 0;
        
        while let Some(msg) = read.next().await {
            match msg {
                Ok(msg) => {
                    if let Message::Text(text) = msg {
                        message_count += 1;
                        if message_count % 100 == 0 {
                            println!("📈 OKX WebSocket received {} messages", message_count);
                        }
                        
                        if let Ok(data) = serde_json::from_str::<Value>(&text) {
                            if let Some(channel) = data["arg"]["channel"].as_str() {
                                if channel == "tickers" {
                                    if let Some(ticker_data) = data["data"].as_array() {
                                        for ticker in ticker_data {
                                            if let Some(inst_id) = ticker["instId"].as_str() {
                                                // 🔥 ИСПРАВЛЕНИЕ: Более надежный парсинг цен с проверками
                                                let bid = ticker["bidPx"].as_str()
                                                    .and_then(|s| s.parse::<f64>().ok())
                                                    .filter(|&p| p > 0.0)
                                                    .unwrap_or_else(|| {
                                                        ticker["last"].as_str()
                                                            .and_then(|s| s.parse::<f64>().ok())
                                                            .unwrap_or(0.0)
                                                    });
                                                
                                                let ask = ticker["askPx"].as_str()
                                                    .and_then(|s| s.parse::<f64>().ok())
                                                    .filter(|&p| p > 0.0)
                                                    .unwrap_or_else(|| {
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
                                                
                                                // 🔥 ПРОВЕРКА: Если все цены 0.0, пропускаем
                                                if bid <= 0.0 && ask <= 0.0 && last <= 0.0 {
                                                    if message_count % 100 == 0 {
                                                        println!("⚠️ Skipping {} - all prices are zero", inst_id);
                                                    }
                                                    continue;
                                                }
                                                
                                                // 🔥 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Если bid или ask 0.0, используем last
                                                let final_bid = if bid > 0.0 { bid } else { last };
                                                let final_ask = if ask > 0.0 { ask } else { last };
                                                
                                                let ws_data = WebSocketMarketData {
                                                    symbol: inst_id.to_string(),
                                                    bid: final_bid,
                                                    ask: final_ask,
                                                    last,
                                                    volume,
                                                    timestamp: chrono::Utc::now().timestamp(),
                                                };
                                                
                                                let mut data = market_data.lock().await;
                                                data.insert(inst_id.to_string(), ws_data);
                                                
                                                if message_count % 100 == 0 {
                                                    println!("📊 OKX {}: bid={:.4}, ask={:.4}, last={:.4}", inst_id, final_bid, final_ask, last);
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                Err(e) => {
                    println!("❌ OKX WebSocket error: {:?}", e);
                    break;
                }
            }
        }
        println!("❌ OKX WebSocket stream ended");
    }

    pub async fn get_market_data(&self, symbol: &str) -> Option<WebSocketMarketData> {
        let data = self.market_data.lock().await;
        
        // Try exact match first
        if let Some(result) = data.get(symbol).cloned() {
            return Some(result);
        }
        
        // Try normalized versions
        let normalized_symbols = Self::normalize_symbol(symbol);
        for normalized in normalized_symbols {
            if let Some(result) = data.get(&normalized).cloned() {
                return Some(result);
            }
        }
        
        // Тихо возвращаем None без логирования
        None
    }
    
    fn normalize_symbol(symbol: &str) -> Vec<String> {
        let mut variants = Vec::new();
        
        // Add original
        variants.push(symbol.to_string());
        
        // Convert between different formats
        if symbol.contains("-USDT-SWAP") {
            // OKX format to Binance format
            let binance_format = symbol.replace("-USDT-SWAP", "USDT");
            variants.push(binance_format);
        } else if symbol.ends_with("USDT") && !symbol.contains("-") {
            // Binance format to OKX format
            let okx_format = symbol.replace("USDT", "-USDT-SWAP");
            variants.push(okx_format);
        }
        
        variants
    }
} 