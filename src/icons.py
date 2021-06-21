import os

class Icons:
    def __init__(self, args):
        # Discover which icon files are available in the icons directory.
        self.id = {} # tag set -> style ID
        self.url = {} # tag set -> url
        file_list = os.listdir('icons')
        for filename in file_list:
            pos = filename.rfind(os.extsep)
            if pos > 0:
                basename = filename[:pos]
                tag_set = frozenset(basename.split('-'))
                if '-local-icons' in args:
                    urlbase = 'C:/Users/Chris/Documents/GitHub/lightroom-gps-extractor/icons/'
                else:
                    urlbase = 'https://fred-rum.github.io/lightroom-gps-extractor/icons/'
                url = urlbase + filename
                self.id[tag_set] = basename
                self.url[tag_set] = url

    def get_id(self, tag_set):
        f_set = frozenset(tag_set)
        if f_set in self.id:
            return self.id[f_set]
        else:
            return None

    def get_url(self, tag_set):
        f_set = frozenset(tag_set)
        return self.url[f_set]
