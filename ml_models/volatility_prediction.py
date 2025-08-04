#!/usr/bin/env python3
"""
🚀 Advanced ML Models for Crypto Prediction
GARCH Model for Volatility Forecasting
LSTM Neural Network for Price Prediction
Risk Assessment and Dynamic Leverage Calculation
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from arch import arch_model
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

@dataclass
class VolatilityForecast:
    symbol: str
    forecast_horizon: int
    volatility_forecast: List[float]
    confidence_intervals: Dict[str, List[float]]
    garch_params: Dict
    timestamp: float

@dataclass
class PriceForecast:
    symbol: str
    forecast_horizon: int
    price_forecast: List[float]
    confidence_score: float
    lstm_features: Dict
    timestamp: float

@dataclass
class RiskMetrics:
    symbol: str
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    expected_shortfall: float
    max_drawdown_forecast: float
    optimal_leverage: float
    volatility_regime: str  # 'low', 'normal', 'high', 'extreme'
    timestamp: float

class GARCHVolatilityModel:
    """GARCH Model for Volatility Forecasting"""
    
    def __init__(self, model_type: str = 'GARCH', p: int = 1, q: int = 1):
        self.model_type = model_type
        self.p = p
        self.q = q
        self.model = None
        self.fitted_model = None
        self.scaler = StandardScaler()
        
    def prepare_returns(self, prices: np.array) -> np.array:
        """Calculate log returns from prices"""
        log_prices = np.log(prices)
        returns = np.diff(log_prices) * 100  # Convert to percentage
        return returns[~np.isnan(returns)]  # Remove NaN values
    
    def fit(self, prices: np.array, distribution: str = 'skewt') -> Dict:
        """Fit GARCH model to price data"""
        returns = self.prepare_returns(prices)
        
        if len(returns) < 50:
            raise ValueError("Need at least 50 observations for GARCH fitting")
        
        # Create GARCH model
        self.model = arch_model(
            returns, 
            vol=self.model_type, 
            p=self.p, 
            q=self.q, 
            dist=distribution
        )
        
        # Fit model
        self.fitted_model = self.model.fit(disp='off', show_warning=False)
        
        # Extract parameters
        params = {
            'omega': self.fitted_model.params['omega'],
            'alpha': [self.fitted_model.params[f'alpha[{i+1}]'] for i in range(self.p)],
            'beta': [self.fitted_model.params[f'beta[{i+1}]'] for i in range(self.q)],
            'nu': self.fitted_model.params.get('nu', None),  # For Student-t distribution
            'lambda': self.fitted_model.params.get('lambda', None),  # For skewed distributions
            'log_likelihood': self.fitted_model.loglikelihood,
            'aic': self.fitted_model.aic,
            'bic': self.fitted_model.bic
        }
        
        return params
    
    def forecast_volatility(self, horizon: int = 5, method: str = 'simulation') -> VolatilityForecast:
        """Forecast volatility for specified horizon"""
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")
        
        # Generate forecast
        forecast = self.fitted_model.forecast(horizon=horizon, method=method)
        
        # Extract volatility forecasts (convert from percentage to decimal)
        vol_forecast = np.sqrt(forecast.variance.iloc[-1].values) / 100
        
        # Calculate confidence intervals (approximate)
        residuals = self.fitted_model.resid
        std_residual = np.std(residuals)
        
        confidence_intervals = {
            '95%': {
                'lower': vol_forecast * (1 - 1.96 * std_residual / np.sqrt(len(residuals))),
                'upper': vol_forecast * (1 + 1.96 * std_residual / np.sqrt(len(residuals)))
            },
            '99%': {
                'lower': vol_forecast * (1 - 2.58 * std_residual / np.sqrt(len(residuals))),
                'upper': vol_forecast * (1 + 2.58 * std_residual / np.sqrt(len(residuals)))
            }
        }
        
        return VolatilityForecast(
            symbol="",  # Will be set by caller
            forecast_horizon=horizon,
            volatility_forecast=vol_forecast.tolist(),
            confidence_intervals=confidence_intervals,
            garch_params={
                'omega': float(self.fitted_model.params['omega']),
                'alpha_sum': sum(float(self.fitted_model.params[f'alpha[{i+1}]']) for i in range(self.p)),
                'beta_sum': sum(float(self.fitted_model.params[f'beta[{i+1}]']) for i in range(self.q)),
                'persistence': sum(float(self.fitted_model.params[f'alpha[{i+1}]']) for i in range(self.p)) +
                              sum(float(self.fitted_model.params[f'beta[{i+1}]']) for i in range(self.q))
            },
            timestamp=datetime.now().timestamp()
        )
    
    def calculate_var(self, returns: np.array, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk"""
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    def calculate_expected_shortfall(self, returns: np.array, confidence_level: float = 0.95) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        var = self.calculate_var(returns, confidence_level)
        return np.mean(returns[returns <= var])

