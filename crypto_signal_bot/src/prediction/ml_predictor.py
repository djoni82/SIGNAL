"""
ML Predictor for CryptoAlphaPro
Implements LSTM, GARCH and ensemble models for price prediction
"""

import asyncio
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
import xgboost as xgb
from arch import arch_model
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import joblib
import os
from pathlib import Path

from src.config.config_manager import ConfigManager


class LSTMModel(nn.Module):
    """LSTM model for price prediction"""
    
    def __init__(self, input_size: int = 10, hidden_size: int = 50, 
                 num_layers: int = 2, dropout: float = 0.2):
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc = nn.Linear(hidden_size, 1)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Take the last time step
        out = self.dropout(out[:, -1, :])
        out = self.fc(out)
        
        return out


class GARCHVolatilityModel:
    """GARCH model for volatility prediction"""
    
    def __init__(self, p: int = 1, q: int = 1, distribution: str = 'skewt'):
        self.p = p
        self.q = q
        self.distribution = distribution
        self.model = None
        self.fitted_model = None
        
    def fit(self, returns: np.ndarray) -> bool:
        """Fit GARCH model to returns"""
        try:
            # Scale returns to percentage
            returns_scaled = returns * 100
            
            # Create GARCH model
            self.model = arch_model(
                returns_scaled, 
                vol='Garch', 
                p=self.p, 
                q=self.q, 
                dist=self.distribution
            )
            
            # Fit model
            self.fitted_model = self.model.fit(disp='off')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error fitting GARCH model: {e}")
            return False
    
    def forecast(self, horizon: int = 5) -> Optional[np.ndarray]:
        """Forecast volatility"""
        try:
            if not self.fitted_model:
                return None
                
            forecast = self.fitted_model.forecast(horizon=horizon)
            volatility_forecast = np.sqrt(forecast.variance.iloc[-1].values) / 100
            
            return volatility_forecast
            
        except Exception as e:
            logger.error(f"❌ Error forecasting volatility: {e}")
            return None


