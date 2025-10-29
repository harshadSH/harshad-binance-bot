import argparse
import sys
from broker import Broker
from validators import Validator
from market_orders import place_market_order
from limit_orders import place_limit_order
from advanced.stop_limit import place_stop_limit_order
from advanced.oco import place_oco_order
from advanced.twap import TWAPOrder
from advanced.grid import GridTrader
import logging
from datetime import datetime


# -------------------------------------------------------------------------
# CONFIGURE LOGGER
# -------------------------------------------------------------------------
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# MAIN CLI HANDLER
# -------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Binance Futures Order Bot CLI - Supports Market, Limit, Stop-Limit, OCO, TWAP, and Grid Orders"
    )

    # Common arguments
    parser.add_argument("symbol", type=str, help="Trading symbol, e.g., BTCUSDT")
    parser.add_argument("side", type=str, choices=["buy", "sell"], help="Order side")
    parser.add_argument("order_type", type=str, choices=["market", "limit", "stop_limit", "oco", "twap", "grid"],
                        help="Type of order to place")
    parser.add_argument("--quantity", type=float, required=True, help="Order quantity")
    parser.add_argument("--price", type=float, help="Order price (for limit/stop orders)")
    parser.add_argument("--stop_price", type=float, help="Stop trigger price (for stop-limit orders)")
    parser.add_argument("--take_profit", type=float, help="Take-profit price (for OCO orders)")
    parser.add_argument("--stop_loss", type=float, help="Stop-loss price (for OCO orders)")
    parser.add_argument("--interval", type=int, help="Time interval in seconds (for TWAP)")
    parser.add_argument("--slices", type=int, help="Number of slices for TWAP")
    parser.add_argument("--lower_price", type=float, help="Lower grid price (for Grid strategy)")
    parser.add_argument("--upper_price", type=float, help="Upper grid price (for Grid strategy)")
    parser.add_argument("--grids", type=int, help="Number of grids (for Grid strategy)")
    parser.add_argument("--investment", type=float, help="Total investment (for Grid strategy)")

    args = parser.parse_args()

    # Initialize broker and validator
    broker = Broker()
    validator = Validator()

    try:
        # Common validation
        validator.validate_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.price if args.price else 0,
            order_type=args.order_type.upper(),
        )

        logger.info(f"CLI command received: {args.order_type.upper()} | {args.symbol} | {args.side.upper()} | Qty: {args.quantity}")

        # -------------------------------------------------------------------------
        # Handle Different Order Types
        # -------------------------------------------------------------------------

        # 1️⃣ Market Order
        if args.order_type == "market":
            order = place_market_order(symbol=args.symbol, side=args.side, quantity=args.quantity)
            response = order.execute(broker)
            print(f"✅ Market Order executed: {response}")
            logger.info(f"Market Order executed successfully: {response}")

        # 2️⃣ Limit Order
        elif args.order_type == "limit":
            if not args.price:
                raise ValueError("Price required for LIMIT order.")
            place_limit_order(symbol=args.symbol, side=args.side, quantity=args.quantity, price=args.price)


        # 3️⃣ Stop-Limit Order
        elif args.order_type == "stop_limit":
            if not args.price or not args.stop_price:
                raise ValueError("Both --price and --stop_price are required for STOP-LIMIT order.")
            place_stop_limit_order(symbol=args.symbol, side=args.side, quantity=args.quantity,
                                   stop_price=args.stop_price, limit_price=args.price)
        
            

        # 4️⃣ OCO Order
        elif args.order_type == "oco":
            if not args.take_profit or not args.stop_loss:
                raise ValueError("Both --take_profit and --stop_loss are required for OCO order.")
            order = place_oco_order(symbol=args.symbol, side=args.side, quantity=args.quantity,
                             take_profit=args.take_profit, stop_loss=args.stop_loss)
            response = order.execute(broker)
            print(f"✅ OCO Order placed: {response}")
            logger.info(f"OCO Order placed successfully: {response}")

        # 5️⃣ TWAP Order
        elif args.order_type == "twap":
            if not args.interval or not args.slices:
                raise ValueError("Both --interval and --slices are required for TWAP order.")
            order = TWAPOrder(symbol=args.symbol, side=args.side, quantity=args.quantity,
                                 total_slices=args.slices, interval_seconds=args.interval)
            order.execute(broker)
            print("✅ TWAP Strategy execution started.")
            logger.info("TWAP Strategy execution started.")

        # 6️⃣ GRID Order
        elif args.order_type == "grid":
            if not args.lower_price or not args.upper_price or not args.grids or not args.investment:
                raise ValueError("Grid strategy requires --lower_price, --upper_price, --grids, and --investment.")
            grid = GridTrader(symbol=args.symbol,
                              lower_price=args.lower_price,
                              upper_price=args.upper_price,
                              grid_count=args.grids,
                              investment=args.investment,
                              side=args.side)
            grid.initialize_grid()
            grid.execute_orders(broker)
            print("✅ Grid Strategy executed successfully.")
            logger.info("Grid Strategy executed successfully.")

    except Exception as e:
        logger.error(f"Order execution failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
