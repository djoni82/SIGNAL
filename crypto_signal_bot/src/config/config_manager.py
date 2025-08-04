"""
Configuration Manager for CryptoAlphaPro
Handles loading and validation of configuration files
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
from pydantic import BaseModel, validator
from dotenv import load_dotenv


class DatabaseConfig(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str
    max_connections: int


class ExchangeConfig(BaseModel):
    api_key: str
    secret: str
    passphrase: Optional[str] = None
    sandbox: bool = False
    rate_limit: int


class TradingConfig(BaseModel):
    pairs: list
    timeframes: list
    update_frequency: int


class RiskManagementConfig(BaseModel):
    max_leverage: float
    default_leverage: float
    max_position_size: float
    stop_loss_atr_multiplier: float
    take_profit_levels: list
    hedge_ratio: float


class ConfigManager:
    """Configuration manager class"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_env_variables()
    
    def _load_env_variables(self):
        """Load environment variables"""
        # Try to load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        
        # Also try loading from project root
        root_env_path = Path(__file__).parent.parent.parent / ".env"
        if root_env_path.exists():
            load_dotenv(root_env_path)
    
    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as file:
                raw_config = yaml.safe_load(file)
            
            # Substitute environment variables
            self.config = self._substitute_env_vars(raw_config)
            
            # Validate configuration
            self._validate_config()
            
            logger.info(f"✅ Configuration loaded from {self.config_path}")
            return self.config
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            raise
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config"""
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            value = os.getenv(env_var)
            if value is None:
                logger.warning(f"⚠️  Environment variable {env_var} not found, using placeholder")
                return config
            return value
        else:
            return config
    
    def _validate_config(self):
        """Validate configuration structure"""
        required_sections = [
            'app', 'databases', 'exchanges', 'trading', 
            'risk_management', 'telegram', 'indicators'
        ]
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate database configurations
        for db_name, db_config in self.config['databases'].items():
            try:
                DatabaseConfig(**db_config)
            except Exception as e:
                raise ValueError(f"Invalid database configuration for {db_name}: {e}")
        
        # Validate exchange configurations
        for exchange_name, exchange_config in self.config['exchanges'].items():
            try:
                ExchangeConfig(**exchange_config)
            except Exception as e:
                raise ValueError(f"Invalid exchange configuration for {exchange_name}: {e}")
        
        logger.info("✅ Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_database_config(self, db_name: str) -> DatabaseConfig:
        """Get database configuration"""
        db_config = self.get(f'databases.{db_name}')
        if not db_config:
            raise ValueError(f"Database configuration not found: {db_name}")
        return DatabaseConfig(**db_config)
    
    def get_exchange_config(self, exchange_name: str) -> ExchangeConfig:
        """Get exchange configuration"""
        exchange_config = self.get(f'exchanges.{exchange_name}')
        if not exchange_config:
            raise ValueError(f"Exchange configuration not found: {exchange_name}")
        return ExchangeConfig(**exchange_config)
    
    def get_trading_pairs(self) -> list:
        """Get list of trading pairs"""
        return self.get('trading.pairs', [])
    
    def get_timeframes(self) -> list:
        """Get list of timeframes"""
        return self.get('trading.timeframes', [])
    
    def get_risk_config(self) -> RiskManagementConfig:
        """Get risk management configuration"""
        risk_config = self.get('risk_management')
        if not risk_config:
            raise ValueError("Risk management configuration not found")
        return RiskManagementConfig(**risk_config)
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram bot configuration"""
        return self.get('telegram', {})
    
    def get_ml_config(self) -> Dict[str, Any]:
        """Get ML models configuration"""
        return self.get('ml_models', {})
    
    def get_indicators_config(self) -> Dict[str, Any]:
        """Get technical indicators configuration"""
        return self.get('indicators', {})
    
    def get_arbitrage_config(self) -> Dict[str, Any]:
        """Get arbitrage configuration"""
        return self.get('arbitrage', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.get('monitoring', {})
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('app.debug', False)
    
    def get_log_level(self) -> str:
        """Get log level"""
        return self.get('app.log_level', 'INFO')
    
    def reload_config(self):
        """Reload configuration from file"""
        return self.load_config()
    
    def update_config(self, key: str, value: Any):
        """Update configuration value"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the key to update
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Update the value
        config[keys[-1]] = value
        logger.info(f"Updated configuration: {key} = {value}")
    
    def save_config(self, filepath: Optional[str] = None):
        """Save current configuration to file"""
        if filepath is None:
            filepath = self.config_path
        
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
            logger.info(f"✅ Configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
            raise 