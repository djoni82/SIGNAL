use std::collections::VecDeque;
use std::time::{Duration, Instant};
use std::sync::Arc;
use tokio::sync::Mutex;
use anyhow::Result;
use serde_json::Value;
use std::collections::HashMap;

use crate::exchange::Exchange;
use crate::risk::RiskManager;

#[derive(Debug, Clone, PartialEq)]
pub enum OrderSide {
    Buy,
    Sell,
}

#[derive(Debug, Clone)]
pub struct OrderInfo {
    pub exchange: String,
    pub pair: String,
    pub side: OrderSide,
    pub price: f64,
    pub size: f64,
    pub order_id: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

// 🔥 ЛОКАЛЬНОЕ ХРАНЕНИЕ ОРДЕРОВ
#[derive(Debug, Clone)]
pub struct LocalOrder {
    pub pair: String,
    pub side: String,
    pub price: f64,
    pub size: f64,
    pub order_id: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

// 🔥 ИНФОРМАЦИЯ О СИМВОЛЕ
#[derive(Debug, Clone)]
pub struct SymbolInfo {
    pub tick_size: f64,
    pub step_size: f64,
    pub min_qty: f64,
    pub min_notional: f64,
    pub status: String, // "TRADING", "BREAK", etc.
}

// 🔥 УЛУЧШЕННЫЙ PAIR STATUS MANAGER
#[derive(Clone)]
pub struct PairStatusManager {
    pub disabled: Arc<Mutex<HashMap<String, Instant>>>,
    pub disable_period: Duration,
    pub error_counts: Arc<Mutex<HashMap<String, u32>>>,
    pub max_errors: u32,
}

impl PairStatusManager {
    pub fn new(disable_minutes: u64, max_errors: u32) -> Self {
        Self {
            disabled: Arc::new(Mutex::new(HashMap::new())),
            disable_period: Duration::from_secs(disable_minutes * 60),
            error_counts: Arc::new(Mutex::new(HashMap::new())),
            max_errors,
        }
    }

    /// Отключаем пару на disable_minutes
    pub async fn disable(&self, pair: &str) {
        let mut disabled = self.disabled.lock().await;
        disabled.insert(pair.to_string(), Instant::now());
        println!("⚠️ [PAIR DISABLED]: {} на {} минут", pair, self.disable_period.as_secs() / 60);
    }

    /// 🔥 УМНОЕ ОТКЛЮЧЕНИЕ: Увеличиваем время отключения при повторных ошибках
    pub async fn smart_disable(&self, pair: &str) {
        let mut disabled = self.disabled.lock().await;
        let mut error_counts = self.error_counts.lock().await;
        
        let error_count = error_counts.entry(pair.to_string()).or_insert(0);
        *error_count += 1;
        
        // 🔥 ПРОГРЕССИВНОЕ УВЕЛИЧЕНИЕ ВРЕМЕНИ ОТКЛЮЧЕНИЯ
        let disable_minutes = match *error_count {
            1..=2 => 5,    // 5 минут после 1-2 ошибок
            3..=5 => 15,   // 15 минут после 3-5 ошибок
            6..=10 => 30,  // 30 минут после 6-10 ошибок
            _ => 60,       // 1 час после 10+ ошибок
        };
        
        let disable_period = Duration::from_secs(disable_minutes * 60);
        disabled.insert(pair.to_string(), Instant::now());
        
        println!("🚨 [PAIR SMART DISABLED]: {} на {} минут (ошибка #{})", 
                pair, disable_minutes, *error_count);
    }

    /// Проверяем, не отключена ли пара (и если пора, интегрируем обратно)
    pub async fn is_disabled(&self, pair: &str) -> bool {
        let mut disabled = self.disabled.lock().await;
        if let Some(&instant) = disabled.get(pair) {
            // 🔥 ПРОГРЕССИВНОЕ ВРЕМЯ ОТКЛЮЧЕНИЯ
            let mut error_counts = self.error_counts.lock().await;
            let error_count = error_counts.get(pair).unwrap_or(&0);
            
            let disable_minutes = match error_count {
                1..=2 => 5,
                3..=5 => 15,
                6..=10 => 30,
                _ => 60,
            };
            
            let disable_period = Duration::from_secs(disable_minutes * 60);
            
            if Instant::now().duration_since(instant) < disable_period {
                true // всё ещё отключено
            } else {
                // время вышло — заново включаем!
                disabled.remove(pair);
                error_counts.remove(pair);
                println!("✅ [PAIR RE-ENABLED]: {} (было отключено на {} минут)", pair, disable_minutes);
                false
            }
        } else {
            false
        }
    }