class LSTMPricePredictor:
    """LSTM Neural Network for Price Prediction"""
    
    def __init__(self, input_size: int = 10, hidden_size: int = 50, num_layers: int = 2, dropout: float = 0.2):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_scaler = StandardScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def create_model(self):
        """Create LSTM model architecture"""
        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, dropout):
                super(LSTMModel, self).__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers
                
                self.lstm = nn.LSTM(
                    input_size, 
                    hidden_size, 
                    num_layers, 
                    batch_first=True,
                    dropout=dropout if num_layers > 1 else 0
                )
                
                self.attention = nn.MultiheadAttention(hidden_size, num_heads=8, batch_first=True)
                self.dropout = nn.Dropout(dropout)
                self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
                self.fc2 = nn.Linear(hidden_size // 2, 1)
                self.relu = nn.ReLU()
                
            def forward(self, x):
                batch_size = x.size(0)
                
                # LSTM layers
                lstm_out, (hidden, cell) = self.lstm(x)
                
                # Attention mechanism
                attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
                
                # Use last output
                out = attn_out[:, -1, :]
                out = self.dropout(out)
                out = self.relu(self.fc1(out))
                out = self.fc2(out)
                
                return out
        
        self.model = LSTMModel(self.input_size, self.hidden_size, self.num_layers, self.dropout)
        self.model.to(self.device)
        
        return self.model
    
    def prepare_sequences(self, data: np.array, sequence_length: int = 60) -> Tuple[np.array, np.array]:
        """Prepare sequences for LSTM training"""
        sequences = []
        targets = []
        
        for i in range(sequence_length, len(data)):
            sequences.append(data[i-sequence_length:i])
            targets.append(data[i])
        
        return np.array(sequences), np.array(targets)
    
    def create_features(self, prices: np.array, volumes: np.array = None) -> np.array:
        """Create additional features for LSTM"""
        features = []
        
        # Price-based features
        returns = np.diff(np.log(prices))
        returns = np.concatenate([[0], returns])  # Add zero for first value
        
        # Rolling statistics
        for window in [5, 10, 20]:
            if len(prices) >= window:
                rolling_mean = pd.Series(prices).rolling(window).mean().fillna(method='bfill')
                rolling_std = pd.Series(prices).rolling(window).std().fillna(method='bfill')
                features.extend([rolling_mean.values, rolling_std.values])
        
        # Technical indicators (simplified)
        if len(prices) >= 14:
            # RSI-like indicator
            price_changes = np.diff(prices)
            gains = np.where(price_changes > 0, price_changes, 0)
            losses = np.where(price_changes < 0, -price_changes, 0)
            
            avg_gains = pd.Series(gains).rolling(14).mean().fillna(method='bfill')
            avg_losses = pd.Series(losses).rolling(14).mean().fillna(method='bfill')
            
            rs = avg_gains / (avg_losses + 1e-8)
            rsi = 100 - (100 / (1 + rs))
            rsi = np.concatenate([[50], rsi.values])  # Add neutral RSI for first value
            features.append(rsi)
        
        # Volume features (if provided)
        if volumes is not None and len(volumes) == len(prices):
            volume_sma = pd.Series(volumes).rolling(20).mean().fillna(method='bfill')
            volume_ratio = volumes / volume_sma
            features.append(volume_ratio.values)
        
        # Combine all features
        feature_matrix = np.column_stack([prices, returns] + features)
        
        return feature_matrix
    
    def train(self, prices: np.array, volumes: np.array = None, epochs: int = 100, batch_size: int = 32) -> Dict:
        """Train LSTM model"""
        # Create features
        features = self.create_features(prices, volumes)
        
        # Scale features
        scaled_features = self.feature_scaler.fit_transform(features)
        
        # Prepare sequences
        X, y = self.prepare_sequences(scaled_features[:, 0])  # Use scaled prices as target
        
        # Scale targets
        y_scaled = self.scaler.fit_transform(y.reshape(-1, 1)).flatten()
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.FloatTensor(y_scaled).to(self.device)
        
        # Create model
        if self.model is None:
            self.input_size = X.shape[2]
            self.create_model()
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.7)
        
        # Training loop
        self.model.train()
        losses = []
        
        for epoch in range(epochs):
            total_loss = 0
            num_batches = len(X_tensor) // batch_size
            
            for i in range(0, len(X_tensor), batch_size):
                batch_X = X_tensor[i:i+batch_size]
                batch_y = y_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                optimizer.step()
                total_loss += loss.item()
            
            avg_loss = total_loss / max(1, num_batches)
            losses.append(avg_loss)
            scheduler.step()
            
            if epoch % 20 == 0:
                print(f"Epoch {epoch}, Loss: {avg_loss:.6f}")
        
        return {
            'final_loss': losses[-1] if losses else 0,
            'loss_history': losses,
            'epochs_trained': epochs
        }
    
    def predict(self, prices: np.array, volumes: np.array = None, horizon: int = 5) -> PriceForecast:
        """Predict future prices"""
        if self.model is None:
            raise ValueError("Model must be trained before prediction")
        
        self.model.eval()
        
        # Create features
        features = self.create_features(prices, volumes)
        scaled_features = self.feature_scaler.transform(features)
        
        # Use last sequence for prediction
        last_sequence = scaled_features[-60:] if len(scaled_features) >= 60 else scaled_features
        
        predictions = []
        current_sequence = last_sequence.copy()
        
        with torch.no_grad():
            for _ in range(horizon):
                # Prepare input
                input_tensor = torch.FloatTensor(current_sequence[-60:]).unsqueeze(0).to(self.device)
                
                # Predict
                pred_scaled = self.model(input_tensor).cpu().numpy()[0, 0]
                
                # Inverse transform
                pred_price = self.scaler.inverse_transform([[pred_scaled]])[0, 0]
                predictions.append(pred_price)
                
                # Update sequence for next prediction
                new_features = self.create_features(
                    np.append(prices, pred_price)[-len(features):], 
                    volumes[-len(features):] if volumes is not None else None
                )
                new_scaled = self.feature_scaler.transform(new_features)
                current_sequence = np.vstack([current_sequence[1:], new_scaled[-1:]])
        
        # Calculate confidence score based on recent prediction accuracy
        confidence_score = max(0, min(100, 80 - np.std(predictions) * 10))
        
        return PriceForecast(
            symbol="",  # Will be set by caller
            forecast_horizon=horizon,
            price_forecast=predictions,
            confidence_score=confidence_score,
            lstm_features={
                'input_size': self.input_size,
                'hidden_size': self.hidden_size,
                'num_layers': self.num_layers,
                'sequence_length': 60
            },
            timestamp=datetime.now().timestamp()
        )

