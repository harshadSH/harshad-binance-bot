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
    logging.error("Missing Binance API credentials.")
    print("Error: Missing Binance API credentials in .env file.")
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
# Validate Trading Symbol
# -----------------------------
def validate_symbol(symbol: str) -> bool:
    """Check if the trading symbol exists on Binance Futures."""
    try:
        info = client.futures_exchange_info()
        symbols = [s['symbol'] for s in info['symbols']]
        return symbol.upper() in symbols
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


# -----------------------------
# Validate Price and Quantity
# -----------------------------
def validate_inputs(symbol: str, price: float, quantity: float) -> bool:
    """Ensure price and quantity are positive numbers."""
    if not validate_symbol(symbol):
        print(f"❌ Invalid symbol: {symbol}")
        logging.error(f"Invalid symbol: {symbol}")
        return False

    if price <= 0:
        print("❌ Price must be greater than 0.")
        logging.error("Invalid price entered.")
        return False

    if quantity <= 0:
        print("❌ Quantity must be greater than 0.")
        logging.error("Invalid quantity entered.")
        return False

    return True


# -----------------------------
# Place Limit Order
# -----------------------------
def place_limit_order(symbol: str, side: str, quantity: float, price: float, time_in_force="GTC"):
    """
    Place a LIMIT order on Binance Futures.
    GTC = Good Till Cancelled
    IOC = Immediate or Cancel
    FOK = Fill or Kill
    """
    side = side.upper()

    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side! Use 'BUY' or 'SELL'.")
        logging.error(f"Invalid side entered: {side}")
        return

    if not validate_inputs(symbol, price, quantity):
        return

    try:
        logging.info(f"Placing limit order: {symbol} {side} {quantity} @ {price} ({time_in_force})")

        order = client.futures_create_order(
            symbol=symbol.upper(),
            side=side,
            type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce=time_in_force
        )

        logging.info(f"✅ Limit order placed successfully: {order}")
        print(f"✅ Limit order placed successfully! Order ID: {order['orderId']}")

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
    parser = argparse.ArgumentParser(description="Binance Futures Limit Order Bot")

    parser.add_argument("symbol", type=str, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("side", type=str, help="BUY or SELL")
    parser.add_argument("quantity", type=float, help="Order quantity")
    parser.add_argument("price", type=float, help="Limit price")
    parser.add_argument("--tif", type=str, default="GTC", help="Time in Force: GTC/IOC/FOK (default=GTC)")

    args = parser.parse_args()

    place_limit_order(args.symbol, args.side, args.quantity, args.price, args.tif)
