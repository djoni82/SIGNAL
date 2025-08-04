use std::collections::VecDeque;
use crate::exchange::MarketData;

pub struct PricingEngine {
    price_history: VecDeque<f64>,
    max_history_size: usize,
}

impl PricingEngine {
    pub fn new() -> Self {
        Self {
            price_history: VecDeque::new(),
            max_history_size: 1000,
        }
    }

    pub fn calculate_prices(&self, bid: f64, ask: f64, spread: f64) -> (f64, f64) {
        let mid_price = (bid + ask) / 2.0;
        let half_spread = spread / 2.0;
        
        let buy_price = mid_price * (1.0 - half_spread);
        let sell_price = mid_price * (1.0 + half_spread);
        
        (buy_price, sell_price)
    }

    pub fn update_price_history(&mut self, price: f64) {
        self.price_history.push_back(price);
        
        if self.price_history.len() > self.max_history_size {
            self.price_history.pop_front();
        }
    }

    // 🔥 НОВЫЙ МЕТОД: Расчет волатильности
    pub fn calculate_volatility(&self) -> f64 {
        if self.price_history.len() < 2 {
            return 0.0;
        }

        let prices: Vec<f64> = self.price_history.iter().cloned().collect();
        let returns: Vec<f64> = prices.windows(2)
            .map(|window| (window[1] - window[0]) / window[0])
            .collect();

        if returns.is_empty() {
            return 0.0;
        }

        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter()
            .map(|r| (r - mean).powi(2))
            .sum::<f64>() / returns.len() as f64;

        variance.sqrt()
    }
}

pub struct MarketState {
    pub volatility: f64,
    pub spread: f64,
    pub volume: f64,
    pub rsi: f64,
    pub price_history: VecDeque<f64>,
    pub max_history_size: usize,
}

impl Default for MarketState {
    fn default() -> Self {
        Self {
            volatility: 0.0,
            spread: 0.0,
            volume: 0.0,
            rsi: 50.0,
            price_history: VecDeque::new(),
            max_history_size: 100,
        }
    }
}

impl MarketState {
    pub fn new() -> Self {
        Self {
            price_history: VecDeque::new(),
            max_history_size: 100,
            volatility: 0.0,
            spread: 0.0,
            volume: 0.0,
            rsi: 50.0,
        }
    }

    pub fn update(&mut self, market_data: &MarketData) {
        // Add current price to history
        self.price_history.push_back(market_data.last);
        if self.price_history.len() > self.max_history_size {
            self.price_history.pop_front();
        }
        
        // Update indicators
        self.volatility = self.calculate_volatility();
        self.spread = self.calculate_spread(market_data.bid, market_data.ask);
        self.volume = market_data.volume;
        self.rsi = self.calculate_rsi();
    }

    pub fn volatility(&self) -> f64 {
        self.volatility
    }

    pub fn spread(&self) -> f64 {
        self.spread
    }

    pub fn volume(&self) -> f64 {
        self.volume
    }

    pub fn rsi(&self) -> f64 {
        self.rsi
    }

    fn calculate_volatility(&self) -> f64 {
        if self.price_history.len() < 10 {
            return 0.001; // Минимальная волатильность если мало данных
        }
        
        let mut returns = Vec::new();
        let prices: Vec<f64> = self.price_history.iter().cloned().collect();
        
        for i in 1..prices.len() {
            let return_val = (prices[i] - prices[i-1]) / prices[i-1];
            returns.push(return_val.abs()); // Абсолютные значения изменений
        }
        
        // Рассчитываем среднюю волатильность как среднее абсолютных изменений
        let avg_volatility = returns.iter().sum::<f64>() / returns.len() as f64;
        
        // Возвращаем реальную волатильность без лишних операций
        // Clamp к разумному диапазону (0.05% - 5%)
        avg_volatility.clamp(0.0005, 0.05)
    }

    fn calculate_spread(&self, bid: f64, ask: f64) -> f64 {
        let raw_spread = (ask - bid) / bid;
        raw_spread.max(0.00005) // Minimum 0.005% spread
    }

    fn calculate_rsi(&self) -> f64 {
        if self.price_history.len() < 14 {
            return 50.0; // Нейтральный RSI если недостаточно данных
        }
        
        let mut gains = 0.0;
        let mut losses = 0.0;
        
        // Рассчитываем изменения цены
        for i in 1..self.price_history.len() {
            let change = self.price_history[i] - self.price_history[i - 1];
            if change > 0.0 {
                gains += change;
            } else {
                losses += change.abs();
            }
        }
        
        // Если нет потерь, RSI = 100
        if losses == 0.0 {
            return 100.0;
        }
        
        // Если нет прибыли, RSI = 0
        if gains == 0.0 {
            return 0.0;
        }
        
        // Рассчитываем относительную силу (RS)
        let rs = gains / losses;
        
        // Правильная формула RSI
        let rsi = 100.0 - (100.0 / (1.0 + rs));
        
        // Ограничиваем RSI диапазоном 0-100
        rsi.clamp(0.0, 100.0)
    }
} 