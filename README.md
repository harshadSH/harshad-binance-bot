**🦾 Binance Trading Bot**

An automated trading bot built in Python that supports multiple order types — including Market, Limit, TWAP, and Grid strategies — using the Binance Futures API.
It provides a CLI (Command-Line Interface) to place and manage trades programmatically.

**⚙️ Features**
✅ Market Orders 
✅ Limit Orders
✅ Stop-Limit Orders  
✅ OCO (One Cancels the Other) Orders 
✅ TWAP (Time-Weighted Average Price) Strategy
✅ Grid Trading Strategy
✅ Auto-validation of symbols, quantities, and price ranges
✅ Dual support for python-binance SDK and direct REST API
✅ Structured logging and error handling

**🚀 Installation & Setup**
1️⃣ Clone the Repository
git clone https://github.com/harshadSH/harshad-binance-bot.git
cd binance-trading-bot


🔑 API Setup Instructions
Create a .env file in the project root:

BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_key_here

**💻 Usage — Running the Bot**
The bot provides a CLI interface via src/cli.py.
**📈 1. Market Order**
Place an instant buy/sell order:
python src/cli.py BTCUSDT buy market --quantity 0.01

Example output:
✅ Market Order executed: {'symbol': 'BTCUSDT', 'orderId': 12345, 'status': 'FILLED'}

**💰 2. Limit Order**
Place a limit order at a specific price:
python src/cli.py BTCUSDT sell limit --quantity 0.01 --price 68000

**⛔ 3. Stop-Limit Order**
A Stop-Limit Order combines a stop price (trigger) and a limit price.
When the stop price is reached, a limit order is placed.
python src/cli.py BTCUSDT sell stop_limit --quantity 0.01 --stop_price 67500 --price 67400

Arguments:
--stop_price: The trigger price for the order
--price: The limit price at which the order will be placed

**🔄 4. OCO Order (One Cancels the Other)**
An OCO Order places two orders simultaneously — one limit and one stop-limit.
If one is executed, the other is automatically canceled.
python src/cli.py BTCUSDT sell oco --quantity 0.01 --price 70000 --stop_price 67500 --stop_limit_price 67400

Arguments:
--price: Target limit sell price
--stop_price: The trigger price for stop-limit
--stop_limit_price: The actual stop-limit price after the trigge

**⏱️ 5. TWAP (Time-Weighted Average Price)**
Split a large order into smaller slices executed over time:
python src/cli.py BTCUSDT buy twap --quantity 0.01 --interval 30 --slices 10
--interval: Seconds between orders
--slices: Total number of sub-orders

**📊 6. Grid Strategy**
Execute a grid trading strategy between price ranges:
python src/cli.py BTCUSDT buy grid --lower_price 60000 --upper_price 70000 --grids 5 --investment 100 --quantity 0.001
--lower_price: Lower bound of grid
--upper_price: Upper bound of grid
--grids: Number of grid levels
--investment: Total capital allocation
--quantity: Amount per trade

🧠 Example — Directly Run from Script

You can also execute directly:

python src/market_orders.py BTCUSDT BUY 0.01
