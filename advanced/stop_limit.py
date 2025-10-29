import argparse
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
import sys
from dotenv import load_dotenv

# -----------------------------
# Load API Keys
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
    """Ensure the trading symbol exists on Binance Futures."""
    try:
        info = client.futures_exchange_info()
        symbols = [s['symbol'] for s in info['symbols']]
        return symbol.upper() in symbols
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


# -----------------------------
# Input Validation
# -----------------------------
def validate_inputs(symbol: str, stop_price: float, limit_price: float, quantity: float) -> bool:
    """Validate numeric inputs."""
    if not validate_symbol(symbol):
        print(f"❌ Invalid symbol: {symbol}")
        logging.error(f"Invalid symbol: {symbol}")
        return False

    if stop_price <= 0 or limit_price <= 0 or quantity <= 0:
        print("❌ Stop price, limit price, and quantity must all be greater than 0.")
        logging.error("Invalid input values for stop/limit/quantity.")
        return False

    return True


# -----------------------------
# Place Stop-Limit Order
# -----------------------------
def place_stop_limit_order(symbol: str, side: str, quantity: float, stop_price: float, limit_price: float, time_in_force="GTC"):
    """
    Place a Stop-Limit order on Binance Futures.

    The order triggers when the `stop_price` is reached,
    and then places a Limit order at `limit_price`.
    """
    side = side.upper()

    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side! Use 'BUY' or 'SELL'.")
        logging.error(f"Invalid side entered: {side}")
        return

    if not validate_inputs(symbol, stop_price, limit_price, quantity):
        return

    try:
        logging.info(f"Placing Stop-Limit order: {symbol} {side} {quantity} STOP={stop_price} LIMIT={limit_price}")

        order = client.futures_create_order(
            symbol=symbol.upper(),
            side=side,
            type="STOP_LIMIT",
            quantity=quantity,
            price=limit_price,
            stopPrice=stop_price,
            timeInForce=time_in_force
        )

        logging.info(f"✅ Stop-Limit order placed successfully: {order}")
        print(f"✅ Stop-Limit order placed successfully! Order ID: {order['orderId']}")

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
    parser = argparse.ArgumentParser(description="Binance Futures Stop-Limit Order Bot")

    parser.add_argument("symbol", type=str, help="Trading symbol, e.g. BTCUSDT")
    parser.add_argument("side", type=str, help="BUY or SELL")
    parser.add_argument("quantity", type=float, help="Order quantity")
    parser.add_argument("stop_price", type=float, help="Stop trigger price")
    parser.add_argument("limit_price", type=float, help="Limit order price after trigger")
    parser.add_argument("--tif", type=str, default="GTC", help="Time in Force: GTC/IOC/FOK (default=GTC)")

    args = parser.parse_args()

    place_stop_limit_order(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        stop_price=args.stop_price,
        limit_price=args.limit_price,
        time_in_force=args.tif
    )
