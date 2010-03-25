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

class VkontaktePlugin(rb.Plugin):
		
	def activate(self, shell):
		entry_type = shell.props.db.entry_register_type("VkontakteEntryType")
		source_group = rb.rb_source_group_get_by_name("library")
		self.source = gobject.new(VkontakteSource, name=_("Vkontakte"), shell=shell, plugin=self, entry_type=entry_type, source_group=source_group)
		# Set the source's icon
		width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_LARGE_TOOLBAR)
		icon = gtk.gdk.pixbuf_new_from_file_at_size(self.find_file("icon.ico"), width, height)
		self.source.props.icon = icon
		
		shell.append_source(self.source, None)
		shell.register_entry_type_for_source(self.source, entry_type)

	def deactivate(self, shell):
		self.source.delete_thyself()
		del self.source
