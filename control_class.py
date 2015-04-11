import os
import fnmatch
import re
import tifffile
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
        """Return the part of the name of the object, matching regex."""
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
        return filter(os.path.isdir, [os.path.join(self.path,f)
                      for f in os.listdir(self.path)])

    def get_all_children(self):
        dir_list = []
        for root, dirnames, filenames in os.walk(self.path):
            for dirname in dirnames:
                dir_list.append(os.path.join(root, dirname))
        return dir_list

    def get_name(self, regex):
        """Return the part of the name of the current directory,
        matching regex."""
        path = os.path.normpath(self.path)
        return super(Directory, self).get_name(path, regex)

    def get_files(self, regex):
        return filter(os.path.isfile, [os.path.join(self.path,f)
                      for f in fnmatch.filter(os.listdir(self.path), regex)])

    def get_all_files(self, regex):
        """Return a list of all files matching regex, recursively."""
        file_list = []
        for root, dirnames, filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, regex):
                file_list.append(os.path.join(root, filename))
        return file_list

    def base_type(self):
        """"Return a string representing the type of object this is."""
        return 'directory'

class File(Base):
    """A file.
    If the file is an image, use PIL Image class to open the image.
    Search xml data using lxml.
    """

    namespace = {'ns':'http://www.openmicroscopy.org/Schemas/OME/2008-09'}

    #def meta_data(self):
    #    """Open an image and find the meta data and return it as ascii."""
    #    im = Image.open(self.path)
    #    return normalize('NFKD', im.tag[270]).encode('ascii','ignore')

    def read_image(self):
        with tifffile.TiffFile(self.path) as tif:
            return tif.asarray()

    def meta_data(self):
        with tifffile.TiffFile(self.path) as tif:
            return tif[0].image_description

    #def save_image(self, path, data, metadata):
    #    tifffile.imsave(path, data, description=metadata)

    def serial_no(self):
        """Open an image and find the serial number of the objective that
        acquired the image."""
        asci = self.meta_data()
        root = etree.fromstring(asci)
        return root.xpath('//ns:Objective/@SerialNumber',
                                   namespaces=self.namespace)[0]

    def get_name(self, regex):
        """Return the part of the name of the file, matching regex."""
        path = self.path
        return super(File, self).get_name(path, regex)

    def base_type(self):
        """"Return a string representing the type of object this is."""
        return 'file'
