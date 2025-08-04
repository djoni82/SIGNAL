use std::collections::{HashMap, HashSet};
use serde_json::Value;
use anyhow::Result;

#[derive(Debug, Clone)]
pub struct SymbolInfo {
    pub inst_id: String,
    pub tick_size: f64,
    pub lot_size: f64,
    pub min_qty: f64,
    pub min_notional: f64,
    pub status: String,
}

#[derive(Debug, Clone)]
pub struct SymbolValidator {
    pub allowed_pairs: HashSet<String>,
    pub symbol_info: HashMap<String, SymbolInfo>,
}

impl SymbolValidator {
    pub async fn new() -> Result<Self> {
        let (allowed_pairs, symbol_info) = Self::fetch_all_exchange_symbols().await?;
        
        println!("✅ Loaded {} valid trading pairs from exchanges", allowed_pairs.len());
        println!("📋 Sample pairs: {:?}", 
            allowed_pairs.iter().take(10).collect::<Vec<_>>());
        
        Ok(Self {
            allowed_pairs,
            symbol_info,
        })
    }

    // 🔥 ЗАГРУЗКА СИМВОЛОВ С ВСЕХ БИРЖ (OKX + BINANCE)
    async fn fetch_all_exchange_symbols() -> Result<(HashSet<String>, HashMap<String, SymbolInfo>)> {
        let mut allowed = HashSet::new();
        let mut symbol_map = HashMap::new();
        
        // 🔥 ЗАГРУЗКА С OKX
        let (okx_pairs, okx_symbols) = Self::fetch_okx_swap_symbols().await?;
        let okx_count = okx_pairs.len();
        allowed.extend(okx_pairs);
        symbol_map.extend(okx_symbols);
        
        // 🔥 ЗАГРУЗКА С BINANCE
        let (binance_pairs, binance_symbols) = Self::fetch_binance_futures_symbols().await?;
        let binance_count = binance_pairs.len();
        allowed.extend(binance_pairs);
        symbol_map.extend(binance_symbols);
        
        println!("🔍 OKX pairs: {}, Binance pairs: {}", okx_count, binance_count);
        
        Ok((allowed, symbol_map))
    }

    // 🔥 ЗАГРУЗКА С BINANCE FUTURES
    async fn fetch_binance_futures_symbols() -> Result<(HashSet<String>, HashMap<String, SymbolInfo>)> {
        let url = "https://fapi.binance.com/fapi/v1/exchangeInfo";
        
        println!("🔍 Fetching trading pairs from Binance Futures...");
        
        let response = reqwest::get(url).await?;
        let data: Value = response.json().await?;
        
        let mut allowed = HashSet::new();
        let mut symbol_map = HashMap::new();
        
        if let Some(symbols) = data["symbols"].as_array() {
            for symbol in symbols {
                if let Some(symbol_name) = symbol["symbol"].as_str() {
                    if let Some(status) = symbol["status"].as_str() {
                        // Только активные символы
                        if status == "TRADING" && symbol_name.ends_with("USDT") {
                            allowed.insert(symbol_name.to_string());
                            
                            let tick_size = symbol["filters"]
                                .as_array()
                                .and_then(|filters| {
                                    filters.iter().find(|f| f["filterType"] == "PRICE_FILTER")
                                })
                                .and_then(|f| f["tickSize"].as_str())
                                .and_then(|s| s.parse::<f64>().ok())
                                .unwrap_or(0.00001);
                            
                            let step_size = symbol["filters"]
                                .as_array()
                                .and_then(|filters| {
                                    filters.iter().find(|f| f["filterType"] == "LOT_SIZE")
                                })
                                .and_then(|f| f["stepSize"].as_str())
                                .and_then(|s| s.parse::<f64>().ok())
                                .unwrap_or(0.001);
                            
                            let min_qty = symbol["filters"]
                                .as_array()
                                .and_then(|filters| {
                                    filters.iter().find(|f| f["filterType"] == "LOT_SIZE")
                                })
                                .and_then(|f| f["minQty"].as_str())
                                .and_then(|s| s.parse::<f64>().ok())
                                .unwrap_or(0.001);
                            
                            let min_notional = symbol["filters"]
                                .as_array()
                                .and_then(|filters| {
                                    filters.iter().find(|f| f["filterType"] == "MIN_NOTIONAL")
                                })
                                .and_then(|f| f["notional"].as_str())
                                .and_then(|s| s.parse::<f64>().ok())
                                .unwrap_or(5.0);
                            
                            symbol_map.insert(
                                symbol_name.to_string(),
                                SymbolInfo {
                                    inst_id: symbol_name.to_string(),
                                    tick_size,
                                    lot_size: step_size,
                                    min_qty,
                                    min_notional,
                                    status: status.to_string(),
                                }
                            );
                        }
                    }
                }
            }
        }
        
        println!("✅ Loaded {} Binance Futures symbols", allowed.len());
        Ok((allowed, symbol_map))
    }