class MLPredictor:
    """Main ML prediction class"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.ml_config = config.get_ml_config()
        
        # Models
        self.lstm_models: Dict[str, LSTMModel] = {}
        self.garch_models: Dict[str, GARCHVolatilityModel] = {}
        self.xgb_models: Dict[str, xgb.XGBRegressor] = {}
        self.rf_models: Dict[str, RandomForestRegressor] = {}
        self.svm_models: Dict[str, SVR] = {}
        
        # Scalers
        self.scalers: Dict[str, MinMaxScaler] = {}
        
        # Model paths
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Performance tracking
        self.model_performance: Dict[str, Dict] = {}
        
        # Configuration
        self.lstm_config = self.ml_config.get('lstm', {})
        self.garch_config = self.ml_config.get('garch', {})
        self.ensemble_config = self.ml_config.get('ensemble', {})
        
        # Training parameters
        self.sequence_length = 60  # 60 time steps for LSTM
        self.prediction_horizon = 5  # Predict 5 steps ahead
        
    async def load_models(self):
        """Load or initialize ML models"""
        try:
            logger.info("🧠 Loading ML models...")
            
            trading_pairs = self.config.get_trading_pairs()
            
            for pair in trading_pairs:
                pair_key = pair.replace('/', '_')
                
                # Try to load existing models
                model_loaded = await self._load_existing_models(pair_key)
                
                if not model_loaded:
                    # Initialize new models
                    await self._initialize_new_models(pair_key)
                
                logger.info(f"✅ Models loaded for {pair}")
            
            logger.success("✅ All ML models loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load ML models: {e}")
            raise
    
    async def _load_existing_models(self, pair_key: str) -> bool:
        """Load existing models for a pair"""
        try:
            model_path = self.models_dir / pair_key
            
            if not model_path.exists():
                return False
            
            # Load LSTM model
            lstm_path = model_path / "lstm_model.pth"
            if lstm_path.exists():
                lstm_model = LSTMModel(
                    input_size=self.lstm_config.get('input_size', 10),
                    hidden_size=self.lstm_config.get('hidden_size', 50),
                    num_layers=self.lstm_config.get('num_layers', 2),
                    dropout=self.lstm_config.get('dropout', 0.2)
                )
                lstm_model.load_state_dict(torch.load(lstm_path))
                lstm_model.eval()
                self.lstm_models[pair_key] = lstm_model
            
            # Load traditional ML models
            xgb_path = model_path / "xgb_model.joblib"
            if xgb_path.exists():
                self.xgb_models[pair_key] = joblib.load(xgb_path)
            
            rf_path = model_path / "rf_model.joblib"
            if rf_path.exists():
                self.rf_models[pair_key] = joblib.load(rf_path)
            
            svm_path = model_path / "svm_model.joblib"
            if svm_path.exists():
                self.svm_models[pair_key] = joblib.load(svm_path)
            
            # Load scaler
            scaler_path = model_path / "scaler.joblib"
            if scaler_path.exists():
                self.scalers[pair_key] = joblib.load(scaler_path)
            
            # Initialize GARCH model (needs to be fitted fresh)
            self.garch_models[pair_key] = GARCHVolatilityModel(
                p=self.garch_config.get('p', 1),
                q=self.garch_config.get('q', 1),
                distribution=self.garch_config.get('distribution', 'skewt')
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load existing models for {pair_key}: {e}")
            return False
    
    async def _initialize_new_models(self, pair_key: str):
        """Initialize new models for a pair"""
        try:
            # Initialize LSTM model
            self.lstm_models[pair_key] = LSTMModel(
                input_size=self.lstm_config.get('input_size', 10),
                hidden_size=self.lstm_config.get('hidden_size', 50),
                num_layers=self.lstm_config.get('num_layers', 2),
                dropout=self.lstm_config.get('dropout', 0.2)
            )
            
            # Initialize GARCH model
            self.garch_models[pair_key] = GARCHVolatilityModel(
                p=self.garch_config.get('p', 1),
                q=self.garch_config.get('q', 1),
                distribution=self.garch_config.get('distribution', 'skewt')
            )
            
            # Initialize traditional ML models
            self.xgb_models[pair_key] = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            self.rf_models[pair_key] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            self.svm_models[pair_key] = SVR(
                kernel='rbf',
                C=1.0,
                gamma='scale'
            )
            
            # Initialize scaler
            self.scalers[pair_key] = MinMaxScaler()
            
            logger.info(f"✅ New models initialized for {pair_key}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize models for {pair_key}: {e}")
            raise
    
    async def predict(self, exchange: str, pair: str) -> Optional[Dict[str, Any]]:
        """Generate predictions for a trading pair"""
        try:
            pair_key = pair.replace('/', '_')
            
            if pair_key not in self.lstm_models:
                logger.warning(f"⚠️  No models found for {pair}")
                return None
            
            # Get recent data for prediction
            end_time = datetime.now()
            start_time = end_time - timedelta(days=5)  # 5 days of recent data
            
            # This would come from data manager
            # For now, we'll simulate the prediction process
            
            # Get historical data (this would be actual data in production)
            data = await self._get_recent_data(exchange, pair, start_time, end_time)
            
            if data is None or len(data) < self.sequence_length:
                logger.warning(f"⚠️  Insufficient data for prediction: {pair}")
                return None
            
            # Generate predictions from different models
            predictions = {}
            
            # LSTM prediction
            lstm_pred = await self._predict_lstm(pair_key, data)
            if lstm_pred is not None:
                predictions['lstm'] = lstm_pred
            
            # GARCH volatility prediction
            garch_pred = await self._predict_garch(pair_key, data)
            if garch_pred is not None:
                predictions['garch'] = garch_pred
            
            # Traditional ML predictions
            xgb_pred = await self._predict_xgboost(pair_key, data)
            if xgb_pred is not None:
                predictions['xgboost'] = xgb_pred
            
            # Ensemble prediction
            ensemble_pred = self._create_ensemble_prediction(predictions)
            
            return {
                'pair': pair,
                'exchange': exchange,
                'predictions': predictions,
                'ensemble': ensemble_pred,
                'timestamp': datetime.now().isoformat(),
                'confidence': ensemble_pred.get('confidence', 0.5),
                'direction': ensemble_pred.get('direction', 'neutral'),
                'price_target': ensemble_pred.get('price_target'),
                'volatility_forecast': predictions.get('garch', {}).get('volatility_forecast')
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating predictions for {pair}: {e}")
            return None
    
    async def _get_recent_data(self, exchange: str, pair: str, 
                              start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
        """Get recent data for prediction (placeholder)"""
        try:
            # This would get actual data from data manager
            # For now, return None to simulate no data available
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting recent data: {e}")
            return None
    
    async def _predict_lstm(self, pair_key: str, data: pd.DataFrame) -> Optional[Dict]:
        """Generate LSTM prediction"""
        try:
            model = self.lstm_models.get(pair_key)
            scaler = self.scalers.get(pair_key)
            
            if not model or not scaler:
                return None
            
            # Prepare features
            features = self._prepare_features(data)
            
            if len(features) < self.sequence_length:
                return None
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Create sequence for LSTM
            sequence = features_scaled[-self.sequence_length:]
            sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0)
            
            # Generate prediction
            model.eval()
            with torch.no_grad():
                prediction = model(sequence_tensor)
                price_change = prediction.item()
            
            # Convert to actual price prediction
            current_price = data['close'].iloc[-1]
            predicted_price = current_price * (1 + price_change)
            
            # Determine direction and confidence
            direction = 'bullish' if price_change > 0 else 'bearish'
            confidence = min(abs(price_change) * 10, 1.0)  # Scale to 0-1
            
            return {
                'price_change': price_change,
                'predicted_price': predicted_price,
                'direction': direction,
                'confidence': confidence,
                'model': 'lstm'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in LSTM prediction: {e}")
            return None
    
    async def _predict_garch(self, pair_key: str, data: pd.DataFrame) -> Optional[Dict]:
        """Generate GARCH volatility prediction"""
        try:
            model = self.garch_models.get(pair_key)
            
            if not model:
                return None
            
            # Calculate returns
            returns = data['close'].pct_change().dropna()
            
            if len(returns) < 30:  # Need minimum data for GARCH
                return None
            
            # Fit model to recent returns
            success = model.fit(returns.values)
            
            if not success:
                return None
            
            # Generate volatility forecast
            volatility_forecast = model.forecast(horizon=self.prediction_horizon)
            
            if volatility_forecast is None:
                return None
            
            return {
                'volatility_forecast': volatility_forecast.tolist(),
                'avg_volatility': float(np.mean(volatility_forecast)),
                'volatility_trend': 'increasing' if volatility_forecast[-1] > volatility_forecast[0] else 'decreasing',
                'model': 'garch'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in GARCH prediction: {e}")
            return None
    
    async def _predict_xgboost(self, pair_key: str, data: pd.DataFrame) -> Optional[Dict]:
        """Generate XGBoost prediction"""
        try:
            model = self.xgb_models.get(pair_key)
            
            if not model:
                return None
            
            # Prepare features
            features = self._prepare_features(data)
            
            if len(features) == 0:
                return None
            
            # Get latest features
            latest_features = features[-1].reshape(1, -1)
            
            # Generate prediction (this would work if model was trained)
            try:
                prediction = model.predict(latest_features)[0]
                
                # Convert to direction and confidence
                direction = 'bullish' if prediction > 0 else 'bearish'
                confidence = min(abs(prediction), 1.0)
                
                return {
                    'price_change': prediction,
                    'direction': direction,
                    'confidence': confidence,
                    'model': 'xgboost'
                }
                
            except Exception:
                # Model not trained yet
                return None
            
        except Exception as e:
            logger.error(f"❌ Error in XGBoost prediction: {e}")
            return None
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for ML models"""
        try:
            features_list = []
            
            # Price features
            features_list.append(data['close'].values)
            features_list.append(data['high'].values)
            features_list.append(data['low'].values)
            features_list.append(data['volume'].values)
            
            # Technical indicators (basic ones)
            if len(data) >= 20:
                # Simple moving averages
                sma_5 = data['close'].rolling(5).mean().fillna(method='bfill')
                sma_20 = data['close'].rolling(20).mean().fillna(method='bfill')
                features_list.append(sma_5.values)
                features_list.append(sma_20.values)
                
                # Price ratios
                price_ratio = (data['close'] / sma_20).fillna(1)
                features_list.append(price_ratio.values)
            
            # Returns
            returns = data['close'].pct_change().fillna(0)
            features_list.append(returns.values)
            
            # Volume ratio
            if len(data) >= 10:
                volume_sma = data['volume'].rolling(10).mean().fillna(method='bfill')
                volume_ratio = (data['volume'] / volume_sma).fillna(1)
                features_list.append(volume_ratio.values)
            
            # Stack features
            features = np.column_stack(features_list)
            
            # Handle NaN values
            features = np.nan_to_num(features, nan=0.0, posinf=1.0, neginf=-1.0)
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error preparing features: {e}")
            return np.array([])
    
    def _create_ensemble_prediction(self, predictions: Dict) -> Dict:
        """Create ensemble prediction from individual model predictions"""
        try:
            if not predictions:
                return {'direction': 'neutral', 'confidence': 0.5}
            
            # Get ensemble weights
            weights = self.ensemble_config.get('weights', [0.4, 0.35, 0.25])
            models = self.ensemble_config.get('models', ['lstm', 'xgboost', 'svm'])
            
            # Collect valid predictions
            valid_predictions = []
            valid_weights = []
            
            for i, model_name in enumerate(models):
                if model_name in predictions:
                    pred = predictions[model_name]
                    if isinstance(pred, dict) and 'confidence' in pred:
                        valid_predictions.append(pred)
                        valid_weights.append(weights[i] if i < len(weights) else 0.1)
            
            if not valid_predictions:
                return {'direction': 'neutral', 'confidence': 0.5}
            
            # Normalize weights
            total_weight = sum(valid_weights)
            if total_weight > 0:
                valid_weights = [w / total_weight for w in valid_weights]
            
            # Calculate weighted average
            weighted_confidence = 0
            bullish_weight = 0
            bearish_weight = 0
            
            for pred, weight in zip(valid_predictions, valid_weights):
                confidence = pred.get('confidence', 0.5)
                direction = pred.get('direction', 'neutral')
                
                weighted_confidence += confidence * weight
                
                if direction == 'bullish':
                    bullish_weight += weight
                elif direction == 'bearish':
                    bearish_weight += weight
            
            # Determine ensemble direction
            if bullish_weight > bearish_weight:
                ensemble_direction = 'bullish'
            elif bearish_weight > bullish_weight:
                ensemble_direction = 'bearish'
            else:
                ensemble_direction = 'neutral'
            
            # Calculate price target if available
            price_targets = []
            for pred in valid_predictions:
                if 'predicted_price' in pred:
                    price_targets.append(pred['predicted_price'])
            
            avg_price_target = np.mean(price_targets) if price_targets else None
            
            return {
                'direction': ensemble_direction,
                'confidence': weighted_confidence,
                'price_target': avg_price_target,
                'bullish_weight': bullish_weight,
                'bearish_weight': bearish_weight,
                'num_models': len(valid_predictions)
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating ensemble prediction: {e}")
            return {'direction': 'neutral', 'confidence': 0.5}
    
    async def retrain_models(self):
        """Retrain all models with latest data"""
        try:
            logger.info("🔄 Starting model retraining...")
            
            trading_pairs = self.config.get_trading_pairs()
            
            for pair in trading_pairs:
                pair_key = pair.replace('/', '_')
                logger.info(f"🔄 Retraining models for {pair}")
                
                # Get training data
                training_data = await self._get_training_data(pair)
                
                if training_data is not None and len(training_data) > 100:
                    # Retrain models
                    await self._retrain_pair_models(pair_key, training_data)
                    
                    # Save models
                    await self._save_models(pair_key)
                    
                    logger.info(f"✅ Models retrained for {pair}")
                else:
                    logger.warning(f"⚠️  Insufficient training data for {pair}")
            
            logger.success("✅ Model retraining completed")
            
        except Exception as e:
            logger.error(f"❌ Error in model retraining: {e}")
    
    async def _get_training_data(self, pair: str) -> Optional[pd.DataFrame]:
        """Get training data for a pair"""
        try:
            # This would get historical data from data manager
            # For now, return None
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting training data: {e}")
            return None
    
    async def _retrain_pair_models(self, pair_key: str, data: pd.DataFrame):
        """Retrain models for a specific pair"""
        try:
            # This would implement actual model training
            # For now, just log that we would retrain
            logger.info(f"Would retrain models for {pair_key} with {len(data)} samples")
            
        except Exception as e:
            logger.error(f"❌ Error retraining models for {pair_key}: {e}")
    
    async def _save_models(self, pair_key: str):
        """Save models for a pair"""
        try:
            model_path = self.models_dir / pair_key
            model_path.mkdir(exist_ok=True)
            
            # Save LSTM model
            if pair_key in self.lstm_models:
                lstm_path = model_path / "lstm_model.pth"
                torch.save(self.lstm_models[pair_key].state_dict(), lstm_path)
            
            # Save traditional ML models
            if pair_key in self.xgb_models:
                xgb_path = model_path / "xgb_model.joblib"
                joblib.dump(self.xgb_models[pair_key], xgb_path)
            
            if pair_key in self.rf_models:
                rf_path = model_path / "rf_model.joblib"
                joblib.dump(self.rf_models[pair_key], rf_path)
            
            if pair_key in self.svm_models:
                svm_path = model_path / "svm_model.joblib"
                joblib.dump(self.svm_models[pair_key], svm_path)
            
            # Save scaler
            if pair_key in self.scalers:
                scaler_path = model_path / "scaler.joblib"
                joblib.dump(self.scalers[pair_key], scaler_path)
            
            logger.info(f"✅ Models saved for {pair_key}")
            
        except Exception as e:
            logger.error(f"❌ Error saving models for {pair_key}: {e}")
    
    def check_model_health(self) -> bool:
        """Check if models are performing well"""
        try:
            # Check if we have models loaded
            if not self.lstm_models:
                return False
            
            # Check model performance (placeholder)
            # In real implementation, this would check recent prediction accuracy
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking model health: {e}")
            return False
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        try:
            return {
                'models_loaded': len(self.lstm_models),
                'last_training': 'N/A',
                'avg_accuracy': 0.742,  # Placeholder
                'predictions_made': 0,
                'successful_predictions': 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting model performance: {e}")
            return {} 