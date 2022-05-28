#!/cygdrive/c/Python37/python
#!/usr/bin/env python

# Find photos in the Lightroom database with selected tags, get the
# GPS coordinates of those photos, and make a file of geo-located
# icons to be applied to maps.
#
# I use the results in CalTopo (the website), Google Earth (the PC app),
# and Avenza Maps (on Android).
#
# The various apps support either KML/KMZ or GeoJSON.  A KMZ file can
# include the PNG icons directly in the KMZ file.  The other formats
# require that the PNG icons are hosted on a website.
#
# When multiple facilities are near each other, I prefer to group
# them together and show their icons in some non-overlapping manner.
# There are two possible ways to handle these clustered facilities.
# Due to differences in support in the various apps, I've implemented
# both of these and use the best one for each circumstance:
#
# 1. hotspot manipulation: the "hotspot" of each icon is centered on
# the given GPS location.  A single icon should have its hotspot in
# the center of the icon, but in a cluster of icons, the hotspot of
# each icon should be offset so that icons only overlap at their
# edges.
#
# 2. combined icons: a PNG is created for each clustered combination
# of icons, and the cluster is then rendered with that single
# clustered PNG.  In order to look natural, this clustered icon
# should be displayed larger than any individual icon.
# 
#
# In Google Earth, hotspot manipulation only properly offsets the
# icons when looking straight down.  Any tilt of the 3-D camera messes
# up the offset so that the icons overlap.  Therefore, for Google
# Earth I use combined icons.  Google Earth only supports KML/KMZ.  My
# script initially created only a KML file (which uses externally
# hosted icons), but the script now also creats a KMZ file (with
# integrated icons).  Either one works in Google Earth.
#
# Avenza Maps also supports KML/KMZ.  It can't read icons from a
# separate website, however, so my script creates a KMZ file with
# integrated icons for use with Avenza Maps.  (It also works with
# Google Earth as mentioned above.)  Unfortunately, Avenza Maps
# doesn't support icon scaling or hotspot manipulation.  The best I
# can do for now is to emit combined icons and accept that they aren't
# scaled correctly.
#
# CalTopo has some support for KML/KMZ, but not icon scaling or
# hotspot manipulation.  However, CalTopo supports icon scaling in
# GeoJSON, so I create a GeoJSON file for CalTopo.
#
# Note that I don't end up using hotspot manipulation for any of
# the above cases.  I implemented it in the hopes that I could get
# it to work in Avenza Maps, but now I don't use it for anything.


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
#
# These tags are sorted in the order in which their icons should be clustered,
# starting in the upper left and proceeding in rows.
tag_data = (
    ('parking', 'parking'),
    ('restroom', 'restroom'),
    ('water', 'drinking fountain'),
    ('table', 'table'),
    ('bench', 'bench'),
    ('seat', 'log/boulder')
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

def by_lat(avg_coord):
    return -avg_coord.lat

coords = sorted(cluster.avg_coords, key=by_lat)

for coord in coords:
    for fold in fold_tags:
        if fold[0] in coord.tags:
            coord.tags.discard(fold[1])

    # Create a sorted list of tags associated with the coordinate.
    # We'll either create a cluster icons in this order or use a
    # premade cluster icon that we expect to be named in this order.
    coord.tag_list = []
    for x in tag_data:
        tag = x[0]
        if tag in coord.tags:
            coord.tag_list.append(tag)

###############################################################################
# Write KML

def combined_id(tag_list):
    return '-'.join(tag_list)

def write_style(w, id, i, n, relative, small_icons):
    # default values; certain cases below change these values
    style = id
    icon = id
    x = '0.5' # from left side of icon
    y = '0.5' # from bottom of icon
    scale = ''

    if '-' in id:
        if small_icons:
            # When <scale> isn't supported, use the grouped icon
            # that tries to fit big symbols into a small icon.
            icon += '-s'
        else:
            # <scale> expands the grouped icon so that each icon in
            # the group is as large as a single icon.
            scale = f'\n        <scale>2</scale>'

    icon_set.add(icon)

    # If the icon is part of a split cluster, give it an extended ID
    # and adjust its hotspot accordingly.
    if n > 1:
        style += f'-{i}{n}'

        if n > 2:
            if i < 2:
                y = '0.03'
            else: # i >= 2
                y = '0.97'
        # else keep y = 0.5

        if i == 0 or (i == 2 and n == 4):
            x = '0.97'
        elif i == 1 or i == 3:
            x = '0.03'
        # else keep x = 0.5

    if style in style_set:
        # We've already written the style for this ID.
        return

    style_set.add(style)

    url = icons.get_url(icon, relative)

    w.write(f"""    <Style id="{id}">
      <IconStyle>{scale}
        <Icon><href>{url}</href></Icon>
        <hotSpot x="{x}" xunits="fraction" y="{y}" yunits="fraction"/>
      </IconStyle>
    </Style>
""")

def write_kml(w, relative=False, split_clusters=False, small_icons=False):
    # relative = False: use GitHub URLs
    # rslative = True: use relative filenames within the filesystem
    #
    # split_clusters = False: emit a cluster of icons as a single clustered icon
    # split_clusters = True: emit as separate icons with hotspot offsets

    w.write('''<?xml version="1.0"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <name>Chris Nelson's Bay Area hiking facilities</name>
''')

    # Google Earth allows a placemark style to be defined inline with
    # its first usage, but Avenza Maps can't handle that.  So we define
    # all styles first, then list the placemark locations.
    for coord in coords:
        for fold in fold_tags:
            if fold[0] in coord.tags:
                coord.tags.discard(fold[1])

        if split_clusters:
            # I implemented split_clusters to try to work around
            # Avenza's lack of support for icon scales, but then I
            # discovered that Avenza also fails to support hotspot
            # offsets.  Dammit!  So now split_clusters doesn't get
            # used.
            coord.id_list = coord.tag_list
        else:
            coord.id_list = [combined_id(coord.tag_list)]

        for i, id in enumerate(coord.id_list):
            write_style(w, id, i, len(coord.id_list), relative, small_icons)

    for coord in coords:
        for id in coord.id_list:
            w.write('    <Placemark>\n')
            w.write(f'      <styleUrl>#{id}</styleUrl>\n')
            w.write(f'      <Point><coordinates>{coord.lon:.6f},{coord.lat:.6f},0</coordinates></Point>\n')
            w.write('    </Placemark>\n')

    w.write('''  </Document>
</kml>
''')


###############################################################################
# Write KMZ
#
# Collect the KML file and PNG icons into a single KMZ file

# Either the Python support for directly writing into a ZIP file is awkward
# or the documentation is particularly terrible (or both).  The only way I've
# figured out how to do it is to extract the bytes from io.StringIO

def write_kmz(filename, split_clusters, small_icons):
    global icon_set, style_set

    icon_set = set()
    style_set = set()

    s = io.StringIO()
    write_kml(s,
              relative=True,
              split_clusters=split_clusters,
              small_icons=small_icons)

    with zipfile.ZipFile(filename, mode='w') as archive:
        archive.writestr('facilities.kml', s.getvalue())

        for icon in icon_set:
            filename = icons.get_url(icon, relative=True)
            archive.write(filename)


write_kmz('facilities_google.kmz',
          split_clusters=False,
          small_icons=False)

write_kmz('_facilities_avenza.kmz',
          split_clusters=False,
          small_icons=True)


###############################################################################
# Write GeoJSON
#
# CalTopo reads the scale (marker-size) correctly in GeoJSON format.
# But Google Earth can't read GeoJSON.

with open('facilities_caltopo.json', 'w') as w:
    w.write('{"features":\n')
    w.write(' [\n')

    first = True
    for coord in coords:
        id = combined_id(coord.tag_list)
        if first:
            first = False
        else:
            w.write('  },\n')
        w.write('  {"geometry":\n')
        w.write(f'   {{"coordinates": [{coord.lon:.6f},{coord.lat:.6f},0,0], "type":"Point"}},\n')
        w.write('   "properties": {\n')
        if '-' in id:
            w.write('    "marker-size":2,\n')
        url = icons.get_url(id)
        w.write(f'    "marker-symbol": "{url}"\n')
        w.write('   }\n')

    w.write('  }\n')
    w.write(' ],\n')
    w.write(' "type": "FeatureCollection"\n')
    w.write('}\n')
