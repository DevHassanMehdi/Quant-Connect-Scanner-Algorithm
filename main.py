# Import the necessary libraries
from AlgorithmImports import *
from typing import List
import datetime, pytz, time
import pandas as pd
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data.UniverseSelection import *


# Define the ScannerAlgorithm class that inherits from QCAlgorithm
class ScannerAlgorithm(QCAlgorithm):
	
	def Initialize(self):
		# Set the backtest starting date to some previous date
		self.yesterday = datetime.datetime.today() - datetime.timedelta(days=5)
		
		# Set the start and end dates for the backtest
		self.SetStartDate(self.yesterday)
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
		self.trade_size = 0.1
		self.max_trade_size = 50000
		self.interval_size = 1000
		self.IT = 1000
		self.duration = 5
		
		# Function to automate the reference time (This is only used to backtesting)
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
		self.Schedule.On(self.DateRules.EveryDay(),
						 self.TimeRules.At(future_hour, future_minute),
						 self.ScanRussell3000)  # replace self.TimeRules.At(11, 30)	to run the algo at 11:30 AM
	
	def CoarseSelectionFunction(self, coarse):
		# Filter the coarse universe to include only US equities with market cap between 3-6 billion
		filtered = [x for x in coarse if
					x.HasFundamentalData and
					x.Price > 0.5 and
					x.DollarVolume > 100000 and
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
			
			# Check if the symbol has data
			if not security.HasData:
				continue
			
			# Get the current market cap (MarketCap)
			fundamental = security.Fundamentals
			if not fundamental:
				continue
			
			# Get the trade bar
			trade_bar = self.ActiveSecurities[symbol]
			if trade_bar is None:
				continue
			
			# Get the current market price for the symbol (P)
			self.P = trade_bar.Close
			if not isinstance(self.P, (int, float)) and not self.P > 0:
				continue
			
			# Get the current Volume for the symbol (V)
			self.V = trade_bar.Volume
			if not isinstance(self.V, (int, float)) and not self.V > 0:
				continue
			
			# Get the Historic volume of the sybmbol (Hvol)
			try:
				self.Hvol = self.History(symbol, self.LM, Resolution.Minute)['volume'].sum()
				if not isinstance(self.Hvol, (int, float)) and not self.Hvol > 0:
					continue
			except KeyError:
				continue
			
			# Get the market cap
			self.MarketCap = fundamental.MarketCap / 1_000_000_000
			
			# Calculate the new market cap (NMC)
			self.NMC = round((self.MarketCap) ** self.power_factor, 2)
			
			# Get the volume for the passed second (Vsec) and the exact time interval of the trade (Vt)
			for index in range(1, self.LS):
				try:
					# Get the volume for the nearest passed second
					volume_data = self.History(symbol, index + 1, Resolution.Second)
					self.Vsec = volume_data.loc[symbol].iloc[0]['volume']
				# Make sure volume data exists in the history
				except KeyError:
					continue
				# Make sure Vsec value is correct
				if not isinstance(self.Vsec, (int, float)) and not self.Vsec > 0:
					continue
				# Get the exact time of the trade
				time_of_vsec = volume_data.iloc[volume_data.index.get_loc(volume_data.last_valid_index()):].index[0]
				# Get the datetime object of the previous second
				if isinstance(time_of_vsec, tuple):
					time_of_vsec = pd.Timestamp(time_of_vsec[1])
				# Set the Vt value as the time difference between the current second and the last trade second
				self.Vt = float(f"{index}.{self.Time.microsecond}")
				# Make sure the Vt value is correct
				if not isinstance(self.Vt, (int, float)) and not self.Vt >= 1:
					continue
				# Calculate the Vsec value for the passed second
				self.Vsec = self.Vsec / self.Vt
				# Break out of the loop
				break
			
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
			
			# All the required information for each stock
			self.Debug(
				f"Symbol: {symbol}, P: {self.P}, V: {self.V}, Pr: {self.Pr}, Hvol: {self.Hvol}, Market Cap: {self.MarketCap}, NMC: {self.NMC}, Vsec: {self.Vsec}, Vt: {self.Vt}")
			self.Debug(
				f"Vmin: {self.Vmin}, VPnow: {self.VPnow}, VPold: {self.VPold}, MinDecline: {self.MinDecline}, ActualDescent: {self.ActualDescent}, Y: {self.Y}, Z: {self.Z}")
			
			# Check if thresholds are met
			if self.Y > self.Ya and self.Z > self.Za and self.ActualDescent > self.MinDecline:
				# # Get the symbol Information
				# All the required information for each stock
				self.Debug(
					f"Symbol: {symbol}, P: {self.P}, V: {self.V}, Pr: {self.Pr}, Hvol: {self.Hvol}, Market Cap: {self.MarketCap}, NMC: {self.NMC}, Vsec: {self.Vsec}, Vt: {self.Vt}")
				self.Debug(
					f"Vmin: {self.Vmin}, VPnow: {self.VPnow}, VPold: {self.VPold}, MinDecline: {self.MinDecline}, ActualDescent: {self.ActualDescent}, Y: {self.Y}, Z: {self.Z}")
				
				# Append the symbol to the list of found tickers
				found_tickers.append(symbol)
		
		# If only one ticker is found, execute the trade
		if found_tickers and len(found_tickers) == 1:
			self.ExecuteTrade(found_tickers[0])
	
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