    /// 🔥 АВТОМАТИЧЕСКОЕ ВОССТАНОВЛЕНИЕ ПАР (каждые 5 минут)
    pub async fn auto_re_enable_pairs(&self) {
        let mut disabled = self.disabled.lock().await;
        let now = Instant::now();
        let mut to_remove = Vec::new();
        
        for (pair, &disabled_time) in disabled.iter() {
            if now.duration_since(disabled_time) >= Duration::from_secs(300) { // 5 минут
                to_remove.push(pair.clone());
            }
        }
        
        let removed_count = to_remove.len();
        for pair in to_remove {
            disabled.remove(&pair);
            println!("✅ [AUTO RE-ENABLED]: {}", pair);
        }
        
        if removed_count > 0 {
            println!("🔄 Auto re-enabled {} pairs", removed_count);
        }
    }

    /// Увеличиваем счетчик ошибок и отключаем при превышении лимита
    pub async fn record_error(&self, pair: &str) {
        let mut error_counts = self.error_counts.lock().await;
        let count = error_counts.entry(pair.to_string()).or_insert(0);
        *count += 1;
        
        if *count >= self.max_errors {
            self.smart_disable(pair).await;
            error_counts.remove(pair);
        }
    }

    /// Сбрасываем счетчик ошибок при успешной операции
    pub async fn reset_error_count(&self, pair: &str) {
        let mut error_counts = self.error_counts.lock().await;
        error_counts.remove(pair);
    }
}

// 🔥 ФУНКЦИЯ ФИЛЬТРА КРИТИЧЕСКИХ ОШИБОК
pub fn is_critical_error(e: &str) -> bool {
    e.contains("Instrument ID") || e.contains("doesn't exist")
    || e.contains("No market data") || e.contains("All prices are zero")
    || e.contains("Order validation failed") || e.contains("Pair is temporarily disabled")
    || e.contains("Precision is over") || e.contains("min_qty") || e.contains("min_notional")
    || e.contains("Margin is insufficient") || e.contains("Invalid price")
}

// 🔥 УМНЫЙ SYMBOL MANAGER для правильного округления
#[derive(Clone)]
pub struct SymbolManager {
    pub symbols: Arc<Mutex<HashMap<String, SymbolInfo>>>,
    pub pair_status: PairStatusManager,
}

impl SymbolManager {
    pub fn new() -> Self {
        let pair_status = PairStatusManager::new(2, 3); // 2 минуты, 3 ошибки (уменьшил с 10 до 2)
        Self {
            symbols: Arc::new(Mutex::new(HashMap::new())),
            pair_status,
        }
    }

    // 🔥 ПРАВИЛЬНОЕ ОКРУГЛЕНИЕ ЦЕН И РАЗМЕРОВ
    pub fn round_to_tick(&self, price: f64, tick_size: f64) -> f64 {
        if tick_size <= 0.0 {
            return price;
        }
        (price / tick_size).floor() * tick_size
    }

    pub fn round_to_step(&self, size: f64, step_size: f64) -> f64 {
        if step_size <= 0.0 {
            return size;
        }
        (size / step_size).floor() * step_size
    }

    // 🔥 ПРОВЕРКА ВАЛИДНОСТИ ОРДЕРА
    pub fn validate_order(&self, price: f64, size: f64, min_qty: f64, min_notional: f64) -> bool {
        if price <= 0.0 || size <= 0.0 {
            println!("❌ {}: Invalid order parameters: price={:.6}, size={:.6}", "VALIDATION", price, size);
            return false;
        }
        
        // Проверяем минимальный размер
        if size < min_qty {
            println!("❌ {}: Size {} < min_qty {}", "VALIDATION", size, min_qty);
            return false;
        }
        
        // Проверяем минимальный номинал
        let notional = price * size;
        if notional < min_notional {
            println!("❌ {}: Notional {} < min_notional {}", "VALIDATION", notional, min_notional);
            return false;
        }
        
        true
    }

