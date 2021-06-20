#!/cygdrive/c/Python37/python
#!/usr/bin/env python

clump_dist = 100

import sqlite3
import math

sql_con = sqlite3.connect("C:/Users/Chris/Pictures/Lightroom/Photos.lrcat")

sql_con.row_factory = sqlite3.Row

sql_results = sql_con.execute("""SELECT
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
AND AgLibraryKeyword.lc_name = 'table';""")


clump_dist_squared = clump_dist * clump_dist

class Coord:
    pass

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

        # Calculate the latitude as meters from the equator.
        # Assume that the earth's circumference is 40000km.
        self.m_lat = 40000000 / 360 * lat

        # Calculate the longitude as meters from the prime meridian,
        # as measured around the corresponding latitude line.
        # The total length of the latitude line is 40000km times
        # the sine of the latitude.
        lat_len = 40000000 * math.sin(math.radians(lat))
        self.m_lon = lat_len / 360 * lon

        # Initialize a new AvgCoord.
        # If we find other coordinates (with their own AvgCoords) nearby,
        # we'll merge them into this one.
        self.avg_coord = AvgCoord(self, lat, lon)

        for coord in coords:
            # Check whether the previously recorded coordinate is within
            # the clump distance of the current coordinate.  We assume a
            # "flat earth" here, which will result in very weird behavior
            # near the poles, but I don't care about the poles.
            m_lat_diff = self.m_lat - coord.m_lat
            m_lon_diff = self.m_lon - coord.m_lon
            dist_squared = (m_lat_diff * m_lat_diff) + (m_lon_diff * m_lon_diff)
            if dist_squared < clump_dist_squared:
                if  self.avg_coord == coord.avg_coord:
                    # If the nearby coordinate already uses the same avg_coord
                    # as the current coordinate, that's because it was in the
                    # same AvgCoord as a previous coordinate that got
                    # integrated.  So we shouldn't integrate it again.
                    pass
                else:
                    nearby_avg_coord = coord.avg_coord
                    self.avg_coord.integrate(nearby_avg_coord)

        # Add this coordinate to the master list of coordinates.
        coords.add(self)

class AvgCoord:
    pass

    def __init__(self, coord, lat, lon):
        self.lat = lat
        self.lon = lon
        self.n = 1

        self.coords = set()
        self.coords.add(coord)

        # Add this AvgCoord to the master list.
        print(f'add {self}')
        avg_coords.add(self)

    # Combine another AvgCoord into this one.
    def integrate(self, other):
        # Calculate the weighted average of their coordinates.
        self.lat = (self.lat*self.n + other.lat*other.n) / (self.n + other.n)
        self.lon = (self.lon*self.n + other.lon*other.n) / (self.n + other.n)
        self.n += other.n

        # Modify the coordinates that were using the other AvgCoord to instead
        # point to this one.
        for coord in other.coords:
            self.coords.add(coord)
            coord.avg_coord = self

        # Remove the other AvgCoord from the master list.
        print(f'remove {other}')
        avg_coords.remove(other)

coords = set()
avg_coords = set()

for r in sql_results:
    Coord(r['longitude'], r['latitude'])

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
    for avg_coord in avg_coords:
        w.write(f'''      <Placemark>
        <Style>
          <IconStyle>
            <hotSpot x="0.5" xunits="fraction" y="0.5" yunits="fraction"/>
            <Icon>
              <href>http://caltopo.com/icon.png?cfg=picnicbench%2C000000%231.0</href>
            </Icon>
          </IconStyle>
        </Style>
        <description/>
        <name/>
        <Point>
          <coordinates>{avg_coord.lat},{avg_coord.lon},0</coordinates>
        </Point>
      </Placemark>
''')
    w.write('''    </Folder>
  </Document>
</kml>
''')

sql_con.close()
