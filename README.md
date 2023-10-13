# Quant Connect Russel3000 Equity Scanner Algorithm

## Parameters

| Name               | Type  | Required | Values(default) | Description                                                                                                                              |
|--------------------|-------|----------|-----------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Tr                 | time  | Yes      | None            | The time at which the algorithm will run, set to 11:30 AM.                                                                               |
| LM                 | int   | Yes      | None            | The number of minutes to consider for calculating the historic volume.                                                                   |
| LS                 | int   | Yes      | None            | The number of seconds to consider for calculating the volume for the passed second (Vsec) and the exact time interval of the trade (Vt). |
| A                  | float | Yes      | None            | A constant used in the algorithm to calculate (VPnow).                                                                                   |
| C                  | int   | Yes      | None            | A constant used in the algorithm to calculate (Z).                                                                                       |
| min_market_cap     | int   | Yes      | None            | The minimum market capitalization for a stock to be considered.                                                                          |
| max_market_cap     | int   | Yes      | None            | The maximum market capitalization for a stock to be considered.                                                                          |
| min_descent        | int   | Yes      | None            | The minimum descent for a stock to be considered.                                                                                        |
| power_factor       | float | Yes      | None            | A constant used in the algorithm to calculate (NMC).                                                                                     |
| timer              | int   | Yes      | None            | The maximum running time for the algorithm.                                                                                              |
| counter            | int   | Yes      | None            | A counter to count the number of iterations of the scan.                                                                                 |
| Pr                 | None  | No       | None            | A variable that stores the price of the stock at the reference time.                                                                     |
| Hvol               | None  | No       | None            | A variable that stores the historic volume of the stock.                                                                                 |
| P                  | None  | No       | None            | A variable that stores the current price of the stock.                                                                                   |
| MarketCap          | None  | No       | None            | A variable that stores the market capitalization of the stock.                                                                           |
| NMC                | None  | No       | None            | A variable that stores the new market capitalization of the stock.                                                                       |
| Vsec               | None  | No       | None            | A variable that stores the volume for the passed second.                                                                                 |
| V                  | None  | No       | None            | A variable that stores the volume of the stock.                                                                                          |
| Vt                 | None  | No       | None            | A variable that stores the exact time interval of the trade.                                                                             |
| Vmin               | None  | No       | None            | A variable that stores the minimum volume of the stock.                                                                                  |
| VPnow              | None  | No       | None            | A variable that stores the current volume of the stock.                                                                                  |
| VPold              | None  | No       | None            | A variable that stores the old volume of the stock.                                                                                      |
| MinDecline         | None  | No       | None            | A variable that stores the minimum decline of the stock.                                                                                 |
| ActualDescent      | None  | No       | None            | A variable that stores the actual descent of the stock.                                                                                  |
| Y                  | None  | No       | None            | A variable that stores the Y threshold value.                                                                                            |
| Z                  | None  | No       | None            | A variable that stores the Z threshold value.                                                                                            |
| pr                 | None  | No       | None            | A dictionary that stores the price of the stock at 11:30 AM.                                                                             |
| volume_last_second | None  | No       | None            | A dictionary that stores the volume of the stock for the last second                                                                     |
| Ya                 | float | Yes      | None            | A threshold value used in the algorithm to finalize the ticker.                                                                          |
| Za                 | float | Yes      | None            | A threshold value used in the algorithm to finalize the ticker.                                                                          |
| trade_size         | float | Yes      | None            | The total size of the trade.                                                                                                             |
| max_trade_size     | int   | Yes      | None            | The maximum size of a trade in amount.                                                                                                   |
| interval_size      | int   | Yes      | None            | The size of each interval between individual trades.                                                                                     |
| IT                 | int   | Yes      | None            | Size of each individual trade.                                                                                                           |
| duration           | int   | Yes      | None            | The duration of the after which a buy order id placed to execute the trade.                                                              |

## Functionality

**Initialize**
The Initialize method sets up the backtest starting date, cash, brokerage model, and defines the stocks' universe. It
also defines constants, variables, thresholds, and broker configurations.

