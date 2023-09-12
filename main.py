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
		self.SetStartDate(self.Time - timedelta(days=30))
		# Setting the initial cash available for trading
		self.SetCash(100000)
		
		# Setting the resolution of the data
		self.UniverseSettings.Resolution = Resolution.Minute
		
		# Adding a universe selection function to select the securities to trade
		self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
		
		self.min_market_cap = 3
		self.max_market_cap = 6
		self.pr = {}
		self.volume_last_second = {}
		
		# Schedule the Trade function to run every day at 11:30 AM NYT
		# self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(11, 30), self.Trade)
		self.Schedule.On(self.DateRules.EveryDay(),
						 self.TimeRules.Every(timedelta(minutes=1)),
						 self.Trade)
	
	# Defining the CoarseSelectionFunction method that takes a coarse universe of symbols as input and returns a list of symbols
	def CoarseSelectionFunction(self, coarse):
		self.Debug("CoarseSelectionFunction called")
		
		# Filter the universe of stocks
		sortedByDollarVolume = sorted(coarse, key=lambda x: x.DollarVolume, reverse=True)
		coarse_objetcs = [x.Symbol for x in sortedByDollarVolume if
						  x.HasFundamentalData and
						  x.DollarVolume >= 100000]
		
		self.Debug(f"Filtered Symbols: {len(coarse_objetcs)}")
		
		# Returning the filtered symbols as a list
		return coarse_objetcs
	
	def FineSelectionFunction(self, fine):
		self.Debug("FineSelectionFunction called")
		
		# Fine Filter the universe of stocks
		fine_objects = [x.Symbol for x in fine if
						x.MarketCap >= self.min_market_cap * 1
						and x.MarketCap <= self.max_market_cap * 10000000000]
		
		self.Debug(f"fine objects: {len(fine_objects)}")
		
		# Return the fine filtered symbols
		return fine_objects
	
	def Trade(self):
		self.Debug("Trade called")
		
		# # Getting the current time
		# current_time = self.Time
		# # If the current time is outside the specified interval, do nothing and return
		# if current_time.time() < datetime.time(self.min_hour, self.min_minute) or current_time.time() > datetime.time(
		# 		self.max_hour, self.max_minute):
		# 	return
		
		# # Getting the elapsed time
		# elapsed_time = (datetime.now() - self.start_time).total_seconds()
		# # If the elapsed time is less than the Tr value, do nothing and return
		# if elapsed_time < self.Tr:
		# 	return
		#
		
		# Looping through each symbol in the list of symbols
		for security in self.ActiveSecurities.Values:
			symbol = security.Symbol
			self.Debug(f"Trade symbol: {symbol}")
			self.pr[symbol] = 0
			self.volume_last_second[symbol] = 0
			
			# Getting the current trade bar for the symbol
			trade_bar = self.ActiveSecurities[symbol]
			# Checking if the trade bar is not None
			if trade_bar is None:
				continue
			
			# Getting the current market price for the symbol
			current_price = trade_bar.Close
			
			# Getting the historic volume for the symbol
			history = self.History(symbol, 60, Resolution.Minute)
			try:
				historic_volume = history.loc[symbol].iloc[-1]['volume']
				fundamental = security.Fundamentals
				market_cap = fundamental.MarketCap
				# Calculating the new market cap for the symbol
				new_market_cap = round((market_cap / 1000000000) ** 0.5, 2)
				
				# Getting the volume for the current second
				current_second = self.Time.second
				volume_this_second = self.ActiveSecurities[symbol].Volume - self.volume_last_second[symbol]
				self.volume_last_second[symbol] = self.ActiveSecurities[symbol].Volume
				
				# Getting the exact time interval of the last "second"
				exact_time_interval = self.Time - timedelta(seconds=current_second)
				
				# Printing the preliminary values for the symbol
				self.Debug(
					f"Symbol: {symbol}, Pr: {self.pr[symbol]}, Hvol: {historic_volume}, P: {current_price}, Market Cap: {market_cap}, NMC: {new_market_cap}, Vsec: {volume_this_second}, Vt: {exact_time_interval}")
			
			except KeyError:
				self.Debug(f"Historic data not available for {symbol}")
# symbol = security.Symbol
# self.Debug(f"Trade symbol: {symbol}")
#
# history = self.History(symbol, 60, Resolution.Minute)
# self.Debug(f"Symbol history: {[x for x in history]}")
#
# # Checking if the historical data is not empty
# if history.empty:
# 	continue
#
# # Getting the current trade bar for the symbol
# trade_bar = self.ActiveSecurities[symbol]
# # Checking if the trade bar is not None
# if trade_bar is None:
# 	continue
#
# # Checking if the Close and Volume attribute exists in the trade bar
# if not hasattr(trade_bar, "Close"):
# 	continue
#
# # Checking if the Close and Volume attribute exists in the trade bar
# if not hasattr(trade_bar, "Volume"):
# 	continue

# # Retrieving the current price for the symbol
# current_price = history['close'][-1]
# self.Debug(f"Curent Price: {current_price}")

# # Retrieving the current volume for the symbol
# current_volume = history['volume'][-1]
# self.Debug(f"Curent Volume: {current_volume}")

# # Calculating the mean of the historical closing prices
# historic_price = history['close'].mean()
# self.Debug(f"Historic Price: {historic_price}")

# # Calculating the mean of the historical volumes
# historic_volume = history['volume'].mean()
# self.Debug(f"Historic Volume: {historic_volume}")

# # Comparing the current price/volume data to the historical data to determine the recent historic price behavior
# if current_price > historic_price and current_volume > historic_volume:
# 	# Placing trades based on the comparison of the current price/volume data to the recent historic price behavior
# 	self.SetHoldings(symbol, 1 / len(self.ActiveSecurities))
# 	self.Debug(f"Trade placed for {symbol}")
# else:
# 	# Liquidating the position if the current price/volume data is not favorable
# 	self.Liquidate(symbol)
# 	self.Debug(f"Position liquidated for {symbol}")
