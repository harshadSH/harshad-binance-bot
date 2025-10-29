import math
from datetime import datetime


class GridTrader:
    """
    Implements a Grid Trading Strategy.

    The grid trading strategy places a series of buy and sell orders
    at incrementally increasing or decreasing prices to capture profits
    from price fluctuations in a ranging market.

    Example:
        grid = GridTrader(symbol='BTCUSDT', lower_price=25000, upper_price=27000,
                          grid_count=10, investment=1000, side='buy')
        grid.initialize_grid()
        grid.execute_orders(broker)
    """

    def __init__(self, symbol, lower_price, upper_price, grid_count, investment, side="buy"):
        """
        Initialize grid strategy parameters.

        Args:
            symbol (str): Trading symbol, e.g., 'BTCUSDT'.
            lower_price (float): Lowest grid price.
            upper_price (float): Highest grid price.
            grid_count (int): Number of grid levels between lower and upper prices.
            investment (float): Total capital allocated to this strategy.
            side (str): Initial order side ('buy' or 'sell').
        """
        self.symbol = symbol
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.grid_count = grid_count
        self.investment = investment
        self.side = side.lower()
        self.grid_levels = []
        self.active_orders = []
        self.order_log = []

        # Calculate price step and per-order amount
        self.price_step = (upper_price - lower_price) / grid_count
        self.order_size = investment / grid_count  # simplified assumption

    def initialize_grid(self):
        """Create grid levels based on configuration."""
        self.grid_levels = [
            self.lower_price + i * self.price_step for i in range(self.grid_count + 1)
        ]
        print(f"\n[INFO] Initialized {len(self.grid_levels)} grid levels for {self.symbol}")
        print(f"       Range: {self.lower_price} → {self.upper_price}")
        print(f"       Step: {self.price_step:.2f}")
        print(f"       Order Size: {self.order_size:.2f}\n")

    def execute_orders(self, broker):
        """
        Place buy/sell limit orders at all grid levels.

        Args:
            broker (object): Object with `place_limit_order(symbol, side, quantity, price)` method.
        """
        if not self.grid_levels:
            raise ValueError("Grid not initialized. Call initialize_grid() before execute_orders().")

        print(f"[INFO] Executing Grid Strategy for {self.symbol}...\n")

        for i, price in enumerate(self.grid_levels):
            side = self.side if i % 2 == 0 else ("sell" if self.side == "buy" else "buy")

            try:
                response = broker.place_limit_order(
                    symbol=self.symbol,
                    side=side,
                    quantity=self._calculate_quantity(price),
                    price=price
                )

                self.active_orders.append({
                    "price": price,
                    "side": side,
                    "quantity": self._calculate_quantity(price),
                    "status": "open",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "response": response
                })

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Placed {side.upper()} LIMIT order at {price:.2f}")

            except Exception as e:
                print(f"[ERROR] Failed to place order at {price:.2f}: {e}")

        print(f"\n[INFO] Grid setup completed for {self.symbol}.\n")

    def _calculate_quantity(self, price):
        """
        Compute quantity for a given price based on uniform investment per level.
        """
        return round(self.order_size / price, 6)

    def update_orders(self, market_price, broker):
        """
        Monitor and update grid orders as price moves.

        Args:
            market_price (float): Current market price.
            broker (object): Broker with methods `cancel_order()` and `place_limit_order()`.
        """
        for order in self.active_orders:
            if order["status"] == "open":
                # Check for executed orders
                if (order["side"] == "buy" and market_price <= order["price"]) or \
                   (order["side"] == "sell" and market_price >= order["price"]):

                    print(f"[INFO] {order['side'].upper()} order at {order['price']:.2f} triggered.")

                    order["status"] = "executed"
                    self.order_log.append(order)

                    # Place the opposite order to maintain grid balance
                    new_side = "sell" if order["side"] == "buy" else "buy"
                    new_price = order["price"] + (self.price_step if new_side == "sell" else -self.price_step)

                    # Ensure new order remains within grid range
                    if self.lower_price <= new_price <= self.upper_price:
                        qty = self._calculate_quantity(new_price)
                        broker.place_limit_order(self.symbol, new_side, qty, new_price)
                        print(f"[AUTO] Placed {new_side.upper()} LIMIT order at {new_price:.2f} for grid rebalance.\n")

    def get_active_orders(self):
        """Return all active grid orders."""
        return [o for o in self.active_orders if o["status"] == "open"]

    def get_order_history(self):
        """Return all executed order logs."""
        return self.order_log


# Example usage
if __name__ == "__main__":
    class MockBroker:
        def place_limit_order(self, symbol, side, quantity, price):
            return {"status": "placed", "symbol": symbol, "side": side, "quantity": quantity, "price": price}

    broker = MockBroker()
    grid = GridTrader(symbol="BTCUSDT", lower_price=60000, upper_price=70000, grid_count=5, investment=100, side="buy")
    grid.initialize_grid()
    grid.execute_orders(broker)

    # Simulate market updates
    grid.update_orders(26000, broker)
