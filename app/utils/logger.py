import logging
import time
from functools import wraps
from datetime import datetime
import sys

# Configuración de colores para terminal
class ColoredFormatter(logging.Formatter):
    """Formatter con colores para logs en terminal"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if sys.stdout.isatty():  # Solo si es terminal
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        return super().format(record)


def setup_logging(name: str = __name__):
    """
    Configura logging con formato bonito y colores.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Formato con timestamp, nivel, módulo y mensaje
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_execution_time(func):
    """
    Decorador que registra el tiempo de ejecución de una función.
    
    Uso:
        @log_execution_time
        def mi_funcion():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        start_time = time.time()
        logger.info(f"⏱️  Iniciando: {func.__name__}()")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Formatea el tiempo según duración
            if execution_time < 1:
                time_str = f"{execution_time*1000:.2f}ms"
            elif execution_time < 60:
                time_str = f"{execution_time:.2f}s"
            else:
                minutes = execution_time / 60
                time_str = f"{minutes:.2f}m"
            
            logger.info(f"✅ Completado: {func.__name__}() en {time_str}")
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Error en {func.__name__}() después de {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper


def get_logger(name: str):
    """
    Obtiene un logger configurado para un módulo.
    
    Uso:
        logger = get_logger(__name__)
    """
    return setup_logging(name)