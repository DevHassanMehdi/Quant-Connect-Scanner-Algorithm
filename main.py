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
		self.SetStartDate(self.Time - timedelta(days=60))
		# Setting the initial cash available for trading
		self.SetCash(100000)
		
		# Setting the resolution of the data
		self.UniverseSettings.Resolution = Resolution.Minute
		
		# Adding a universe selection function to select the securities to trade
		self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
		
		self.min_market_cap = 3
		self.max_market_cap = 6
		
		# Defining the symbols attribute
		self.symbols = []
		
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
						x.MarketCap >= self.min_market_cap * 1000000000
						and x.MarketCap <= self.max_market_cap * 1000000000]
		
		self.Debug(f"fine objects: {len(fine_objects)}")
		
		# Return the fine filtered symbols
		return fine_objects
	
	def Trade(self):
		self.Debug("Trade called")
		for security in self.ActiveSecurities.Values:

			self.Debug(f"{security.Symbol}")
		# # Checking if the data object is not None
		# if data is None:
		# 	return
		#
		# # # Getting the current time
		# # current_time = self.Time
		# # # If the current time is outside the specified interval, do nothing and return
		# # if current_time.time() < datetime.time(self.min_hour, self.min_minute) or current_time.time() > datetime.time(
		# # 		self.max_hour, self.max_minute):
		# # 	return
		#
		# # # Getting the elapsed time
		# # elapsed_time = (datetime.now() - self.start_time).total_seconds()
		# # # If the elapsed time is less than the Tr value, do nothing and return
		# # if elapsed_time < self.Tr:
		# # 	return
		# #
		# # Looping through each symbol in the list of symbols
		# for symbol in data:
		# 	self.Debug(f"Trade symbol: {symbol}")
		# 	# Checking if the symbol exists in the data object
		# 	if symbol not in data:
		# 		continue
		#
		# 	history = self.History(symbol, 1, Resolution.Daily)
		# 	# Checking if the historical data is not empty
		# 	if not history.empty:
		# 		# Checking if the symbol exists in the data object
		# 		if symbol not in data:
		# 			continue
		#
		# 		# Getting the current trade bar for the symbol
		# 		trade_bar = data[symbol]
		# 		# Checking if the trade bar is not None
		# 		if trade_bar is None:
		# 			continue
		#
		# 		# Checking if the Close attribute exists in the trade bar
		# 		if not hasattr(trade_bar, "Close"):
		# 			continue
		#
		# 		# Retrieving the current price for the symbol
		# 		current_price = data[symbol].Close
		# 		self.Debug(f"Curent Price: {current_price}")
		# 		# Retrieving the current volume for the symbol
		# 		current_volume = data[symbol].Volume
		# 		self.Debug(f"Curent Volume: {current_volume}")
		# 		# Calculating the mean of the historical closing prices
		# 		historic_price = history['close'].mean()
		# 		# Calculating the mean of the historical volumes
		# 		historic_volume = history['volume'].mean()
		# 		# Comparing the current price/volume data to the historical data to determine the recent historic price behavior
		# 		if current_price > historic_price and current_volume > historic_volume:
		# 			# Placing trades based on the comparison of the current price/volume data to the recent historic price behavior
		# 			self.SetHoldings(symbol, 1 / len(self.symbols))
		# 			self.Debug(f"Trade placed for {symbol}")
		# 		else:
		# 			# Liquidating the position if the current price/volume data is not favorable
		# 			self.Liquidate(symbol)
		# 			self.Debug(f"Position liquidated for {symbol}")

# # Defining the OnData method that is called every time new data is received
# def OnData(self, data):
# 	self.Debug("OnData called")
# 	# Checking if the data object is not None
# 	if data is None:
# 		return
#
# 	# # Getting the current time
# 	# current_time = self.Time
# 	# # If the current time is outside the specified interval, do nothing and return
# 	# if current_time.time() < datetime.time(self.min_hour, self.min_minute) or current_time.time() > datetime.time(
# 	# 		self.max_hour, self.max_minute):
# 	# 	return
#
# 	# # Getting the elapsed time
# 	# elapsed_time = (datetime.now() - self.start_time).total_seconds()
# 	# # If the elapsed time is less than the Tr value, do nothing and return
# 	# if elapsed_time < self.Tr:
# 	# 	return
# 	#
# 	# Looping through each symbol in the list of symbols
# 	for symbol in self.symbols:
# 		# Checking if the symbol exists in the data object
# 		if symbol not in data:
# 			continue
#
# 		history = self.History(symbol, 1, Resolution.Daily)
# 		# Checking if the historical data is not empty
# 		if not history.empty:
# 			# Checking if the symbol exists in the data object
# 			if symbol not in data:
# 				continue
#
# 			# Getting the current trade bar for the symbol
# 			trade_bar = data[symbol]
# 			# Checking if the trade bar is not None
# 			if trade_bar is None:
# 				continue
#
# 			# Checking if the Close attribute exists in the trade bar
# 			if not hasattr(trade_bar, "Close"):
# 				continue
#
# 			# Retrieving the current price for the symbol
# 			current_price = data[symbol].Close
# 			self.Debug(f"Curent Price: {current_price}")
# 			# Retrieving the current volume for the symbol
# 			current_volume = data[symbol].Volume
# 			self.Debug(f"Curent Volume: {current_volume}")
# 			# Calculating the mean of the historical closing prices
# 			historic_price = history['close'].mean()
# 			# Calculating the mean of the historical volumes
# 			historic_volume = history['volume'].mean()
# 			# Comparing the current price/volume data to the historical data to determine the recent historic price behavior
# 			if current_price > historic_price and current_volume > historic_volume:
# 				# Placing trades based on the comparison of the current price/volume data to the recent historic price behavior
# 				self.SetHoldings(symbol, 1 / len(self.symbols))
# 				self.Debug(f"Trade placed for {symbol}")
# 			else:
# 				# Liquidating the position if the current price/volume data is not favorable
# 				self.Liquidate(symbol)
# 				self.Debug(f"Position liquidated for {symbol}")
