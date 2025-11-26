import threading
import time
from typing import Dict, List, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PriceFeedService:
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PriceFeedService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.symbols: Set[str] = set()
            self.prices: Dict[str, Dict] = {}
            self.running = False
            self.update_thread = None
            self.update_interval = 5
            self._initialized = True
    
    def add_symbol(self, symbol: str) -> None:
        
        symbol = symbol.upper()
        if symbol not in self.symbols:
            self.symbols.add(symbol)
            self.prices[symbol] = self._get_mock_price(symbol)
            logger.info(f"Added symbol to tracking: {symbol}")
    
    def add_symbols(self, symbols: List[str]) -> None:
        
        for symbol in symbols:
            self.add_symbol(symbol)
    
    def remove_symbol(self, symbol: str) -> None:
        
        symbol = symbol.upper()
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            if symbol in self.prices:
                del self.prices[symbol]
            logger.info(f"Removed symbol from tracking: {symbol}")
    
    def get_prices(self, symbols: List[str] = None) -> Dict[str, Dict]:
        
        if symbols is None:
            symbols = list(self.symbols)
        
        result = {}
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in self.prices:
                result[symbol] = self.prices[symbol].copy()
            else:
                result[symbol] = self._get_mock_price(symbol)
        
        return result
    
    def _get_mock_price(self, symbol: str) -> Dict:
        
        base_price = 100.0 + (hash(symbol) % 200)
        change = (hash(symbol + str(time.time())) % 10) - 5
        
        return {
            'price': round(base_price, 2),
            'change': round(change, 2),
            'change_percent': round((change / base_price) * 100, 2),
            'volume': 1000000 + (hash(symbol) % 5000000),
            'last_updated': datetime.utcnow().isoformat(),
            'error': None
        }
    
    def fetch_prices(self) -> Dict[str, Dict]:
        
        new_prices = {}
        
        for symbol in self.symbols:
            try:
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    history = ticker.history(period="1d")
                    
                    if not history.empty:
                        current_price = float(history['Close'].iloc[-1])
                        prev_close = float(history['Open'].iloc[0])
                        change = current_price - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                        volume = int(history['Volume'].iloc[-1])
                        
                        new_prices[symbol] = {
                            'price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': volume,
                            'last_updated': datetime.utcnow().isoformat(),
                            'error': None
                        }
                    else:
                        new_prices[symbol] = self._get_mock_price(symbol)
                except ImportError:
                    new_prices[symbol] = self._get_mock_price(symbol)
                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {e}, using mock data")
                    new_prices[symbol] = self._get_mock_price(symbol)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                new_prices[symbol] = self._get_mock_price(symbol)
        
        return new_prices
    
    def update_prices(self) -> None:
        
        new_prices = self.fetch_prices()
        if new_prices:
            self.prices.update(new_prices)
    
    def _update_loop(self) -> None:
        
        logger.info("Price feed service started")
        
        while self.running:
            try:
                self.update_prices()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                time.sleep(self.update_interval)
        
        logger.info("Price feed service stopped")
    
    def start(self) -> None:
        
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("Price feed service started")
            
            try:
                self.update_prices()
            except Exception as e:
                logger.error(f"Initial price fetch failed: {e}")
    
    def stop(self) -> None:
        
        if self.running:
            self.running = False
            if self.update_thread:
                self.update_thread.join(timeout=5)
            logger.info("Price feed service stopped")
    
    def get_status(self) -> Dict:
        
        return {
            'running': self.running,
            'symbols_count': len(self.symbols),
            'symbols': list(self.symbols),
            'update_interval': self.update_interval
        }
