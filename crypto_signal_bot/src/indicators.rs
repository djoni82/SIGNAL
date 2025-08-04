use std::collections::VecDeque;

pub fn calculate_volatility(prices: &[f64]) -> f64 {
    if prices.len() < 2 {
        return 0.0;
    }
    
    let returns: Vec<f64> = prices
        .windows(2)
        .map(|window| (window[1] - window[0]) / window[0])
        .collect();
    
    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns.iter()
        .map(|r| (r - mean).powi(2))
        .sum::<f64>() / returns.len() as f64;
    
    variance.sqrt()
}

pub fn calculate_spread(bid: f64, ask: f64) -> f64 {
    (ask - bid) / bid
}

pub fn calculate_rsi(prices: &[f64], period: usize) -> f64 {
    if prices.len() < period + 1 {
        return 50.0;
    }
    
    let mut gains = 0.0;
    let mut losses = 0.0;
    
    for i in 1..=period {
        let change = prices[prices.len() - i] - prices[prices.len() - i - 1];
        if change > 0.0 {
            gains += change;
        } else {
            losses += change.abs();
        }
    }
    
    if losses == 0.0 {
        return 100.0;
    }
    
    let rs = gains / losses;
    100.0 - (100.0 / (1.0 + rs))
} 