```python    
def Initialize(self):
	# Set the backtest starting date to some previous date
	self.yesterday = datetime.datetime.today() - datetime.timedelta(days=30)
	# Set the start and end dates for the backtest
	self.SetStartDate(2023, 9, 11)
	self.SetCash(100000)
	self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)
	
	# Define the stocks universe
	self.russell3000 = self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
	
	# Define constants
	self.Tr = self.Time.replace(hour=11, minute=30, second=0, microsecond=0)
	self.LM = 60
	self.LS = 120
	self.A = 0.3
	self.C = 2500
	self.min_market_cap = 3
	self.max_market_cap = 6
	self.min_descent = 10
	self.power_factor = 0.5
	self.timer = 60
	self.counter = 1
	
	# Define variables
	self.stock = None
	self.Pr = None
	self.Hvol = None
	self.P = None
	self.MarketCap = None
	self.NMC = None
	self.Vsec = None
	self.V = None
	self.Vt = None
	self.Vmin = None
	self.VPnow = None
	self.VPold = None
	self.MinDecline = None
	self.ActualDescent = None
	self.Y = None
	self.Z = None
	self.pr = {}
	self.volume_last_second = {}
	
	# Define thresholds
	self.Ya = 0.5
	self.Za = 0.5
	
	# Define broker configurations
	self.trade_size = 1
	self.max_trade_size = 50000
	self.interval_size = 1000
	self.IT = 1000
	self.duration = 5
	
	# Function to automate the reference time (This is only used for backtesting)
	# Get the current time in the UTC time zone
	now_utc = datetime.datetime.utcnow()
	# Convert the UTC time to the time zone used by QuantConnect
	tz = pytz.timezone('America/New_York')
	now = now_utc.replace(tzinfo=pytz.utc).astimezone(tz)
	# Add 2 minutes to the current minute
	future_minute = now.minute + 1
	if future_minute >= 60:
		future_minute -= 60
		future_hour = now.hour + 1
	else:
		future_hour = now.hour
	
	# Schedule function to run at a specific time
	self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(future_hour, future_minute), self.ScanRussell3000)
# replace self.TimeRules.At(11, 30) to run the algo at 11:30 AM 
```

**CoarseSelectionFunction**
The CoarseSelectionFunction method filters the coarse universe of stocks to include only US equities with price greater
than 0.5, a dollar volume greater than 100,000, and a security type of equity in the US market.

```python
def CoarseSelectionFunction(self, coarse):
	# Filter the coarse universe to include only US equities with market cap between 3-6 billion
	filtered = [x for x in coarse if
				x.HasFundamentalData and x.Price > 0.5 and x.DollarVolume > 100000 and x.Symbol.SecurityType == SecurityType.Equity and x.Symbol.ID.Market == Market.USA]
	# Sort the filtered universe by dollar volume in descending order
	sortedByDollarVolume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
	# Return the top 100 securities by dollar volume
	coarse_objects = [x.Symbol for x in sortedByDollarVolume]
	self.Debug(f"-> Coarse objects: {len(coarse_objects)}")
	return coarse_objects
```

**FineSelectionFunction**
The FineSelectionFunction method further filters the universe of stocks based on the market capitalization.

```python
def FineSelectionFunction(self, fine):
	# Fine Filter the universe of stocks
	fine_objects = [x.Symbol for x in fine if
					x.MarketCap >= self.min_market_cap * 1000000000 and x.MarketCap <= self.max_market_cap * 1000000000]
	self.Debug(f"-> fine objects: {len(fine_objects)}")
	return fine_objects[:5]
```

**ScanRussell3000**
The ScanRussell3000 method is responsible for scanning the Russell 3000 universe of stocks and executing trades based on
the defined criteria. The method is scheduled to run at a specific time using the self.Schedule.On function.

