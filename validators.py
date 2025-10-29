import re


class Validator:
    """
    Validates all order inputs before execution.
    Ensures that the symbol, price, and quantity follow expected formats and ranges.
    """

    SUPPORTED_SYMBOLS = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"
    ]  # You can fetch dynamically from Binance if using API keys.

    def __init__(self, min_qty=0.001, max_qty=1000, min_price=0.01):
        self.min_qty = min_qty
        self.max_qty = max_qty
        self.min_price = min_price

    # -------------------------------------------------------------------------
    # SYMBOL VALIDATION
    # -------------------------------------------------------------------------
    def validate_symbol(self, symbol: str) -> bool:
        """
        Check if the symbol is in the supported list and matches Binance format.

        Args:
            symbol (str): e.g., "BTCUSDT"

        Returns:
            bool: True if valid, False otherwise.
        """
        if not symbol or not re.match(r"^[A-Z]{3,10}USDT$", symbol):
            raise ValueError(f"❌ Invalid symbol format: {symbol}")

        if symbol not in self.SUPPORTED_SYMBOLS:
            raise ValueError(f"❌ Unsupported symbol: {symbol}. Add it to SUPPORTED_SYMBOLS list.")

        return True

    # -------------------------------------------------------------------------
    # QUANTITY VALIDATION
    # -------------------------------------------------------------------------
    def validate_quantity(self, quantity: float) -> bool:
        """
        Check if quantity is within the allowed range.

        Args:
            quantity (float): Order quantity (lot size)

        Returns:
            bool: True if valid
        """
        if quantity <= 0:
            raise ValueError("❌ Quantity must be greater than 0.")

        if quantity < self.min_qty:
            raise ValueError(f"❌ Quantity too small. Minimum allowed is {self.min_qty}")

        if quantity > self.max_qty:
            raise ValueError(f"❌ Quantity too large. Maximum allowed is {self.max_qty}")

        return True

    # -------------------------------------------------------------------------
    # PRICE VALIDATION
    # -------------------------------------------------------------------------
    def validate_price(self, price: float) -> bool:
        """
        Check if price is valid (positive and above threshold).

        Args:
            price (float): Price per unit.

        Returns:
            bool: True if valid
        """
        if price <= 0:
            raise ValueError("❌ Price must be positive.")

        if price < self.min_price:
            raise ValueError(f"❌ Price must be at least {self.min_price}.")

        return True

    # -------------------------------------------------------------------------
    # SIDE VALIDATION
    # -------------------------------------------------------------------------
    def validate_side(self, side: str) -> bool:
        """
        Check if side is either 'buy' or 'sell'.

        Args:
            side (str): 'buy' or 'sell'

        Returns:
            bool: True if valid
        """
        if side.lower() not in ["buy", "sell"]:
            raise ValueError("❌ Side must be either 'buy' or 'sell'.")
        return True

    # -------------------------------------------------------------------------
    # ORDER TYPE VALIDATION
    # -------------------------------------------------------------------------
    def validate_order_type(self, order_type: str) -> bool:
        """
        Check if the order type is supported.

        Args:
            order_type (str): e.g., 'MARKET', 'LIMIT', 'STOP_LIMIT', 'OCO'

        Returns:
            bool: True if valid
        """
        valid_types = ["MARKET", "LIMIT", "STOP_LIMIT", "OCO", "TWAP", "GRID"]
        if order_type.upper() not in valid_types:
            raise ValueError(f"❌ Invalid order type: {order_type}. Supported types: {valid_types}")
        return True

    # -------------------------------------------------------------------------
    # COMBINED VALIDATION
    # -------------------------------------------------------------------------
    
    def validate_order(self, symbol, side, quantity, price=None, order_type="MARKET") -> bool:
        """
        Validate all inputs for an order before execution.

        Args:
            symbol (str): Trading symbol.
            side (str): 'buy' or 'sell'.
            quantity (float): Quantity of asset.
            price (float, optional): Price (for limit/stop orders).
            order_type (str): Order type.

        Returns:
            bool: True if all validations pass.
        """
        self.validate_symbol(symbol)
        self.validate_side(side)
        self.validate_quantity(quantity)
        self.validate_order_type(order_type)

        if order_type.upper() in ["LIMIT", "STOP_LIMIT", "OCO", "GRID"] and price is not None:
            self.validate_price(price)

        return True


# -------------------------------------------------------------------------
# Example Usage
# -------------------------------------------------------------------------
if __name__ == "__main__":
    validator = Validator()

    try:
        validator.validate_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.01,
            price=68000,
            order_type="LIMIT"
        )
        print("✅ Order validation successful!")

    except ValueError as e:
        print(e)
