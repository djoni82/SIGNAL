"""
Prometheus Metrics for CryptoAlphaPro
Collects and exposes system metrics for monitoring
"""

import time
from typing import Dict, Any, Optional
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Info
from loguru import logger
from datetime import datetime


class PrometheusMetrics:
    """Prometheus metrics collector"""
    
    def __init__(self, port: int = 9090):
        self.port = port
        self.server_started = False
        
        # System metrics
        self.system_info = Info('cryptoalphapro_system', 'System information')
        self.uptime = Gauge('cryptoalphapro_uptime_seconds', 'System uptime in seconds')
        self.start_time = time.time()
        
        # Signal metrics
        self.signals_generated = Counter('cryptoalphapro_signals_total', 'Total signals generated', ['pair', 'action'])
        self.signal_confidence = Histogram('cryptoalphapro_signal_confidence', 'Signal confidence distribution', 
                                         buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        self.signal_generation_time = Histogram('cryptoalphapro_signal_generation_seconds', 
                                              'Time to generate signals', buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0])
        
        # Data collection metrics
        self.data_points_collected = Counter('cryptoalphapro_data_points_total', 
                                           'Data points collected', ['exchange', 'pair', 'type'])
        self.data_latency = Histogram('cryptoalphapro_data_latency_seconds', 
                                    'Data collection latency', ['exchange'], 
                                    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0])
        self.exchange_connection_status = Gauge('cryptoalphapro_exchange_connected', 
                                              'Exchange connection status', ['exchange'])
        
        # ML model metrics
        self.model_predictions = Counter('cryptoalphapro_ml_predictions_total', 
                                       'ML model predictions', ['model', 'pair'])
        self.model_accuracy = Gauge('cryptoalphapro_ml_accuracy', 
                                  'ML model accuracy', ['model', 'pair'])
        self.model_training_time = Histogram('cryptoalphapro_ml_training_seconds', 
                                           'ML model training time', ['model'])
        
        # Risk management metrics
        self.portfolio_value = Gauge('cryptoalphapro_portfolio_value', 'Current portfolio value')
        self.daily_pnl = Gauge('cryptoalphapro_daily_pnl_percent', 'Daily P&L percentage')
        self.max_drawdown = Gauge('cryptoalphapro_max_drawdown_percent', 'Maximum drawdown percentage')
        self.open_positions = Gauge('cryptoalphapro_open_positions', 'Number of open positions')
        self.risk_score = Gauge('cryptoalphapro_risk_score', 'Overall risk score')
        
        # Trading metrics
        self.trades_executed = Counter('cryptoalphapro_trades_total', 
                                     'Total trades executed', ['pair', 'side', 'result'])
        self.trade_pnl = Histogram('cryptoalphapro_trade_pnl_percent', 
                                 'Trade P&L percentage', buckets=[-10, -5, -2, -1, 0, 1, 2, 5, 10, 20])
        
        # System performance metrics
        self.cpu_usage = Gauge('cryptoalphapro_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('cryptoalphapro_memory_usage_bytes', 'Memory usage in bytes')
        self.disk_usage = Gauge('cryptoalphapro_disk_usage_percent', 'Disk usage percentage')
        
        # Database metrics
        self.database_queries = Counter('cryptoalphapro_database_queries_total', 
                                      'Database queries', ['database', 'operation'])
        self.database_query_time = Histogram('cryptoalphapro_database_query_seconds', 
                                           'Database query time', ['database'])
        self.database_connections = Gauge('cryptoalphapro_database_connections', 
                                        'Active database connections', ['database'])
        
        # Alert metrics
        self.alerts_sent = Counter('cryptoalphapro_alerts_total', 
                                 'Alerts sent', ['type', 'severity'])
        
        # Initialize system info
        self._set_system_info()
        
    def start_server(self):
        """Start Prometheus metrics server"""
        try:
            if not self.server_started:
                start_http_server(self.port)
                self.server_started = True
                logger.info(f"📊 Prometheus metrics server started on port {self.port}")
                
        except Exception as e:
            logger.error(f"❌ Failed to start Prometheus server: {e}")
    
    def _set_system_info(self):
        """Set system information"""
        try:
            self.system_info.info({
                'version': '1.0.0',
                'name': 'CryptoAlphaPro',
                'start_time': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Error setting system info: {e}")
    
    def update_uptime(self):
        """Update system uptime"""
        try:
            current_uptime = time.time() - self.start_time
            self.uptime.set(current_uptime)
        except Exception as e:
            logger.error(f"❌ Error updating uptime: {e}")
    
    # Signal metrics methods
    def record_signal_generated(self, pair: str, action: str, confidence: float, generation_time: float):
        """Record signal generation metrics"""
        try:
            self.signals_generated.labels(pair=pair, action=action).inc()
            self.signal_confidence.observe(confidence)
            self.signal_generation_time.observe(generation_time)
            
        except Exception as e:
            logger.error(f"❌ Error recording signal metrics: {e}")
    
    # Data collection metrics methods
    def record_data_point(self, exchange: str, pair: str, data_type: str, latency: float):
        """Record data collection metrics"""
        try:
            self.data_points_collected.labels(exchange=exchange, pair=pair, type=data_type).inc()
            self.data_latency.labels(exchange=exchange).observe(latency)
            
        except Exception as e:
            logger.error(f"❌ Error recording data metrics: {e}")
    
    def set_exchange_status(self, exchange: str, connected: bool):
        """Set exchange connection status"""
        try:
            self.exchange_connection_status.labels(exchange=exchange).set(1 if connected else 0)
            
        except Exception as e:
            logger.error(f"❌ Error setting exchange status: {e}")
    
    # ML model metrics methods
    def record_model_prediction(self, model: str, pair: str):
        """Record ML model prediction"""
        try:
            self.model_predictions.labels(model=model, pair=pair).inc()
            
        except Exception as e:
            logger.error(f"❌ Error recording model prediction: {e}")
    
    def set_model_accuracy(self, model: str, pair: str, accuracy: float):
        """Set ML model accuracy"""
        try:
            self.model_accuracy.labels(model=model, pair=pair).set(accuracy)
            
        except Exception as e:
            logger.error(f"❌ Error setting model accuracy: {e}")
    
    def record_model_training(self, model: str, training_time: float):
        """Record ML model training time"""
        try:
            self.model_training_time.labels(model=model).observe(training_time)
            
        except Exception as e:
            logger.error(f"❌ Error recording model training: {e}")
    
    # Risk management metrics methods
    def update_portfolio_metrics(self, portfolio_value: float, daily_pnl: float, 
                                max_drawdown: float, open_positions_count: int, risk_score: float):
        """Update portfolio metrics"""
        try:
            self.portfolio_value.set(portfolio_value)
            self.daily_pnl.set(daily_pnl * 100)  # Convert to percentage
            self.max_drawdown.set(max_drawdown * 100)  # Convert to percentage
            self.open_positions.set(open_positions_count)
            self.risk_score.set(risk_score)
            
        except Exception as e:
            logger.error(f"❌ Error updating portfolio metrics: {e}")
    
    # Trading metrics methods
    def record_trade(self, pair: str, side: str, result: str, pnl_percent: float):
        """Record trade execution"""
        try:
            self.trades_executed.labels(pair=pair, side=side, result=result).inc()
            self.trade_pnl.observe(pnl_percent)
            
        except Exception as e:
            logger.error(f"❌ Error recording trade: {e}")
    
    # System performance metrics methods
    def update_system_metrics(self, cpu_percent: float, memory_bytes: int, disk_percent: float):
        """Update system performance metrics"""
        try:
            self.cpu_usage.set(cpu_percent)
            self.memory_usage.set(memory_bytes)
            self.disk_usage.set(disk_percent)
            
        except Exception as e:
            logger.error(f"❌ Error updating system metrics: {e}")
    
    # Database metrics methods
    def record_database_query(self, database: str, operation: str, query_time: float):
        """Record database query"""
        try:
            self.database_queries.labels(database=database, operation=operation).inc()
            self.database_query_time.labels(database=database).observe(query_time)
            
        except Exception as e:
            logger.error(f"❌ Error recording database query: {e}")
    
    def set_database_connections(self, database: str, connections: int):
        """Set database connection count"""
        try:
            self.database_connections.labels(database=database).set(connections)
            
        except Exception as e:
            logger.error(f"❌ Error setting database connections: {e}")
    
    # Alert metrics methods
    def record_alert(self, alert_type: str, severity: str):
        """Record alert sent"""
        try:
            self.alerts_sent.labels(type=alert_type, severity=severity).inc()
            
        except Exception as e:
            logger.error(f"❌ Error recording alert: {e}")
    
    # Batch update methods
    def update_all_metrics(self, metrics_data: Dict[str, Any]):
        """Update multiple metrics at once"""
        try:
            # Update uptime
            self.update_uptime()
            
            # Update portfolio metrics if available
            if 'portfolio' in metrics_data:
                portfolio = metrics_data['portfolio']
                self.update_portfolio_metrics(
                    portfolio.get('value', 0),
                    portfolio.get('daily_pnl', 0),
                    portfolio.get('max_drawdown', 0),
                    portfolio.get('open_positions', 0),
                    portfolio.get('risk_score', 0)
                )
            
            # Update system metrics if available
            if 'system' in metrics_data:
                system = metrics_data['system']
                self.update_system_metrics(
                    system.get('cpu_percent', 0),
                    system.get('memory_bytes', 0),
                    system.get('disk_percent', 0)
                )
            
            # Update exchange statuses if available
            if 'exchanges' in metrics_data:
                for exchange, status in metrics_data['exchanges'].items():
                    self.set_exchange_status(exchange, status.get('connected', False))
            
            # Update model accuracies if available
            if 'models' in metrics_data:
                for model_name, model_data in metrics_data['models'].items():
                    for pair, accuracy in model_data.get('accuracies', {}).items():
                        self.set_model_accuracy(model_name, pair, accuracy)
            
        except Exception as e:
            logger.error(f"❌ Error updating all metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        try:
            return {
                'uptime_seconds': time.time() - self.start_time,
                'server_running': self.server_started,
                'port': self.port,
                'metrics_count': len([
                    self.signals_generated, self.signal_confidence, self.signal_generation_time,
                    self.data_points_collected, self.data_latency, self.exchange_connection_status,
                    self.model_predictions, self.model_accuracy, self.model_training_time,
                    self.portfolio_value, self.daily_pnl, self.max_drawdown, self.open_positions,
                    self.risk_score, self.trades_executed, self.trade_pnl, self.cpu_usage,
                    self.memory_usage, self.disk_usage, self.database_queries,
                    self.database_query_time, self.database_connections, self.alerts_sent
                ]),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting metrics summary: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on metrics system"""
        try:
            return {
                'healthy': True,
                'server_running': self.server_started,
                'uptime': time.time() - self.start_time,
                'port': self.port,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in metrics health check: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 