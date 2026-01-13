# src/strategies/ml_engine_real.py
"""
Реальный ML движок с ансамблем градиентного бустинга.
Заменяет эвристический MLEngine на XGBoost + LightGBM + CatBoost.
"""
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
import numpy as np
import joblib
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class RealMLEngine:
    """
    Ансамбль из 3 моделей градиентного бустинга.
    Взвешенное голосование для финального предсказания.
    """
    def __init__(self, model_path="models/"):
        self.models = {
            'xgb': None,
            'lgbm': None,
            'catboost': None
        }
        self.feature_columns = []
        # Начальные веса (можно адаптировать динамически)
        self.model_weights = {
            'xgb': 0.4,
            'lgbm': 0.3,
            'catboost': 0.3
        }
        self.model_path = model_path
        self._ensure_model_dir()
        self._load_models()

    def _ensure_model_dir(self):
        """Создает директорию для моделей если не существует"""
        os.makedirs(self.model_path, exist_ok=True)

    def _load_models(self):
        """Загрузка предобученных моделей из файлов"""
        try:
            xgb_path = f"{self.model_path}xgb_model.json"
            lgbm_path = f"{self.model_path}lgbm_model.txt"
            cat_path = f"{self.model_path}catboost_model.cbm"
            feat_path = f"{self.model_path}features.pkl"
            
            if os.path.exists(xgb_path):
                self.models['xgb'] = xgb.XGBClassifier()
                self.models['xgb'].load_model(xgb_path)
                logger.info("✅ XGBoost model loaded")
            
            if os.path.exists(lgbm_path):
                self.models['lgbm'] = lgb.Booster(model_file=lgbm_path)
                logger.info("✅ LightGBM model loaded")
            
            if os.path.exists(cat_path):
                self.models['catboost'] = CatBoostClassifier()
                self.models['catboost'].load_model(cat_path)
                logger.info("✅ CatBoost model loaded")
            
            if os.path.exists(feat_path):
                with open(feat_path, "rb") as f:
                    self.feature_columns = joblib.load(f)
                logger.info(f"✅ Feature schema loaded: {len(self.feature_columns)} features")
                
        except Exception as e:
            logger.warning(f"⚠️  Could not load ML models: {e}. Training needed.")

    def train_models(self, X_train, y_train, X_val, y_val):
        """
        Обучение всех 3 моделей на данных.
        Вызывается из data_pipeline.py
        """
        logger.info("🎓 Starting model training...")
        
        # 1. XGBoost
        logger.info("Training XGBoost...")
        self.models['xgb'] = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.01,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric='logloss',
            random_state=42,
            use_label_encoder=False
        )
        self.models['xgb'].fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        self.models['xgb'].save_model(f"{self.model_path}xgb_model.json")

        # 2. LightGBM
        logger.info("Training LightGBM...")
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.01,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        self.models['lgbm'] = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
        )
        self.models['lgbm'].save_model(f"{self.model_path}lgbm_model.txt")

        # 3. CatBoost
        logger.info("Training CatBoost...")
        self.models['catboost'] = CatBoostClassifier(
            iterations=500,
            depth=6,
            learning_rate=0.01,
            loss_function='Logloss',
            random_seed=42,
            verbose=False
        )
        self.models['catboost'].fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            early_stopping_rounds=50,
            verbose=False
        )
        self.models['catboost'].save_model(f"{self.model_path}catboost_model.cbm")
        
        # Сохраняем список фич для consistency
        self.feature_columns = list(X_train.columns)
        with open(f"{self.model_path}features.pkl", "wb") as f:
            joblib.dump(self.feature_columns, f)
            
        logger.info("✅ All models trained and saved!")

    def predict_probability(self, features: dict) -> float:
        """
        Взвешенное предсказание ансамбля.
        Возвращает вероятность класса 1 (прибыльный сигнал).
        """
        if not any(self.models.values()) or not self.feature_columns:
            logger.warning("Models not trained. Returning neutral 0.5")
            return 0.5

        try:
            # Подготовка вектора фич в правильном порядке
            feature_vector = []
            for col in self.feature_columns:
                feature_vector.append(features.get(col, 0.0))
            
            X = np.array(feature_vector).reshape(1, -1)
            predictions = {}
            
            # XGBoost prediction
            if self.models['xgb']:
                prob = self.models['xgb'].predict_proba(X)[0][1]
                predictions['xgb'] = prob
            
            # LightGBM prediction
            if self.models['lgbm']:
                prob = self.models['lgbm'].predict(X)[0]
                # LightGBM может возвращать raw score, нормализуем sigmoid
                prob = 1 / (1 + np.exp(-prob))
                predictions['lgbm'] = float(prob)

            # CatBoost prediction
            if self.models['catboost']:
                prob = self.models['catboost'].predict_proba(X)[0][1]
                predictions['catboost'] = prob

            # Взвешенное среднее
            if predictions:
                weighted_prob = sum(
                    pred * self.model_weights.get(name, 0.33)
                    for name, pred in predictions.items()
                )
                return float(np.clip(weighted_prob, 0.0, 1.0))
                
        except Exception as e:
            logger.error(f"ML Prediction Error: {e}")
            
        return 0.5

    def update_weights(self, model_performances: Dict[str, float]):
        """
        Динамическое обновление весов на основе performance.
        model_performances = {'xgb': 0.78, 'lgbm': 0.82, 'catboost': 0.75}
        """
        total = sum(model_performances.values())
        if total > 0:
            for model_name, perf in model_performances.items():
                self.model_weights[model_name] = perf / total
            logger.info(f"Updated weights: {self.model_weights}")
