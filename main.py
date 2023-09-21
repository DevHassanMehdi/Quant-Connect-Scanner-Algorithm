# region imports
from AlgorithmImports import *
# endregion
from typing import List
from datetime import datetime, timedelta
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data.UniverseSelection import *


class ScannerAlgorithm(QCAlgorithm):
	
	def Initialize(self):
		# Setting the start and end dates for the backtest
		self.SetStartDate(2023, 9, 20)  # set the start date to 60 minutes ago
		self.SetCash(100000)
		self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Cash)
		
		# Define universe
		self.russell3000 = self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
		
		# Define constants
		self.Tr = datetime.strptime('11:30:00', '%H:%M:%S').time()
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
		
		# Schedule function to run every second
		self.Schedule.On(self.DateRules.EveryDay(),
						 self.TimeRules.Every(timedelta(minutes=1)),
						 self.ScanRussell3000)
	
	# Defining the CoarseSelectionFunction method that takes a coarse universe of symbols as input and returns a list of symbols
	def CoarseSelectionFunction(self, coarse):
		# Filter the coarse universe to include only US equities with market cap between 3- billion
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
		self.Debug(f"Scanning US Equities Russel3000")
		
		# Store the processed symbols that can a potetial ticker in a list
		found_tickers = []
		
		# Loop through each symbol in the list of symbols
		for security in self.ActiveSecurities.Values:
			symbol = security.Symbol
			# Get the current trade bar for the symbol
			trade_bar = self.ActiveSecurities[symbol]
			if trade_bar is None:
				continue
			
			# Get the current market price for the symbol (P)
			self.P = trade_bar.Close
			if not self.P > 0:
				continue
			self.V = trade_bar.Volume
			if not self.V > 0:
				continue
			# Get the historic volume for the last hour (Hvol)
			history = self.History(symbol, self.LM, Resolution.Hour)
			try:
				self.Hvol = history.loc[symbol].iloc[-1]['volume']
			except KeyError:
				self.Debug(f"Historic data not available for {symbol}")
				continue
			
			# Get the current market cap (MarketCap)
			fundamental = security.Fundamentals
			if not fundamental:
				continue
			
			self.MarketCap = fundamental.MarketCap / 1_000_000_000
			
			# Calculate the new market cap (NMC)
			self.NMC = round((self.MarketCap) ** self.power_factor, 2)
			
			# Get the volume for the current second (Vsec)
			current_second = self.Time.second
			self.Vsec = self.V - self.volume_last_second.get(symbol, 0)
			self.volume_last_second[symbol] = self.V
			if self.Vsec <= 0:
				continue
			
			# Get the exact time interval of the last "second" (Vt)
			self.Vt = datetime.now().second - self.Time.second
			if self.Vt <= 0:
				continue
			
			# Calculate Pr based on your reference time (e.g., 11:30 AM)
			self.Tr = self.Time.replace(hour=11, minute=30, second=0, microsecond=0)
			if self.Time == self.Tr:
				self.Pr = self.P
			else:
				self.Pr = self.pr.get(symbol, 0)  # Use the previous Pr if not at reference time
			
			# Store the current Pr for the next iteration
			self.pr[symbol] = self.P
			
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
				# # Now you have all the required information for each stock
				self.Debug(
					f"Potential Ticker: {symbol}, "
					f"P: {self.P}, "
					f"V: {self.V}, "
					f"Pr: {self.Pr}, "
					f"Hvol: {self.Hvol}, "
					f"Market Cap: {self.MarketCap}, "
					f"NMC: {self.NMC}, "
					f"Vsec: {self.Vsec}, "
					f"Vt: {self.Vt}, "
					f"Vmin: {self.Vmin}, "
					f"VPnow: {self.VPnow}, "
					f"VPold: {self.VPold}, "
					f"MinDecline: {self.MinDecline}, "
					f"ActualDescent: {self.ActualDescent}, "
					f"Y: {self.Y}, "
					f"Z: {self.Z}")
				found_tickers.append(symbol)
		
		if found_tickers and len(found_tickers) == 1:
			self.ExecuteTrade(self, found_tickers[0])
	
	def ExecuteTrade(self, symbol):
		self.Debug(f"Executing Trade on ticker: {symbol.Value}")
		# Place bracket order to short the stock
		self.MarketOrder(symbol, - self.trade_size)
		self.StopMarketOrder(symbol, self.trade_size, self.Securities[symbol].Close * 1.02)
		self.StopMarketOrder(symbol, self.trade_size, self.Securities[symbol].Close * 0.98)
		time.sleep(self.duration)
		self.ExitTrade()
	
	def ExitTrade(self):
		self.Debug(f"Exiting Trade")
		# Place buy order to exit the trade
		for holding in self.Portfolio.Values:
			if holding.Invested and holding.IsShort:
				self.MarketOrder(holding.Symbol, abs(holding.Quantity))
