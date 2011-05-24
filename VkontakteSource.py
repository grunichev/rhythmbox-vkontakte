# - encoding: utf8 - 
#
# Copyright © 2010 Alexey Grunichev
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import rb, rhythmdb
import gobject, gtk, glib, os
import shutil, tempfile
from VkontakteSearch import VkontakteSearch
from VkontakteConfig import VkontakteConfig
import rhythmdb
	
class VkontakteSource(rb.Source):
	def __init__(self):
		rb.Source.__init__(self)
		self.config = VkontakteConfig()
		self.initialised = False
		self.downloading = False
		self.download_queue = []
		self.__load_current_size = 0
		self.__load_total_size = 0
		self.error_msg = ''
	
	def initialise(self):
		shell = self.props.shell
		
		self.entry_view = rb.EntryView(shell.props.db, shell.get_player(), "", True, False)
		
		query_model = rhythmdb.QueryModel()
		self.props.query_model = query_model
		
		self.entry_view.append_column(rb.ENTRY_VIEW_COL_TITLE, True)
		self.entry_view.append_column(rb.ENTRY_VIEW_COL_ARTIST, False)
		self.entry_view.append_column(rb.ENTRY_VIEW_COL_DURATION, False)
		self.entry_view.set_sorting_order("Title", gtk.SORT_ASCENDING)
		self.entry_view.set_model(query_model)
		self.entry_view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.entry_view.set_shadow_type(gtk.SHADOW_IN)
		
		# Set up the search bar and button UI. This could probably be done in a better way.
		search_entry = gtk.combo_box_entry_new_text()
		self.search_button = gtk.Button("Search")
		alignment = gtk.Alignment()
		alignment.add(self.search_button)
		hbox = gtk.HBox()
		hbox.pack_start(search_entry)
		hbox.pack_start(alignment)
		hbox.set_child_packing(search_entry, True, True, 0, gtk.PACK_START)
		hbox.set_child_packing(alignment, True, True, 2, gtk.PACK_START)
		vbox = gtk.VBox()
		vbox.pack_start(hbox)
		vbox.set_child_packing(hbox, False, False, 2, gtk.PACK_START)
		vbox.pack_start(self.entry_view)
		self.add(vbox)
		self.show_all()
		
		self.search_button.connect("clicked", self.on_search_button_clicked, search_entry)
		search_entry.child.set_activates_default(True)
		search_entry.connect("changed", self.on_search_entry_changed)
		self.search_button.set_flags(gtk.CAN_DEFAULT)
		
		self.searches = {} # Dictionary of searches, with the search term as keys
		self.current_search = "" # The search term of the search results currently being shown

		ev = self.get_entry_view()
		ev.connect_object("show_popup", self.show_popup_cb, self, 0)
		
		action = gtk.Action ('CopyURL', 'Copy URL', 'Copy URL to Clipboard', "")
		action.connect ('activate', self.copy_url, shell)
		action2 = gtk.Action ('Download', 'Download', 'Download', "")
		action2.connect ('activate', self.download, shell)
		action_group = gtk.ActionGroup ('VkontakteSourceViewPopup')
		action_group.add_action (action)
		action_group.add_action (action2)
		shell.get_ui_manager().insert_action_group (action_group)
		
		popup_ui = """
<ui>
  <popup name="VkontakteSourceViewPopup">
    <menuitem name="CopyURL" action="CopyURL"/>
    <menuitem name="Download" action="Download"/>
    <separator/>
  </popup>
</ui>
"""

		self.ui_id = shell.get_ui_manager().add_ui_from_string(popup_ui)
		shell.get_ui_manager().ensure_update()
		
		self.initialised = True
		
	def do_impl_get_entry_view(self):
		return self.entry_view
	
	# rhyhtmbox api break up (0.13.2 - 0.13.3)
	def do_impl_activate(self):
		self.do_selected()

	def do_selected(self):
		if not self.initialised:
			self.initialise()
		self.search_button.grab_default()

	# rhyhtmbox api break up (0.13.2 - 0.13.3)
	def do_impl_get_status(self):
		return self.do_get_status()

	def do_get_status(self):
		if self.error_msg:
			error_msg = self.error_msg
			self.error_msg = ''
			return (error_msg, "", 1)
		if self.downloading:
			if self.__load_total_size > 0:
				# Got data
				progress = min (float(self.__load_current_size) / self.__load_total_size, 1.0)
			else:
				# Download started, no data yet received
				progress = -1.0
			str = "Downloading %s" % self.filename[:70]
			if self.download_queue:
				str += " (%s files more in queue)" % len(self.download_queue)
			return (str, "", progress)
		if self.current_search:
			if self.searches[self.current_search].is_complete():
				return (self.props.query_model.compute_status_normal("Found %d result", "Found %d results"), "", 1)
			else:
				return ("Searching for \"{0}\"".format(self.current_search), "", -1)
			
		else:
			return ("", "", 1)
			
	def do_impl_delete_thyself(self):
		if self.initialised:
			self.props.shell.props.db.entry_delete_by_type(self.props.entry_type)
		rb.Source.do_impl_delete_thyself(self)
		
	def do_impl_can_add_to_queue(self):
		return True
		
	def do_impl_can_pause(self):
		return True
		
	def on_search_button_clicked(self, button, entry):
		# Only do anything if there is text in the search entry
		if entry.get_active_text():
			entry_exists = entry.get_active_text() in self.searches
			# sometimes links become obsolete, so, re-search enabled
			self.searches[entry.get_active_text()] = VkontakteSearch(entry.get_active_text(), self.props.shell.props.db, self.props.entry_type)
			# Start the search asynchronously
			glib.idle_add(self.searches[entry.get_active_text()].start, priority=glib.PRIORITY_HIGH_IDLE)
			# do not create new item in dropdown list if already exists
			if not entry_exists:
				entry.prepend_text(entry.get_active_text())
			# Update the entry view and source so the display the query model relevant to the current search
			self.current_search = entry.get_active_text()
			self.props.query_model = self.searches[self.current_search].query_model
			self.entry_view.set_model(self.props.query_model)
			
	def on_search_entry_changed(self, entry):
		if entry.get_active_text() in self.searches:
			self.current_search = entry.get_active_text()
			self.props.query_model = self.searches[self.current_search].query_model
			self.entry_view.set_model(self.props.query_model)
			
	def show_popup_cb(self, source, some_int, some_bool):
		# rhythmbox api break up (0.13.2 - 0.13.3)
		if hasattr(self, 'show_source_popup'):
			self.show_source_popup("/VkontakteSourceViewPopup")
		else:
			self.show_page_popup("/VkontakteSourceViewPopup")

	def copy_url(self, action, shell):
		# rhythmbox api break up (0.13.2 - 0.13.3)
		try:
			selected_source = shell.get_property("selected-source")
		except:
			selected_source = shell.get_property("selected-page")
		download_url = selected_source.get_entry_view().get_selected_entries()[0].get_playback_uri();
		clipboard = gtk.clipboard_get()
		clipboard.set_text(download_url)
		clipboard.store()

	def download(self, action, shell):
		# rhythmbox api break up (0.13.2 - 0.13.3)
		try:
			selected_source = shell.get_property("selected-source")
		except:
			selected_source = shell.get_property("selected-page")
		for entry in selected_source.get_entry_view().get_selected_entries():
			self.download_queue.append(entry)
		if not self.downloading:
			entry = self.download_queue.pop(0)
			self._start_download(entry)

	def _start_download(self, entry):
		shell = self.props.shell
		self.download_url = entry.get_playback_uri()

		filemask = self.config.get('filemask')
		artist = shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST)[:50].replace('/', '')
		title = shell.props.db.entry_get(entry, rhythmdb.PROP_TITLE)[:50].replace('/', '')
		filemask = filemask.replace('%A', artist)
		filemask = filemask.replace('%T', title)

		self.filename = u"%s - %s" % (shell.props.db.entry_get(entry, rhythmdb.PROP_ARTIST), shell.props.db.entry_get(entry, rhythmdb.PROP_TITLE))
		self.save_location = os.path.expanduser(filemask)
		dir, file = os.path.split(self.save_location)
		if not os.path.exists(dir):
			try:
				os.makedirs(dir)
			except:
				self.error_msg = "Can't create or access directory. Check settings (Edit => Plugins => Configure)"
				self.notify_status_changed()
				return

		# Download file to the temporary folder
		self.output_file = tempfile.NamedTemporaryFile(delete=False)
		self.downloading = True
		self.notify_status_changed()

		self.downloader = rb.ChunkLoader()
		self.downloader.get_url_chunks(self.download_url, 64 * 1024, True, self.download_callback, self.output_file)


	def download_callback (self, result, total, out):
		if not result:
			# Download finished
			out.file.close()
			self.__load_current_size = 0
			self.downloading = False
			# Move temporary file to the save location
			try:
				shutil.move(out.name, self.save_location)
			except:
				self.error_msg = "Can't write to directory. Check settings (Edit => Plugins => Configure)"
				self.notify_status_changed()
				return
			if self.download_queue:
				entry = self.download_queue.pop(0)
				return self._start_download(entry)
			else:
				self.downloading = False
		elif isinstance(result, Exception):
			# Exception occured - should be handled correctly
			print 'Error during downloading process happened'
			pass

		if self.downloading:
			# Write to the file, update downloaded size
			out.file.write(result)
			self.__load_current_size += len(result)
			self.__load_total_size = total

		self.notify_status_changed()
		

gobject.type_register(VkontakteSource)
