use chrono::{Utc, Duration};
use std::collections::VecDeque;
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, Duration as StdDuration};

// 🔥 КОНСТАНТЫ ДЛЯ СТОП-УРОВНЕЙ
pub const STOP_LOSS_PCT: f64 = 0.001;      // 0.1%
pub const TAKE_PROFIT_PCT: f64 = 0.0015;   // 0.15%
pub const TRAILING_PCT: f64 = 0.0005;      // 0.05%

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub timestamp: chrono::DateTime<Utc>,
    pub pair: String,
    pub side: String,
    pub price: f64,
    pub size: f64,
    pub pnl: f64,
}

#[derive(Debug, Clone)]
pub struct Position {
    pub id: String,
    pub exchange: String,
    pub pair: String,
    pub side: String, // "LONG" or "SHORT"
    pub entry_price: f64,
    pub current_price: f64,
    pub size: f64,
    pub leverage: f64,
    pub entry_time: chrono::DateTime<Utc>,
    pub pnl: f64,
    pub pnl_percent: f64,

    pub stop_loss_price: f64,
    pub take_profit_price: f64,
    pub trailing_stop_price: Option<f64>,
    pub high_water_mark: f64,

    pub order_id: String,
    pub open_time: SystemTime,
}

pub struct RiskManager {
    balance: f64,
    trades: VecDeque<Trade>,
    max_daily_loss: f64,
    daily_pnl: f64,
    positions: Vec<Position>,
    max_positions: usize,
}

impl RiskManager {
    pub fn new(balance: f64) -> Self {
        Self {
            balance,
            trades: VecDeque::new(),
            max_daily_loss: balance * 0.02,
            daily_pnl: 0.0,
            positions: Vec::new(),
            max_positions: 10,
        }
    }

    // 🔥 НОВЫЙ КОНСТРУКТОР для HFT с дневным стопом
    pub fn new_with_daily_stop(balance: f64, daily_stop_loss: f64) -> Self {
        Self {
            balance,
            trades: VecDeque::new(),
            max_daily_loss: daily_stop_loss,
            daily_pnl: 0.0,
            positions: Vec::new(),
            max_positions: 10,
        }
    }

    pub fn update_balance(&mut self, balance: f64) {
        self.balance = balance;
        self.max_daily_loss = balance * 0.02;
    }

    pub fn record_trade(&mut self, trade: Trade) {
        self.daily_pnl += trade.pnl;
        self.trades.push_back(trade);
        if self.trades.len() > 1000 { self.trades.pop_front(); }
    }

    pub fn can_trade(&self, _size: f64) -> bool {
        // Ограничение по max_daily_loss и количеству открытых позиций
        if self.daily_pnl <= -self.max_daily_loss || self.positions.len() >= self.max_positions {
            return false;
        }
        true
    }

    pub fn add_position(
        &mut self,
        mut position: Position,
        stop_loss_pct: f64,
        take_profit_pct: f64,
        trailing_pct: f64
    ) {
        // Задаем stop-цены и trailing_stop для позиции
        let (sl, tp, hwm) = if &position.side == "LONG" {
            (
                position.entry_price * (1.0 - stop_loss_pct),
                position.entry_price * (1.0 + take_profit_pct),
                position.entry_price
            )
        } else {
            (
                position.entry_price * (1.0 + stop_loss_pct),
                position.entry_price * (1.0 - take_profit_pct),
                position.entry_price
            )
        };
        position.stop_loss_price = sl;
        position.take_profit_price = tp;
        position.trailing_stop_price = Some(if &position.side == "LONG" {
            position.entry_price * (1.0 - trailing_pct)
        } else {
            position.entry_price * (1.0 + trailing_pct)
        });
        position.high_water_mark = position.entry_price;

        println!("✅ Position {} added: SL={:.4}, TP={:.4}, TS={:.4}", 
                 position.id, position.stop_loss_price, position.take_profit_price, 
                 position.trailing_stop_price.unwrap_or(0.0));

        self.positions.push(position);
    }

    /// На каждом тике/обновлении - обновлять trailing stop
    pub fn update_position(&mut self, position_id: &str, current_price: f64, trailing_pct: f64) -> Option<Position> {
        for pos in &mut self.positions {
            if pos.id == position_id {
                pos.current_price = current_price;

                // Рассчитываем PnL
                if pos.entry_price > 0.0 {
                    let price_diff = if &pos.side == "LONG" { current_price - pos.entry_price } else { pos.entry_price - current_price };
                    pos.pnl = price_diff * pos.size * pos.leverage;
                    pos.pnl_percent = price_diff / pos.entry_price * 100.0;
                }
                
                // 🔥 ПРАВИЛЬНЫЙ ТРЕЙЛИНГ-СТОП: обновляем high_water_mark и trailing_stop
                if &pos.side == "LONG" {
                    // Для LONG: обновляем high_water_mark если цена выше
                    if current_price > pos.high_water_mark {
                        pos.high_water_mark = current_price;
                        // Трейлинг-стоп = high_water_mark * (1.0 - trailing_pct)
                        let new_trailing_stop = current_price * (1.0 - trailing_pct);
                        pos.trailing_stop_price = Some(new_trailing_stop);
                        println!("📈 Trailing stop updated for LONG {}: HWM={:.4} -> TS={:.4}", 
                                 position_id, pos.high_water_mark, new_trailing_stop);
                    }
                } else {
                    // Для SHORT: обновляем high_water_mark если цена ниже (это минимум для SHORT)
                    if current_price < pos.high_water_mark {
                        pos.high_water_mark = current_price;
                        // Трейлинг-стоп = high_water_mark * (1.0 + trailing_pct)
                        let new_trailing_stop = current_price * (1.0 + trailing_pct);
                        pos.trailing_stop_price = Some(new_trailing_stop);
                        println!("📉 Trailing stop updated for SHORT {}: LWM={:.4} -> TS={:.4}", 
                                 position_id, pos.high_water_mark, new_trailing_stop);
                    }
                }
                return Some(pos.clone());
            }
        }
        None
    }

