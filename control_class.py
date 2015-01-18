import os
import fnmatch
import re

class Compartment(object):
    """A compartment on the plate. Compartments have the following properties:

    Attributes:
        path: A string representing the path to the compartment.
    """

    def __init__(self, path):
        """Return a Compartment object whose path is *path*"""
        self.path = path

    def get_parent(self):
        """Return parent directory."""
        return os.path.abspath(os.path.join(self.path, os.pardir))

    def get_children(self):
        """Return a list of child directories."""
        return next(os.walk(self.path))[1]

    def get_dir(self):
        """Return current directory."""
        return os.path.dirname(self.path)

    def get_name(self):
        """Return the id of the current directory."""
        match = re.search('.\d\d--.\d\d', os.path.dirname(self.path))
        if match:                      
            return match.group()
        else:
            return None

    def get_all_files(self, regex):
        """Return a list of all files matching regex, recursively."""
        file_list = []
        for root, dirnames, filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, regex):
            file_list.append(os.path.join(root, filename))
        return file_list

        #self.commands = commands

from PIL import Image
from lxml import etree

class My_image(object):
    """An image.
    Use PIL Image class to open image.
    Search xml data using lxml.

    Attributes:
        path: A string representing the path to the image.
    """

    namespace = {'ns':'http://www.openmicroscopy.org/Schemas/OME/2008-09'}

    def __init__(self, path):
        self.path

    def serial_no(self):
        """Open an image and find the serial number of the objective that
        acquired the image"""
        im = Image.open(self.path)
        root = etree.fromstring(im.tag[270])
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
        match = re.search(regex, os.path.basename(self.path))
        if match:                      
            return match.group()
        else:
            return None
        
