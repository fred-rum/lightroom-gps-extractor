import math

# clump_dist measures how close two of the same facility must be for them
# to get clumped together.  It is measured in meters.
# I used to have 100, but that's not for situations where I was moving
# quickly (e.g. biking) and my camera's time was a bit off, leading to
# badly ascribed GPS coordinates.
clump_dist = 200

clump_dist_squared = clump_dist * clump_dist

class Coord:
    pass

    def __init__(self, cluster, tag, lat, lon, cluster_unlike):
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
        self.avg_coord = AvgCoord(cluster, self, tag)

        for coord in cluster.coords:
            # Check whether the previously recorded coordinate is within
            # the clump distance of the current coordinate.  We assume a
            # "flat earth" here, which will result in very weird behavior
            # near the poles, but I don't care about the poles.
            m_lat_diff = self.m_lat - coord.m_lat
            m_lon_diff = self.m_lon - coord.m_lon
            dist_squared = (m_lat_diff * m_lat_diff) + (m_lon_diff * m_lon_diff)
            if (dist_squared < clump_dist_squared and
                (cluster_unlike or tag in coord.avg_coord.tags)):
                if self.avg_coord == coord.avg_coord:
                    # If the nearby coordinate already uses the same avg_coord
                    # as the current coordinate, that's because it was in the
                    # same AvgCoord as a previous coordinate that got
                    # integrated.  So we shouldn't integrate it again.
                    pass
                else:
                    nearby_avg_coord = coord.avg_coord
                    self.avg_coord.integrate(cluster, nearby_avg_coord)

        # Add this coordinate to the master list of coordinates.
        cluster.coords.add(self)

class AvgCoord:
    pass

    def __init__(self, cluster, coord, tag):
        self.tags = {tag}
        self.lat = coord.lat
        self.lon = coord.lon
        self.n = 1

        self.coords = {coord}

        # Add this AvgCoord to the master list.
        # print(f'add {self}')
        cluster.avg_coords.add(self)

    # Combine another AvgCoord into this one.
    def integrate(self, cluster, other):
        self.tags.update(other.tags)

        # Calculate the weighted average of both sets of coordinates.
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
        cluster.avg_coords.remove(other)

class Cluster:
    pass

    def __init__(self, cluster_unlike):
        self.coords = set()
        self.avg_coords = set()
        self.cluster_unlike = cluster_unlike

    def add_coord(self, tag, lat, lon):
        Coord(self, tag, lat, lon, self.cluster_unlike)
