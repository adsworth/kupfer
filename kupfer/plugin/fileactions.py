import gio
import os
# since "path" is a very generic name, you often forget..
from os import path as os_path

from kupfer.objects import Action, FileLeaf
from kupfer import utils, pretty


__kupfer_name__ = _("File Actions")
__kupfer_sources__ = ()
__kupfer_text_sources__ = ()
__kupfer_actions__ = (
		"Trash",
		"MoveTo",
		"CopyTo",
		"UnpackHere",
		"CreateArchive"
	)
__description__ = _("More file actions")
__version__ = ""
__author__ = "Ulrik Sverdrup <ulrik.sverdrup@gmail.com>"

class Trash (Action):
	# this should never be default
	rank_adjust = -10
	def __init__(self):
		Action.__init__(self, _("Move to Trash"))

	def activate(self, leaf):
		gfile = gio.File(leaf.object)
		gfile.trash()
	def valid_for_item(self, item):
		return os.access(item.object, os.R_OK | os.W_OK)
	def get_description(self):
		return _("Move this file to trash")
	def get_icon_name(self):
		return "user-trash-full"
	def item_types(self):
		yield FileLeaf

def _good_destination(dpath, spath):
	"""If directory path @dpath is a valid destination for file @spath
	to be copied or moved to
	"""
	if not os_path.isdir(dpath):
		return False
	spath = os_path.normpath(spath)
	dpath = os_path.normpath(dpath)
	dest_filename = os_path.join(dpath, os_path.basename(spath))
	if os_path.exists(dest_filename):
		return False
	if not os.access(dpath, os.R_OK | os.W_OK | os.X_OK):
		return False
	cpfx = os_path.commonprefix((spath, dpath))
	parent_spath = os_path.dirname(spath)
	if (os_path.samefile(dpath, spath) or (cpfx == spath) or
			(dpath == parent_spath)):
		return False
	return True

class MoveTo (Action, pretty.OutputMixin):
	def __init__(self):
		Action.__init__(self, _("Move To..."))
	def activate(self, leaf, obj):
		sfile = gio.File(leaf.object)
		bname = sfile.get_basename()
		dfile = gio.File(os_path.join(obj.object, bname))
		try:
			ret = sfile.move(dfile)
			self.output_debug("Move %s to %s (ret: %s)" % (sfile, dfile, ret))
		except gio.Error, exc:
			self.output_error("Move %s to %s Error: %s" % (sfile, dfile, exc))

	def valid_for_item(self, item):
		return os.access(item.object, os.R_OK | os.W_OK)
	def requires_object(self):
		return True

	def item_types(self):
		yield FileLeaf
	def object_types(self):
		yield FileLeaf
	def valid_object(self, obj, for_item):
		return _good_destination(obj.object, for_item.object)
	def get_description(self):
		return _("Move file to new location")

class CopyTo (Action, pretty.OutputMixin):
	def __init__(self):
		Action.__init__(self, _("Copy To..."))

	def is_async(self):
		return True
	def activate(self, leaf, obj):
		return self._start_action, self._finish_action

	def _start_action(self, leaf, iobj=None):
		sfile = gio.File(leaf.object)
		bname = sfile.get_basename()
		dfile = gio.File(os_path.join(iobj.object, bname))
		ret = sfile.copy(dfile)
		self.output_debug("Copy %s to %s (ret: %s)" % (sfile, dfile, ret))

	def _finish_action(self, ret):
		pass

	def item_types(self):
		yield FileLeaf
	def valid_for_item(self, item):
		return (not item.is_dir()) and os.access(item.object, os.R_OK)
	def requires_object(self):
		return True
	def object_types(self):
		yield FileLeaf
	def valid_object(self, obj, for_item):
		return _good_destination(obj.object, for_item.object)
	def get_description(self):
		return _("Copy file to a chosen location")

class UnpackHere (Action):
	def __init__(self):
		Action.__init__(self, _("Extract Here"))
		self.extensions_set = set((".rar", ".7z", ".zip", ".gz", ".tgz",
			".tar", ".lzma", ".bz2"))
	def activate(self, leaf):
		utils.launch_commandline("file-roller --extract-here %s" % leaf.object)

	def valid_for_item(self, item):
		tail, ext = os.path.splitext(item.object)
		# FIXME: Make this detection smarter
		return ext.lower() in self.extensions_set

	def item_types(self):
		yield FileLeaf
	def get_description(self):
		return _("Extract compressed archive")

class CreateArchive (Action):
	def __init__(self):
		Action.__init__(self, _("Create Archive"))
	def activate(self, leaf):
		utils.launch_commandline("file-roller --add %s" % leaf.object)

	def valid_for_item(self, item):
		# FIXME: Only for directories right now
		return item.is_dir()
	def item_types(self):
		yield FileLeaf
	def get_description(self):
		return _("Create a compressed archive from folder")
