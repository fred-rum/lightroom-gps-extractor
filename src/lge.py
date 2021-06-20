#!/cygdrive/c/Python37/python
#!/usr/bin/env python

import sqlite3

# My files
from group import *

icons = (
    ('table', 'table', 'http://caltopo.com/icon.png?cfg=picnicbench%2C000000%231.0'),
    ('water', 'drinking fountain', 'https://fred-rum.github.io/lightroom-gps-extractor/icons/water.png')
)

sql_con = sqlite3.connect("C:/Users/Chris/Pictures/Lightroom/Photos.lrcat")
sql_con.row_factory = sqlite3.Row

with open('facilities.kml', 'w') as w:
    w.write('''<?xml version="1.0"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <name>Chris Nelson's Bay Area park facilities</name>
    <description>Chris Nelson's Bay Area park facilities</description>
    <Folder>
      <open>1</open>
      <name>Picnic Tables</name>
''')

    for icon in icons:
        (tag, keyword, href) = icon

        sql_results = sql_con.execute(f"""SELECT
AgHarvestedExifMetadata.gpsLatitude as 'latitude',
AgHarvestedExifMetadata.gpsLongitude as 'longitude'
FROM
Adobe_images,
AgLibraryKeywordImage,
AgLibraryKeyword,
AgHarvestedExifMetadata
WHERE
AgHarvestedExifMetadata.hasGPS = 1
AND AgHarvestedExifMetadata.image = Adobe_images.id_local
AND AgLibraryKeywordImage.image = Adobe_images.id_local
AND AgLibraryKeywordImage.tag = AgLibraryKeyword.id_local
AND AgLibraryKeyword.lc_name = '{keyword}';""")

        group = Group(tag, href, sql_results)
        group.write(w)

    w.write('''    </Folder>
  </Document>
</kml>
''')

sql_con.close()