    // 🔥 ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СИМВОЛЕ
    pub async fn get_symbol_info(&self, pair: &str) -> Option<SymbolInfo> {
        let symbols = self.symbols.lock().await;
        symbols.get(pair).cloned()
    }

    // 🔥 ПРОВЕРКА ЧТО ПАРА НЕ ОТКЛЮЧЕНА
    pub async fn is_pair_enabled(&self, pair: &str) -> bool {
        !self.pair_status.is_disabled(pair).await
    }

    // 🔥 ОТКЛЮЧЕНИЕ ПАРЫ
    pub async fn disable_pair(&self, pair: &str) {
        self.pair_status.disable(pair).await;
    }

    // 🔥 ЗАГРУЗКА ИНФОРМАЦИИ О СИМВОЛАХ
    pub async fn load_symbol_info(&self, exchange: &Arc<dyn Exchange>) -> Result<()> {
        // 🔥 ДИНАМИЧЕСКАЯ ЗАГРУЗКА С БИРЖИ
        match exchange.name() {
            "okx" => {
                println!("🔍 Loading symbol info from OKX...");
                
                // Получаем список инструментов
                let url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP";
                let response = reqwest::get(url).await?;
                let json: serde_json::Value = response.json().await?;
                
                let mut symbols = self.symbols.lock().await;
                
                if let Some(data) = json["data"].as_array() {
                    for instrument in data {
                        if let Some(inst_id) = instrument["instId"].as_str() {
                            if let Some(state) = instrument["state"].as_str() {
                                if state == "live" && inst_id.contains("USDT") {
                                    // Получаем параметры инструмента
                                    let tick_size = instrument["tickSz"].as_str()
                                        .and_then(|s| s.parse::<f64>().ok())
                                        .unwrap_or(0.00001);
                                    
                                    let lot_size = instrument["lotSz"].as_str()
                                        .and_then(|s| s.parse::<f64>().ok())
                                        .unwrap_or(1.0);
                                    
                                    let min_qty = instrument["minSz"].as_str()
                                        .and_then(|s| s.parse::<f64>().ok())
                                        .unwrap_or(1.0);
                                    
                                    let min_notional = 5.0; // стандартное значение
                                    
                                    symbols.insert(inst_id.to_string(), SymbolInfo {
                                        tick_size,
                                        step_size: lot_size,
                                        min_qty,
                                        min_notional,
                                        status: "TRADING".to_string(),
                                    });
                                }
                            }
                        }
                    }
                }
                
                println!("✅ Loaded {} OKX symbol configurations", symbols.len());
            },
            "binance" => {
                println!("🔍 Loading symbol info from Binance Futures...");
                
                // Получаем список символов
                let url = "https://fapi.binance.com/fapi/v1/exchangeInfo";
                let response = reqwest::get(url).await?;
                let json: serde_json::Value = response.json().await?;
                
                let mut symbols = self.symbols.lock().await;
                
                if let Some(symbols_data) = json["symbols"].as_array() {
                    for symbol in symbols_data {
                        if let Some(symbol_name) = symbol["symbol"].as_str() {
                            if let Some(status) = symbol["status"].as_str() {
                                if status == "TRADING" && symbol_name.ends_with("USDT") {
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
                                    
                                    symbols.insert(symbol_name.to_string(), SymbolInfo {
                                        tick_size,
                                        step_size,
                                        min_qty,
                                        min_notional,
                                        status: "TRADING".to_string(),
                                    });
                                }
                            }
                        }
                    }
                }
                
                println!("✅ Loaded {} Binance symbol configurations", symbols.len());
            },
            _ => {
                println!("⚠️ Unknown exchange: {}, using fallback symbols", exchange.name());
                // Fallback для других бирж
                let mut symbols = self.symbols.lock().await;
                
                // Базовые значения
                let base_symbols = vec![
                    ("BTCUSDT", 0.01, 0.001, 0.001, 5.0),
                    ("ETHUSDT", 0.01, 0.001, 0.001, 5.0),
                    ("BNBUSDT", 0.001, 0.01, 0.01, 5.0),
                ];

                for (pair, tick_size, step_size, min_qty, min_notional) in base_symbols {
                    symbols.insert(pair.to_string(), SymbolInfo {
                        tick_size,
                        step_size,
                        min_qty,
                        min_notional,
                        status: "TRADING".to_string(),
                    });
                }
                
                println!("✅ Loaded {} fallback symbol configurations", symbols.len());
            }
        }
        
        Ok(())
    }
}

// 🔥 УМНЫЙ RATE LIMITER с двумя лимитами
#[derive(Clone)]
pub struct RateLimiter {
    pub max_per_sec: usize,
    pub max_per_min: usize,
    pub timestamps_sec: VecDeque<Instant>,
    pub timestamps_min: VecDeque<Instant>,
}

impl RateLimiter {
    pub fn new(max_per_sec: usize, max_per_min: usize) -> Self {
        Self {
            max_per_sec,
            max_per_min,
            timestamps_sec: VecDeque::new(),
            timestamps_min: VecDeque::new(),
        }
    }

