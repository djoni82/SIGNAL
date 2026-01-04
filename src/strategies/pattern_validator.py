# src/strategies/pattern_validator.py
import numpy as np
from typing import Dict, List
import hashlib
import logging

logger = logging.getLogger(__name__)

class PatternValidator:
    def __init__(self, historical_patterns: Dict):
        self.historical_patterns = historical_patterns
        self.similarity_cache = {}
        
    def validate_signal(self, symbol: str, current_pattern: Dict, current_price: float, **kwargs) -> Dict:
        """Validate signal via searching similar patterns"""
        
        if symbol not in self.historical_patterns:
            return {'confidence_boost': 0, 'historical_win_rate': 0.5}
        
        hist_patterns = self.historical_patterns[symbol]
        
        # Find similar patterns using DTW
        similar_patterns = self._find_similar_patterns_dtw(current_pattern, hist_patterns)
        
        if len(similar_patterns) < 3:
            return {'confidence_boost': 0, 'historical_win_rate': 0.5}
        
        # Calculate historical performance
        outcomes = [p['outcome'] for p in similar_patterns]
        win_rate = sum(1 for o in outcomes if o > 0) / len(outcomes)
        avg_return = np.mean(outcomes)
        
        # Calculate confidence boost (Original logic)
        if win_rate > 0.6 and avg_return > 0.5:
            confidence_boost = min(0.3, win_rate * avg_return / 10)
        elif win_rate < 0.4 or avg_return < -0.5:
            confidence_boost = -0.1
        else:
            confidence_boost = 0.0
            
        return {
            'confidence_boost': confidence_boost,
            'historical_win_rate': win_rate,
            'historical_avg_return': avg_return,
            'pattern_count': len(similar_patterns),
            'similarity_score': np.mean([p['similarity'] for p in similar_patterns])
        }
    
    def _find_similar_patterns_dtw(self, current: Dict, historical: List[Dict], threshold: float = 0.7) -> List[Dict]:
        """Search similar patterns using DTW (Simplified Euclidean as in original)"""
        similar = []
        
        for hist in historical:
            # Cache key
            cache_key = f"{hash(frozenset(current.items()))}_{hash(frozenset(hist['features'].items()))}"
            
            if cache_key in self.similarity_cache:
                similarity = self.similarity_cache[cache_key]
            else:
                similarity = self._calculate_dtw_similarity(current, hist['features'])
                self.similarity_cache[cache_key] = similarity
            
            if similarity > threshold:
                similar.append({
                    'features': hist['features'],
                    'outcome': hist['outcome'],
                    'similarity': similarity
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:10]
    
    def _calculate_dtw_similarity(self, pattern1: Dict, pattern2: Dict) -> float:
        """Calculate similarity via DTW (simplified version of original)"""
        try:
            seq1 = np.array(list(pattern1.values()))
            seq2 = np.array(list(pattern2.values()))
            
            if len(seq1) == len(seq2):
                # Use Euclidean distance as base
                distance = np.linalg.norm(seq1 - seq2)
                max_distance = np.linalg.norm(np.ones_like(seq1) * np.max([np.abs(seq1), np.abs(seq2)]))
                similarity = 1 - (distance / (max_distance + 1e-10))
                return float(similarity)
            else:
                return 0.0
        except Exception as e:
            logger.debug(f"DTW Calc error: {e}")
            return 0.0
