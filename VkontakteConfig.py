import gconf

class VkontakteConfig(object):
	def __init__(self):
		self.gconf_keys = {
			'filemask': '/apps/rhythmbox/plugins/vkontakte/filemask',
		}

		self.gconf = gconf.client_get_default()
		if not self.get('filemask'):
			self.set("filemask", "~/Music/%A - %T.mp3")

	def get(self, key):
		if self.gconf.get_string(self.gconf_keys[key]):
			return self.gconf.get_string(self.gconf_keys[key])
		else:
			return ""

	def set(self, key, value):
		self.gconf.set_string(self.gconf_keys[key], value)
