import math

clump_dist = 100

clump_dist_squared = clump_dist * clump_dist

class Coord:
    pass

    def __init__(self, group, lat, lon):
        self.group = group
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
        self.avg_coord = AvgCoord(self.group, self, lat, lon)

        for coord in group.coords:
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
        self.group.coords.add(self)

class AvgCoord:
    pass

    def __init__(self, group, coord, lat, lon):
        self.group = group
        self.lat = lat
        self.lon = lon
        self.n = 1

        self.coords = set()
        self.coords.add(coord)

        # Add this AvgCoord to the master list.
        # print(f'add {self}')
        self.group.avg_coords.add(self)

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
        # print(f'remove {other}')
        self.group.avg_coords.remove(other)

class Group:
    pass

    def __init__(self, tag, href, sql_results):
        self.tag = tag
        self.href = href

        self.coords = set()
        self.avg_coords = set()
        for r in sql_results:
            Coord(self, r['longitude'], r['latitude'])

    def write(self, w):
        first = True
        for avg_coord in self.avg_coords:
            w.write('      <Placemark>\n')
            if first:
                w.write(f"""        <Style id="{self.tag}">
          <IconStyle>
            <hotSpot x="0.5" xunits="fraction" y="0.5" yunits="fraction"/>
            <Icon>
              <href>{self.href}</href>
            </Icon>
          </IconStyle>
        </Style>
""")
                first = False
            else:
                w.write(f'        <styleUrl>#{self.tag}</styleUrl>\n')
            w.write(f'        <Point><coordinates>{avg_coord.lat},{avg_coord.lon},0</coordinates></Point>\n')
            w.write('      </Placemark>\n')