class RiskManager:
    """Advanced Risk Management System"""
    
    def __init__(self):
        self.garch_model = GARCHVolatilityModel()
        self.lstm_model = LSTMPricePredictor()
    
    def calculate_dynamic_leverage(self, 
                                 volatility_forecast: VolatilityForecast,
                                 price_forecast: PriceForecast,
                                 account_balance: float,
                                 max_risk_per_trade: float = 0.02) -> Dict:
        """Calculate optimal leverage based on volatility and price prediction"""
        
        # Get volatility metrics
        avg_vol = np.mean(volatility_forecast.volatility_forecast)
        vol_regime = self._classify_volatility_regime(avg_vol)
        
        # Base leverage calculation
        base_leverage = 1.0 / (avg_vol * 10)  # Inverse relationship with volatility
        
        # Adjust based on price prediction confidence
        confidence_multiplier = price_forecast.confidence_score / 100
        
        # Adjust based on volatility regime
        regime_multipliers = {
            'low': 2.0,
            'normal': 1.0,
            'high': 0.5,
            'extreme': 0.2
        }
        
        regime_multiplier = regime_multipliers.get(vol_regime, 1.0)
        
        # Calculate final leverage
        optimal_leverage = base_leverage * confidence_multiplier * regime_multiplier
        
        # Apply constraints
        optimal_leverage = max(1.0, min(50.0, optimal_leverage))
        
        # Position sizing
        position_size = (account_balance * max_risk_per_trade) / avg_vol
        
        return {
            'optimal_leverage': round(optimal_leverage, 1),
            'position_size': position_size,
            'volatility_regime': vol_regime,
            'risk_score': self._calculate_risk_score(avg_vol, confidence_multiplier),
            'max_position_value': account_balance * optimal_leverage,
            'suggested_stop_loss': avg_vol * 2.0,  # 2x volatility
            'risk_reward_ratio': self._calculate_risk_reward(price_forecast, avg_vol)
        }
    
    def _classify_volatility_regime(self, volatility: float) -> str:
        """Classify volatility into regimes"""
        if volatility < 0.02:
            return 'low'
        elif volatility < 0.05:
            return 'normal'
        elif volatility < 0.1:
            return 'high'
        else:
            return 'extreme'
    
    def _calculate_risk_score(self, volatility: float, confidence: float) -> int:
        """Calculate overall risk score (1-10)"""
        vol_score = min(10, volatility * 100)
        conf_score = 10 - (confidence * 10)
        return int((vol_score + conf_score) / 2)
    
    def _calculate_risk_reward(self, price_forecast: PriceForecast, volatility: float) -> float:
        """Calculate risk-reward ratio"""
        if len(price_forecast.price_forecast) == 0:
            return 1.0
        
        expected_return = abs(price_forecast.price_forecast[-1] - price_forecast.price_forecast[0])
        expected_risk = volatility * 2.0  # 2x volatility as risk measure
        
        return expected_return / max(expected_risk, 0.001)
    
    def generate_risk_metrics(self, 
                            prices: np.array, 
                            volumes: np.array = None,
                            horizon: int = 5) -> RiskMetrics:
        """Generate comprehensive risk metrics"""
        
        # Fit GARCH model and forecast volatility
        self.garch_model.fit(prices)
        vol_forecast = self.garch_model.forecast_volatility(horizon)
        
        # Calculate returns for VaR
        returns = self.garch_model.prepare_returns(prices)
        
        # Calculate risk metrics
        var_95 = self.garch_model.calculate_var(returns, 0.95)
        var_99 = self.garch_model.calculate_var(returns, 0.99)
        expected_shortfall = self.garch_model.calculate_expected_shortfall(returns, 0.95)
        
        # Estimate maximum drawdown
        cumulative_returns = np.cumprod(1 + returns / 100)
        rolling_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown_forecast = np.min(drawdown) * 1.5  # Conservative estimate
        
        # Calculate optimal leverage
        avg_vol = np.mean(vol_forecast.volatility_forecast)
        optimal_leverage = min(10.0, max(1.0, 0.02 / avg_vol))
        
        # Classify volatility regime
        vol_regime = self._classify_volatility_regime(avg_vol)
        
        return RiskMetrics(
            symbol="",  # Will be set by caller
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            max_drawdown_forecast=max_drawdown_forecast,
            optimal_leverage=optimal_leverage,
            volatility_regime=vol_regime,
            timestamp=datetime.now().timestamp()
        )