```python
    def ScanRussell3000(self):
	# Debugging message
	self.Debug(f"-> Scanning US Equities Russel3000, Itteration: {self.counter}")
	# Local variables
	# Store the processed symbols that can a potential ticker in a list
	found_tickers = []
	# Timer for measuring the time taken to scan the symbols
	start_time = time.time()
	# Timer for measuring the total run time of the algorithm
	run_time = time.time()
	# Counter for number of successful symbol scans
	symbols_scanned = 0
	# Loop through each symbol in the list of symbols
	for i, security in enumerate(self.ActiveSecurities.Values):
		# Check if all symbols have been scanned
		if i == len(self.ActiveSecurities.Values) - 1:
			# Calculate the time it took for the stocks to scan
			elapsed_time = time.time() - start_time
			self.Debug(
				f"-> Itteration: {self.counter} completed in {elapsed_time} seconds with {symbols_scanned} symbol(s) scanned.")
			# Increment the counter
			self.counter += 1
			# Reset the start time for the next round of scanning
			start_time = time.time()
			# Reset the symbols list iterator
			i = -1
			
			# Check if we have only one symbol meeting our thresholds and execute the trade if yes.
			if len(found_tickers) == 1:
				self.ExecuteTrade(found_tickers[0])
				break
		
		# # # Start the next scan itteration
		# self.ScanRussell3000
		
		# Quit when the algorithm running time exceeds the timer
		if (time.time() - run_time) >= self.timer:
			self.Debug(f"Algorith run time exceeded: {self.timer} seconds")
			self.Debug(f"Terminating scan")
			self.Quit()
			break
		
		# Get the stock symbol
		symbol = security.Symbol
		
		# Get the trade bar
		self.P = self.ActiveSecurities[symbol].Close
		if not self.P or not isinstance(self.P, (int, float)) and not self.P > 0:
			continue
		
		# Get the Historic volume of the sybmbol (Hvol)
		try:
			self.Hvol = self.History(symbol, self.LM, Resolution.Minute)['volume'].sum()
			if not isinstance(self.Hvol, (int, float)) and not self.Hvol > 0:
				continue
		except KeyError:
			continue
		
		# Get the market cap
		self.MarketCap = security.Fundamentals.MarketCap / 1_000_000_000
		
		# Calculate the new market cap (NMC)
		self.NMC = round((self.MarketCap) ** self.power_factor, 2)
		# Get the volume for the passed second (Vsec) and the exact time interval of the trade (Vt)
		for index in range(1, self.LS):
			try:
				# Get the volume for the nearest passed second
				volume_data = self.History(symbol, index, Resolution.Second)
				self.Vsec = volume_data.loc[symbol]['volume'].sum()
				if not isinstance(self.Vsec, (int, float)) and not self.Vsec > 0:
					continue
			# self.Debug(f"-> Actual Vsec at the index: {self.Vsec}. Time: {self.Time}")
			# Make sure volume data exists in the history
			except KeyError:
				continue
			
			# Get the exact time of the trade
			time_of_vsec = volume_data.iloc[volume_data.index.get_loc(volume_data.last_valid_index()):].index[0]
			# Get the datetime object of the previous second
			if isinstance(time_of_vsec, tuple):
				time_of_vsec = pd.Timestamp(time_of_vsec[1])
			
			# Set the Vt value as the time difference between the current second and the last trade second
			self.Vt = (self.Time - time_of_vsec).total_seconds()
			# Make sure the Vt value is correct
			if not isinstance(self.Vt, (int, float)) and not self.Vt > 0:
				continue
			
			# If self.Vt is less than 1, set the value to 1
			if self.Vt < 1:
				self.Vt = 1
			
			# Calculate the Vsec value for the passed second
			self.Vsec = self.Vsec / self.Vt
			
			# Break out of the loop
			break
		if self.Vsec is None:
			self.RemoveSecurity(symbol)
			# self.Debug(f"Stock deleted! No trade found for {symbol} in the last 120 seconds.")
			continue
		
		# Get the Price of the stock at the reference time (self.Tr)
		if not self.pr.get(symbol, 0):
			# Store the price value at 11:30
			self.pr[symbol] = self.P
			self.Pr = self.pr.get(symbol, 0)
		if not isinstance(self.Pr, (int, float)) and not self.Pr > 0:
			continue
		
		# Calculate Vmin
		self.Vmin = self.Vsec / self.Vt * 60
		
		# Calculate VPnow
		self.VPnow = self.Vmin * self.P * self.A / 1000
		
		# Calculate VPold
		self.VPold = self.Pr * self.Hvol / 1000
		
		# Calculate MinDecline and ActualDescent
		self.MinDecline = self.min_descent / self.NMC / 10000
		self.ActualDescent = (self.Pr - self.P) / self.Pr
		
		# Calculate Y and Z
		self.Y = self.VPnow / self.NMC
		self.Z = self.C * self.NMC * self.VPnow / self.VPold
		
		# Increment the the number of sumbols scanned 
		symbols_scanned += 1
		
		# # All the required information for each stock
		# self.Debug(
		# 	f"-> Symbol: {symbol}, P: {self.P}, Pr: {self.Pr}, Hvol: {self.Hvol}, Market Cap: {self.MarketCap}, NMC: {self.NMC}, Vsec: {self.Vsec}, Vt: {self.Vt}")
		# self.Debug(
		# 	f"Vmin: {self.Vmin}, VPnow: {self.VPnow}, VPold: {self.VPold}, MinDecline: {self.MinDecline}, ActualDescent: {self.ActualDescent}, Y: {self.Y}, Z: {self.Z}")
		
		# Check if thresholds are met
		if self.Y > self.Ya and self.Z > self.Za and self.ActualDescent > self.MinDecline:
			# Get the symbol Information
			# All the required information for each stock
			self.Debug(
				f" -> -> -> Ticker: {symbol}, P: {self.P}, Pr: {self.Pr}, Hvol: {self.Hvol}, Market Cap: {self.MarketCap}, NMC: {self.NMC}, Vsec: {self.Vsec}, Vt: {self.Vt}")
			self.Debug(
				f"Vmin: {self.Vmin}, VPnow: {self.VPnow}, VPold: {self.VPold}, MinDecline: {self.MinDecline}, ActualDescent: {self.ActualDescent}, Y: {self.Y}, Z: {self.Z}")
			
			# Append the potential ticker to the tickers list
			found_tickers.append(symbol)
```

