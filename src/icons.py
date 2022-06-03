import os

class Icons:
    def __init__(self, args):
        self.local_url = ('-local-icons' in args)

        # Discover which icon files are available in the icons directory.
        file_list = os.listdir('icons')
        self.id_set = set()
        for filename in file_list:
            pos = filename.rfind(os.extsep)
            if pos > 0:
                id = filename[:pos]
                self.id_set.add(id)

    def get_id_set(self):
        return self.id_set

    def get_url(self, id, relative=False):
        if id not in self.id_set:
            print(f'No icon found for {id}')

            # Pretend that the icon exists from now on to prevent repeated
            # error messages.
            self.id_set.add(id)

        if relative:
            base = 'icons/'
        elif self.local_url:
            base = 'C:/Users/Chris/Documents/GitHub/lightroom-gps-extractor/icons/'
        else:
            base = 'https://fred-rum.github.io/lightroom-gps-extractor/icons/'

        return f'{base}{id}.png'