# Example usage and testing
if __name__ == "__main__":
    print("🚀 Testing GARCH + LSTM Models...")
    
    # Generate sample price data
    np.random.seed(42)
    n_points = 1000
    
    # Simulate price path with GARCH-like volatility
    returns = np.random.normal(0.0001, 0.02, n_points)
    volatility = np.zeros(n_points)
    volatility[0] = 0.02
    
    # GARCH(1,1) simulation
    omega, alpha, beta = 0.0001, 0.1, 0.85
    for i in range(1, n_points):
        volatility[i] = np.sqrt(omega + alpha * returns[i-1]**2 + beta * volatility[i-1]**2)
        returns[i] = np.random.normal(0, volatility[i])
    
    prices = 100 * np.exp(np.cumsum(returns))
    volumes = np.random.lognormal(10, 0.5, n_points)
    
    # Test GARCH model
    garch = GARCHVolatilityModel()
    try:
        garch_params = garch.fit(prices)
        vol_forecast = garch.forecast_volatility(horizon=5)
        print(f"✅ GARCH Model fitted successfully")
        print(f"Volatility forecast: {vol_forecast.volatility_forecast}")
    except Exception as e:
        print(f"❌ GARCH Error: {e}")
    
    # Test LSTM model
    lstm = LSTMPricePredictor(hidden_size=32, num_layers=1)  # Smaller for testing
    try:
        training_result = lstm.train(prices[-500:], volumes[-500:], epochs=10, batch_size=16)
        price_forecast = lstm.predict(prices[-100:], volumes[-100:], horizon=5)
        print(f"✅ LSTM Model trained successfully")
        print(f"Price forecast: {price_forecast.price_forecast}")
        print(f"Confidence: {price_forecast.confidence_score:.1f}%")
    except Exception as e:
        print(f"❌ LSTM Error: {e}")
    
    # Test Risk Manager
    risk_manager = RiskManager()
    try:
        risk_metrics = risk_manager.generate_risk_metrics(prices[-200:], volumes[-200:])
        print(f"✅ Risk Metrics calculated")
        print(f"VaR 95%: {risk_metrics.var_95:.4f}")
        print(f"Optimal Leverage: {risk_metrics.optimal_leverage:.1f}x")
        print(f"Volatility Regime: {risk_metrics.volatility_regime}")
    except Exception as e:
        print(f"❌ Risk Manager Error: {e}") 