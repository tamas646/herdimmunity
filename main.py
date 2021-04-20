#!/usr/bin/python3.7
import gi, math, cairo, threading, time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, Gdk, GLib
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
		self.area_size = (0, 0)
		self.speed_ratio = 1
		self.entities = []
		# simulation settings
		self.entity_velocity = 20 # in px/seconds
		self._initial_virus_carrier_number = 2
		self._entity_number = 25
		self.infection_chance = 12 # 0-100 %
		self.healing_time = 12 # in seconds
		self.immunity_time = 30 # in seconds
		self.infectious_distance = 10

	""" Main entry point """
	def run_app(self):
		self.print_debug('Running app...')
		self._window = MainWindow(self, debugging=False)
		self._window.connect('delete-event', self.stop_app)
		self._window.show_all()
		self._window.init()
		self._main_thread = MainThread(self, tick=20, debugging=False)
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
		"""
		   Generating entities
		"""
		# raffle infected entities
		infected_entities = []
		for i in range(self._initial_virus_carrier_number):
			index = randint(1, self._entity_number) - 1
			while index in infected_entities:
				index += 1
			infected_entities.append(index)
		# request area size
		self.area_size = self._window.get_area_size()
		# generate entities
		self.entities = []
		for i in range(self._entity_number):
			is_infected = i in infected_entities
			position = (randint(0, self.area_size[0] - 1), randint(0, self.area_size[1] - 1))
			direction = uniform(0, math.pi)
			entity = self.Entity(i, is_infected, position, direction)
			self.entities.append(entity)
		# print entities to debug console
		debug_output = 'Generated entities: '
		for entity in self.entities:
			debug_output += '\n' + str(entity)
		self.print_debug(debug_output)
		"""
			Starting thread
		"""
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
		self.entities = []
		self.refresh_simulation_area(0)

	def change_simulation_speed(self, speed_ratio):
		self.print_debug('Changing simulation speed to ' + str(speed_ratio) + 'x')
		self.speed_ratio = speed_ratio

	def refresh_simulation_area(self, time):
		self._window.render_area()
		Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self._window.display_info, time)

	""" Entity class """
	class Entity:
		STATE_HEALTHY = 1
		STATE_INFECTED = 2
		STATE_IMMUNE = 3

		def __init__(self, index, infected, position, direction):
			self.id = index
			self.state = self.STATE_INFECTED if infected else self.STATE_HEALTHY
			self.position = ((float)(position[0]), (float)(position[1])) # (x, y)
			self.direction = (float)(direction) # 0-2π
			self.state_time = 0 # in milliseconds

		def __str__(self):
			return f"{{id: {self.id}, state: {self.state}, position: {self.position}, direction: {self.direction}, state_time: {self.state_time}}}"

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
		self.set_default_size(600, 300)
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
		self._drawing_area.set_size_request(360, 260)

		# Information box
		info_area = Gtk.Box(width_request=200, orientation=Gtk.Orientation.VERTICAL)
		self._status_label = Gtk.Label(label='Megállítva')
		info_area.pack_start(self._status_label, True, True, 0)

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
		self._entity_radius = 5
		self._entity_color = {
			HerdImmunity.Entity.STATE_HEALTHY: (0, 1, 0),
			HerdImmunity.Entity.STATE_INFECTED: (1, 0, 0),
			HerdImmunity.Entity.STATE_IMMUNE: (0, 0, 1),
		}

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
		# draw entities
		for entity in self._herdimmunity.entities:
			color = self._entity_color[entity.state]
			context.set_source_rgb(color[0], color[1], color[2])
			context.arc(self._border_width + self._entity_radius + entity.position[0], self._border_width + self._entity_radius + entity.position[1], self._entity_radius, 0, 2 * math.pi)
			context.fill()

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

	""" Get the 'livable' size of the area """
	def get_area_size(self):
		width = self._drawing_area.get_allocated_width() - 2 * self._border_width - 2 * self._entity_radius
		height = self._drawing_area.get_allocated_height() - 2 * self._border_width - 2 * self._entity_radius
		return (width, height)

	""" Redraw DrawingArea """
	def render_area(self):
		self._drawing_area.queue_draw()

	""" Display simulation info """
	def display_info(self, time):
		self._status_label.set_label(str(time))

	""" Print debug message """
	def print_debug(self, text):
		if self._debugging:
			self._herdimmunity.print_debug('MainWindow: ' + text)


# ======  End of MainWindow Class  =======


# ========================================
# =           MainThread Class           =
# ========================================

class MainThread(threading.Thread):

	""" Constructor """
	def __init__(self, herdimmunity, **kwargs):
		super(MainThread, self).__init__()
		self._herdimmunity = herdimmunity
		self._debugging = kwargs['debugging'] if 'debugging' in kwargs else True
		self._tick = kwargs['tick'] if 'tick' in kwargs else 100 # in milliseconds

	""" Inherited function - call start() instead """
	def run(self):
		self.print_debug('Thread is running...')
		self._time = 0 # in milliseconds
		self._is_running = True
		self._s_paused = False
		self._s_started = False
		while self._is_running:
			if self._s_started:
				if not self._s_paused:
					# infect new entities

					# change entity states if necessary

					# move entities
					for entity in self._herdimmunity.entities:
						s = self._herdimmunity.entity_velocity * self._tick / 1000.0 * self._herdimmunity.speed_ratio
						dx = math.cos(entity.direction) * s
						dy = math.sin(entity.direction) * s
						nx = entity.position[0] + dx
						ny = entity.position[1] + dy
						if nx < 0:
							nx = entity.position[0] - dx
							entity.direction = math.pi - entity.direction
						elif nx > self._herdimmunity.area_size[0]:
							nx = entity.position[0] - dx
							entity.direction = math.pi - entity.direction
						if ny < 0:
							ny = entity.position[1] - dy
							entity.direction = 2 * math.pi - entity.direction
						elif ny > self._herdimmunity.area_size[1]:
							ny = entity.position[1] - dy
							entity.direction = 2 * math.pi - entity.direction
						self.print_debug(f"id: {entity.id}, x: {entity.position[0]}, y: {entity.position[1]} -> dx: {dx}, dy: {dy} -> nx: {nx}, ny: {ny}")
						entity.position = (nx, ny)
					# increase time
					self._time += self._tick * self._herdimmunity.speed_ratio
				self._herdimmunity.refresh_simulation_area(self._time)
			else:
				self._time = 0
			time.sleep(self._tick / 1000.0)
		self.print_debug('Thread stopped')

	""" Controller functions """
	def s_start(self):
		self._s_started = True

	def s_pause(self):
		self._s_paused = True

	def s_continue(self):
		self._s_paused = False

	def s_stop(self):
		self._s_started = False

	""" Terminate thread """
	def stop(self):
		self._is_running = False

	""" Print debug message """
	def print_debug(self, text):
		if self._debugging:
			self._herdimmunity.print_debug('MainThread: ' + text)


# ======  End of MainThread Class  =======


# -----------  Start the application  -----------

herdimmunity = HerdImmunity(version='1.0.0', debugging=True)
herdimmunity.run_app()