**ExecuteTrade**
This function is responsible for executing a trade on a given stock symbol. It places a bracket order to short the stock
and manages the trade size to ensure it does not exceed the maximum trade size defined in the algorithm.

```python
        def ExecuteTrade(self, symbol):
	# Place a bracket order to short the stock
	self.Debug(f"Executing Trade on ticker: {symbol.Value}")
	# Calculate the total trade size
	self.trade_size = self.trade_size * self.Vsec
	# Abort trade if the trade size exceeds the the maximum ammount
	if self.trade_size > self.max_trade_size:
		self.Debug(
			f"Aborting Trade on ticker: {symbol.Value}. Trade size exceeded maximum value: {self.max_trade_size}")
		self.Quit()
	# Place individual trades at the specified time intervals
	while True:
		if self.trade_size >= self.IT:
			self.MarketOrder(symbol, - self.IT)
			self.StopMarketOrder(symbol, self.IT, self.Securities[symbol].Close * 1.02)
			self.StopMarketOrder(symbol, self.IT, self.Securities[symbol].Close * 0.98)
			self.trade_size -= self.IT
		elif self.trade_size < self.IT and self.trade_size != 0:
			self.MarketOrder(symbol, - self.trade_size)
			self.StopMarketOrder(symbol, self.trade_size, self.Securities[symbol].Close * 1.02)
			self.StopMarketOrder(symbol, self.trade_size, self.Securities[symbol].Close * 0.98)
			break
		else:
			break
		time.sleep((self.interval_size) / 1000)
	# Execute the trade after the specified duration
	time.sleep((self.duration))
	self.ExitTrade()
```

**ExitTrade**
This function is responsible for exiting a trade by placing a buy order to cover the short position. It iterates over
the portfolio holdings and checks if a holding is invested and is a short position. If it is, it places a market order
to buy the quantity of shares equal to the absolute value of the holding's quantity.

```python
    def ExitTrade(self):
	# Place a buy order to exit the trade
	self.Debug(f"Exiting Trade")
	for holding in self.Portfolio.Values:
		if holding.Invested and holding.IsShort:
			self.MarketOrder(holding.Symbol, abs(holding.Quantity))
	self.Quit()
```
