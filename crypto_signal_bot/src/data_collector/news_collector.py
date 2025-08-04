"""
News Collector for CryptoAlphaPro
Real-time crypto news and social sentiment collection
"""

import aiohttp
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import re
from urllib.parse import urlencode
import hashlib


class NewsCollector:
    """Real-time crypto news and social sentiment collector"""
    
    def __init__(self, config):
        self.config = config
        self.cryptopanic_config = config.get('cryptopanic', {})
        self.twitter_config = config.get('twitter', {})
        
        # Rate limiting
        self.cryptopanic_last_request = 0
        self.twitter_last_request = 0
        self.min_interval = 60  # 1 minute between requests
        
        # Cache to avoid duplicate news
        self.processed_news = set()
        self.cache_timeout = 3600  # 1 hour
        
        # Crypto symbols mapping
        self.symbol_keywords = {
            'BTC': ['bitcoin', 'btc', 'satoshi'],
            'ETH': ['ethereum', 'eth', 'ether', 'vitalik'],
            'BNB': ['binance', 'bnb', 'cz'],
            'ADA': ['cardano', 'ada'],
            'SOL': ['solana', 'sol'],
            'XRP': ['ripple', 'xrp'],
            'DOT': ['polkadot', 'dot'],
            'AVAX': ['avalanche', 'avax'],
            'MATIC': ['polygon', 'matic'],
            'ATOM': ['cosmos', 'atom']
        }
        
    async def get_crypto_news(self) -> Optional[List[Dict]]:
        """Get crypto news from CryptoPanic"""
        try:
            # Rate limiting check
            current_time = time.time()
            if current_time - self.cryptopanic_last_request < self.min_interval:
                return None
            
            if not self.cryptopanic_config.get('api_key'):
                logger.warning("⚠️  CryptoPanic API key not configured")
                return None
            
            # Build API request
            base_url = self.cryptopanic_config.get('base_url', 'https://cryptopanic.com/api/v1')
            params = {
                'auth_token': self.cryptopanic_config['api_key'],
                'kind': 'news',
                'filter': 'hot',
                'public': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/posts/?{urlencode(params)}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.cryptopanic_last_request = current_time
                        
                        news_items = self._process_cryptopanic_data(data)
                        logger.info(f"📰 Fetched {len(news_items)} news items from CryptoPanic")
                        return news_items
                    else:
                        logger.error(f"❌ CryptoPanic API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Error fetching crypto news: {e}")
            return None
    
    def _process_cryptopanic_data(self, data: Dict) -> List[Dict]:
        """Process CryptoPanic API response"""
        news_items = []
        
        try:
            results = data.get('results', [])
            
            for item in results:
                # Skip if already processed
                item_id = item.get('id')
                if item_id in self.processed_news:
                    continue
                
                # Extract relevant information
                title = item.get('title', '')
                url = item.get('url', '')
                source = item.get('domain', '')
                published_at = item.get('published_at', '')
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()
                
                # Extract symbols from title and content
                affected_symbols = self._extract_symbols_from_text(title)
                
                # Calculate basic sentiment score
                sentiment_score = self._calculate_basic_sentiment(title)
                
                # Determine importance score
                importance_score = self._calculate_importance(item)
                
                news_item = {
                    'id': item_id,
                    'title': title,
                    'url': url,
                    'source': source,
                    'published_at': timestamp,
                    'symbols': affected_symbols,
                    'sentiment_score': sentiment_score,
                    'importance_score': importance_score,
                    'votes': {
                        'negative': item.get('votes', {}).get('negative', 0),
                        'neutral': item.get('votes', {}).get('neutral', 0),
                        'positive': item.get('votes', {}).get('positive', 0),
                        'important': item.get('votes', {}).get('important', 0)
                    },
                    'metadata': {
                        'kind': item.get('kind'),
                        'currencies': [c.get('code') for c in item.get('currencies', [])],
                        'created_at': item.get('created_at')
                    }
                }
                
                news_items.append(news_item)
                self.processed_news.add(item_id)
            
            # Clean old processed items
            self._clean_processed_cache()
            
            return news_items
            
        except Exception as e:
            logger.error(f"❌ Error processing CryptoPanic data: {e}")
            return []
    
    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """Extract cryptocurrency symbols from text"""
        text_lower = text.lower()
        found_symbols = []
        
        for symbol, keywords in self.symbol_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_symbols.append(symbol)
        
        # If no specific symbols found, default to BTC
        return found_symbols if found_symbols else ['BTC']
    
    def _calculate_basic_sentiment(self, text: str) -> float:
        """Calculate basic sentiment score from text"""
        # Positive words
        positive_words = [
            'bull', 'bullish', 'moon', 'rocket', 'pump', 'surge', 'rally',
            'breakthrough', 'adoption', 'institutional', 'partnership',
            'upgrade', 'improvement', 'positive', 'gains', 'rise', 'up'
        ]
        
        # Negative words
        negative_words = [
            'bear', 'bearish', 'crash', 'dump', 'plunge', 'fall', 'drop',
            'regulation', 'ban', 'hack', 'scam', 'fraud', 'concern',
            'warning', 'risk', 'negative', 'losses', 'down', 'decline'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_importance(self, item: Dict) -> float:
        """Calculate importance score based on votes and source"""
        try:
            votes = item.get('votes', {})
            important_votes = votes.get('important', 0)
            total_votes = sum(votes.values())
            
            # Base importance from votes
            importance = important_votes / max(total_votes, 1)
            
            # Boost for known important sources
            important_sources = ['coindesk.com', 'cointelegraph.com', 'bloomberg.com', 'reuters.com']
            source = item.get('domain', '').lower()
            
            if any(imp_source in source for imp_source in important_sources):
                importance += 0.2
            
            return min(1.0, importance)
            
        except:
            return 0.5
    
    def _clean_processed_cache(self):
        """Clean old processed news IDs"""
        # This is a simple cleanup - in production, you'd want to track timestamps
        if len(self.processed_news) > 1000:
            # Keep only recent 500 items
            self.processed_news = set(list(self.processed_news)[-500:])
    
    async def get_twitter_sentiment(self) -> Optional[List[Dict]]:
        """Get Twitter sentiment data"""
        try:
            # Rate limiting check
            current_time = time.time()
            if current_time - self.twitter_last_request < self.min_interval:
                return None
            
            if not self.twitter_config.get('bearer_token'):
                logger.warning("⚠️  Twitter Bearer Token not configured")
                return None
            
            # Get sentiment for monitored accounts
            accounts = self.twitter_config.get('accounts_to_monitor', [])
            sentiment_data = []
            
            async with aiohttp.ClientSession() as session:
                for account in accounts:
                    try:
                        account_sentiment = await self._get_account_sentiment(session, account)
                        if account_sentiment:
                            sentiment_data.extend(account_sentiment)
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to get sentiment for {account}: {e}")
            
            self.twitter_last_request = current_time
            
            if sentiment_data:
                logger.info(f"💭 Fetched sentiment data for {len(sentiment_data)} tweets")
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching Twitter sentiment: {e}")
            return None
    
    async def _get_account_sentiment(self, session: aiohttp.ClientSession, account: str) -> List[Dict]:
        """Get sentiment data for a specific Twitter account"""
        try:
            # Twitter API v2 endpoint
            url = f"https://api.twitter.com/2/users/by/username/{account}"
            headers = {
                'Authorization': f"Bearer {self.twitter_config['bearer_token']}"
            }
            
            # Get user info first
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"⚠️  Twitter API error for {account}: {response.status}")
                    return []
                
                user_data = await response.json()
                user_id = user_data['data']['id']
            
            # Get recent tweets
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                'max_results': 10,
                'tweet.fields': 'created_at,public_metrics,context_annotations'
            }
            
            async with session.get(tweets_url, headers=headers, params=params, timeout=10) as response:
                if response.status != 200:
                    return []
                
                tweets_data = await response.json()
                tweets = tweets_data.get('data', [])
                
                sentiment_items = []
                for tweet in tweets:
                    # Extract symbols and sentiment
                    text = tweet.get('text', '')
                    symbols = self._extract_symbols_from_text(text)
                    sentiment_score = self._calculate_basic_sentiment(text)
                    
                    # Skip neutral tweets
                    if abs(sentiment_score) < 0.1:
                        continue
                    
                    metrics = tweet.get('public_metrics', {})
                    
                    for symbol in symbols:
                        sentiment_items.append({
                            'source': 'twitter',
                            'account': account,
                            'symbol': symbol,
                            'sentiment_score': sentiment_score,
                            'volume_mentions': 1,
                            'timestamp': datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                            'metadata': {
                                'tweet_id': tweet['id'],
                                'text': text[:100],  # First 100 chars
                                'retweet_count': metrics.get('retweet_count', 0),
                                'like_count': metrics.get('like_count', 0),
                                'reply_count': metrics.get('reply_count', 0)
                            }
                        })
                
                return sentiment_items
                
        except Exception as e:
            logger.error(f"❌ Error getting sentiment for {account}: {e}")
            return []
    
    async def get_trending_topics(self) -> Optional[List[Dict]]:
        """Get trending crypto topics (fallback method)"""
        try:
            # This would integrate with other news sources or trending APIs
            # For now, return mock trending topics
            trending = [
                {
                    'topic': 'Bitcoin ETF',
                    'symbol': 'BTC',
                    'mentions': 150,
                    'sentiment_score': 0.3,
                    'importance': 0.8
                },
                {
                    'topic': 'Ethereum Upgrade',
                    'symbol': 'ETH',
                    'mentions': 89,
                    'sentiment_score': 0.6,
                    'importance': 0.7
                }
            ]
            
            return trending
            
        except Exception as e:
            logger.error(f"❌ Error getting trending topics: {e}")
            return None
    
    async def analyze_market_sentiment(self, news_items: List[Dict]) -> Dict[str, float]:
        """Analyze overall market sentiment from news"""
        try:
            symbol_sentiments = {}
            
            for item in news_items:
                symbols = item.get('symbols', [])
                sentiment = item.get('sentiment_score', 0)
                importance = item.get('importance_score', 0.5)
                
                # Weight sentiment by importance
                weighted_sentiment = sentiment * importance
                
                for symbol in symbols:
                    if symbol not in symbol_sentiments:
                        symbol_sentiments[symbol] = []
                    symbol_sentiments[symbol].append(weighted_sentiment)
            
            # Calculate average sentiment for each symbol
            final_sentiments = {}
            for symbol, sentiments in symbol_sentiments.items():
                if sentiments:
                    final_sentiments[symbol] = sum(sentiments) / len(sentiments)
            
            return final_sentiments
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market sentiment: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get news collector performance statistics"""
        return {
            'processed_news_count': len(self.processed_news),
            'cryptopanic_last_request': self.cryptopanic_last_request,
            'twitter_last_request': self.twitter_last_request,
            'cache_size': len(self.processed_news)
        } 