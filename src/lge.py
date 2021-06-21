#!/cygdrive/c/Python37/python
#!/usr/bin/env python

import sqlite3
import sys

# My files
from cluster import *
from icons import *

# The keywords data is a list of tuples, with each tuple as follows:
#   tag: a safe XML ID and the expected icon name
#   keyword: as used in Lightroom
tag_data = (
    ('restroom', 'restroom'),
    ('table', 'table'),
    ('bench', 'bench'),
    ('seat', 'log/boulder'),
    ('water', 'drinking fountain')
)

sql_con = sqlite3.connect("file:C:/Users/Chris/Pictures/Lightroom/Photos.lrcat?mode=ro", uri=True)
sql_con.row_factory = sqlite3.Row

cluster = Cluster()
icons = Icons(sys.argv)

with open('facilities.kml', 'w') as w:
    w.write('''<?xml version="1.0"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <name>Chris Nelson's Bay Area hiking facilities</name>
''')

    for x in tag_data:
        (tag, keyword) = x

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

        for r in sql_results:
            cluster.add_coord(tag, r['latitude'], r['longitude'])

    id_set = set()
    for avg_coord in cluster.avg_coords:
        w.write('      <Placemark>\n')

        id = icons.get_id(avg_coord.tags)
        if not id:
            print(f'Need icon for {avg_coord.tags}')
        elif id not in id_set:
            url = icons.get_url(avg_coord.tags)
            w.write(f"""        <Style id="{id}">
      <IconStyle>
""")

            # Caltopo doesn't support <scale>, which is unfortunately.
            # But I go ahead and emit it in case I'm using the KML with
            # Google Earth, which does support it.
            if '-' in id:
                w.write(f'        <scale>1.95</scale>\n')

            w.write(f"""        <hotSpot x="0.5" xunits="fraction" y="0.5" yunits="fraction"/>
        <Icon>
          <href>{url}</href>
        </Icon>
      </IconStyle>
    </Style>
""")
            id_set.add(id)
        else:
            w.write(f'        <styleUrl>#{id}</styleUrl>\n')
        w.write(f'        <Point><coordinates>{avg_coord.lon},{avg_coord.lat},0</coordinates></Point>\n')
        w.write('      </Placemark>\n')

    w.write('''  </Document>
</kml>
''')

sql_con.close()
