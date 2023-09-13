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
		self.SetStartDate(self.Time - timedelta(hours=1))
		# Setting the initial cash available for trading
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
		
		# Define variables
		self.stock = None
		self.Pr = None
		self.Hvol = None
		self.P = None
		self.MarketCap = None
		self.NMC = None
		self.Vsec = None
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
						 self.TimeRules.Every(timedelta(seconds=1)),
						 self.ScanRussell3000)
	
	# Defining the CoarseSelectionFunction method that takes a coarse universe of symbols as input and returns a list of symbols
	def CoarseSelectionFunction(self, coarse):
		# Filter the universe of stocks
		sortedByDollarVolume = sorted(coarse, key=lambda x: x.DollarVolume, reverse=True)
		coarse_objetcs = [x.Symbol for x in sortedByDollarVolume if
						  x.HasFundamentalData and
						  x.DollarVolume >= 100000]
		self.Debug(f"Coarse objects: {len(coarse_objetcs)}")
		# Returning the filtered symbols as a list
		return coarse_objetcs
	
	def FineSelectionFunction(self, fine):
		# Fine Filter the universe of stocks
		fine_objects = [x.Symbol for x in fine if
						x.MarketCap >= self.min_market_cap * 1000000000 and
						x.MarketCap <= self.max_market_cap * 10000000000]
		self.Debug(f"fine objects: {len(fine_objects)}")
		
		# Return the fine filtered symbols
		return fine_objects
	
	def ScanRussell3000(self):
		# Loop through each symbol in the list of symbols
		for security in self.ActiveSecurities.Values:
			symbol = security.Symbol
			
			# Get the current trade bar for the symbol
			trade_bar = self.ActiveSecurities[symbol]
			if trade_bar is None:
				continue
			
			# Check if we are in the warm-up period
			if self.IsWarmingUp:
				self.Debug("Still warming up, data may not be available.")
				return
			
			# Get the current market price for the symbol (P)
			self.P = trade_bar.Close
			
			# Get the historic volume for the last hour (Hvol)
			history = self.History(symbol, self.LM, Resolution.Minute)
			try:
				self.Hvol = history.loc[symbol].iloc[-1]['volume']
			except KeyError:
				self.Debug(f"Historic data not available for {symbol}")
			
			# Get the current market cap (MarketCap)
			fundamental = security.Fundamentals
			self.MarketCap = fundamental.MarketCap
			
			# Calculate the new market cap (NMC)
			self.NMC = round((self.MarketCap / 1_000_000_000) ** 0.5, 2)
			
			# Get the volume for the current second (Vsec)
			current_second = self.Time.second
			self.Vsec = self.ActiveSecurities[symbol].Volume - self.volume_last_second.get(symbol, 0)
			self.volume_last_second[symbol] = self.ActiveSecurities[symbol].Volume
			
			# Get the exact time interval of the last "second" (Vt)
			self.V = self.Time - timedelta(seconds=current_second)
			
			# Calculate Pr based on your reference time (e.g., 11:30 AM)
			self.Tr = self.Time.replace(hour=11, minute=30, second=0, microsecond=0)
			if self.Time == self.Tr:
				self.Pr = self.P
			else:
				self.Pr = self.pr.get(symbol, 0)  # Use the previous Pr if not at reference time
			
			# Store the current Pr for the next iteration
			self.pr[symbol] = self.P
			
			# Now you have all the required information for each stock
			self.Debug(
				f"Symbol: {symbol}, Pr: {self.Pr}, Hvol: {self.Hvol}, P: {self.P}, "
				f"Market Cap: {self.MarketCap}, NMC: {self.NMC}, Vsec: {self.Vsec}, Vt: {self.Vt}"
			)
