# tests/test_ml_engine.py
"""
Unit tests for Real ML Engine
"""
import pytest
import numpy as np
import pandas as pd
from src.strategies.ml_engine_real import RealMLEngine

class TestRealMLEngine:
    """Tests for ML ensemble"""
    
    def test_initialization(self):
        """Test ML engine initializes correctly"""
        engine = RealMLEngine()
        assert engine is not None
        assert 'xgb' in engine.models
        assert 'lgbm' in engine.models
        assert 'catboost' in engine.models
    
    def test_predict_without_training(self, sample_features):
        """Untrained model should return neutral 0.5"""
        engine = RealMLEngine()
        prob = engine.predict_probability(sample_features)
        assert prob == 0.5
    
    def test_train_models(self, sample_features):
        """Test model training"""
        engine = RealMLEngine()
        
        # Create dummy training data
        n_samples = 100
        X_train = pd.DataFrame([sample_features] * n_samples)
        y_train = pd.Series(np.random.randint(0, 2, n_samples))
        
        X_val = pd.DataFrame([sample_features] * 20)
        y_val = pd.Series(np.random.randint(0, 2, 20))
        
        # Train (this will take a moment)
        engine.train_models(X_train, y_train, X_val, y_val)
        
        # After training, models should exist
        assert engine.models['xgb'] is not None
        assert engine.models['lgbm'] is not None
        assert engine.models['catboost'] is not None
    
    def test_predict_probability_range(self, sample_features):
        """Predictions should be in [0, 1] range"""
        engine = RealMLEngine()
        
        # Even without training
        prob = engine.predict_probability(sample_features)
        assert 0.0 <= prob <= 1.0
    
    def test_update_weights(self):
        """Test dynamic weight updating"""
        engine = RealMLEngine()
        
        new_performances = {
            'xgb': 0.85,
            'lgbm': 0.78,
            'catboost': 0.82
        }
        
        engine.update_weights(new_performances)
        
        # Weights should sum to 1.0
        total_weight = sum(engine.model_weights.values())
        assert abs(total_weight - 1.0) < 0.01
