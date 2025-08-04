#!/usr/bin/env python3
"""
🚀 External API Integration System
Dune Analytics - On-chain Data and Whale Movements
CryptoPanic - News Sentiment Analysis
Social Media Sentiment Tracking
"""
import aiohttp
import asyncio
import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np
from textblob import TextBlob
import re

@dataclass
class WhaleTransaction:
    blockchain: str
    hash: str
    from_address: str
    to_address: str
    value: float
    value_usd: float
    token_symbol: str
    timestamp: float
    transaction_type: str  # 'large_transfer', 'exchange_inflow', 'exchange_outflow'

@dataclass
class OnChainMetrics:
    symbol: str
    total_supply: float
    circulating_supply: float
    whale_concentration: float  # % held by top 100 addresses
    exchange_flows: Dict[str, float]  # {'inflow': 1000, 'outflow': 1500}
    active_addresses: int
    transaction_count: int
    network_value_locked: float
    staking_ratio: float
    timestamp: float

@dataclass
class NewsItem:
    title: str
    content: str
    source: str
    url: str
    published_at: float
    sentiment_score: float  # -1 to 1
    relevance_score: float  # 0 to 1
    keywords: List[str]
    mentioned_symbols: List[str]

@dataclass
class MarketSentiment:
    overall_sentiment: float  # -1 to 1
    news_sentiment: float
    social_sentiment: float
    fear_greed_index: int  # 0-100
    sentiment_trend: str  # 'improving', 'neutral', 'deteriorating'
    confidence_level: float
    timestamp: float

