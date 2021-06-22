#!/cygdrive/c/Python37/python
#!/usr/bin/env python

import sqlite3
import sys
import re

# My files
from cluster import *
from icons import *

# The keywords data is a list of tuples, with each tuple as follows:
#   tag: a safe XML ID and the expected icon name
#   keyword: as used in Lightroom
tag_data = (
    ('parking', 'parking'),
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
supported_tags = set()

for x in tag_data:
    (tag, keyword) = x
    supported_tags.add(tag)

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

tags_used = True
with open('data/points.txt', 'r') as f:
    for index, line in enumerate(f):
        line = line.strip()

        # Look for <latitude>, <longitude> <optional comment>
        matchobj = re.match(r'(-?[0-9]+\.?[0-9]*)\s*,\s*(-?[0-9]+\.?[0-9]*)(?:\s+(.*?))?$', line)
        if matchobj and tags:
            for tag in tags:
                lat = float(matchobj[1])
                lon = float(matchobj[2])
                cluster.add_coord(tag, lat, lon)
            tags_used = True
        elif line in supported_tags:
            if tags_used:
                tags = set()
                tags_used = False
            tags.add(line)
        elif line == '':
            # skip blank lines (including the one followed by EOF)
            pass
        else:
            print(f'Unrecognized line {index} in data/points.txt: {line}')

with open('facilities.kml', 'w') as w:
    w.write('''<?xml version="1.0"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <name>Chris Nelson's Bay Area hiking facilities</name>
''')

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
