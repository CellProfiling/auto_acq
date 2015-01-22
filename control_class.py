import os
import fnmatch
import re
from PIL import Image
from lxml import etree
from unicodedata import normalize
import abc
class Base(object):
    """Base class

    Attributes:
        path: A string representing the path to the object.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, path):
        self.path = path

    def get_dir(self):
        """Return parent directory."""
        return os.path.dirname(self.path)

    @abc.abstractmethod
    def get_name(self, path, regex):
        """Return the name of the object, matching regex."""
        match = re.search(regex, os.path.basename(path))
        if match:                      
            return match.group()
        else:
            print('No match')
            return None

    def cut_path(self, regex):
        """Remove part of path name matching regex, and return result."""
        return re.sub(regex, '', self.path)

    @abc.abstractmethod
    def base_type(self):
        """"Return a string representing the type of object this is."""
        pass

class Directory(Base):
    """A directory on the plate."""

    def get_children(self):
        """Return a list of child directories."""
        return next(os.walk(self.path))[1]

    def get_name(self, regex):
        """Return the name of the current directory, matching regex."""
        path = os.path.normpath(self.path)
        return super(Directory, self).get_name(path, regex)

    def get_all_files(self, regex):
        """Return a list of all files matching regex, recursively."""
        file_list = []
        for root, dirnames, filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, regex):
                file_list.append(os.path.join(root, filename))
        return file_list

        #self.commands = commands

    def base_type(self):
        """"Return a string representing the type of object this is."""
        return 'directory'

class File(Base):
    """A file.
    If the file is an image, use PIL Image class to open the image.
    Search xml data using lxml.
    """

    namespace = {'ns':'http://www.openmicroscopy.org/Schemas/OME/2008-09'}

    def serial_no(self):
        """Open an image and find the serial number of the objective that
        acquired the image"""
        im = Image.open(self.path)
        ascii = normalize('NFKD', im.tag[270]).encode('ascii','ignore')
        root = etree.fromstring(ascii)
        return root.xpath('//ns:Objective/@SerialNumber',
                                   namespaces=self.namespace)[0]

    def get_name(self, regex):
        """Return the name of the file, matching regex."""
        path = self.path
        return super(My_image, self).get_name(path, regex)

    def base_type(self):
        """"Return a string representing the type of object this is."""
        return 'file'
