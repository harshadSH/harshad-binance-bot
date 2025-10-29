import logging
from typing import Dict, Any
from validators import Validator
from utils import log_error

logger = logging.getLogger(__name__)


class MarketOrder:
    """Represents a Binance Futures Market Order."""

    def __init__(self, symbol: str, side: str, quantity: float):
        self.symbol = symbol.upper()
        self.side = side.upper()
        self.quantity = quantity

    def build_payload(self) -> Dict[str, Any]:
        """Prepare the order payload."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "type": "MARKET",
            "quantity": self.quantity,
        }

    def execute(self, broker) -> Dict[str, Any]:
        """Execute the market order using the provided broker."""
        try:
            logger.info(f"Placing MARKET order: {self.symbol} {self.side} {self.quantity}")

            # Validate before execution
            Validator().validate_order(
                symbol=self.symbol,
                side=self.side,
                quantity=self.quantity,
                price=None,
                order_type="MARKET"
            )

            payload = self.build_payload()
            response = broker.place_order(payload)

            logger.info(f"✅ Market order executed successfully: {response}")
            return response

        except Exception as e:
            log_error(f"❌ Market order failed: {e}")
            raise


def place_market_order(symbol: str, side: str, quantity: float) -> MarketOrder:
    """Factory function that returns a MarketOrder instance."""
    return MarketOrder(symbol, side, quantity)
