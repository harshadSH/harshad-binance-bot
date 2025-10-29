import argparse
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
import sys
from dotenv import load_dotenv

# -----------------------------
# Load Binance API Credentials
# -----------------------------
load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ Missing Binance API credentials. Please check your .env file.")
    sys.exit(1)

# -----------------------------
# Setup Logging
# -----------------------------
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -----------------------------
# Initialize Client
# -----------------------------
client = Client(API_KEY, API_SECRET)


# -----------------------------
# Symbol Validation
# -----------------------------
def validate_symbol(symbol: str) -> bool:
    """Ensure that the symbol exists on Binance Spot Market."""
    try:
        info = client.get_exchange_info()
        symbols = [s['symbol'] for s in info['symbols']]
        return symbol.upper() in symbols
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


# -----------------------------
# Input Validation
# -----------------------------
def validate_inputs(symbol: str, quantity: float, price: float, stop_price: float, stop_limit_price: float) -> bool:
    """Validate numeric input fields."""
    if not validate_symbol(symbol):
        print(f"❌ Invalid symbol: {symbol}")
        logging.error(f"Invalid symbol: {symbol}")
        return False

    if quantity <= 0:
        print("❌ Quantity must be greater than 0.")
        logging.error("Invalid quantity.")
        return False

    if price <= 0 or stop_price <= 0 or stop_limit_price <= 0:
        print("❌ Price and stop values must be greater than 0.")
        logging.error("Invalid price or stop value.")
        return False

    return True


# -----------------------------
# Place OCO Order
# -----------------------------
def place_oco_order(symbol: str, side: str, quantity: float, price: float, stop_price: float, stop_limit_price: float, stop_limit_time_in_force="GTC"):
    """
    Place an OCO (One-Cancels-the-Other) order.

    This includes:
      - A limit (take-profit) order
      - A stop-limit (stop-loss) order
    """
    side = side.upper()

    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side! Use 'BUY' or 'SELL'.")
        logging.error(f"Invalid side entered: {side}")
        return

    if not validate_inputs(symbol, quantity, price, stop_price, stop_limit_price):
        return

    try:
        logging.info(
            f"Placing OCO order: {symbol} {side} {quantity} | TP={price}, SL={stop_price}/{stop_limit_price}"
        )

        order = client.order_oco(
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            price=price,  # Take-profit price
            stopPrice=stop_price,  # Stop trigger
            stopLimitPrice=stop_limit_price,  # Stop-limit execution price
            stopLimitTimeInForce=stop_limit_time_in_force
        )

        logging.info(f"✅ OCO order placed successfully: {order}")
        print(f"✅ OCO order placed successfully! Order List ID: {order['orderListId']}")

    except BinanceAPIException as e:
        logging.error(f"Binance API Error: {e.message}")
        print(f"❌ Binance API Error: {e.message}")
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        print(f"❌ Unexpected Error: {e}")


# -----------------------------
# CLI Entry Point
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance OCO Order Bot (One-Cancels-the-Other)")

    parser.add_argument("symbol", type=str, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("side", type=str, help="BUY or SELL")
    parser.add_argument("quantity", type=float, help="Order quantity")
    parser.add_argument("price", type=float, help="Take-profit limit price")
    parser.add_argument("stop_price", type=float, help="Stop price (trigger for stop-limit order)")
    parser.add_argument("stop_limit_price", type=float, help="Stop-limit execution price after trigger")
    parser.add_argument("--tif", type=str, default="GTC", help="Time in Force for stop-limit order (default=GTC)")

    args = parser.parse_args()

    place_oco_order(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
        stop_limit_price=args.stop_limit_price,
        stop_limit_time_in_force=args.tif
    )
