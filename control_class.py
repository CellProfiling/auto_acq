import os
import fnmatch
import re
from PIL import Image
from lxml import etree
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
        """Return current directory."""
        return os.path.dirname(self.path)

    @abc.abstractmethod
    def get_name(self, path, regex):
        """Get name of idtag of image. idtag can be either
        well, job, field, slice or channel."""
        match = re.search(regex, os.path.basename(path))
        if match:                      
            return match.group()
        else:
            print('No match')
            return None

    @abc.abstractmethod
    def base_type(self):
        """"Return a string representing the type of object this is."""
        pass

class Directory(Base):
    """A directory on the plate."""

    #def __init__(self, path):
    #    super(Directory, self).__init__(path)

    def get_children(self):
        """Return a list of child directories."""
        return next(os.walk(self.path))[1]

    def get_name(self):
        """Return the id of the current directory."""

        path = os.path.normpath(self.path)
        regex = '.\d\d--.\d\d'
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

class My_image(Base):
    """An image.
    Use PIL Image class to open image.
    Search xml data using lxml.
    """

    #def __init__(self, path):
    #    super(My_image, self).__init__(path)

    namespace = {'ns':'http://www.openmicroscopy.org/Schemas/OME/2008-09'}

    def serial_no(self):
        """Open an image and find the serial number of the objective that
        acquired the image"""
        im = Image.open(self.path)
        serial = etree.tostring(im.tag[270], encoding='UTF-8')
        root = etree.fromstring(serial)
        return root.xpath('//ns:Objective/@SerialNumber',
                                   namespaces=namespace)[0]

    def get_name(self, idtag):
        """Get name of idtag of image. idtag can be either
        well, job, field, slice or channel."""

        if idtag == 'well':
            regex = 'U\d\d--V\d\d'
        if idtag == 'job':
            regex = 'J\d+'
        if idtag == 'field':
            regex = 'X\d\d--Y\d\d'
        if idtag == 'slice':
            regex = 'Z\d\d'
        if idtag == 'channel':
            regex = 'C\d\d'

        path = self.path
        return super(My_image, self).get_name(path, regex)

    def base_type(self):
        """"Return a string representing the type of object this is."""
        return 'image'
