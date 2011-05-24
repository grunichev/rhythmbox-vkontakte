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
import gobject, gtk
from VkontakteSource import VkontakteSource
from VkontakteConfigDialog import VkontakteConfigDialog
from VkontakteConfig import VkontakteConfig

popup_ui = """
<ui>
	<popup name="VkontakteSourceViewPopup">
		<menuitem name="AddToQueueLibraryPopup" action="AddToQueue"/>
	</popup>
</ui>
"""

class VkontakteEntryType(rhythmdb.EntryType):
	def __init__(self):
		rhythmdb.EntryType.__init__(self, name='vkontakte')

	def can_sync_metadata(self, entry):
		return True

class VkontaktePlugin(rb.Plugin):
	def __init__(self):
		self.config = VkontakteConfig()

		rb.Plugin.__init__(self)
		
	def activate(self, shell):
		try:
			entry_type = VkontakteEntryType()
			shell.props.db.register_entry_type(entry_type)
		except NotImplementedError:
			# backward compatibility with 0.12 version
			entry_type = shell.props.db.entry_register_type("VkontakteEntryType")
		# Set the source's icon
		width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_LARGE_TOOLBAR)
		icon = gtk.gdk.pixbuf_new_from_file_at_size(self.find_file("icon.ico"), width, height)
		# rhythmbox api break up (0.13.2 - 0.13.3)
		if hasattr(rb, 'rb_source_group_get_by_name'):
			source_group = rb.rb_source_group_get_by_name("library")
			self.source = gobject.new(VkontakteSource, name=_("Vkontakte"), shell=shell, icon=icon, plugin=self, entry_type=entry_type, source_group=source_group)
			shell.register_entry_type_for_source(self.source, entry_type)
			shell.append_source(self.source, None)
		else:
			source_group = rb.rb_display_page_group_get_by_id ("library")
			self.source = gobject.new(VkontakteSource, name=_("Vkontakte"), shell=shell, plugin=self, pixbuf=icon, entry_type=entry_type)
			shell.register_entry_type_for_source(self.source, entry_type)
			shell.append_display_page(self.source, source_group)

		ui = shell.get_ui_manager()
		self.uid = ui.add_ui_from_string(popup_ui)
		ui.ensure_update()

		self.source.initialise()
	
	def deactivate(self, shell):
		self.source.delete_thyself()
		del self.source
	
	def create_configure_dialog(self, dialog=None):
		if not dialog:
			builder_file = self.find_file("vkontakte-prefs.ui")
			dialog = VkontakteConfigDialog (builder_file, self.config).get_dialog()
		dialog.present()
		return dialog
