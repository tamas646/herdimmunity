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


# ========================================
# =           MainWindow Class           =
# ========================================

class MainWindow(Gtk.Window):

	""" Constructor """
	def __init__(self, herdimmunity, **kwargs):
		self._herdimmunity = herdimmunity
		self._debugging = kwargs['debugging'] if 'debugging' in kwargs else True
		self.print_debug('Preparing main window...')
		Gtk.Window.__init__(self)
		self.set_default_size(800, 400)
		self.set_resizable(True)

		# -----------  Header bar  -----------

		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(True)
		header_bar.props.title = f"Nyájimmunitás {self._herdimmunity.version}"
		self.set_titlebar(header_bar)

		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		Gtk.StyleContext.add_class(box.get_style_context(), 'linked')

		# Stop button
		self._stop_button = Gtk.Button()
		image = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name='media-playback-stop'), Gtk.IconSize.BUTTON)
		self._stop_button.add(image)
		box.add(self._stop_button)

		# Start button
		self._start_button = Gtk.Button()
		image = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name='media-playback-start'), Gtk.IconSize.BUTTON)
		self._start_button.add(image)
		box.add(self._start_button)

		# Speedup button
		self._speedup_button = Gtk.ToggleButton()
		image = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name='media-seek-forward'), Gtk.IconSize.BUTTON)
		self._speedup_button.add(image)
		box.add(self._speedup_button)

		# Pause button
		self._pause_button = Gtk.ToggleButton()
		image = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name='media-playback-pause'), Gtk.IconSize.BUTTON)
		self._pause_button.add(image)
		box.add(self._pause_button)

		header_bar.pack_start(box)

		# Settings button
		self._properties_button = Gtk.Button()
		image = Gtk.Image.new_from_gicon(Gio.ThemedIcon(name='applications-system'), Gtk.IconSize.BUTTON)
		self._properties_button.add(image)

		header_bar.pack_end(self._properties_button)

		# -----------  Window content  -----------

		box = Gtk.Box(margin=20)

		# Drawing area
		self._drawing_area = Gtk.DrawingArea()

		# Information box
		info_area = Gtk.Box(width_request=200, orientation=Gtk.Orientation.VERTICAL)
		self.status_label = Gtk.Label(label='Megállítva')
		info_area.pack_start(self.status_label, True, True, 0)

		box.pack_start(self._drawing_area, True, True, 0)
		box.pack_start(info_area, False, False, 0)
		self.add(box)

		# -----------  Register events  -----------

		self._drawing_area.connect('draw', self._draw)
		self._start_button.connect('clicked', self._start)
		self._pause_button.connect('clicked', self._pause)
		self._speedup_button.connect('clicked', self._speedup)
		self._stop_button.connect('clicked', self._stop)
		self._properties_button.connect('clicked', self._properties)

	""" Initialize window (after shown) """
	def init(self):
		self.print_debug('Initializing window...')
		self._stop_button.hide()
		self._pause_button.set_sensitive(False)
		self._speedup_button.set_sensitive(False)
		self._speedup_ratio = 2
		self._border_color = (0.7, 0.7, 0.7)
		self._border_width = 10

	""" Button events """
	def _draw(self, widget, context):
		self.print_debug('Drawing area...')
		context.set_source_rgb(self._border_color[0], self._border_color[1], self._border_color[2])
		max_width = widget.get_allocated_width()
		max_height = widget.get_allocated_height()
		# draw border
		context.rectangle(0, 0, self._border_width, max_height)
		context.rectangle(0, max_height - self._border_width, max_width, max_height)
		context.rectangle(max_width - self._border_width, 0, max_width, max_height)
		context.rectangle(0, 0, max_width, self._border_width)
		context.fill()
		context.stroke()

	def _start(self, widget):
		self.print_debug('Start button clicked')
		self._start_button.hide()
		self._stop_button.show()
		self._pause_button.set_sensitive(True)
		self._speedup_button.set_sensitive(True)
		self.set_resizable(False)
		self._herdimmunity.start_simulation()

	def _stop(self, widget):
		self.print_debug('Stop button clicked')
		self._stop_button.hide()
		self._start_button.show()
		self._pause_button.set_sensitive(False)
		self._speedup_button.set_sensitive(False)
		self.set_resizable(True)
		self._herdimmunity.stop_simulation()

	def _pause(self, widget):
		if widget.get_active():
			self.print_debug('Pause button pressed')
			self._herdimmunity.pause_simulation()
		else:
			self.print_debug('Pause button released')
			self._herdimmunity.continue_simulation()

	def _speedup(self, widget):
		if widget.get_active():
			self.print_debug('Speedup button pressed')
			self._herdimmunity.change_simulation_speed(self._speedup_ratio)
		else:
			self.print_debug('Speedup button released')
			self._herdimmunity.change_simulation_speed(1)

	def _properties(self, widget):
		self.print_debug('Properties button clicked')

	""" Print debug message """
	def print_debug(self, text):
		if self._debugging:
			self._herdimmunity.print_debug('MainWindow: ' + text)


# ======  End of MainWindow Class  =======

# -----------  Start the application  -----------

herdimmunity = HerdImmunity(version='1.0.0', debugging=True)
herdimmunity.run_app()
