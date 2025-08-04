use std::sync::Arc;
use tokio::{sync::{Mutex, Semaphore}, time::{interval, Duration}};
use anyhow::Result;
use chrono::Utc;
use std::collections::VecDeque;
use std::time::SystemTime;
use futures_util::{StreamExt, SinkExt};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use serde::{Deserialize, Serialize};

// modules:
mod config;
mod exchange;
mod risk;
mod pricing;
mod order;
mod indicators;
mod telegram;
mod web_ui;
mod websocket;
mod symbol_validator;

use crate::exchange::{Exchange, MarketData, Binance, Okx};
use crate::risk::{RiskManager, Trade};
use crate::order::{OrderManager, OrderInfo, OrderSide};
use crate::pricing::PricingEngine;
use crate::symbol_validator::SymbolValidator;

// Глобальные переменные
lazy_static::lazy_static! {
    static ref ACTIVE_ORDERS: Arc<Mutex<Vec<OrderInfo>>> = Arc::new(Mutex::new(Vec::new()));
    static ref OPEN_POSITIONS: Arc<Mutex<Vec<Position>>> = Arc::new(Mutex::new(Vec::new()));
}

// 🔥 ГЛОБАЛЬНЫЕ КОНСТАНТЫ С УЧЕТОМ КОМИССИЙ
const COMMISSION_MAKER: f64 = 0.0002; // 0.02% - комиссия мейкера
const COMMISSION_TAKER: f64 = 0.0005; // 0.05% - комиссия тейкера  
const MIN_PROFIT_MARGIN: f64 = 0.0001; // 0.01% - минимальная прибыль

// 🔥 АГРЕССИВНЫЕ НАСТРОЙКИ ДЛЯ HFT СКАЛЬПИНГА (С УЧЕТОМ КОМИССИЙ)
const TAKE_PROFIT_PCT: f64 = 0.0015;   // 0.15% - покрывает комиссии + прибыль
const STOP_LOSS_PCT: f64 = 0.0010;     // 0.10% - быстрый SL с учетом комиссий
const TRAILING_STOP_PCT: f64 = 0.0005; // 0.05% - тайтовый trailing

// 🔥 СТРУКТУРА ПОЗИЦИИ
#[derive(Clone)]
struct Position {
    pair: String,
    side: String,           // "BUY" или "SELL"
    entry_price: f64,
    size: f64,
    timestamp: chrono::DateTime<Utc>,
    order_id: String,
    high_since_entry: f64,  // для trailing stop
    low_since_entry: f64,   // для trailing stop
}

// 🔥 WEB SOCKET СТРУКТУРЫ
#[derive(Deserialize)]
struct OkxTick {
    asks: Vec<[String; 2]>,
    bids: Vec<[String; 2]>,
    ts: String,
    #[serde(default)]
    last: Option<String>,
}

#[derive(Deserialize)]
struct BinanceBookTick {
    b: Vec<[String;2]>,     // bids ["цена", "объем"]
    a: Vec<[String;2]>,     // asks
    E: Option<i64>,         // event time
}

// 🔥 ДИФФЕРЕНЦИРОВАННЫЕ ПОРОГИ СПРЕДА ПО КЛАССАМ ПАР (РЕАЛЬНЫЙ HFT)
fn min_spread_for_pair(pair: &str) -> f64 {
    // Базовый спред = 2 * мейкер_комиссия + минимальная прибыль
    // Убираем тейкер комиссию - она только при закрытии рыночным ордером
    let base_spread = 2.0 * COMMISSION_MAKER + MIN_PROFIT_MARGIN;
    // base_spread = 2 * 0.0002 + 0.0001 = 0.0005 (0.05%)
    
    match pair {
        // Топ-пары: базовый спред без надбавки
        "BTC-USDT-SWAP" | "ETH-USDT-SWAP" => base_spread, // 0.05%
        
        // Популярные альты: базовый спред + 10%
        "SOL-USDT-SWAP" | "BNB-USDT-SWAP" => base_spread * 1.1, // 0.055%
        
        // Средние альты: базовый спред + 20%
        "DOGE-USDT-SWAP" | "PEPE-USDT-SWAP" | "FIL-USDT-SWAP" | "BLUR-USDT-SWAP" => base_spread * 1.2, // 0.06%
        
        // Менее ликвидные: базовый спред + 30%
        "OP-USDT-SWAP" | "SHIB-USDT-SWAP" | "WLD-USDT-SWAP" | "ARB-USDT-SWAP" | 
        "SUI-USDT-SWAP" | "ATOM-USDT-SWAP" | "AAVE-USDT-SWAP" => base_spread * 1.3, // 0.065%
        
        // Мемкоины и рискованные: базовый спред + 40%
        "MEME-USDT-SWAP" | "AI-USDT-SWAP" | "SEI-USDT-SWAP" | "AEVO-USDT-SWAP" => base_spread * 1.4, // 0.07%
        
        // Остальные: базовый спред + 50%
        _ => base_spread * 1.5 // 0.075%
    }
}

// 🔥 ОБНОВЛЕННАЯ AI-ЛОГИКА РАСЧЕТА СПРЕДА С УЧЕТОМ ТРЕНДА
pub fn calculate_ai_spread(
    _commission: f64,
    _min_profit: f64,
    volatility: f64,
    _volume: f64,
    _min_volume: f64,
    _rolling_pnl: f64,
    _recent_tick_moves: &[f64],
    _prev_avg_spread: f64,
    _last_spread: f64,
    _risk_mode: bool,
    _is_new_high: bool,
    pair: &str,
    trend_strength: f64,  // 🔥 ДОБАВИЛИ СИЛУ ТРЕНДА
) -> f64 {
    // 🔥 НАЧИНАЕМ С ГАРАНТИРОВАННО ПРИБЫЛЬНОГО СПРЕДА
    let min_spread = min_spread_for_pair(pair);
    let mut ai_spread = min_spread;

    // 🔥 АДАПТАЦИЯ К ТРЕНДУ - КЛЮЧЕВОЕ ИЗМЕНЕНИЕ!
    if trend_strength.abs() > 0.003 {
        // Увеличиваем спред при сильном тренде (избегаем торговли против рынка)
        ai_spread += 0.0005;
        println!("📈 {}: Trend detected ({:.3}%), increasing spread by 0.05%", 
                 pair, trend_strength * 100.0);
    }

    // 🔥 АДАПТАЦИЯ К ВОЛАТИЛЬНОСТИ - УВЕЛИЧИВАЕМ ПОРОГ
    if volatility > 0.005 { // Увеличиваем с 0.002 до 0.005
        let volatility_addon = volatility * 0.5; // Увеличиваем коэффициент с 0.3 до 0.5
        ai_spread += volatility_addon;
        println!("🌊 {}: High volatility ({:.3}%), adding {:.4}%", 
                 pair, volatility * 100.0, volatility_addon * 100.0);
    }

    // 🔥 ЗАЩИТА ОТ СВЕРХУЗКИХ СПРЕДОВ
    let max_spread = min_spread * 3.0; // Максимум в 3 раза больше минимального
    ai_spread = ai_spread.clamp(min_spread, max_spread);
    
    println!("🧠 {}: AI spread: min={:.3}%, final={:.3}%, trend={:.3}%", 
             pair, min_spread * 100.0, ai_spread * 100.0, trend_strength * 100.0);
    
    ai_spread
}

