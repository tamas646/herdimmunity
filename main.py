#!/usr/bin/python3.7
import gi, math, cairo, threading, time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
from random import *
from datetime import datetime

# ==========================================
# =           HerdImmunity Class           =
# ==========================================

class HerdImmunity:

	""" Constructor """
	def __init__(self, **kwargs):
		self.version = kwargs['version'] if 'version' in kwargs else '0.0.0'
		self._debugging = kwargs['debugging'] if 'debugging' in kwargs else False

	""" Main entry point """
	def run_app(self):
		self.print_debug('Running app...')
		self._window = MainWindow(self, debugging=False)
		self._window.connect('delete-event', self.stop_app)
		self._window.show_all()
		self._window.init()
		self._main_thread = MainThread(self, tick=100, debugging=True)
		self._main_thread.start()
		self.print_debug('Executing Gtk.main()...')
		Gtk.main()

	""" Main exit point """
	def stop_app(self, window = None, event = None):
		self.print_debug('Stopping app...')
		self._main_thread.stop()
		Gtk.main_quit()

	""" Simulation controllers """
	def start_simulation(self):
		self.print_debug('Starting simulation...')
		self._main_thread.s_start()

	def pause_simulation(self):
		self.print_debug('Simulation paused')
		self._main_thread.s_pause()

	def continue_simulation(self):
		self.print_debug('Continue simulation...')
		self._main_thread.s_continue()

	def stop_simulation(self):
		self.print_debug('Stopping simulation...')
		self._main_thread.s_stop()

	def change_simulation_speed(self, speed_ratio):
		self.print_debug('Changing simulation speed to ' + str(speed_ratio) + 'x')

	""" Print debug message """
	def print_debug(self, text):
		if self._debugging:
			print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] ' + text)


# ======  End of HerdImmunity Class  =======


# -----------  Start the application  -----------

herdimmunity = HerdImmunity(version='1.0.0', debugging=True)
herdimmunity.run_app()