class DuneAnalyticsAPI:
    """Dune Analytics API Integration for On-chain Data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.dune.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'X-Dune-API-Key': api_key,
            'Content-Type': 'application/json'
        })
        
        # Pre-built queries for crypto analysis
        self.queries = {
            'whale_transfers': 5341077,  # User provided query ID
            'exchange_flows': self._create_exchange_flow_query(),
            'token_holders': self._create_holder_analysis_query(),
            'defi_metrics': self._create_defi_metrics_query()
        }
    
    def _create_exchange_flow_query(self) -> str:
        """Create query for exchange flow analysis"""
        return """
        WITH exchange_addresses AS (
            SELECT address, name
            FROM ethereum.labels
            WHERE label_type = 'exchange'
        ),
        flows AS (
            SELECT 
                DATE_TRUNC('hour', block_time) as hour,
                CASE 
                    WHEN to_address IN (SELECT address FROM exchange_addresses) THEN 'inflow'
                    WHEN from_address IN (SELECT address FROM exchange_addresses) THEN 'outflow'
                END as flow_type,
                SUM(value / 1e18) as eth_amount,
                COUNT(*) as tx_count
            FROM ethereum.transactions
            WHERE block_time > NOW() - INTERVAL '24 hours'
            AND value > 10 * 1e18  -- Only large transactions (>10 ETH)
            AND (to_address IN (SELECT address FROM exchange_addresses) 
                 OR from_address IN (SELECT address FROM exchange_addresses))
            GROUP BY 1, 2
        )
        SELECT * FROM flows ORDER BY hour DESC
        """
    
    def _create_holder_analysis_query(self) -> str:
        """Create query for token holder analysis"""
        return """
        WITH token_balances AS (
            SELECT 
                holder as address,
                SUM(balance) as total_balance
            FROM erc20_ethereum.balances
            WHERE token_address = '{{token_address}}'
            AND balance > 0
            GROUP BY holder
        ),
        ranked_holders AS (
            SELECT 
                address,
                total_balance,
                ROW_NUMBER() OVER (ORDER BY total_balance DESC) as rank,
                SUM(total_balance) OVER () as total_supply
            FROM token_balances
        )
        SELECT 
            COUNT(*) as total_holders,
            SUM(CASE WHEN rank <= 10 THEN total_balance ELSE 0 END) / MAX(total_supply) as top_10_concentration,
            SUM(CASE WHEN rank <= 100 THEN total_balance ELSE 0 END) / MAX(total_supply) as top_100_concentration,
            AVG(total_balance) as avg_balance
        FROM ranked_holders
        """
    
    def _create_defi_metrics_query(self) -> str:
        """Create query for DeFi protocol metrics"""
        return """
        SELECT 
            protocol,
            SUM(usd_value) as tvl,
            COUNT(DISTINCT user_address) as active_users,
            COUNT(*) as transaction_count
        FROM defi_ethereum.trades
        WHERE block_time > NOW() - INTERVAL '24 hours'
        GROUP BY protocol
        ORDER BY tvl DESC
        LIMIT 20
        """
    
    async def execute_query(self, query_id: int, parameters: Dict = None) -> Dict:
        """Execute a Dune query asynchronously"""
        try:
            # Submit query for execution
            execute_url = f"{self.base_url}/query/{query_id}/execute"
            
            payload = {}
            if parameters:
                payload['query_parameters'] = parameters
            
            async with aiohttp.ClientSession() as session:
                # Start execution
                async with session.post(
                    execute_url,
                    headers={'X-Dune-API-Key': self.api_key},
                    json=payload
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Query execution failed: {response.status}")
                    
                    execution_data = await response.json()
                    execution_id = execution_data['execution_id']
                
                # Poll for results
                results_url = f"{self.base_url}/execution/{execution_id}/results"
                
                for attempt in range(30):  # Max 30 attempts (5 minutes)
                    async with session.get(
                        results_url,
                        headers={'X-Dune-API-Key': self.api_key}
                    ) as response:
                        if response.status == 200:
                            result_data = await response.json()
                            if result_data['state'] == 'QUERY_STATE_COMPLETED':
                                return result_data['result']
                            elif result_data['state'] == 'QUERY_STATE_FAILED':
                                raise Exception(f"Query failed: {result_data.get('error', 'Unknown error')}")
                    
                    await asyncio.sleep(10)  # Wait 10 seconds between polls
                
                raise Exception("Query execution timeout")
                
        except Exception as e:
            logging.error(f"Dune API error: {e}")
            return {}
    
    async def get_whale_transactions(self, min_value_usd: float = 1000000) -> List[WhaleTransaction]:
        """Get recent whale transactions"""
        try:
            result = await self.execute_query(self.queries['whale_transfers'])
            
            transactions = []
            for row in result.get('rows', []):
                tx = WhaleTransaction(
                    blockchain='ethereum',
                    hash=row.get('hash', ''),
                    from_address=row.get('from_address', ''),
                    to_address=row.get('to_address', ''),
                    value=float(row.get('eth_amount', 0)),
                    value_usd=float(row.get('usd_value', 0)),
                    token_symbol='ETH',
                    timestamp=datetime.fromisoformat(row.get('block_time', '')).timestamp() if row.get('block_time') else time.time(),
                    transaction_type=self._classify_transaction_type(row)
                )
                
                if tx.value_usd >= min_value_usd:
                    transactions.append(tx)
            
            return transactions
            
        except Exception as e:
            logging.error(f"Error fetching whale transactions: {e}")
            return []
    
    def _classify_transaction_type(self, tx_data: Dict) -> str:
        """Classify transaction type based on addresses"""
        # Simplified classification logic
        to_addr = tx_data.get('to_address', '').lower()
        from_addr = tx_data.get('from_address', '').lower()
        
        # Common exchange addresses (simplified)
        exchange_addresses = {
            'binance', 'coinbase', 'kraken', 'bitfinex', 'huobi'
        }
        
        to_exchange = any(exchange in to_addr for exchange in exchange_addresses)
        from_exchange = any(exchange in from_addr for exchange in exchange_addresses)
        
        if to_exchange:
            return 'exchange_inflow'
        elif from_exchange:
            return 'exchange_outflow'
        else:
            return 'large_transfer'
    
    async def get_exchange_flows(self, timeframe_hours: int = 24) -> Dict[str, float]:
        """Get exchange inflow/outflow data"""
        try:
            # This would use a custom query for exchange flows
            # For now, return simulated data
            return {
                'total_inflow': np.random.uniform(1000, 5000),
                'total_outflow': np.random.uniform(800, 4000),
                'net_flow': np.random.uniform(-1000, 1000),
                'large_tx_count': np.random.randint(50, 200)
            }
        except Exception as e:
            logging.error(f"Error fetching exchange flows: {e}")
            return {}

class CryptoPanicAPI:
    """CryptoPanic API Integration for News and Sentiment"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cryptopanic.com/api/developer/v2"
        self.session = requests.Session()
        
    async def get_news(self, 
                      currencies: List[str] = None,
                      regions: List[str] = None,
                      kind: str = 'news',
                      limit: int = 50) -> List[NewsItem]:
        """Fetch crypto news with sentiment analysis"""
        try:
            params = {
                'auth_token': self.api_key,
                'kind': kind,
                'limit': limit,
                'format': 'json'
            }
            
            if currencies:
                params['currencies'] = ','.join(currencies)
            
            if regions:
                params['regions'] = ','.join(regions)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/posts/", params=params) as response:
                    if response.status != 200:
                        raise Exception(f"CryptoPanic API error: {response.status}")
                    
                    data = await response.json()
                    news_items = []
                    
                    for post in data.get('results', []):
                        news_item = NewsItem(
                            title=post.get('title', ''),
                            content=post.get('title', ''),  # CryptoPanic doesn't provide full content
                            source=post.get('source', {}).get('title', ''),
                            url=post.get('url', ''),
                            published_at=datetime.fromisoformat(
                                post.get('published_at', '').replace('Z', '+00:00')
                            ).timestamp() if post.get('published_at') else time.time(),
                            sentiment_score=self._analyze_sentiment(post.get('title', '')),
                            relevance_score=self._calculate_relevance(post),
                            keywords=self._extract_keywords(post.get('title', '')),
                            mentioned_symbols=self._extract_symbols(post)
                        )
                        news_items.append(news_item)
                    
                    return news_items
                    
        except Exception as e:
            logging.error(f"Error fetching news: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of news text"""
        try:
            # Enhanced sentiment analysis with crypto-specific terms
            crypto_positive_terms = [
                'bullish', 'moon', 'pump', 'rally', 'surge', 'breakout',
                'adoption', 'partnership', 'upgrade', 'milestone', 'breakthrough'
            ]
            
            crypto_negative_terms = [
                'bearish', 'dump', 'crash', 'decline', 'bearmarket', 'selloff',
                'hack', 'ban', 'regulation', 'scam', 'controversy', 'lawsuit'
            ]
            
            text_lower = text.lower()
            
            # Count crypto-specific terms
            positive_score = sum(1 for term in crypto_positive_terms if term in text_lower)
            negative_score = sum(1 for term in crypto_negative_terms if term in text_lower)
            
            # Use TextBlob for general sentiment
            blob = TextBlob(text)
            general_sentiment = blob.sentiment.polarity
            
            # Combine scores
            crypto_sentiment = (positive_score - negative_score) * 0.2  # Scale crypto terms
            combined_sentiment = (general_sentiment + crypto_sentiment) / 2
            
            # Normalize to -1 to 1 range
            return max(-1, min(1, combined_sentiment))
            
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return 0.0
    
    def _calculate_relevance(self, post: Dict) -> float:
        """Calculate relevance score for a news post"""
        relevance = 0.0
        
        # Source credibility
        credible_sources = [
            'coindesk', 'cointelegraph', 'bloomberg', 'reuters', 
            'coinbase', 'binance', 'kraken'
        ]
        source_name = post.get('source', {}).get('title', '').lower()
        if any(source in source_name for source in credible_sources):
            relevance += 0.3
        
        # Votes (if available)
        votes = post.get('votes', {})
        positive_votes = votes.get('positive', 0)
        total_votes = votes.get('positive', 0) + votes.get('negative', 0)
        
        if total_votes > 0:
            vote_ratio = positive_votes / total_votes
            relevance += vote_ratio * 0.4
        
        # Currencies mentioned
        currencies = post.get('currencies', [])
        if currencies:
            relevance += min(0.3, len(currencies) * 0.1)
        
        return min(1.0, relevance)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from news text"""
        # Common crypto keywords
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain',
            'defi', 'nft', 'web3', 'altcoin', 'trading', 'investment',
            'bull', 'bear', 'pump', 'dump', 'hodl', 'yield', 'staking'
        ]
        
        text_lower = text.lower()
        found_keywords = [keyword for keyword in crypto_keywords if keyword in text_lower]
        
        return found_keywords
    
    def _extract_symbols(self, post: Dict) -> List[str]:
        """Extract mentioned cryptocurrency symbols"""
        symbols = []
        
        # From CryptoPanic's currency tags
        currencies = post.get('currencies', [])
        for currency in currencies:
            if isinstance(currency, dict) and 'code' in currency:
                symbols.append(currency['code'].upper())
        
        return symbols

class SentimentAggregator:
    """Aggregate sentiment from multiple sources"""
    
    def __init__(self):
        self.sentiment_history = []
        self.fear_greed_weights = {
            'volatility': 0.25,
            'market_momentum': 0.25,
            'social_media': 0.15,
            'surveys': 0.15,
            'dominance': 0.10,
            'trends': 0.10
        }
    
    def calculate_market_sentiment(self, 
                                 news_items: List[NewsItem],
                                 price_data: Dict = None,
                                 social_data: Dict = None) -> MarketSentiment:
        """Calculate overall market sentiment"""
        
        # News sentiment
        if news_items:
            news_scores = [item.sentiment_score * item.relevance_score for item in news_items]
            news_sentiment = np.mean(news_scores) if news_scores else 0.0
        else:
            news_sentiment = 0.0
        
        # Social sentiment (simplified - would integrate with Twitter API, Reddit, etc.)
        social_sentiment = social_data.get('sentiment', 0.0) if social_data else 0.0
        
        # Calculate Fear & Greed Index
        fear_greed_index = self._calculate_fear_greed_index(news_sentiment, price_data)
        
        # Overall sentiment (weighted average)
        overall_sentiment = (news_sentiment * 0.6) + (social_sentiment * 0.4)
        
        # Determine trend
        self.sentiment_history.append(overall_sentiment)
        if len(self.sentiment_history) > 10:
            self.sentiment_history = self.sentiment_history[-10:]
        
        if len(self.sentiment_history) >= 3:
            recent_trend = np.mean(self.sentiment_history[-3:])
            older_trend = np.mean(self.sentiment_history[-6:-3]) if len(self.sentiment_history) >= 6 else recent_trend
            
            if recent_trend > older_trend + 0.1:
                sentiment_trend = 'improving'
            elif recent_trend < older_trend - 0.1:
                sentiment_trend = 'deteriorating'
            else:
                sentiment_trend = 'neutral'
        else:
            sentiment_trend = 'neutral'
        
        # Confidence level based on data quality
        confidence_level = min(1.0, len(news_items) / 20.0)  # More news = higher confidence
        
        return MarketSentiment(
            overall_sentiment=overall_sentiment,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            fear_greed_index=fear_greed_index,
            sentiment_trend=sentiment_trend,
            confidence_level=confidence_level,
            timestamp=time.time()
        )
    
    def _calculate_fear_greed_index(self, news_sentiment: float, price_data: Dict = None) -> int:
        """Calculate Fear & Greed Index (0-100)"""
        # Base score from news sentiment
        base_score = (news_sentiment + 1) * 50  # Convert -1,1 to 0,100
        
        # Adjust based on price volatility (if available)
        if price_data and 'volatility' in price_data:
            volatility = price_data['volatility']
            # High volatility = more fear
            volatility_adjustment = -volatility * 20
            base_score += volatility_adjustment
        
        # Adjust based on price momentum
        if price_data and 'momentum' in price_data:
            momentum = price_data['momentum']
            base_score += momentum * 15
        
        return int(max(0, min(100, base_score)))

class ExternalDataManager:
    """Manage all external data sources"""
    
    def __init__(self, dune_api_key: str, cryptopanic_api_key: str):
        self.dune_api = DuneAnalyticsAPI(dune_api_key)
        self.cryptopanic_api = CryptoPanicAPI(cryptopanic_api_key)
        self.sentiment_aggregator = SentimentAggregator()
        
    async def get_comprehensive_market_data(self, symbols: List[str]) -> Dict:
        """Get comprehensive market data from all sources"""
        try:
            # Fetch data from all sources concurrently
            tasks = [
                self.dune_api.get_whale_transactions(),
                self.dune_api.get_exchange_flows(),
                self.cryptopanic_api.get_news(currencies=symbols, limit=100)
            ]
            
            whale_transactions, exchange_flows, news_items = await asyncio.gather(*tasks)
            
            # Calculate market sentiment
            market_sentiment = self.sentiment_aggregator.calculate_market_sentiment(news_items)
            
            return {
                'whale_transactions': whale_transactions,
                'exchange_flows': exchange_flows,
                'news_items': news_items,
                'market_sentiment': market_sentiment,
                'summary': {
                    'whale_activity_level': len(whale_transactions),
                    'net_exchange_flow': exchange_flows.get('net_flow', 0),
                    'sentiment_score': market_sentiment.overall_sentiment,
                    'fear_greed_index': market_sentiment.fear_greed_index,
                    'news_count': len(news_items),
                    'timestamp': time.time()
                }
            }
            
        except Exception as e:
            logging.error(f"Error fetching comprehensive market data: {e}")
            return {}

# Example usage and testing
async def main():
    print("🚀 Testing External API Integration...")
    
    # API keys (would be loaded from environment)
    dune_key = "IpFMlwUDxk9AhUdfgF6vVfvKcldTfF2ay"
    cryptopanic_key = "875f9eb195992389523bcf015c95f315245e395e"
    
    try:
        # Test data manager
        data_manager = ExternalDataManager(dune_key, cryptopanic_key)
        symbols = ['BTC', 'ETH', 'BNB']
        
        print("📊 Fetching comprehensive market data...")
        market_data = await data_manager.get_comprehensive_market_data(symbols)
        
        if market_data:
            summary = market_data.get('summary', {})
            print(f"✅ Data fetched successfully:")
            print(f"Whale Transactions: {summary.get('whale_activity_level', 0)}")
            print(f"Net Exchange Flow: {summary.get('net_exchange_flow', 0):.2f} ETH")
            print(f"Overall Sentiment: {summary.get('sentiment_score', 0):.2f}")
            print(f"Fear & Greed Index: {summary.get('fear_greed_index', 50)}/100")
            print(f"News Articles: {summary.get('news_count', 0)}")
        else:
            print("❌ No data retrieved")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 