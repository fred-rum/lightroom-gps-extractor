import os

class Icons:
    def __init__(self, args):
        # Discover which icon files are available in the icons directory.
        self.id = {} # tag set -> style ID
        self.url = {} # tag set -> url
        self.filename = {} # tag set -> relative filename
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
                self.id[tag_set] = basename
                self.url[tag_set] = urlbase + filename
                self.filename[tag_set] = 'icons/' + filename

    def get_id(self, tag_set):
        f_set = frozenset(tag_set)
        if f_set not in self.id:
            # Print an error message and record the tag set so that we don't
            # print the error message again later for the same set.
            print(f'Need icon for {tag_set}')
            self.id[f_set] = None
        return self.id[f_set]

    def get_url(self, tag_set, relative=False):
        f_set = frozenset(tag_set)
        if f_set in self.id:
            if relative:
                return self.filename[f_set]
            else:
                return self.url[f_set]
        else:
            return None
