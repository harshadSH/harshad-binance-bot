import time
from datetime import datetime

class TWAPOrder:
    """
    Time-Weighted Average Price (TWAP) strategy.
    Splits a total order into equal smaller orders executed at fixed intervals.
    """

    def __init__(self, symbol, side, quantity, total_slices, interval_seconds=60):
        """
        Initialize TWAP order parameters.

        Args:
            symbol (str): Trading pair symbol, e.g., 'BTCUSDT'
            side (str): 'buy' or 'sell'
            quantity (float): Total quantity to trade
            total_slices (int): Number of parts to divide the order into
            interval_seconds (int): Time interval between consecutive orders
        """
        self.symbol = symbol
        self.side = side.lower()
        self.total_quantity = quantity
        self.total_slices = total_slices
        self.interval_seconds = interval_seconds
        self.order_log = []

        self.order_size = quantity / total_slices

    def execute(self, broker):
        """
        Execute TWAP strategy by placing multiple smaller orders.
        """
        print(f"\n[INFO] Starting TWAP for {self.symbol}")
        print(f"       Total Quantity: {self.total_quantity}")
        print(f"       Slices: {self.total_slices}")
        print(f"       Interval: {self.interval_seconds}s")
        print(f"       Each Order Size: {self.order_size:.6f}\n")

        for i in range(self.total_slices):
            try:
                res = broker.place_order({
                    "symbol": self.symbol.upper(),
                    "side": self.side.upper(),
                    "type": "MARKET",
                    "quantity": round(self.order_size, 6)
                })

                self.order_log.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "interval": i + 1,
                    "side": self.side,
                    "quantity": self.order_size,
                    "response": res
                })

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Executed {self.side.upper()} order "
                      f"#{i + 1}/{self.total_slices} for {self.order_size:.6f} {self.symbol}")

            except Exception as e:
                print(f"[ERROR] Failed at slice {i + 1}: {str(e)}")

            # Wait between orders
            time.sleep(self.interval_seconds)

        print(f"\n✅ TWAP execution completed for {self.symbol}.\n")

    def get_execution_log(self):
        """Return list of executed order logs."""
        return self.order_log


# ------------------- Example Usage -------------------
if __name__ == "__main__":
    class MockBroker:
        def place_order(self, payload):
            print(f"Simulated Order: {payload}")
            return {"status": "success", "payload": payload}

    broker = MockBroker()
    twap = TWAPOrder(symbol="BTCUSDT", side="buy", quantity=0.01, total_slices=5, interval_seconds=2)
    twap.execute(broker)