    // 🔥 ЗАГРУЗКА РЕАЛЬНЫХ ТИКЕРОВ С OKX SWAP
    async fn fetch_okx_swap_symbols() -> Result<(HashSet<String>, HashMap<String, SymbolInfo>)> {
        let url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP";
        
        println!("🔍 Fetching real trading pairs from OKX SWAP...");
        
        let response = reqwest::get(url).await?;
        let data: Value = response.json().await?;
        
        let mut allowed = HashSet::new();
        let mut symbol_map = HashMap::new();
        
        if let Some(instruments) = data["data"].as_array() {
            for instrument in instruments {
                if let Some(inst_id) = instrument["instId"].as_str() {
                    if let Some(state) = instrument["state"].as_str() {
                        // Только активные инструменты
                        if state == "live" {
                            allowed.insert(inst_id.to_string());
                            
                            let tick_size = instrument["tickSz"].as_str()
                                .unwrap_or("0.0001")
                                .parse()
                                .unwrap_or(0.0001);
                            
                            let lot_size = instrument["lotSz"].as_str()
                                .unwrap_or("0.001")
                                .parse()
                                .unwrap_or(0.001);
                            
                            let min_qty = instrument["minSz"].as_str()
                                .unwrap_or("0.001")
                                .parse()
                                .unwrap_or(0.001);
                            
                            let min_notional = instrument.get("minNotional")
                                .and_then(|v| v.as_str())
                                .unwrap_or("5.0")
                                .parse()
                                .unwrap_or(5.0);
                            
                            symbol_map.insert(
                                inst_id.to_string(),
                                SymbolInfo {
                                    inst_id: inst_id.to_string(),
                                    tick_size,
                                    lot_size,
                                    min_qty,
                                    min_notional,
                                    status: state.to_string(),
                                }
                            );
                        }
                    }
                }
            }
        }
        
        Ok((allowed, symbol_map))
    }

    // 🔥 ПРОВЕРКА ЧТО ПАРА СУЩЕСТВУЕТ
    pub fn is_valid_pair(&self, pair: &str) -> bool {
        self.allowed_pairs.contains(pair)
    }

    // 🔥 ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СИМВОЛЕ
    pub fn get_symbol_info(&self, pair: &str) -> Option<&SymbolInfo> {
        self.symbol_info.get(pair)
    }

    // 🔥 ФИЛЬТРАЦИЯ СПИСКА ПАР
    pub fn filter_valid_pairs(&self, pairs: &[String]) -> Vec<String> {
        pairs.iter()
            .filter(|p| self.is_valid_pair(p))
            .cloned()
            .collect()
    }

    // 🔥 ПОЛУЧЕНИЕ БЕЗОПАСНОГО СПИСКА ПАР
    pub fn get_safe_trading_pairs(&self, max_pairs: usize) -> Vec<String> {
        // 🔥 ОБНОВЛЕННЫЙ СПИСОК ПАР С ВОЛАТИЛЬНЫМИ АЛЬТАМИ (ПРИОРИТЕТ ВОЛАТИЛЬНЫМ)
        let verified_pairs = vec![
            // Мемкоины (очень высокий спред) - ПРИОРИТЕТ
            "SHIB-USDT-SWAP".to_string(),
            "MEME-USDT-SWAP".to_string(),
            "AI-USDT-SWAP".to_string(),
            "SEI-USDT-SWAP".to_string(),
            "AEVO-USDT-SWAP".to_string(),
            "PEPE-USDT-SWAP".to_string(),
            "DOGE-USDT-SWAP".to_string(),
            
            // Альты (высокий спред)
            "ARB-USDT-SWAP".to_string(),
            "SUI-USDT-SWAP".to_string(),
            "RNDR-USDT-SWAP".to_string(),
            "WLD-USDT-SWAP".to_string(),
            "BLUR-USDT-SWAP".to_string(),
            "OP-USDT-SWAP".to_string(),
            "THETA-USDT-SWAP".to_string(),
            "FIL-USDT-SWAP".to_string(),
            "ATOM-USDT-SWAP".to_string(),
            "AAVE-USDT-SWAP".to_string(),
            
            // Mid-cap (средний спред)
            "BNB-USDT-SWAP".to_string(), 
            "SOL-USDT-SWAP".to_string(),
            
            // Топ пары (низкий спред) - В КОНЦЕ
            "BTC-USDT-SWAP".to_string(),
            "ETH-USDT-SWAP".to_string(),
        ];
        
        println!("🔍 Using verified pairs for both OKX and Binance: {:?}", verified_pairs);
        
        // Фильтруем только те, что есть в allowed_pairs
        let mut safe_pairs: Vec<String> = verified_pairs.into_iter()
            .filter(|p| self.allowed_pairs.contains(p))
            .collect();
        
        println!("✅ Verified pairs found in APIs: {:?}", safe_pairs);
        
        safe_pairs.truncate(max_pairs);
        safe_pairs
    }

    // 🔥 ПРИОРИТЕТ ПАР (основные пары имеют высокий приоритет)
    fn get_pair_priority(pair: &str) -> i32 {
        let major_pairs = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX"];
        
        for (i, major) in major_pairs.iter().enumerate() {
            if pair.contains(major) {
                return (major_pairs.len() - i) as i32;
            }
        }
        0
    }

    // 🔥 ОКРУГЛЕНИЕ ЦЕНЫ И РАЗМЕРА
    pub fn round_to_tick(&self, price: f64, pair: &str) -> f64 {
        if let Some(info) = self.get_symbol_info(pair) {
            if info.tick_size > 0.0 {
                return (price / info.tick_size).floor() * info.tick_size;
            }
        }
        price
    }

    pub fn round_to_step(&self, size: f64, pair: &str) -> f64 {
        if let Some(info) = self.get_symbol_info(pair) {
            if info.lot_size > 0.0 {
                return (size / info.lot_size).floor() * info.lot_size;
            }
        }
        size
    }

    // 🔥 ВАЛИДАЦИЯ ОРДЕРА
    pub fn validate_order(&self, pair: &str, price: f64, size: f64) -> bool {
        if let Some(info) = self.get_symbol_info(pair) {
            let rounded_price = self.round_to_tick(price, pair);
            let rounded_size = self.round_to_step(size, pair);
            let notional = rounded_price * rounded_size;
            
            rounded_size >= info.min_qty && notional >= info.min_notional
        } else {
            false
        }
    }
} 