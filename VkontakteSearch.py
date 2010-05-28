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

import rhythmdb
from xml.dom import minidom
from VkontakteResult import VkontakteResult
import urllib2
import hashlib

APP_ID = 1850196
SECRET_KEY = 'nk0n6I6vjQ'
USER_ID = 76347967

class VkontakteSearch:
	def __init__(self, search_term, db, entry_type):
		self.search_term = search_term
		self.db = db
		self.entry_type = entry_type
		self.query_model = rhythmdb.QueryModel()
		self.result_count = 0
		self.ready_result_count = 0
	
	def make_sig(self, method, query):
		str = "%sapi_id=%scount=200method=%sq=%stest_mode=1v=2.0%s" % (USER_ID, APP_ID, method, query, SECRET_KEY)
		return hashlib.md5(str).hexdigest()
		
	# Returns true if the search is complete, false if it isn't
	def is_complete(self):
		return self.ready_result_count == self.result_count
	
	def add_entry(self, result):
		# Create the db entry and add it to the query model for this search
		entry = self.db.entry_lookup_by_location(result.url)
		if entry == None:
			entry = self.db.entry_new(self.entry_type, result.url)
			if result.title:
				self.db.set(entry, rhythmdb.PROP_TITLE, result.title)
			if result.duration:
				self.db.set(entry, rhythmdb.PROP_DURATION, result.duration)
			if result.artist:
				self.db.set(entry, rhythmdb.PROP_ARTIST, result.artist)
		self.query_model.add_entry(entry, -1)
		self.ready_result_count += 1

	# Starts searching
	def start(self):
		sig = self.make_sig('audio.search', self.search_term)
		path = "http://api.vk.com/api.php?api_id=%s&count=200&v=2.0&method=audio.search&sig=%s&test_mode=1&q=%s" % (APP_ID, sig, urllib2.quote(self.search_term))
		xmldoc = minidom.parse(urllib2.urlopen(path))
		audios = xmldoc.getElementsByTagName("audio")
		for audio in audios:
			self.result_count += 1 
			self.add_entry(VkontakteResult(audio))