// 🔥 ФУНКЦИЯ ПРОВЕРКИ УСЛОВИЙ ЗАКРЫТИЯ ПОЗИЦИИ (TP/SL/TRAILING)
fn should_close_position(entry_price: f64, current_price: f64, side: &str, high_since_entry: f64, low_since_entry: f64) -> Option<&'static str> {
    match side {
        "BUY" => {
            let take_profit = entry_price * (1.0 + TAKE_PROFIT_PCT);
            let stop_loss = entry_price * (1.0 - STOP_LOSS_PCT);
            
            // 🔥 УЛУЧШЕННАЯ ЛОГИКА TRAILING STOP
            let trailing_stop = if high_since_entry > entry_price {
                // Если цена была выше входа - используем trailing stop от high
                high_since_entry * (1.0 - TRAILING_STOP_PCT)
            } else {
                // Если цена не была выше входа - используем обычный stop loss
                stop_loss
            };
            
            // 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ BUY ПОЗИЦИИ
            if current_price >= take_profit {
                println!("🎯 [TP CHECK] BUY: current={:.5} >= tp={:.5} (entry={:.5} + {:.1}%)", 
                         current_price, take_profit, entry_price, TAKE_PROFIT_PCT * 100.0);
                Some("tp") // Take-profit сработал
            } else if current_price <= stop_loss {
                println!("🎯 [SL CHECK] BUY: current={:.5} <= sl={:.5} (entry={:.5} - {:.1}%)", 
                         current_price, stop_loss, entry_price, STOP_LOSS_PCT * 100.0);
                Some("sl") // Stop-loss сработал
            } else if current_price <= trailing_stop && high_since_entry > entry_price {
                println!("🎯 [TRAILING CHECK] BUY: current={:.5} <= trailing={:.5} (high={:.5} - {:.1}%)", 
                         current_price, trailing_stop, high_since_entry, TRAILING_STOP_PCT * 100.0);
                Some("trailing") // Trailing stop сработал
            } else {
                None
            }
        }
        "SELL" => {
            let take_profit = entry_price * (1.0 - TAKE_PROFIT_PCT);
            let stop_loss = entry_price * (1.0 + STOP_LOSS_PCT);
            
            // 🔥 УЛУЧШЕННАЯ ЛОГИКА TRAILING STOP
            let trailing_stop = if low_since_entry < entry_price {
                // Если цена была ниже входа - используем trailing stop от low
                low_since_entry * (1.0 + TRAILING_STOP_PCT)
            } else {
                // Если цена не была ниже входа - используем обычный stop loss
                stop_loss
            };
            
            // 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ SELL ПОЗИЦИИ
            if current_price <= take_profit {
                println!("🎯 [TP CHECK] SELL: current={:.5} <= tp={:.5} (entry={:.5} - {:.1}%)", 
                         current_price, take_profit, entry_price, TAKE_PROFIT_PCT * 100.0);
                Some("tp")
            } else if current_price >= stop_loss {
                println!("🎯 [SL CHECK] SELL: current={:.5} >= sl={:.5} (entry={:.5} + {:.1}%)", 
                         current_price, stop_loss, entry_price, STOP_LOSS_PCT * 100.0);
                Some("sl")
            } else if current_price >= trailing_stop && low_since_entry < entry_price {
                println!("🎯 [TRAILING CHECK] SELL: current={:.5} >= trailing={:.5} (low={:.5} + {:.1}%)", 
                         current_price, trailing_stop, low_since_entry, TRAILING_STOP_PCT * 100.0);
                Some("trailing")
            } else {
                None
            }
        }
        _ => None
    }
}

