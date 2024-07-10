import os
import sys
import time
import datetime
import socket
import threading
import json

import RPi.GPIO as GPIO

def printLog(msg) :
	t = '[' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '] '
	print(t + msg)

class FanController :
	def __init__(self) :
		# load settings
		if os.path.isfile('settings.json') :
			self.settings = self.loadSettings()
		else :
			self.settings = self.getDefaultSettings()
		self.saveSettings(self.settings)

		# load off time
		self.offTime = self.getOffTime(self.settings['offTime'])

		# setup GPIO
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(21, GPIO.OUT)

	def start(self) :
		self.threadFlag = True

		self.thread = threading.Thread(target=self.run)
		self.thread.deamon = True
		self.thread.start()

	def stop(self) :
		self.threadFlag = False

	def run(self) :
		self.isFanOn = False
		self.fanOnOff(self.isFanOn)

		while self.threadFlag :
			fanOnRequired = False
			fanOffRequired = False

			oneShot = True
			while oneShot :
				oneShot = False

				# check enabled
				if not self.settings['enabled'] :
					if self.isFanOn :
						fanOffRequired = True
					break

				# check off time
				if self.offTime :
					now = datetime.datetime.now().time()
					if self.offTime['start'] < self.offTime['end'] :
						if self.offTime['start'] < now and now < self.offTime['end'] :
							if self.isFanOn :
								fanOffRequired = True
							break
					else :
						if self.offTime['end'] > now or now > self.offTime['start'] :
							if self.isFanOn :
								fanOffRequired = True
							break

				# check temperature
				temperature = self.getTemperature()
				if temperature < self.settings['minTemp'] and self.isFanOn:
					fanOffRequired = True
					break
				elif  temperature > self.settings['maxTemp'] and not self.isFanOn:
					fanOnRequired = True
					break

			# control fan on/off
			if fanOnRequired :
				self.fanOnOff(True)
				printLog('fan on. temp: ' + str(temperature))

			elif fanOffRequired :
				self.fanOnOff(False)
				printLog('fan off. temp: ' + str(temperature))

			# sleep
			time.sleep(self.settings['period'])

	def getTemperature(self) :
		file = open('/sys/class/thermal/thermal_zone0/temp', 'r')
		temp = float(file.read()) / 1000.0
		file.close()
		return temp

	def fanOnOff(self, isOn) :
		self.isFanOn = isOn
		GPIO.output(21, not isOn)

	def getDefaultSettings(self) :
		settings = {}
		settings['enabled'] = True
		settings['period'] = 1 # seconds
		settings['minTemp'] = 38.0
		settings['maxTemp'] = 42.0
		settings['offTime'] = '23:30-09:00'
		return settings

	def loadSettings(self) :
		file = open('settings.json', 'r')
		settings = json.loads(file.read())
		file.close()

		defaultSettings = self.getDefaultSettings()
		for key in defaultSettings.keys() :
			if not settings.get(key) :
				settings[key] = defaultSettings[key]

		return settings

	def saveSettings(self, settings) :
		file = open('settings.json', 'w')
		file.write(json.dumps(settings))
		file.close()

	def getOffTime(self, offTimeStr) :
		times = offTimeStr.split('-')

		if len(times) != 2 :
			return None

		try :
			offTime = {}
			offTime['start'] = datetime.datetime.strptime(times[0], '%H:%M').time()
			offTime['end'] = datetime.datetime.strptime(times[1], '%H:%M').time()
			return offTime
		except :
			return None

	def setEnabled(self, enabled) :
		if enabled == '0' and self.settings['enabled'] :
			self.settings['enabled'] = False
			self.saveSettings(self.settings)
			printLog('fan control disabled')

		elif enabled == '1' and not self.settings['enabled'] :
			self.settings['enabled'] = True
			self.saveSettings(self.settings)
			printLog('fan control enabled')

	def setPeriod(self, period) :
		try :
			period = float(period)
			self.settings['period'] = period
			self.saveSettings(self.settings)
			printLog('control period changed: ' + str(period))
		except :
			pass

	def setMinTemperature(self, temp) :
		try :
			temp = float(temp)
			self.settings['minTemp'] = temp

			if self.settings['maxTemp'] < (self.settings['minTemp'] + 1.0) :
				self.settings['maxTemp'] = self.settings['minTemp'] + 1.0
			self.saveSettings(self.settings)

			printLog('min temperature changed: ' + str(temp))
		except :
			pass

	def setMaxTemperature(self, temp) :
		try :
			temp = float(temp)
			self.settings['maxTemp'] = temp

			if self.settings['minTemp'] > (self.settings['maxTemp'] - 1.0) :
				self.settings['minTemp'] = self.settings['maxTemp'] - 1.0
			self.saveSettings(self.settings)

			printLog('max temperature changed: ' + str(temp))
		except :
			pass

	def setOffTime(self, offTimeStr) :
		if not offTimeStr or offTimeStr == 'disable' :
			self.settings['offTime'] = ''
			self.offTime = None
			self.saveSettings(self.settings)
			printLog('off time disabled')

		else :
			ot = self.getOffTime(offTimeStr)
			if ot :
				self.settings['offTime'] = offTimeStr
				self.offTime = ot
				self.saveSettings(self.settings)
				printLog('off time changed: ' + offTimeStr)

def processCommand(fanController, command) :
	if command['cmd'] == 'enable' :
		fanController.setEnabled(command['val'])

	elif command['cmd'] == 'period' :
		fanController.setPeriod(command['val'])

	elif command['cmd'] == 'min_temp' :
		fanController.setMinTemperature(command['val'])
		
	elif command['cmd'] == 'max_temp' :
		fanController.setMaxTemperature(command['val'])
		
	elif command['cmd'] == 'off_time' :
		fanController.setOffTime(command['val'])

	elif command['cmd'] == 'control' :
		if command['val'] == '0' and fanController.isFanOn :
			fanController.fanOnOff(False)
		elif command['val'] == '1' and not fanController.isFanOn  :
			fanController.fanOnOff(True)

	else :
		printLog('unknown command received')

fanController = FanController()
fanController.start()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
address = ('127.0.0.1', 10105)
sock.bind(address)
sock.listen(1)

try :
	while True :
		conn, addr = sock.accept()
		printLog("accept: " + str(conn) + ", " + str(addr))

		data = conn.recv(4096)
		if len(data) <= 0 :
			conn.close()
			continue

		decodedData = ''
		try :
			decodedData = data.decode()
		except :
			conn.close()
			printLog('decoding received data failed')
			continue

		printLog('command received: ' + decodedData)
		try :
			processCommand(fanController, json.loads(decodedData))
		except :
			conn.close()
			printLog('command format error: ' + decodedData)
			continue

		conn.close()

except KeyboardInterrupt :
	sock.close()
	fanController.stop()
	printLog('successfully terminated')
	sys.exit(0)
