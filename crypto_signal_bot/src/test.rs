use std::sync::Arc;
use anyhow::Result;
use crate::config::{Config, load_config};
use crate::exchange::{Exchange, Binance, Okx};

pub async fn test_exchanges() -> Result<()> {
    println!("🧪 Testing HFT Market Making Bot...");

    // Load configuration
    let config = load_config().await?;
    
    // Test Binance
    println!("\n🔗 Testing Binance connection...");
    let binance_config = config.exchanges.iter().find(|e| e.name == "binance").unwrap();
    let binance = Arc::new(Binance::new(binance_config.clone()));
    
    match binance.connect().await {
        Ok(_) => println!("✅ Binance connection successful"),
        Err(e) => println!("❌ Binance connection failed: {}", e),
    }
    
    match binance.check_balance().await {
        Ok(balance) => println!("💰 Binance balance: {:.2} USDT", balance),
        Err(e) => println!("❌ Failed to get Binance balance: {}", e),
    }
    
    // Test market data
    for pair in &binance_config.pairs[..2] { // Test first 2 pairs
        match binance.get_market_data(pair).await {
            Ok(data) => println!("📊 {} - Bid: {:.4}, Ask: {:.4}, Last: {:.4}, Volume: {:.2}", 
                pair, data.bid, data.ask, data.last, data.volume),
            Err(e) => println!("❌ Failed to get {} market data: {}", pair, e),
        }
    }
    
    // Test OKX
    println!("\n🔗 Testing OKX connection...");
    let okx_config = config.exchanges.iter().find(|e| e.name == "okx").unwrap();
    let okx = Arc::new(Okx::new(okx_config.clone()));
    
    match okx.connect().await {
        Ok(_) => println!("✅ OKX connection successful"),
        Err(e) => println!("❌ OKX connection failed: {}", e),
    }
    
    match okx.check_balance().await {
        Ok(balance) => println!("💰 OKX balance: {:.2} USDT", balance),
        Err(e) => println!("❌ Failed to get OKX balance: {}", e),
    }
    
    // Test market data
    for pair in &okx_config.pairs[..2] { // Test first 2 pairs
        match okx.get_market_data(pair).await {
            Ok(data) => println!("📊 {} - Bid: {:.4}, Ask: {:.4}, Last: {:.4}, Volume: {:.2}", 
                pair, data.bid, data.ask, data.last, data.volume),
            Err(e) => println!("❌ Failed to get {} market data: {}", pair, e),
        }
    }
    
    println!("\n✅ Testing completed!");
    Ok(())
} 