// 🔥 WEB SOCKET ФУНКЦИИ
pub async fn start_okx_ws(pair: &str, md: Arc<tokio::sync::RwLock<MarketData>>, price_history: Arc<Mutex<VecDeque<f64>>>) {
    let ws_url = "wss://ws.okx.com:8443/ws/v5/public";
    let topic = format!(r#"{{"op":"subscribe","args":[{{"channel":"books5","instId":"{}"}}]}}"#, pair);
    
    println!("🔌 Connecting to OKX WebSocket: {}", ws_url);
    println!("📡 Subscribing to: {}", topic);

    match connect_async(ws_url).await {
        Ok((ws_stream, _)) => {
            let (mut write, mut read) = ws_stream.split();
            
            if let Err(e) = write.send(Message::Text(topic)).await {
                println!("❌ Failed to send OKX subscription: {}", e);
                return;
            }
            
            println!("✅ Connected to OKX WebSocket for {}", pair);

            while let Some(Ok(msg)) = read.next().await {
                if let Message::Text(txt) = msg {
                    // 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
                    if txt.contains("books5") && txt.contains(pair) {
                        println!("📨 OKX message: {}", txt);
                        
                        if txt.contains("asks") && txt.contains("bids") {
                            if let Ok(serde_json::Value::Object(resp)) = serde_json::from_str::<serde_json::Value>(&txt) {
                                if let Some(data) = resp.get("data").and_then(|a| a.as_array()).and_then(|a| a.get(0)) {
                                    // 🔥 ПРЯМОЙ ПАРСИНГ ИЗ JSON - БЕЗ СТРУКТУРЫ
                                    if let (Some(bids), Some(asks)) = (data.get("bids"), data.get("asks")) {
                                        if let (Some(bid_array), Some(ask_array)) = (bids.as_array(), asks.as_array()) {
                                            if let (Some(bid_data), Some(ask_data)) = (bid_array.get(0), ask_array.get(0)) {
                                                if let (Some(bid_str), Some(ask_str)) = (bid_data.as_array().and_then(|b| b.get(0)).and_then(|b| b.as_str()),
                                                                                       ask_data.as_array().and_then(|a| a.get(0)).and_then(|a| a.as_str())) {
                                                    if let (Ok(bid), Ok(ask)) = (bid_str.parse::<f64>(), ask_str.parse::<f64>()) {
                                                        // 🔥 ПРОВЕРЯЕМ ВАЛИДНОСТЬ ЦЕН
                                                        if bid > 0.0 && ask > 0.0 && ask > bid {
                                                            let last = (bid + ask) / 2.0;
                                                            let ts = data.get("ts").and_then(|t| t.as_str()).and_then(|t| t.parse::<i64>().ok()).unwrap_or(Utc::now().timestamp());

                                                            let mut mdw = md.write().await;
                                                            mdw.bid = bid;
                                                            mdw.ask = ask;
                                                            mdw.last = last;
                                                            mdw.timestamp = ts;
                                                            
                                                            // 🔥 ОБНОВЛЯЕМ ИСТОРИЮ ЦЕН
                                                            let mut ph = price_history.lock().await;
                                                            ph.push_back(last);
                                                            if ph.len() > 50 {
                                                                ph.pop_front();
                                                            }
                                                            
                                                            println!("✅ OKX {}: bid={:.8}, ask={:.8}, last={:.8}, spread={:.4}%", 
                                                                     pair, bid, ask, last, ((ask - bid) / last) * 100.0);
                                                        } else {
                                                            println!("⚠️ OKX {}: Invalid prices bid={:.4}, ask={:.4} (ask > bid: {})", 
                                                                     pair, bid, ask, ask > bid);
                                                        }
                                                    } else {
                                                        println!("❌ OKX {}: Failed to parse bid/ask as f64", pair);
                                                    }
                                                } else {
                                                    println!("❌ OKX {}: No bid/ask strings found", pair);
                                                }
                                            } else {
                                                println!("❌ OKX {}: No bid/ask arrays found", pair);
                                            }
                                        } else {
                                            println!("❌ OKX {}: Bids/asks are not arrays", pair);
                                        }
                                    } else {
                                        println!("❌ OKX {}: No bids/asks in data", pair);
                                    }
                                } else {
                                    println!("❌ OKX {}: No data array found", pair);
                                }
                            } else {
                                println!("❌ OKX {}: Failed to parse JSON response", pair);
                            }
                        }
                    }
                }
            }
        }
        Err(e) => {
            println!("❌ Failed to connect to OKX WebSocket: {}", e);
        }
    }
}

pub async fn start_binance_ws(pair: &str, md: Arc<tokio::sync::RwLock<MarketData>>, price_history: Arc<Mutex<VecDeque<f64>>>) {
    // 🔥 НОРМАЛИЗУЕМ СИМВОЛ ДЛЯ BINANCE: BTC-USDT-SWAP -> btcusdt
    let sym = pair
        .replace("-USDT-SWAP", "")
        .replace("-USDT", "")
        .to_ascii_lowercase();
    
    let ws_url = format!("wss://fstream.binance.com/ws/{}@depth5@100ms", sym);
    println!("🔌 Connecting to Binance WebSocket: {}", ws_url);

    match connect_async(ws_url).await {
        Ok((ws_stream, _)) => {
            let (_write, mut read) = ws_stream.split();
            println!("✅ Connected to Binance WebSocket for {}", pair);

            while let Some(Ok(msg)) = read.next().await {
                if let Message::Text(txt) = msg {
                    if let Ok(tick) = serde_json::from_str::<BinanceBookTick>(&txt) {
                        let bid = tick.b.get(0).and_then(|b| b[0].parse().ok()).unwrap_or(0.0);
                        let ask = tick.a.get(0).and_then(|a| a[0].parse().ok()).unwrap_or(0.0);
                        let ts = tick.E.unwrap_or(Utc::now().timestamp());

                        let mut mdw = md.write().await;
                        mdw.bid = bid;
                        mdw.ask = ask;
                        mdw.last = (bid + ask) / 2.0;
                        mdw.timestamp = ts;
                        
                        // 🔥 ОБНОВЛЯЕМ ИСТОРИЮ ЦЕН
                        let mut ph = price_history.lock().await;
                        ph.push_back((bid + ask) / 2.0);
                        if ph.len() > 50 {
                            ph.pop_front();
                        }
                        
                        println!("📊 Binance {}: bid={:.4}, ask={:.4}", pair, bid, ask);
                    }
                }
            }
        }
        Err(e) => {
            println!("❌ Failed to connect to Binance WebSocket: {}", e);
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("🚀 Starting HFT Market Making Bot v8.0 (AI Dynamic Spread System)...");

    let config = config::load_config().await?;
    
    // Поддержка обеих бирж
    let binance = Arc::new(Binance::new(config.exchanges[0].clone()));
    let okx = Arc::new(Okx::new(config.exchanges[1].clone()));
    let exchanges: Vec<Arc<dyn Exchange>> = vec![binance.clone(), okx.clone()];

    // Подключаемся к биржам
    for exchange in &exchanges {
        if let Err(e) = exchange.connect().await {
            println!("❌ Failed to connect to {}: {}", exchange.name(), e);
            continue;
        }
        println!("✅ Connected to {}", exchange.name());
    }

    // 🔥 ЗАГРУЗКА ВАЛИДНЫХ ТИКЕРОВ С БИРЖИ
    let symbol_validator = match SymbolValidator::new().await {
        Ok(validator) => validator,
        Err(e) => {
            println!("❌ Failed to load symbol validator: {}", e);
            println!("⚠️ Using fallback pairs...");
            // 🔥 СОЗДАЕМ FALLBACK VALIDATOR С БАЗОВЫМИ ПАРАМИ
            let fallback_pairs = vec![
                // OKX пары (SWAP формат)
                "BTC-USDT-SWAP".to_string(),
                "ETH-USDT-SWAP".to_string(), 
                "SOL-USDT-SWAP".to_string(),
                "BNB-USDT-SWAP".to_string(),
                "DOGE-USDT-SWAP".to_string(),
                "PEPE-USDT-SWAP".to_string(),
                "FIL-USDT-SWAP".to_string(),
                "BLUR-USDT-SWAP".to_string(),
                "OP-USDT-SWAP".to_string(),
                "SHIB-USDT-SWAP".to_string(),
                "WLD-USDT-SWAP".to_string(),
                "ARB-USDT-SWAP".to_string(),
                "SUI-USDT-SWAP".to_string(),
                "ATOM-USDT-SWAP".to_string(),
                "AAVE-USDT-SWAP".to_string(),
                "MEME-USDT-SWAP".to_string(),
                "AI-USDT-SWAP".to_string(),
                "SEI-USDT-SWAP".to_string(),
                "AEVO-USDT-SWAP".to_string(),
                "RNDR-USDT-SWAP".to_string(),
                
                // Binance пары (без SWAP)
                "BTCUSDT".to_string(),
                "ETHUSDT".to_string(),
                "SOLUSDT".to_string(),
                "BNBUSDT".to_string(),
                "DOGEUSDT".to_string(),
                "PEPEUSDT".to_string(),
                "FILUSDT".to_string(),
                "BLURUSDT".to_string(),
                "OPUSDT".to_string(),
                "SHIBUSDT".to_string(),
                "WLDUSDT".to_string(),
                "ARBUSDT".to_string(),
                "SUIUSDT".to_string(),
                "ATOMUSDT".to_string(),
                "AAVEUSDT".to_string(),
                "RNDRUSDT".to_string(),
            ];
            
            // 🔥 СОЗДАЕМ ПРОСТОЙ FALLBACK VALIDATOR
            let mut fallback_validator = SymbolValidator {
                allowed_pairs: fallback_pairs.iter().cloned().collect(),
                symbol_info: std::collections::HashMap::new(),
            };
            
            // 🔥 ДОБАВЛЯЕМ БАЗОВУЮ ИНФОРМАЦИЮ О СИМВОЛАХ
            for pair in &fallback_pairs {
                fallback_validator.symbol_info.insert(pair.clone(), crate::symbol_validator::SymbolInfo {
                    inst_id: pair.clone(),
                    min_qty: 0.001,
                    min_notional: 10.0,
                    tick_size: 0.0001,
                    lot_size: 0.0001,
                    status: "TRADING".to_string(),
                });
            }
            
            fallback_validator
        }
    };

    // 🔥 ПОЛУЧАЕМ БЕЗОПАСНЫЙ СПИСОК ТОРГУЕМЫХ ПАР
    let tickers = symbol_validator.get_safe_trading_pairs(20); // 🔥 20 ПАР ВКЛЮЧАЯ ВОЛАТИЛЬНЫЕ АЛЬТЫ
    
    if tickers.is_empty() {
        println!("❌ No valid trading pairs found!");
        return Ok(());
    }
    
    println!("🎯 Selected {} safe trading pairs: {:?}", tickers.len(), tickers);

    // 🔥 ПОЛУЧАЕМ РЕАЛЬНЫЙ БАЛАНС С БИРЖИ
    let mut total_balance = 0.0;
    for exchange in &exchanges {
        match exchange.check_balance().await {
            Ok(balance) => {
                println!("💰 {} balance: ${:.2}", exchange.name(), balance);
                total_balance += balance;
            }
            Err(e) => {
                println!("❌ Failed to get {} balance: {}", exchange.name(), e);
                // Используем минимальный баланс если не удалось получить
                total_balance += 100.0;
            }
        }
    }
    
    println!("💰 Total balance across all exchanges: ${:.2}", total_balance);
    
    // 🔥 СОЗДАЕМ РИСК-МЕНЕДЖЕР С РЕАЛЬНЫМ БАЛАНСОМ
    let rm = Arc::new(Mutex::new(RiskManager::new_with_daily_stop(total_balance, 300.0))); // day stop $300
    let om = Arc::new(OrderManager::new(rm.clone(), tickers.clone()));
    
    // 🔥 ГЛОБАЛЬНЫЙ RATE LIMITER: 1 запрос в секунду на пару
    let rate_limit = Arc::new(Semaphore::new(1));

    // 🔥 ИНИЦИАЛИЗИРУЕМ SYMBOL MANAGER для каждой биржи
    for exchange in &exchanges {
        if let Err(e) = om.get_grid_manager().initialize_symbols(exchange).await {
            println!("❌ Failed to initialize symbols for {}: {}", exchange.name(), e);
        } else {
            println!("✅ Initialized symbols for {}", exchange.name());
        }
    }

    // 🔥 ЗАПУСКАЕМ УМНЫЕ GRID ВОРКЕРЫ с раунд-робин
    for (exchange_index, exchange) in exchanges.iter().enumerate() {
        // 🔥 ФИЛЬТРУЕМ ПАРЫ ДЛЯ КОНКРЕТНОЙ БИРЖИ
        let exchange_pairs: Vec<String> = tickers.iter()
            .filter(|pair| {
                match exchange.name() {
                    "okx" => pair.contains("-SWAP"), // OKX формат: BTC-USDT-SWAP
                    "binance" => !pair.contains("-SWAP") && pair.ends_with("USDT"), // Binance формат: BTCUSDT
                    _ => false
                }
            })
            .cloned()
            .collect();
        
        // 🔥 ПРОВЕРЯЕМ ЧТО ЕСТЬ ПАРЫ ДЛЯ ТОРГОВЛИ
        if exchange_pairs.is_empty() {
            println!("⚠️ No pairs available for {} - skipping", exchange.name());
            println!("🔍 Available tickers: {:?}", tickers);
            println!("🔍 Exchange name: {}", exchange.name());
            continue;
        }
        
        println!("🎯 {} will trade {} pairs: {:?}", exchange.name(), exchange_pairs.len(), exchange_pairs);
        
        for (ticker_index, pair) in exchange_pairs.iter().enumerate() {
            let om = om.clone();
            let rm = rm.clone();
            let ex = exchange.clone();
            let pair = pair.clone();
            let validator = Arc::new(symbol_validator.clone());
            let rate_limit = rate_limit.clone();
            
            // 🔥 РАУНД-РОБИН: Задержка между запусками для избежания rate limit
            let delay_ms = (exchange_index * exchange_pairs.len() + ticker_index) * 300;
            
            tokio::spawn(async move {
                tokio::time::sleep(Duration::from_millis(delay_ms as u64)).await;
                grid_worker(ex, om, rm, pair, validator, rate_limit).await;
            });
        }
    }

    // 🔥 ЗАПУСКАЕМ ОТДЕЛЬНЫЙ WORKER ДЛЯ МОНИТОРИНГА ПОЗИЦИЙ
    let positions_exchange = exchanges[0].clone(); // Используем первую доступную биржу
    let positions_om = om.clone();
    let positions_rm = rm.clone();
    
    // 🔥 СОЗДАЕМ ГЛОБАЛЬНЫЙ EXPOSURE MANAGER
    let global_exposure_manager = Arc::new(Mutex::new(ExposureManager::new(total_balance * 0.5))); // 50% от баланса
    
    // 🔥 ЗАПУСКАЕМ EXPOSURE RESET WORKER
    let exposure_reset_manager = global_exposure_manager.clone();
    tokio::spawn(async move {
        exposure_reset_worker(exposure_reset_manager).await;
    });
    
    // 🔥 ЗАГРУЖАЕМ РЕАЛЬНЫЕ ОТКРЫТЫЕ ПОЗИЦИИ С OKX
    println!("🔍 Loading real open positions from OKX...");
    for exchange in &exchanges {
        if exchange.name() == "okx" {
            match exchange.get_open_positions().await {
                Ok(positions) => {
                    println!("✅ Found {} open positions on OKX", positions.len());
                    for pos in positions {
                        let position = Position {
                            pair: pos.pair.clone(),
                            side: pos.side.clone(),
                            entry_price: pos.entry_price,
                            size: pos.size,
                            timestamp: Utc::now() - chrono::Duration::minutes(5), // Предполагаем позиция открыта 5 мин назад
                            order_id: pos.id.clone(),
                            high_since_entry: pos.current_price, // Инициализируем текущей ценой
                            low_since_entry: pos.current_price,
                        };
                        OPEN_POSITIONS.lock().await.push(position.clone());
                        println!("📊 [REAL POSITION] {} {} @ {:.5} (PnL: {:.2}%)", 
                                 position.pair, position.side, position.entry_price, pos.pnl_percent);
                    }
                }
                Err(e) => {
                    println!("❌ Failed to load positions from OKX: {}", e);
                    println!("🧪 Using test positions instead...");
                    
                    // Fallback к тестовым позициям если не удалось загрузить реальные
                    let test_position = Position {
                        pair: "BTC-USDT-SWAP".to_string(),
                        side: "BUY".to_string(),
                        entry_price: 95000.0,
                        size: 0.001,
                        timestamp: Utc::now(),
                        order_id: "test_btc_001".to_string(),
                        high_since_entry: 95200.0, // Выше входа для тестирования TP
                        low_since_entry: 94800.0,
                    };
                    OPEN_POSITIONS.lock().await.push(test_position);
                    println!("🧪 [TEST] Added BTC test position for monitoring");
                }
            }
            break;
        }
    }

    tokio::spawn(async move {
        positions_monitor_worker(positions_exchange, positions_om, positions_rm).await;
    });
    
    // 🔥 ПРИНУДИТЕЛЬНЫЙ ТЕСТ ЗАКРЫТИЯ ЧЕРЕЗ 30 СЕКУНД
    let test_positions = OPEN_POSITIONS.clone();
    let test_exchange = exchanges[0].clone();
    let test_om = om.clone();
    let test_rm = rm.clone();
    tokio::spawn(async move {
        tokio::time::sleep(Duration::from_secs(30)).await;
        println!("⚠️ [TEST] Starting force close test after 30 seconds!");
        
        let positions_snapshot: Vec<Position> = {
            test_positions.lock().await.clone()
        };
        
        for pos in positions_snapshot {
            println!("🛑 [FORCE TEST] Closing {} {} @ {:.5}", pos.pair, pos.side, pos.entry_price);
            
            if let Ok(md) = test_exchange.get_market_data(&pos.pair).await {
                let current_price = if pos.side == "BUY" { md.bid } else { md.ask };
                
                match close_position(&test_exchange, &test_om, &test_rm, &pos, "force_test", current_price).await {
                    Ok(_) => {
                        println!("✅ [FORCE TEST SUCCESS] {} {} closed", pos.pair, pos.side);
                        let mut positions = test_positions.lock().await;
                        positions.retain(|p| p.order_id != pos.order_id);
                    }
                    Err(e) => {
                        println!("❌ [FORCE TEST ERROR] {}", e);
                    }
                }
            }
        }
    });

    // Main monitoring loop
    let mut last_symbol_update = std::time::Instant::now();
    
    loop {
        tokio::time::sleep(Duration::from_secs(10)).await;
        
        // 🔥 АВТО-ВОССТАНОВЛЕНИЕ ПАР каждые 10 секунд
        om.get_grid_manager().symbol_manager.pair_status.auto_re_enable_pairs().await;
        
        // 🔥 ОБНОВЛЕНИЕ СТАТУСА ПАР каждые 5 минут
        if last_symbol_update.elapsed() > Duration::from_secs(300) { // 5 минут
            println!("🔄 Updating symbol statuses...");
            for exchange in &exchanges {
                if let Err(e) = om.get_grid_manager().initialize_symbols(exchange).await {
                    println!("❌ Failed to update symbols for {}: {}", exchange.name(), e);
                } else {
                    println!("✅ Updated symbols for {}", exchange.name());
                }
            }
            last_symbol_update = std::time::Instant::now();
        }
        
        // Мониторинг статы
        let day_pnl = rm.lock().await.daily_pnl();
        let active_orders = ACTIVE_ORDERS.lock().await.len();
        let open_positions = OPEN_POSITIONS.lock().await.len();
        
        // 🔥 ЛОГИРОВАНИЕ АКТИВНЫХ ПАР
        let disabled_pairs = om.get_grid_manager().symbol_manager.pair_status.disabled.lock().await;
        let active_count = tickers.len() - disabled_pairs.len();
        println!("[SUMMARY] Daily PnL: ${:.2} | Active Orders: {} | Open Positions: {} | Active Pairs: {}/{} | Time: {}", 
                 day_pnl, active_orders, open_positions, active_count, tickers.len(), Utc::now().format("%H:%M:%S"));
        
        // 🔥 ЛОГИРОВАНИЕ ОТКРЫТЫХ ПОЗИЦИЙ
        if open_positions > 0 {
            let positions = OPEN_POSITIONS.lock().await;
            for pos in positions.iter() {
                println!("📊 Open Position: {} {} @ {:.5}, size: {:.4}, age: {}s", 
                         pos.pair, pos.side, pos.entry_price, pos.size, 
                         Utc::now().signed_duration_since(pos.timestamp).num_seconds());
            }
        }
        
        if active_count == 0 {
            println!("🚨 [CRITICAL] No active pairs! All pairs are disabled!");
            println!("🚨 Disabled pairs: {:?}", disabled_pairs.keys().collect::<Vec<_>>());
        } else if active_count < tickers.len() / 2 {
            println!("⚠️ [WARNING] Only {}/{} pairs active", active_count, tickers.len());
        }
        
        // Дневной стоп
        if day_pnl < -300.0 {
            println!("🚨 DAY STOP LOSS TRIGGERED! PnL: ${:.2}", day_pnl);
            break;
        }
    }
    
    Ok(())
}

// 🔥 GRID ВОРКЕР - основная логика HFT маркет-мейкинга с AI-спредом
async fn grid_worker(
    exchange: Arc<dyn Exchange>,
    order_manager: Arc<OrderManager>,
    risk_manager: Arc<Mutex<RiskManager>>,
    pair: String,
    symbol_validator: Arc<SymbolValidator>,
    rate_limit: Arc<Semaphore>,
) {
    // 🔥 КОНФИГИ
    const MIN_ORDER_USDT: f64 = 10.0;
    const MAX_ORDER_USDT: f64 = 50.0;
    const RISK_PERCENT: f64 = 0.002; // 0.2% депо
    
    // 🔥 HFT МАРКЕТ-МЕЙКИНГ: AI-СПРЕД КОНСТАНТЫ (РЕАЛЬНЫЙ HFT)
    const COMMISSION_MAKER: f64 = 0.0002; // 0.02% - комиссия мейкера
    const COMMISSION_TAKER: f64 = 0.0005; // 0.05% - комиссия тейкера (для расчета)
    const SAFE_MARGIN: f64 = 0.00002;     // 0.002% - запас на микрофлуктуации
    const MIN_PROFIT: f64 = 0.00002;      // 0.002% - минимальная чистая прибыль
    
    // 🔥 AI-СПРЕД ИСТОРИЯ
    let mut history_of_spreads: Vec<f64> = Vec::new();
    let mut last_spread: f64 = 0.0;
    let mut recent_tick_moves: Vec<f64> = Vec::new();
    let mut risk_mode: bool = false;
    let mut consecutive_losses: i32 = 0;
    
    let price_history = Arc::new(Mutex::new(VecDeque::with_capacity(50)));
    let market_data = Arc::new(tokio::sync::RwLock::new(MarketData { 
        bid: 0.0, 
        ask: 0.0, 
        last: 0.0, 
        volume: 0.0, 
        timestamp: Utc::now().timestamp() 
    }));
    let md_clone = market_data.clone();

    // 🔥 ЗАПУСКАЕМ WEB SOCKET
    let exchange_ws = exchange.clone();
    let pair_ws = pair.clone();
    let price_history_ws = price_history.clone();
    tokio::spawn(async move {
        // 🔥 ИСПОЛЬЗУЕМ WEB SOCKET ВМЕСТО API POLLING
        match exchange_ws.name().to_lowercase().as_str() {
            "okx" => {
                start_okx_ws(&pair_ws, md_clone.clone(), price_history_ws.clone()).await;
            }
            "binance" => {
                start_binance_ws(&pair_ws, md_clone.clone(), price_history_ws.clone()).await;
            }
            _ => {
                // 🔥 FALLBACK - API каждые 1000мс (1 раз в секунду)
                let mut interval = tokio::time::interval(Duration::from_millis(1000));
                loop {
                    interval.tick().await;
                    if let Ok(md) = exchange_ws.get_market_data(&pair_ws).await {
                        let mut md_write = md_clone.write().await;
                        md_write.bid = md.bid;
                        md_write.ask = md.ask;
                        md_write.last = md.last;
                        md_write.volume = md.volume;
                        md_write.timestamp = md.timestamp;

                        let mut ph = price_history_ws.lock().await;
                        ph.push_back(md.last);
                        if ph.len() > 50 {
                            ph.pop_front();
                        }
                    }
                }
            }
        }
    });

    let mut active_orders: Vec<(String, String, f64, f64, chrono::DateTime<Utc>)> = Vec::new(); // pair, side, price, size, timestamp

    println!("🔄 Starting AI-HFT grid worker for {} on {}", pair, exchange.name());

    // 🔥 ГЛАВНЫЙ ЦИКЛ
    loop {
        // 🔥 ПРОВЕРКА ДНЕВНОГО ЛИМИТА
        if risk_manager.lock().await.daily_pnl() < -300.0 {
            println!("🚨 {}: Day stop loss triggered!", pair);
            break;
        }

        // 🔥 ОГРАНИЧЕНИЕ СКОРОСТНОГО API
        let _permit = rate_limit.acquire().await.unwrap();

        // 🔥 1. ПРОВЕРКА СТАТУСА ПАРЫ
        if !order_manager.get_grid_manager().symbol_manager.is_pair_enabled(&pair).await {
            println!("⏸ {}: Pair is temporarily disabled, skipping trading cycle", pair);
            tokio::time::sleep(Duration::from_millis(200)).await;
            continue;
        }

        // 🔥 2. ЧИТАЕМ АКТУАЛЬНЫЕ ДАННЫЕ
        let md = market_data.read().await;
        let (bid, ask, last, volume) = (md.bid, md.ask, md.last, md.volume);

        // 🔥 ДЕТАЛЬНАЯ ОТЛАДКА ДАННЫХ
        println!("🔍 GridWorker {}: BID={:.4}, ASK={:.4}, LAST={:.4}, VOLUME={:.2}, VALID={}", 
                 pair, bid, ask, last, volume, bid > 0.0 && ask > 0.0 && ask > bid);

        if bid <= 0.0 || ask <= 0.0 || last <= 0.0 {
            println!("⚠️ {}: Invalid market data - skipping cycle", pair);
            tokio::time::sleep(Duration::from_millis(200)).await;
            continue;
        }

        // 🔥 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА СПРЕДА
        if ask <= bid {
            println!("⚠️ {}: Invalid spread (ask <= bid): ask={:.4}, bid={:.4}", pair, ask, bid);
            tokio::time::sleep(Duration::from_millis(200)).await;
            continue;
        }

        // 🔥 3. РАСЧЕТ ВОЛАТИЛЬНОСТИ
        let volatility = {
            let ph = price_history.lock().await;
            if ph.len() < 10 {
                println!("⚠️ {}: Not enough price history ({}), using default volatility", pair, ph.len());
                0.01 // 🔥 ДЕФОЛТНАЯ ВОЛАТИЛЬНОСТЬ 1%
            } else {
                let mean = ph.iter().sum::<f64>() / ph.len() as f64;
                let variance = ph.iter().map(|p| (*p - mean).powi(2)).sum::<f64>() / ph.len() as f64;
                (variance.sqrt()) / mean
            }
        };

        // 🔥 4. AI-ДИНАМИЧЕСКИЙ СПРЕД
        let mut recent_tick_moves = Vec::new();
        let mut last_last = last;
        {
            let ph = price_history.lock().await;
            for t in ph.iter() {
                let tm = ((last_last - *t).abs() / ((last_last + *t) / 2.0)).min(0.1);
                recent_tick_moves.push(tm);
                last_last = *t;
            }
        }
        
        let prev_avg_spread = if history_of_spreads.is_empty() {
            0.0
        } else {
            history_of_spreads.iter().sum::<f64>() / history_of_spreads.len() as f64
        };
        
        // 🔥 РАСЧЕТ ROLLING PnL
        let rolling_pnl = {
            let rm = risk_manager.lock().await;
            rm.get_recent_trades(10).iter().map(|t| t.pnl).sum::<f64>()
        };
        
        // 🔥 ОПРЕДЕЛЕНИЕ RISK MODE
        if rolling_pnl < 0.0 {
            consecutive_losses += 1;
            if consecutive_losses >= 3 {
                risk_mode = true;
            }
        } else {
            consecutive_losses = 0;
            risk_mode = false;
        }
        
        // 🔥 ПРОВЕРКА НА НОВЫЙ HIGH
        let is_new_high = {
            let ph = price_history.lock().await;
            if ph.len() >= 20 {
                let recent_high = ph.iter().rev().take(20).fold(0.0_f64, |a, &b| a.max(b));
                last > recent_high * 1.001 // 0.1% выше последних 20 тиков
            } else {
                false
            }
        };
        
        // 🔥 ВЫЗОВ AI-СПРЕД ФУНКЦИИ С ДИНАМИЧЕСКИМИ ОБЪЕМАМИ
        let min_volume = if pair.contains("SHIB") || pair.contains("PEPE") {
            1_000_000.0 // Для low-cap активов - большие объемы
        } else if pair.contains("BTC") || pair.contains("ETH") {
            5000.0 // Топ пары
        } else if pair.contains("SOL") || pair.contains("BNB") {
            2000.0 // Mid-cap
        } else {
            10_000.0 // Для остальных альтов
        };
        
        let new_spread = calculate_ai_spread(
            COMMISSION_MAKER,
            MIN_PROFIT,
            volatility,
            volume,
            min_volume,
            rolling_pnl,
            &recent_tick_moves,
            prev_avg_spread,
            last_spread,
            risk_mode,
            is_new_high,
            &pair,
            calculate_trend(&price_history.lock().await.clone())
        );
        
        history_of_spreads.push(new_spread);
        if history_of_spreads.len() > 20 {
            history_of_spreads.remove(0);
        }
        last_spread = new_spread;

        let mid_price = (bid + ask) / 2.0;

        // 🔥 5. ПРОВЕРКА AI-СПРЕДА НЕ МЕНЬШЕ МИНИМАЛЬНОГО
        let current_spread = (ask - bid) / mid_price;
        let min_spread = min_spread_for_pair(&pair);
        let final_spread = min_spread.max(new_spread); // адаптивно с надбавкой по vol/risk_mode
        
        // 🔥 ПОДРОБНАЯ ВАЛИДАЦИЯ СПРЕДОВ
        println!("[SPREAD VALIDATION] {}: Required={:.5}%, Current={:.5}%, Status={}", 
                 pair, final_spread * 100.0, current_spread * 100.0,
                 if current_spread >= final_spread { "PASS" } else { "FAIL" });
        
        if current_spread < final_spread {
            println!("⚠️ {}: Spread too narrow ({:.5}% < {:.5}%), skipping", 
                     pair, current_spread * 100.0, final_spread * 100.0);
            println!("🤖 AI-Spread factors: vol={:.4}, pnl={:.4}, risk_mode={}, new_high={}", 
                     volatility, rolling_pnl, risk_mode, is_new_high);
            println!("📊 Spread breakdown: current={:.5}%, min_spread={:.5}%, ai_spread={:.5}%, final={:.5}%", 
                     current_spread * 100.0, min_spread * 100.0, new_spread * 100.0, final_spread * 100.0);
            tokio::time::sleep(Duration::from_millis(200)).await;
            continue;
        }

        // 🔥 6. ДОСТУПНЫЙ БАЛАНС И РАСЧЕТ ОБЪЕМА ОРДЕРА
        let avail_balance = risk_manager.lock().await.available_balance();
        let mut order_usdt = avail_balance * RISK_PERCENT;
        if order_usdt < MIN_ORDER_USDT {
            order_usdt = MIN_ORDER_USDT;
        }
        if order_usdt > MAX_ORDER_USDT {
            order_usdt = MAX_ORDER_USDT;
        }
        let order_coins = order_usdt / mid_price;

        // 🔥 7. ПОЛУЧАЕМ ПАРАМЕТРЫ ОГРАНИЧЕНИЯ С SYMBOL_VALIDATOR
        let (min_qty, min_notional, tick_size, step_size) =
            if let Some(info) = symbol_validator.symbol_info.get(&pair) {
                (info.min_qty, info.min_notional, info.tick_size, info.lot_size)
            } else {
                (0.001, 10.0, 0.0001, 0.0001)
            };

        // 🔥 8. ПРОВЕРКА НА МИНИМАЛЬНЫЙ ОБЪЕМ
        if order_coins < min_qty || order_usdt < min_notional {
            println!("⚠️ {}: Order size too small (coins {:.6} < min_qty {:.6} or notional {:.2} < min_notional {:.2}), skipping",
                pair, order_coins, min_qty, order_usdt, min_notional);
            tokio::time::sleep(Duration::from_millis(200)).await;
            continue;
        }

        // 🔥 9. ОКРУГЛЯЕМ ЦЕНУ И РАЗМЕР ОРДЕРА
        let buy_price = round_to_tick(mid_price * (1.0 - new_spread), tick_size);
        let sell_price = round_to_tick(mid_price * (1.0 + new_spread), tick_size);
        let order_coins_rounded = round_to_step(order_coins, step_size);

        if buy_price <= 0.0 || sell_price <= 0.0 || buy_price >= ask || sell_price <= bid {
            println!("⚠️ {}: Invalid order prices (buy: {:.6}, sell: {:.6}), skipping", pair, buy_price, sell_price);
            tokio::time::sleep(Duration::from_millis(200)).await;
                continue;
            }
            
        // 🔥 10. ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
        println!("📊 {}: bid={:.4}, ask={:.4}, last={:.4}, mid={:.4}, current_spread={:.5}%, ai_spread={:.5}%", 
                 pair, bid, ask, last, mid_price, current_spread * 100.0, new_spread * 100.0);
        println!("🤖 AI-Spread factors: vol={:.4}, pnl={:.4}, risk_mode={}, new_high={}, consecutive_losses={}", 
                 volatility, rolling_pnl, risk_mode, is_new_high, consecutive_losses);
        println!("💰 {}: order_usdt=${:.2}, order_coins={:.6}, notional=${:.2}", 
                 pair, order_usdt, order_coins_rounded, order_coins_rounded * mid_price);
        println!("🎯 {}: min_spread={:.5}%, final_spread={:.5}%, PASS={}", 
                 pair, min_spread * 100.0, final_spread * 100.0, current_spread >= final_spread);

        // 🔥 11. УДАЛЯЕМ УСТАРЕВШИЕ ОРДЕРА СТАРШЕ 300 МС
        let now = Utc::now();
        active_orders.retain(|(_, _, _, _, ts)| now.signed_duration_since(*ts).num_milliseconds() < 300);

        // 🔥 РАСЧЕТ СИЛЫ ТРЕНДА ПЕРЕД ВЫСТАВЛЕНИЕМ ОРДЕРОВ
        let trend_strength = {
            let ph = price_history.lock().await;
            calculate_trend(&ph)
        };

        // 🔥 ПРОВЕРКА ТРЕНДА - ОСЛАБЛЯЕМ ДЛЯ БОЛЬШЕГО КОЛИЧЕСТВА СДЕЛОК
        if trend_strength.abs() > 0.02 { // Увеличиваем с 0.01 до 0.02 (2%)
            println!("🌪️ {}: Strong trend ({:.4}%), skipping cycle", 
                     pair, trend_strength * 100.0);
            tokio::time::sleep(Duration::from_millis(200)).await;
            continue;
        }

        // 🔥 СОЗДАЕМ EXPOSURE MANAGER ДЛЯ ЭТОГО ВОРКЕРА
        let exposure_manager = Arc::new(Mutex::new(ExposureManager::new(1000.0))); // $1000 лимит

        // 🔥 12. ПРОВЕРЯЕМ И ВЫСТАВЛЯЕМ BUY ЛИМИТКУ
        if !active_orders.iter().any(|(p, s, price, _, _)| p == &pair && s == "BUY" && (*price - buy_price).abs() < 1e-8) {
            println!("[ORDER TEST] Placing BUY order: {}; Spread: {:.5}%, AI-Spread: {:.5}%, Min: {:.5}%, Final: {:.5}%", 
                     pair, current_spread*100.0, new_spread*100.0, min_spread*100.0, final_spread*100.0);
            ensure_limit_order(&exchange, &order_manager, &mut active_orders, &pair, "BUY", buy_price, order_coins_rounded, &exposure_manager, trend_strength).await;
        }

        // 🔥 13. ПРОВЕРЯЕМ И ВЫСТАВЛЯЕМ SELL ЛИМИТКУ
        if !active_orders.iter().any(|(p, s, price, _, _)| p == &pair && s == "SELL" && (*price - sell_price).abs() < 1e-8) {
            println!("[ORDER TEST] Placing SELL order: {}; Spread: {:.5}%, AI-Spread: {:.5}%, Min: {:.5}%, Final: {:.5}%", 
                     pair, current_spread*100.0, new_spread*100.0, min_spread*100.0, final_spread*100.0);
            ensure_limit_order(&exchange, &order_manager, &mut active_orders, &pair, "SELL", sell_price, order_coins_rounded, &exposure_manager, trend_strength).await;
        }

        // 🔥 14. ОБРАБОТКА ЗАПОЛНЕННЫХ ОРДЕРОВ
        process_filled_orders(&exchange, &order_manager, &mut active_orders, &risk_manager, &market_data, 0.00038, &pair).await;

        // 🔥 УБИРАЕМ ДУБЛИРУЮЩИЙ МОНИТОРИНГ ПОЗИЦИЙ - теперь это делает отдельный positions_monitor_worker
        // Мониторинг позиций перенесен в отдельный dedicated worker для постоянной проверки TP/SL

        // 🔥 15. ИНТЕРВАЛ 500МС (увеличено для снижения нагрузки)
        tokio::time::sleep(Duration::from_millis(500)).await;
    }
}

// 🔥 ПЕРЕРАБОТАННЫЙ МОНИТОРИНГ ПОЗИЦИЙ
async fn positions_monitor_worker(
    exchange: Arc<dyn Exchange>,
    order_manager: Arc<OrderManager>,
    risk_manager: Arc<Mutex<RiskManager>>,
) {
    println!("🔥 Starting ENHANCED positions monitor worker...");
    
    let mut interval = tokio::time::interval(Duration::from_millis(100)); // 🔥 БЫСТРЕЕ ДЛЯ HFT
    
    loop {
        interval.tick().await;
        
        // 🔥 СОЗДАЕМ СНАПШОТ ПОЗИЦИЙ ДЛЯ МИНИМИЗАЦИИ БЛОКИРОВКИ
        let positions_ids: Vec<String> = {
            let positions = OPEN_POSITIONS.lock().await;
            positions.iter().map(|p| p.order_id.clone()).collect()
        };
        
        if positions_ids.is_empty() {
            continue;
        }
        
        println!("📊 [ENHANCED MONITOR] Checking {} positions", positions_ids.len());
        
        for order_id in positions_ids {
            // 🔥 РАБОТАЕМ С КАЖДОЙ ПОЗИЦИЕЙ ОТДЕЛЬНО
            let mut position_opt = None;
            {
                let positions = OPEN_POSITIONS.lock().await;
                if let Some(pos) = positions.iter().find(|p| p.order_id == order_id) {
                    position_opt = Some(pos.clone());
                }
            }
            
            if let Some(mut position) = position_opt {
                // 🔥 ПОЛУЧАЕМ РЫНОЧНЫЕ ДАННЫЕ БЕЗ БЛОКИРОВКИ
                let market_data = match exchange.get_market_data(&position.pair).await {
                    Ok(md) => md,
                    Err(e) => {
                        println!("❌ [MONITOR] Error getting market data for {}: {}", position.pair, e);
                        continue;
                    }
                };
                
                let current_price = if position.side == "BUY" {
                    market_data.bid
                } else {
                    market_data.ask
                };
                
                if current_price <= 0.0 {
                    println!("⚠️ [MONITOR] Invalid price for {}: {}", position.pair, current_price);
                    continue;
                }
                
                // 🔥 ОБНОВЛЯЕМ HIGH/LOW С ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ
                let mut updated = false;
                if current_price > position.high_since_entry {
                    println!("📈 [HIGH UPDATE] {} {}: {:.5} -> {:.5}", 
                             position.pair, position.side, position.high_since_entry, current_price);
                    position.high_since_entry = current_price;
                    updated = true;
                }
                if current_price < position.low_since_entry {
                    println!("📉 [LOW UPDATE] {} {}: {:.5} -> {:.5}", 
                             position.pair, position.side, position.low_since_entry, current_price);
                    position.low_since_entry = current_price;
                    updated = true;
                }
                
                // 🔥 СОХРАНЯЕМ ОБНОВЛЕННУЮ ПОЗИЦИЮ
                if updated {
                    let mut positions = OPEN_POSITIONS.lock().await;
                    if let Some(p) = positions.iter_mut().find(|p| p.order_id == order_id) {
                        p.high_since_entry = position.high_since_entry;
                        p.low_since_entry = position.low_since_entry;
                    }
                }
                
                // 🔥 РАСЧЕТ PnL ДЛЯ ЛОГИРОВАНИЯ
                let pnl_percent = if position.entry_price > 0.0 {
                    match position.side.as_str() {
                        "BUY" => ((current_price - position.entry_price) / position.entry_price) * 100.0,
                        "SELL" => ((position.entry_price - current_price) / position.entry_price) * 100.0,
                        _ => 0.0
                    }
                } else {
                    0.0
                };
                
                println!("📈 [MONITOR] {} {}: entry={:.5}, cur={:.5}, pnl={:.3}%, high={:.5}, low={:.5}", 
                         position.pair, position.side, position.entry_price, current_price, pnl_percent,
                         position.high_since_entry, position.low_since_entry);
                
                // 🔥 ПРОВЕРЯЕМ УСЛОВИЯ ЗАКРЫТИЯ С ОБНОВЛЕННЫМИ ЗНАЧЕНИЯМИ
                if let Some(reason) = should_close_position(
                    position.entry_price, 
                    current_price, 
                    &position.side,
                    position.high_since_entry,
                    position.low_since_entry
                ) {
                    println!("🎯 [CLOSE TRIGGER] {} {}: entry={:.5}, cur={:.5}, reason={}", 
                             position.pair, position.side, position.entry_price, current_price, reason);
                    
                    // 🔥 ЗАКРЫВАЕМ ПОЗИЦИЮ
                    match close_position(&exchange, &order_manager, &risk_manager, &position, &reason, current_price).await {
                        Ok(_) => {
                            println!("✅ [CLOSE SUCCESS] {} {} closed successfully", position.pair, position.side);
                            
                            // 🔥 УДАЛЯЕМ ПОЗИЦИЮ ПОСЛЕ УСПЕШНОГО ЗАКРЫТИЯ
                            let mut positions = OPEN_POSITIONS.lock().await;
                            positions.retain(|p| p.order_id != position.order_id);
                            println!("🗑️ [REMOVED] Position {} {} removed from OPEN_POSITIONS", position.pair, position.side);
                        }
                        Err(e) => {
                            println!("❌ [CLOSE ERROR] Failed to close position: {}", e);
                        }
                    }
                } else {
                    // 🔥 ПРОВЕРЯЕМ TIME-BASED FORCE CLOSE (5 минут)
                    let age_seconds = Utc::now().signed_duration_since(position.timestamp).num_seconds();
                    if age_seconds > 300 { // 5 минут
                        println!("⏰ [TIME FORCE CLOSE] {} {} age: {}s", position.pair, position.side, age_seconds);
                        
                        match close_position(&exchange, &order_manager, &risk_manager, &position, "time_limit", current_price).await {
                            Ok(_) => {
                                let mut positions = OPEN_POSITIONS.lock().await;
                                positions.retain(|p| p.order_id != position.order_id);
                                println!("🗑️ [TIME REMOVED] Position {} {} removed due to time limit", position.pair, position.side);
                            }
                            Err(e) => {
                                println!("❌ [TIME CLOSE ERROR] {}", e);
                            }
                        }
                    }
                }
            }
        }
        
        // 🔥 КАЖДЫЕ 5 СЕКУНД ПОКАЗЫВАЕМ СТАТУС
        static mut LAST_STATUS: i64 = 0;
        let now = Utc::now().timestamp();
        unsafe {
            if now - LAST_STATUS > 5 {
                LAST_STATUS = now;
                let positions = OPEN_POSITIONS.lock().await;
                if positions.is_empty() {
                    println!("ℹ️ [STATUS] No open positions");
                } else {
                    println!("📌 [STATUS] {} active positions:", positions.len());
                    for pos in positions.iter() {
                        let age = Utc::now().signed_duration_since(pos.timestamp).num_seconds();
                        println!("   {} {} @ {:.5}, size: {:.4}, age: {}s", 
                                pos.pair, pos.side, pos.entry_price, pos.size, age);
                    }
                }
            }
        }
    }
}

// 🔥 УЛУЧШЕННАЯ ФУНКЦИЯ ЗАКРЫТИЯ ПОЗИЦИЙ
async fn close_position(
    exchange: &Arc<dyn Exchange>,
    order_manager: &Arc<OrderManager>,
    risk_manager: &Arc<Mutex<RiskManager>>,
    position: &Position,
    reason: &str,
    current_price: f64,
) -> Result<(), String> {
    let close_side = if position.side == "BUY" { "SELL" } else { "BUY" };
    
    println!("🔥 [CLOSING] {} {} -> {} @ {:.5} (reason: {})", 
             position.pair, position.side, close_side, current_price, reason);
    
    // 🔥 ИСПОЛЬЗУЕМ РЫНОЧНЫЙ ОРДЕР ДЛЯ ГАРАНТИРОВАННОГО ЗАКРЫТИЯ
    let order_id = match order_manager.place_market_order(
        exchange, 
        &position.pair, 
        close_side, 
        position.size
    ).await {
        Ok(id) => {
            println!("✅ [MARKET ORDER PLACED] {} {} @ market (order_id: {})", 
                     position.pair, close_side, id);
            id
        }
        Err(e) => {
            let error_msg = format!("Market order failed: {}", e);
            println!("❌ [MARKET ORDER ERROR] {}", error_msg);
            return Err(error_msg);
        }
    };
    
    // 🔥 ЖДЕМ НЕБОЛЬШУЮ ПАУЗУ ДЛЯ ИСПОЛНЕНИЯ РЫНОЧНОГО ОРДЕРА
    tokio::time::sleep(Duration::from_millis(500)).await;
    
    // 🔥 ПОЛУЧАЕМ АКТУАЛЬНУЮ ЦЕНУ ИСПОЛНЕНИЯ
    let fill_price = match exchange.get_market_data(&position.pair).await {
        Ok(md) => {
            if close_side == "BUY" { md.ask } else { md.bid }
        }
        Err(_) => current_price // Fallback к текущей цене
    };
    
    // 🔥 РАСЧЕТ PnL С РЕАЛЬНОЙ ЦЕНОЙ ИСПОЛНЕНИЯ И УЧЕТОМ КОМИССИЙ
    let commission = position.size * fill_price * COMMISSION_TAKER; // Комиссия тейкера при закрытии
    let pnl = if position.side == "BUY" {
        (fill_price - position.entry_price) * position.size - commission
    } else {
        (position.entry_price - fill_price) * position.size - commission
    };
    
    println!("💰 [CLOSED] {} {} @ {:.5} -> filled @ {:.5}, PnL: {:.4} USDT (commission: {:.4}) (reason: {})", 
             position.pair, position.side, position.entry_price, fill_price, pnl, commission, reason);
    
    // 🔥 ЗАПИСЫВАЕМ СДЕЛКУ В РИСК-МЕНЕДЖЕР
    let trade = Trade {
        timestamp: Utc::now(),
        pair: position.pair.clone(),
        side: format!("CLOSE_{}", close_side),
        price: fill_price,
        size: position.size,
        pnl,
    };
    
    risk_manager.lock().await.record_trade(trade);
    
    Ok(())
}

// 🔥 ФУНКЦИИ HFT АРХИТЕКТУРЫ

/// Округление цены до tick_size
fn round_to_tick(price: f64, tick_size: f64) -> f64 {
    if tick_size <= 0.0 { 
        price 
    } else { 
        (price / tick_size).floor() * tick_size 
    }
}

/// Округление размера до step_size
fn round_to_step(size: f64, step_size: f64) -> f64 {
    if step_size <= 0.0 { 
        size 
    } else { 
        (size / step_size).floor() * step_size 
    }
}

// 🔥 ОБНОВЛЕННАЯ ЛОГИКА ВЫСТАВЛЕНИЯ ОРДЕРОВ С ПРОВЕРКОЙ ТРЕНДА И ЭКСПОЗИЦИИ
async fn ensure_limit_order(
    exchange: &Arc<dyn Exchange>,
    order_manager: &Arc<OrderManager>,
    active_orders: &mut Vec<(String, String, f64, f64, chrono::DateTime<Utc>)>,
    pair: &str,
    side: &str,
    price: f64,
    size: f64,
    exposure_manager: &Arc<Mutex<ExposureManager>>,
    trend_strength: f64,
) {
    // 🔥 ПРОВЕРКА ТРЕНДА И ЭКСПОЗИЦИИ
    let can_trade = match side {
        "BUY" => {
            let exposure_ok = exposure_manager.lock().await.can_open_long(size * price);
            let trend_ok = trend_strength > -0.015; // Ослабляем с -0.005 до -0.015
            exposure_ok && trend_ok
        }
        "SELL" => {
            let exposure_ok = exposure_manager.lock().await.can_open_short(size * price);
            let trend_ok = trend_strength < 0.015; // Ослабляем с 0.005 до 0.015
            exposure_ok && trend_ok
        }
        _ => false,
    };

    if !can_trade {
        println!("🚫 {} {} skipped: trend={:.4}% or exposure limit reached", 
                 side, pair, trend_strength * 100.0);
        return;
    }

    // 🔥 ПРОВЕРЯЕМ СУЩЕСТВУЮЩИЕ ОРДЕРА
    let existing_order_info = active_orders.iter()
        .find(|(_, existing_side, _, _, _)| existing_side == side)
        .map(|(id, _, price, size, timestamp)| (id.clone(), *price, *size, *timestamp));
    
    if let Some((existing_order_id, existing_price, existing_size, timestamp)) = existing_order_info {
        let price_diff = (price - existing_price).abs() / existing_price;
        let size_diff = (size - existing_size).abs() / existing_size;
        let age = Utc::now().signed_duration_since(timestamp).num_seconds();
        
        // Обновляем ордер если цена изменилась > 0.01% или размер > 5% или ордер старше 10 секунд
        if price_diff > 0.0001 || size_diff > 0.05 || age > 10 {
            println!("🔄 Updating {} {} order: price {:.5} -> {:.5}, age: {}s", 
                     side, pair, existing_price, price, age);
            
            // Отменяем старый ордер
            if let Err(e) = order_manager.try_cancel_order(exchange, pair, &existing_order_id).await {
                println!("⚠️ Failed to cancel old order: {}", e);
            }
            
            // Удаляем из списка
            active_orders.retain(|(id, _, _, _, _)| *id != existing_order_id);
        } else {
            // Ордер актуален, не обновляем
            return;
        }
    }

    // 🔥 РАЗМЕЩАЕМ НОВЫЙ ОРДЕР
    match order_manager.try_place_order(exchange, pair, side, price, size).await {
        Ok(order_id) => {
            active_orders.push((order_id.clone(), side.to_string(), price, size, Utc::now()));
            println!("✅ {} {} @ {:.5} (size: {:.4}) - order_id: {}", 
                     side, pair, price, size, order_id);
        }
        Err(e) => {
            println!("❌ Failed to place {} {} order: {}", side, pair, e);
        }
    }
}

/// Очистка устаревших ордеров
async fn cleanup_old_orders(
    exchange: &Arc<dyn Exchange>,
    active_orders: &mut Vec<(String, String, f64, f64, chrono::DateTime<Utc>)>,
    max_age_ms: u64
) {
    let now = Utc::now();
    active_orders.retain(|(_, _, _, _, timestamp)| {
        let age = now.signed_duration_since(*timestamp).num_milliseconds();
        age as u64 <= max_age_ms
    });
}

/// Обработка исполненных ордеров
async fn process_filled_orders(
    exchange: &Arc<dyn Exchange>,
    order_manager: &Arc<OrderManager>,
    active_orders: &mut Vec<(String, String, f64, f64, chrono::DateTime<Utc>)>,
    risk_manager: &Arc<Mutex<RiskManager>>,
    market_data: &Arc<tokio::sync::RwLock<MarketData>>,
    commission: f64,
    pair: &str,
) {
    // 🔥 УПРОЩЕННАЯ ВЕРСИЯ - проверяем только глобальные ордера
    let mut global_orders = ACTIVE_ORDERS.lock().await;
    let mut to_remove = Vec::new();
    
    for (i, order) in global_orders.iter().enumerate() {
        if order.pair == pair {
            // 🔥 ИСПОЛЬЗУЕМ УМНУЮ ПРОВЕРКУ СТАТУСА
            match order_manager.try_get_order_status(exchange, pair, &order.order_id).await {
                Ok(status) => {
                    if status.to_uppercase() == "FILLED" {
                        // 🔥 РАСЧЕТ PnL: (fill_price - limit_price) * size - commission
                        let current_md = market_data.read().await;
                        let pnl = if matches!(order.side, OrderSide::Buy) {
                            // BUY исполнен - продаем по текущей цене
                            (current_md.ask - order.price) * order.size - order.size * commission
                        } else {
                            // SELL исполнен - покупаем по текущей цене
                            (order.price - current_md.bid) * order.size - order.size * commission
                        };

                        // Записываем сделку
                        let trade = Trade {
                            timestamp: order.timestamp,
                            pair: order.pair.clone(),
                            side: format!("{:?}", order.side),
                            price: order.price,
                            size: order.size,
                            pnl,
                        };
                        
                        risk_manager.lock().await.record_trade(trade);
                        
                        // 🔥 ДОБАВЛЯЕМ ПОЗИЦИЮ В СПИСОК ОТКРЫТЫХ (только при исполнении!)
                        let current_md = market_data.read().await;
                        let current_price = if matches!(order.side, OrderSide::Buy) {
                            current_md.bid // Для long позиции используем bid
                        } else {
                            current_md.ask // Для short позиции используем ask
                        };
                        
                        let position = Position {
                            pair: order.pair.clone(),
                            side: if matches!(order.side, OrderSide::Buy) { "BUY".to_string() } else { "SELL".to_string() },
                            entry_price: order.price,
                            size: order.size,
                            timestamp: order.timestamp,
                            order_id: order.order_id.clone(),
                            high_since_entry: current_price,
                            low_since_entry: current_price,
                        };
                        
                        OPEN_POSITIONS.lock().await.push(position);
                        
                        println!("💰 Order filled: {} {:?} @ {:.4} | PnL: ${:.4} | Position opened", 
                                 pair, order.side, order.price, pnl);
                        println!("🔄 [POSITION ADDED] {} {}: entry={:.5}, current={:.5}, high={:.5}, low={:.5}", 
                                 pair, if matches!(order.side, OrderSide::Buy) { "BUY" } else { "SELL" }, 
                                 order.price, current_price, current_price, current_price);
                        
                        // Запоминаем индекс для удаления
                        to_remove.push(i);
                    }
                }
                Err(e) => {
                    println!("❌ Failed to get order status: {}", e);
                }
            }
        }
    }
    
    // Удаляем исполненные ордера (в обратном порядке)
    for &index in to_remove.iter().rev() {
        if index < global_orders.len() {
            global_orders.remove(index);
        }
    }
} 

// 🔥 АНАЛИЗ ТРЕНДА ДЛЯ ИЗБЕЖАНИЯ ТОРГОВЛИ ПРОТИВ РЫНКА
fn calculate_trend(price_history: &VecDeque<f64>) -> f64 {
    if price_history.len() < 20 {
        return 0.0;
    }
    
    let prices: Vec<f64> = price_history.iter().copied().collect();
    let short_ma: f64 = prices.iter().rev().take(5).sum::<f64>() / 5.0;
    let long_ma: f64 = prices.iter().rev().take(20).sum::<f64>() / 20.0;
    
    // Сила тренда: % отклонения короткой MA от длинной
    if long_ma > 0.0 {
        (short_ma - long_ma) / long_ma
    } else {
        0.0
    }
}

// 🔥 СИСТЕМА УПРАВЛЕНИЯ ЭКСПОЗИЦИЕЙ
#[derive(Debug, Clone)]
struct ExposureManager {
    long_exposure: f64,
    short_exposure: f64,
    max_exposure: f64,
}

impl ExposureManager {
    fn new(max_exposure: f64) -> Self {
        Self {
            long_exposure: 0.0,
            short_exposure: 0.0,
            max_exposure,
        }
    }

    fn can_open_long(&self, size: f64) -> bool {
        (self.long_exposure - self.short_exposure + size) <= self.max_exposure
    }

    fn can_open_short(&self, size: f64) -> bool {
        (self.short_exposure - self.long_exposure + size).abs() <= self.max_exposure
    }

    fn record_trade(&mut self, side: &str, size: f64, price: f64) {
        let amount = size * price;
        match side {
            "BUY" => self.long_exposure += amount,
            "SELL" => self.short_exposure += amount,
            "CLOSE_BUY" => self.long_exposure -= amount,
            "CLOSE_SELL" => self.short_exposure -= amount,
            _ => {}
        }
    }
    
    fn get_net_exposure(&self) -> f64 {
        self.long_exposure - self.short_exposure
    }
}

// 🔥 МЕХАНИЗМ СБРОСА ЭКСПОЗИЦИИ
async fn exposure_reset_worker(exposure_manager: Arc<Mutex<ExposureManager>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(60));
    loop {
        interval.tick().await;
        let mut em = exposure_manager.lock().await;
        let old_long = em.long_exposure;
        let old_short = em.short_exposure;
        
        em.long_exposure *= 0.95;  // Уменьшаем на 5% каждую минуту
        em.short_exposure *= 0.95;
        
        if old_long > 0.0 || old_short > 0.0 {
            println!("🔄 Exposure reset: long ${:.2} -> ${:.2}, short ${:.2} -> ${:.2}, net: ${:.2}", 
                     old_long, em.long_exposure, old_short, em.short_exposure, em.get_net_exposure());
        }
    }
}