    pub fn should_close_position(&self, position: &Position) -> bool {
        // 🔥 ПРАВИЛЬНАЯ ЛОГИКА: используем реальные стоп-уровни
        
        // 1. STOP-LOSS по цене
        if &position.side == "LONG" && position.current_price <= position.stop_loss_price {
            println!("🛑 [StopLoss] LONG, {:.4} <= {:.4}", position.current_price, position.stop_loss_price); 
            return true;
        }
        if &position.side == "SHORT" && position.current_price >= position.stop_loss_price {
            println!("🛑 [StopLoss] SHORT, {:.4} >= {:.4}", position.current_price, position.stop_loss_price); 
            return true;
        }
        
        // 2. TAKE-PROFIT по цене
        if &position.side == "LONG" && position.current_price >= position.take_profit_price {
            println!("💰 [TakeProfit] LONG, {:.4} >= {:.4}", position.current_price, position.take_profit_price); 
            return true;
        }
        if &position.side == "SHORT" && position.current_price <= position.take_profit_price {
            println!("💰 [TakeProfit] SHORT, {:.4} <= {:.4}", position.current_price, position.take_profit_price); 
            return true;
        }
        
        // 3. TRAILING-STOP по цене
        if let Some(ts) = position.trailing_stop_price {
            if &position.side == "LONG" && position.current_price <= ts {
                println!("🎯 [TrailingStop] LONG, {:.4} <= {:.4}", position.current_price, ts); 
                return true;
            }
            if &position.side == "SHORT" && position.current_price >= ts {
                println!("🎯 [TrailingStop] SHORT, {:.4} >= {:.4}", position.current_price, ts); 
                return true;
            }
        }
        
        // 🔥 УБИРАЕМ АГРЕССИВНЫЕ УСЛОВИЯ:
        // - Закрытие по любой прибыли (pnl_percent > 0.0)
        // - Закрытие по времени (2 секунды)
        // - Закрытие по минимальному P&L
        
        false
    }

    pub fn remove_position(&mut self, position_id: &str) -> Option<Position> {
        let idx = self.positions.iter().position(|p| p.id == position_id);
        if let Some(index) = idx {
            Some(self.positions.remove(index))
        } else { None }
    }

    pub fn get_positions(&self) -> &Vec<Position> { &self.positions }
    pub fn daily_pnl(&self) -> f64 { self.daily_pnl }
    pub fn reset_daily_pnl(&mut self) { self.daily_pnl = 0.0; }
    pub fn available_balance(&self) -> f64 { self.balance }
    
    // 🔥 ПУБЛИЧНЫЙ МЕТОД ДЛЯ ДОСТУПА К ПОСЛЕДНИМ СДЕЛКАМ
    pub fn get_recent_trades(&self, count: usize) -> Vec<&Trade> {
        self.trades.iter().rev().take(count).collect()
    }

    // 🔥 ПРОВЕРКА MIN SIZE/QTY В RUNTIME
    pub fn validate_order_size(&self, size: f64, min_qty: f64, min_notional: f64, price: f64) -> Result<(), String> {
        // Проверка минимального размера
        if size < min_qty {
            let error_msg = format!("Order size {} < min_qty {}", size, min_qty);
            println!("🚨 [RISK MANAGER] {}", error_msg);
            return Err(error_msg);
        }
        
        // Проверка минимального номинала
        let notional = size * price;
        if notional < min_notional {
            let error_msg = format!("Order notional {:.2} < min_notional {:.2}", notional, min_notional);
            println!("🚨 [RISK MANAGER] {}", error_msg);
            return Err(error_msg);
        }
        
        // Проверка баланса
        if notional > self.balance * 0.5 {
            let error_msg = format!("Order notional {:.2} > 50% of balance {:.2}", notional, self.balance);
            println!("🚨 [RISK MANAGER] {}", error_msg);
            return Err(error_msg);
        }
        
        println!("✅ [RISK MANAGER] Order validation passed: size={}, notional={:.2}", size, notional);
        Ok(())
    }

    // 🔥 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОШИБОК РИСК-МЕНЕДЖЕРА
    pub fn log_risk_error(&self, error: &str, pair: &str, size: f64, price: f64) {
        println!("🚨 [RISK MANAGER ERROR] {}: {}", pair, error);
        println!("   Details: size={}, price={}, notional={:.2}, balance={:.2}, daily_pnl={:.2}", 
                size, price, size * price, self.balance, self.daily_pnl);
        println!("   Positions: {}/{}", self.positions.len(), self.max_positions);
    }
    
    pub fn clear_all_positions(&mut self) {
        self.positions.clear();
        println!("🧹 All positions cleared from risk manager");
    }
} 