    pub fn allow(&mut self) -> bool {
        let now = Instant::now();
        
        // Очищаем устаревшие отметки
        while let Some(&front) = self.timestamps_sec.front() {
            if now.duration_since(front) > Duration::from_secs(1) {
                self.timestamps_sec.pop_front();
            } else {
                break;
            }
        }
        
        while let Some(&front) = self.timestamps_min.front() {
            if now.duration_since(front) > Duration::from_secs(60) {
                self.timestamps_min.pop_front();
            } else {
                break;
            }
        }
        
        // Проверка двух лимитов
        if self.timestamps_sec.len() < self.max_per_sec && self.timestamps_min.len() < self.max_per_min {
            self.timestamps_sec.push_back(now);
            self.timestamps_min.push_back(now);
            true
        } else {
            false
        }
    }

    pub fn next_sleep(&self) -> Duration {
        let now = Instant::now();
        
        if let Some(&front) = self.timestamps_sec.front() {
            if self.timestamps_sec.len() >= self.max_per_sec {
                return Duration::from_secs(1)
                    .checked_sub(now.duration_since(front))
                    .unwrap_or(Duration::from_millis(20));
            }
        }
        
        if let Some(&front) = self.timestamps_min.front() {
            if self.timestamps_min.len() >= self.max_per_min {
                return Duration::from_secs(60)
                    .checked_sub(now.duration_since(front))
                    .unwrap_or(Duration::from_millis(50));
            }
        }
        
        Duration::from_millis(0)
    }
}

// 🔥 УМНЫЙ GRID ORDER MANAGER с раунд-робин
#[derive(Clone)]
pub struct GridOrderManager {
    pub rate_limiter: Arc<Mutex<RateLimiter>>,
    pub symbol_manager: SymbolManager,
    pub group_size: usize,
    pub tickers: Vec<String>,
    pub dynamic_delay: usize, // мс, увеличивается при частых rate-limit
    pub risk_manager: Arc<Mutex<RiskManager>>,
    pub local_orders: Arc<Mutex<HashMap<String, LocalOrder>>>, // Добавляем локальное хранение ордеров
}

impl GridOrderManager {
    pub fn new(risk_manager: Arc<Mutex<RiskManager>>, tickers: Vec<String>, group_size: usize) -> Self {
        let rate_limiter = Arc::new(Mutex::new(RateLimiter::new(18, 1100))); // безопасные значения под Binance
        let symbol_manager = SymbolManager::new();
        
        Self {
            rate_limiter,
            symbol_manager,
            group_size,
            tickers,
            dynamic_delay: 180,
            risk_manager,
            local_orders: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn main_grid_loop<F>(&mut self, mut grid_fn: F)
    where
        F: FnMut(&str) -> tokio::task::JoinHandle<()> + Send,
    {
        let n = self.tickers.len();
        let g = self.group_size;
        let group_count = (n + g - 1) / g;
        let mut group = 0;
        
        println!("🔄 Starting Grid Manager: {} tickers, {} per group, {} groups", n, g, group_count);
        
        loop {
            let start = group * g;
            let end = ((group + 1) * g).min(n);
            let trigger_tickers = &self.tickers[start..end];
            
            println!("📊 Processing group {}/{}: {:?}", group + 1, group_count, trigger_tickers);
            
            let mut handles = vec![];
            for pair in trigger_tickers {
                handles.push(grid_fn(pair));
            }
            
            for h in handles {
                let _ = h.await;
            }

            group = (group + 1) % group_count;

            // 🔥 AUTO-BACKOFF! если пересек лимит — увеличь задержку на цикл
            let sleep_time = {
                let rl = self.rate_limiter.lock().await;
                rl.next_sleep().as_millis() as usize
            }
            .max(self.dynamic_delay);

            println!("⏸ Group {} complete, sleeping {}ms", group, sleep_time);
            tokio::time::sleep(Duration::from_millis(sleep_time as u64)).await;
        }
    }

    pub async fn try_order(&self, pair: &str) -> Result<(), String> {
        let mut rl = self.rate_limiter.lock().await;
        if rl.allow() {
            Ok(())
        } else {
            let wait = rl.next_sleep();
            println!("⏸ Rate limit hit for {}, waiting for {:?}", pair, wait);
            tokio::time::sleep(wait).await;
            Err("rate limited".into())
        }
    }

    // 🔥 УМНОЕ РАЗМЕЩЕНИЕ ОРДЕРА с проверками
    pub async fn smart_place_order(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        side: &str,
        price: f64,
        size: f64,
    ) -> Result<String, String> {
        // 1. Проверяем что пара не отключена
        if !self.symbol_manager.is_pair_enabled(pair).await {
            return Err(format!("Pair {} is temporarily disabled", pair));
        }

        // 2. Rate limit check
        self.try_order(pair).await?;

        // 3. Получаем информацию о символе
        let symbol_info = match self.symbol_manager.get_symbol_info(pair).await {
            Some(info) => info,
            None => {
                self.symbol_manager.pair_status.record_error(pair).await;
                return Err(format!("No symbol info for {}", pair));
            }
        };

        // 4. Проверяем что цена не равна 0
        if price <= 0.0 {
            self.symbol_manager.pair_status.record_error(pair).await;
            return Err(format!("Invalid price {} for {}", price, pair));
        }

        // 5. Округляем цену и размер
        let rounded_price = self.symbol_manager.round_to_tick(price, symbol_info.tick_size);
        let rounded_size = self.symbol_manager.round_to_step(size, symbol_info.step_size);

        // 6. Проверяем минимальные требования
        if !self.symbol_manager.validate_order(rounded_price, rounded_size, symbol_info.min_qty, symbol_info.min_notional) {
            let error_msg = format!(
                "Order validation failed: price={:.6}, size={:.6}, min_qty={:.6}, min_notional={:.2}",
                rounded_price, rounded_size, symbol_info.min_qty, symbol_info.min_notional
            );
            self.symbol_manager.pair_status.record_error(pair).await;
            return Err(error_msg);
        }

        // 7. Проверяем баланс
        let available_balance = self.risk_manager.lock().await.available_balance();
        let estimated_notional = rounded_price * rounded_size * 1.1; // +10% для комиссий
        
        if estimated_notional > available_balance * 0.5 { // Уменьшил с 0.8 до 0.5
            let error_msg = format!(
                "Insufficient balance: need ${:.2}, have ${:.2}",
                estimated_notional, available_balance
            );
            self.symbol_manager.pair_status.record_error(pair).await;
            return Err(error_msg);
        }

        // 🔥 8. ПРОВЕРКА РИСК-МЕНЕДЖЕРА
        let risk_validation = {
            let rm = self.risk_manager.lock().await;
            rm.validate_order_size(rounded_size, symbol_info.min_qty, symbol_info.min_notional, rounded_price)
        };
        
        if let Err(error_msg) = risk_validation {
            // 🔥 ЛОГИРУЕМ ОШИБКУ РИСК-МЕНЕДЖЕРА
            {
                let rm = self.risk_manager.lock().await;
                rm.log_risk_error(&error_msg, pair, rounded_size, rounded_price);
            }
            self.symbol_manager.pair_status.record_error(pair).await;
            return Err(format!("Risk manager validation failed: {}", error_msg));
        }

        // 9. Размещаем ордер
        match exchange.place_order(pair, side, rounded_price, rounded_size).await {
            Ok(order_id) => {
                // 🔥 СБРАСЫВАЕМ СЧЕТЧИК ОШИБОК ПРИ УСПЕХЕ
                self.symbol_manager.pair_status.reset_error_count(pair).await;
                
                // 🔥 СОХРАНЯЕМ ОРДЕР В ЛОКАЛЬНОЕ ХРАНЕНИЕ
                self.add_local_order(pair, side, rounded_price, rounded_size, &order_id).await;
                
                println!("✅ Placed {} order: {} @ {:.6} (size: {:.6})", side, pair, rounded_price, rounded_size);
                Ok(order_id)
            }
            Err(e) => {
                let error_msg = e.to_string();
                
                // 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОШИБОК OKX
                if error_msg.contains("OKX API error") {
                    println!("🚨 DETAILED OKX ERROR for {} {} @ {:.6} (size: {:.6}):", pair, side, rounded_price, rounded_size);
                    println!("   Error: {}", error_msg);
                    println!("   Symbol info: tick_size={:.6}, step_size={:.6}, min_qty={:.6}, min_notional={:.2}", 
                        symbol_info.tick_size, symbol_info.step_size, symbol_info.min_qty, symbol_info.min_notional);
                    println!("   Rounded values: price={:.6}, size={:.6}, notional={:.2}", 
                        rounded_price, rounded_size, rounded_price * rounded_size);
                }
                
                // 🔥 ОТКЛЮЧАЕМ ПАРУ ПРИ КРИТИЧЕСКИХ ОШИБАХ
                if is_critical_error(&error_msg) {
                    self.symbol_manager.pair_status.record_error(pair).await;
                }
                
                println!("❌ Failed to place {} order: {}", side, error_msg);
                Err(error_msg)
            }
        }
    }

    // 🔥 УМНАЯ ОТМЕНА ОРДЕРА
    pub async fn smart_cancel_order(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        order_id: &str,
    ) -> Result<(), String> {
        // Rate limit check
        self.try_order(pair).await?;

        match exchange.cancel_order(pair, order_id).await {
            Ok(_) => {
                // 🔥 УДАЛЯЕМ ОРДЕР ИЗ ЛОКАЛЬНОГО ХРАНЕНИЯ
                self.remove_local_order(pair, order_id).await;
                
                println!("✅ Cancelled order: {} {}", pair, order_id);
                Ok(())
            }
            Err(e) => {
                println!("❌ Failed to cancel order: {}", e);
                Err(e.to_string())
            }
        }
    }

    pub async fn get_rate_info(&self) -> (usize, u64) {
        let rl = self.rate_limiter.lock().await;
        (rl.timestamps_sec.len(), self.dynamic_delay as u64)
    }

    // 🔥 ИНИЦИАЛИЗАЦИЯ SYMBOL MANAGER
    pub async fn initialize_symbols(&self, exchange: &Arc<dyn Exchange>) -> Result<()> {
        self.symbol_manager.load_symbol_info(exchange).await
    }

    // 🔥 ДОБАВЛЯЕМ ОРДЕР В ЛОКАЛЬНОЕ ХРАНЕНИЕ
    pub async fn add_local_order(&self, pair: &str, side: &str, price: f64, size: f64, order_id: &str) {
        let mut orders = self.local_orders.lock().await;
        let key = format!("{}_{}_{}", pair, side, order_id);
        
        let local_order = LocalOrder {
            pair: pair.to_string(),
            side: side.to_string(),
            price,
            size,
            order_id: order_id.to_string(),
            timestamp: chrono::Utc::now(),
        };
        
        orders.insert(key, local_order);
        println!("💾 Added local order: {} {} @ {} (ID: {})", pair, side, price, order_id);
    }

    // 🔥 УДАЛЯЕМ ОРДЕР ИЗ ЛОКАЛЬНОГО ХРАНЕНИЯ
    pub async fn remove_local_order(&self, pair: &str, order_id: &str) {
        let mut orders = self.local_orders.lock().await;
        
        // Ищем по order_id (может быть несколько ордеров для одной пары)
        let keys_to_remove: Vec<String> = orders.keys()
            .filter(|key| key.contains(order_id))
            .cloned()
            .collect();
        
        for key in keys_to_remove {
            if let Some(order) = orders.remove(&key) {
                println!("🗑️ Removed local order: {} {} (ID: {})", order.pair, order.side, order.order_id);
            }
        }
    }

    // 🔥 ПОЛУЧАЕМ ЛОКАЛЬНЫЙ ОРДЕР
    pub async fn get_local_order(&self, pair: &str, order_id: &str) -> Option<LocalOrder> {
        let orders = self.local_orders.lock().await;
        
        for (_, order) in orders.iter() {
            if order.pair == pair && order.order_id == order_id {
                return Some(order.clone());
            }
        }
        
        None
    }

    // 🔥 ПОЛУЧАЕМ ВСЕ ЛОКАЛЬНЫЕ ОРДЕРА ДЛЯ ПАРЫ
    pub async fn get_local_orders_for_pair(&self, pair: &str) -> Vec<LocalOrder> {
        let orders = self.local_orders.lock().await;
        
        orders.values()
            .filter(|order| order.pair == pair)
            .cloned()
            .collect()
    }

    // 🔥 УМНАЯ ПРОВЕРКА СТАТУСА ОРДЕРА
    pub async fn smart_get_order_status(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        order_id: &str,
    ) -> Result<String, String> {
        // 🔥 ПРОВЕРЯЕМ ЧТО ОРДЕР ЕСТЬ В ЛОКАЛЬНОМ ХРАНЕНИИ
        if self.get_local_order(pair, order_id).await.is_none() {
            return Err(format!("Order {} not found in local storage for {}", order_id, pair));
        }

        // Rate limit check
        self.try_order(pair).await?;

        match exchange.get_order_status(pair, order_id).await {
            Ok(status) => {
                println!("📊 Order status: {} {} -> {}", pair, order_id, status);
                Ok(status)
            }
            Err(e) => {
                let error_msg = e.to_string();
                
                // 🔥 ЕСЛИ ОРДЕР НЕ НАЙДЕН НА БИРЖЕ, УДАЛЯЕМ ИЗ ЛОКАЛЬНОГО ХРАНЕНИЯ
                if error_msg.contains("51003") || error_msg.contains("not found") {
                    self.remove_local_order(pair, order_id).await;
                    println!("🗑️ Removed invalid order from local storage: {} {}", pair, order_id);
                }
                
                Err(error_msg)
            }
        }
    }
}

// 🔥 СОВМЕСТИМОСТЬ со старым OrderManager
pub struct OrderManager {
    grid_manager: GridOrderManager,
}

impl OrderManager {
    pub fn new(risk_manager: Arc<Mutex<RiskManager>>, tickers: Vec<String>) -> Self {
        let grid_manager = GridOrderManager::new(risk_manager, tickers, 5); // 5 тикеров в группе
        
        Self { grid_manager }
    }

    pub async fn try_place_order(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        side: &str,
        price: f64,
        size: f64,
    ) -> Result<String, String> {
        self.grid_manager.smart_place_order(exchange, pair, side, price, size).await
    }

    pub async fn try_cancel_order(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        order_id: &str,
    ) -> Result<(), String> {
        self.grid_manager.smart_cancel_order(exchange, pair, order_id).await
    }

    pub async fn try_get_order_status(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        order_id: &str,
    ) -> Result<String, String> {
        self.grid_manager.smart_get_order_status(exchange, pair, order_id).await
    }

    pub async fn place_market_order(
        &self,
        exchange: &Arc<dyn Exchange>,
        pair: &str,
        side: &str,
        size: f64,
    ) -> Result<String, String> {
        println!("🚀 [MARKET ORDER] Placing {} {} size: {:.4} @ market", pair, side, size);
        
        // Проверяем rate limit
        let _permit = self.grid_manager.rate_limiter.lock().await.allow();
        
        match exchange.place_market_order(pair, side, size).await {
            Ok(order_id) => {
                println!("✅ [MARKET ORDER SUCCESS] {} {} order_id: {}", pair, side, order_id);
                Ok(order_id)
            }
            Err(e) => {
                println!("❌ [MARKET ORDER FAILED] {} {} error: {}", pair, side, e);
                Err(e.to_string())
            }
        }
    }

    pub async fn get_rate_info(&self) -> (usize, u64) {
        self.grid_manager.get_rate_info().await
    }

    pub fn get_grid_manager(&self) -> &GridOrderManager {
        &self.grid_manager
    }
} 