"""
Sistema de Observabilidade
---------------------------
Logging estruturado JSON, métricas Prometheus e health checks.
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict
from threading import Lock

# JSON Logging
class JsonFormatter(logging.Formatter):
    """Formatter que converte LogRecords para JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adiciona campos extras se existirem
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # Adiciona exception se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_json_logging(logger_name: str = 'hub_financeiro', level: int = logging.INFO) -> logging.Logger:
    """
    Configura logger com JSON formatter.
    
    Args:
        logger_name: Nome do logger
        level: Nível de log (INFO, DEBUG, etc)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Handler com JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    return logger


# Métricas Prometheus
class MetricsCollector:
    """Coletor de métricas compatível com formato Prometheus."""
    
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
    
    def counter_inc(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Incrementa contador."""
        key = self._format_key(metric_name, labels)
        with self._lock:
            self._counters[key] += value
    
    def gauge_set(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Define valor do gauge."""
        key = self._format_key(metric_name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def histogram_observe(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Registra observação no histograma."""
        key = self._format_key(metric_name, labels)
        with self._lock:
            self._histograms[key].append(value)
    
    def _format_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Formata chave com labels Prometheus."""
        if not labels:
            return name
        label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'
    
    def export_prometheus(self) -> str:
        """Exporta métricas em formato Prometheus text."""
        lines = []
        
        with self._lock:
            # Counters
            for key, value in self._counters.items():
                lines.append(f'# TYPE {key.split("{")[0]} counter')
                lines.append(f'{key} {value}')
            
            # Gauges
            for key, value in self._gauges.items():
                lines.append(f'# TYPE {key.split("{")[0]} gauge')
                lines.append(f'{key} {value}')
            
            # Histograms (simplificado: soma, count, quantis)
            for key, values in self._histograms.items():
                base_name = key.split("{")[0]
                lines.append(f'# TYPE {base_name} histogram')
                lines.append(f'{key}_sum {sum(values)}')
                lines.append(f'{key}_count {len(values)}')
                if values:
                    sorted_vals = sorted(values)
                    p50 = sorted_vals[len(sorted_vals) // 2]
                    p95 = sorted_vals[int(len(sorted_vals) * 0.95)]
                    p99 = sorted_vals[int(len(sorted_vals) * 0.99)]
                    lines.append(f'{key}_bucket{{le="0.5"}} {p50}')
                    lines.append(f'{key}_bucket{{le="0.95"}} {p95}')
                    lines.append(f'{key}_bucket{{le="0.99"}} {p99}')
        
        return '\n'.join(lines)
    
    def reset(self):
        """Reseta todas as métricas."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# Instância global de métricas
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Retorna instância global de métricas."""
    return _metrics


def track_duration(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """
    Decorator para medir duração de funções.
    
    Exemplo:
        @track_duration('sync_shopee_duration', labels={'source': 'shopee'})
        def sync_shopee():
            # código...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                _metrics.histogram_observe(metric_name, duration, labels)
        return wrapper
    return decorator


# Health Checks
class HealthCheck:
    """Sistema de health checks para endpoints de monitoramento."""
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
    
    def register(self, name: str, check_fn: callable):
        """Registra health check.
        
        Args:
            name: Nome do check
            check_fn: Função que retorna True se saudável
        """
        self._checks[name] = check_fn
    
    def run_all(self) -> Dict[str, Any]:
        """Executa todos os health checks.
        
        Returns:
            {
                'status': 'healthy'|'unhealthy',
                'checks': {'check_name': {'status': 'pass'|'fail', 'error': '...'}}
            }
        """
        results = {}
        all_healthy = True
        
        for name, check_fn in self._checks.items():
            try:
                is_ok = check_fn()
                results[name] = {'status': 'pass' if is_ok else 'fail'}
                if not is_ok:
                    all_healthy = False
            except Exception as e:
                results[name] = {'status': 'fail', 'error': str(e)}
                all_healthy = False
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': results
        }


# Instância global de health checks
_health = HealthCheck()


def get_health() -> HealthCheck:
    """Retorna instância global de health checks."""
    return _health


# Health checks padrão
def _check_database():
    """Verifica conectividade com banco de dados."""
    try:
        from .database import get_db
        db = get_db()
        db.execute('SELECT 1')
        db.close()
        return True
    except Exception:
        return False


# Registra checks padrão
_health.register('database', _check_database)
