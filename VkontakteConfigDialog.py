import gtk

class VkontakteConfigDialog (object):
	def __init__(self, builder_file, config):
		self.config = config

		builder = gtk.Builder()
		builder.add_from_file(builder_file)

		self.dialog = builder.get_object('preferences_dialog')
		self.filemask = builder.get_object("filemask")
		self.filemask.set_text(self.config.get('filemask'))

		self.dialog.connect("response", self.dialog_response)

	def get_dialog (self):
		return self.dialog

	def dialog_response (self, dialog, response):
		self.config.set('filemask', self.filemask.get_text())
		dialog.hide()
