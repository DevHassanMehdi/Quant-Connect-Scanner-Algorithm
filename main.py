# Import the necessary libraries
from AlgorithmImports import *
from typing import List
import datetime
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data.UniverseSelection import *


# Define the ScannerAlgorithm class that inherits from QCAlgorithm
class ScannerAlgorithm(QCAlgorithm):
	
	def Initialize(self):
		yesterday = datetime.datetime.today() - datetime.timedelta(days=2)
		self.Debug(f"StartDate: {yesterday}")
		
		# Set the start and end dates for the backtest
		self.SetStartDate(yesterday.year, yesterday.month, yesterday.day)  # set the start date to 60 minutes ago
		self.SetCash(100000)
		self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)
		
		# Define universe
		self.russell3000 = self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
		
		# Define constants
		self.Tr = self.Time.replace(hour=11, minute=30, second=0, microsecond=0)
		self.LM = 60
		self.A = 0.3
		self.C = 2500
		self.min_market_cap = 3
		self.max_market_cap = 6
		self.min_descent = 10
		self.power_factor = 0.5
		
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
		
		# Define thresholds
		self.Ya = 0.5
		self.Za = 0.5
		self.pr = {}
		self.volume_last_second = {}
		
		# Define broker configurations
		self.trade_size = 0.1
		self.max_trade_size = 50000
		self.interval_size = 1000
		self.IT = 1000
		self.duration = 30
		
		# Schedule function to run at a specific time
		self.Schedule.On(self.DateRules.EveryDay(),
						 self.TimeRules.Every(timedelta(minutes=1)),
						 self.ScanRussell3000)
	
	# Define the CoarseSelectionFunction method that takes a coarse universe of symbols as input and returns a list of symbols
	def CoarseSelectionFunction(self, coarse):
		# Filter the coarse universe to include only US equities with market cap between 3-6 billion
		filtered = [x for x in coarse if
					x.HasFundamentalData and
					x.Price > 5 and
					x.DollarVolume > 1000000 and
					x.Symbol.SecurityType == SecurityType.Equity and
					x.Symbol.ID.Market == Market.USA]
		# Sort the filtered universe by dollar volume in descending order
		sortedByDollarVolume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
		# Return the top 100 securities by dollar volume
		coarse_objects = [x.Symbol for x in sortedByDollarVolume]
		self.Debug(f"Coarse objects: {len(coarse_objects)}")
		return coarse_objects
	
	def FineSelectionFunction(self, fine):
		# Fine Filter the universe of stocks
		fine_objects = [x.Symbol for x in fine if
						x.MarketCap >= self.min_market_cap * 1000000000 and
						x.MarketCap <= self.max_market_cap * 1000000000]
		self.Debug(f"fine objects: {len(fine_objects)}")
		return fine_objects
	
	def ScanRussell3000(self):
		# Debugging message
		self.Debug(f"Scanning US Equities Russel3000")
		
		# Store the processed symbols that can a potential ticker in a list
		found_tickers = []
		
		# Loop through each symbol in the list of symbols
		for security in self.ActiveSecurities.Values:
			symbol = security.Symbol
			# Get the current market cap (MarketCap)
			fundamental = security.Fundamentals
			if not fundamental:
				continue
			
			# Get the trade bar data for the stock
			history = self.History(symbol, self.LM, Resolution.Minute)
			if history.empty:
				self.Debug(f"Historic data not available for {symbol}")
				continue
			
			# Get the current market price for the symbol (P)
			self.P = history.loc[symbol].iloc[-1]['close']
			# self.Debug(f"P: {symbol}, {self.P}")
			if not self.P > 0:
				continue
			
			self.V = history.loc[symbol].iloc[-1]['volume']
			# self.Debug(f"V: {symbol}, {self.V}")
			if not self.V > 0:
				continue
			
			self.Hvol = self.Hvol = self.History(symbol, self.LM, Resolution.Minute)['volume'].sum()
			# self.Debug(f"Hvol of 60 Minutes: {symbol}, {self.Hvol}")
			if not self.Hvol or not self.Hvol > 0:
				continue
			
			# Get the market cap
			self.MarketCap = fundamental.MarketCap / 1_000_000_000
			
			# Calculate the new market cap (NMC)
			self.NMC = round((self.MarketCap) ** self.power_factor, 2)
			
			# Get the volume for the current second (Vsec)
			current_second = self.Time.second
			self.Vsec = self.V - self.volume_last_second.get(symbol, 0)
			self.volume_last_second[symbol] = self.V
			# self.Debug(f"Vsec: {symbol}, {self.Vsec}")
			if self.Vsec <= 0:
				continue
			
			# Get the exact time interval of the last "second" (Vt)
			self.Vt = datetime.datetime.now().second - current_second
			# self.Debug(f"Vt: {symbol}, {self.Vt}")
			if self.Vt <= 0:
				continue
			
			# Calculate Pr based on your reference time (e.g., 11:30 AM)
			if self.Time == self.Tr:
				self.Pr = self.P
			else:
				self.Pr = self.pr.get(symbol, 0)  # Use the previous Pr if not at reference time
			
			# Store the current Pr for the next iteration
			self.pr[symbol] = self.P
			self.Debug(f"Pr: {symbol}, {self.Pr}")

			if not self.Pr > 0:
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
			
			# Now you have all the required information for each stock
			self.Debug(
				f"Symbol: {symbol}, "
				f"P: {self.P}, "
				f"V: {self.V}, "
				f"Pr: {self.Pr}, "
				f"Hvol: {self.Hvol}, "
				f"Market Cap: {self.MarketCap}, "
				f"NMC: {self.NMC}, "
				f"Vsec: {self.Vsec}, "
				f"Vt: {self.Vt}")
			
			self.Debug(
				f"Vmin: {self.Vmin}, "
				f"VPnow: {self.VPnow}, "
				f"VPold: {self.VPold}, "
				f"MinDecline: {self.MinDecline}, "
				f"ActualDescent: {self.ActualDescent}, "
				f"Y: {self.Y}, "
				f"Z: {self.Z}")
			
			# Check if thresholds are met
			if self.Y > self.Ya and self.Z > self.Za and self.ActualDescent > self.MinDecline:
				# Append the symbol to the list of found tickers
				found_tickers.append(symbol)
		
		# If only one ticker is found, execute the trade
		if found_tickers and len(found_tickers) == 1:
			self.ExecuteTrade(self, found_tickers[0])
	
	def ExecuteTrade(self, symbol):
		# Place a bracket order to short the stock
		self.Debug(f"Executing Trade on ticker: {symbol.Value}")
		self.MarketOrder(symbol, - self.trade_size)
		self.StopMarketOrder(symbol, self.trade_size, self.Securities[symbol].Close * 1.02)
		self.StopMarketOrder(symbol, self.trade_size, self.Securities[symbol].Close * 0.98)
		time.sleep(self.duration)
		self.ExitTrade()
	
	def ExitTrade(self):
		# Place a buy order to exit the trade
		self.Debug(f"Exiting Trade")
		for holding in self.Portfolio.Values:
			if holding.Invested and holding.IsShort:
				self.MarketOrder(holding.Symbol, abs(holding.Quantity))
