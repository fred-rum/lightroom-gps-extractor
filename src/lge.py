#!/cygdrive/c/Python37/python
#!/usr/bin/env python

import sqlite3
import sys
import re
import io
import zipfile

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

# If the first tag is present, the second tag is supercilious and discarded.
fold_tags = (
    ('bench', 'seat'),
    ('table', 'bench'),
    ('table', 'seat')
)

###############################################################################
# Read Lightroom SQL

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

sql_con.close()


###############################################################################
# Read data/points.txt

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


###############################################################################
# Write KML

def write_kml(w, relative=False):
    w.write('''<?xml version="1.0"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <name>Chris Nelson's Bay Area hiking facilities</name>
''')

    # Google Earth allows a placemark style to be defined inline with
    # its first usage, but Avenza Maps can't handle that.  So we define
    # all styles first, then list the placemark locations.
    id_set = set()
    for avg_coord in cluster.avg_coords:
        for fold in fold_tags:
            if fold[0] in avg_coord.tags:
                avg_coord.tags.discard(fold[1])

        id = icons.get_id(avg_coord.tags)
        if id and id not in id_set:
            id_set.add(id)
            url = icons.get_url(avg_coord.tags, relative)
            w.write(f"""    <Style id="{id}">
      <IconStyle>
""")

            # The <scale> expands the grouped icon so that it is twice as big
            # rather than just double the resolution.
            #
            # Avenza Maps doesn't support <scale>, which is unfortunate.
            # But I go ahead and emit it in case I'm using the KML with
            # Google Earth, which does support it.
            #
            # CalTopo also doesn't support the KML scale, but it supports
            # scale in GeoJSON, which we write separately.
            if '-' in id:
                w.write(f'        <scale>2</scale>\n')
            w.write(f"""        <Icon>
          <href>{url}</href>
        </Icon>
      </IconStyle>
    </Style>
""")

    for avg_coord in cluster.avg_coords:
        w.write('    <Placemark>\n')

        id = icons.get_id(avg_coord.tags)
        w.write(f'      <styleUrl>#{id}</styleUrl>\n')
        w.write(f'      <Point><coordinates>{avg_coord.lon},{avg_coord.lat},0</coordinates></Point>\n')
        w.write('    </Placemark>\n')

    w.write('''  </Document>
</kml>
''')

    # Knowing which icons were used is useful when writing a KMZ file.
    return id_set

with open('facilities.kml', 'w') as w:
    write_kml(w, relative=False)


###############################################################################
# Write KMZ
#
# Collect the KML file and PNG icons into a single KMZ file

# Either the Python support for directly writing into a ZIP file is awkward
# or the documentation is particularly terrible (or both).  The only way I've
# figured out how to do it is to extract the bytes from io.StringIO

s = io.StringIO()
id_set = write_kml(s, relative=True)

with zipfile.ZipFile('facilities.kmz', mode='w') as archive:
    archive.writestr('facilities.kml', s.getvalue())

    file_set = set()
    for avg_coord in cluster.avg_coords:
        filename = icons.get_url(avg_coord.tags, relative=True)
        if filename and filename not in file_set:
            file_set.add(filename)
            archive.write(filename)


###############################################################################
# Write GeoJSON
#
# CalTopo reads the scale (marker-size) correctly in GeoJSON format.
# But Google Earth can't read GeoJSON.

with open('facilities.json', 'w') as w:
    w.write('{"features":\n')
    w.write(' [\n')

    first = True
    for avg_coord in cluster.avg_coords:
        id = icons.get_id(avg_coord.tags)
        if id:
            if first:
                first = False
            else:
                w.write('  },\n')
            w.write('  {"geometry":\n')
            w.write(f'   {{"coordinates": [{avg_coord.lon},{avg_coord.lat},0,0], "type":"Point"}},\n')
            w.write('   "properties": {\n')
            if '-' in id:
                w.write('    "marker-size":2,\n')
            url = icons.get_url(avg_coord.tags)
            w.write(f'    "marker-symbol": "{url}"\n')
            w.write('   }\n')

    w.write('  }\n')
    w.write(' ],\n')
    w.write(' "type": "FeatureCollection"\n')
    w.write('}\n')
