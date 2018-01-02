'''
Takes the html of a strava cue sheet (stored in cue-sheet-long.txt )
and a gps file without turn by turn data (stored in Old_tcx.tcx), and creates
a new tcx file that includes turn by turn data
'''
from math import radians, cos, sin, asin, sqrt

from lxml import etree
from lxml import objectify

import numpy as np


from polyline.codec import PolylineCodec

# Creates a CoursePoint element in the xml structure
def addpoint(Loc_data, Route_data):
    new_element = objectify.Element('CoursePoint')
    new_element.Name = Route_data[0][0:10]
    new_element.Time = Loc_data[0]
    new_element.Position = ''
    new_element.Position.LatitudeDegrees = Loc_data[1]
    new_element.Position.LongitudeDegrees = Loc_data[2]
    new_element.PointType = Route_data[1]
    new_element.Notes = Route_data[3]
    etree.strip_attributes(new_element, '{http://codespeak.net/lxml/objectify/pytype}pytype')
    etree.strip_attributes(new_element, '{http://www.w3.org/2001/XMLSchema-instance}nil')
    etree.cleanup_namespaces(new_element)
    return new_element

def find_closest(value,array):
    idx = (np.abs(array-value)).argmin()
    return (array[idx], idx)

def calc_distance(encoding):
    points = PolylineCodec().decode(encoding)

    dist = 0

    for i in range(1,len(points)):
        dist += haversine(points[i-1][1], points[i-1][0], points[i][1], points[i][0])

    return dist


# Calculates the Haversine distance - which takes the distance between two (Lat, Long) pairs,
# using the shortest path across the surface of the earth (ignoring topographic effects)
def haversine(lon1, lat1, lon2, lat2):
    # Greater circle distance b/w two points in km
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    delta_lon = lon2 - lon1
    delta_lat = lat2 - lat1

    # Calculates haversince distance
    a = 2*asin(sqrt(sin(delta_lat/2)**2 + cos(lat1)*cos(lat2)*sin(delta_lon/2)**2))

    # Converts to kms
    km = 6371*a
    
    return km

# Translates from the encoding used by Strava for storing turn-by-turn data in their
# cue sheets
def direction_translate(direction_code, street):
    direction_code = float(direction_code)
    street = street.strip('"')

    direction_flag = 1
    if direction_code == 1:
        direction_out = 'Left'
        direction_label = 'Left'
        direction_code = 1
    elif direction_code == 2:
        direction_out = 'Right'
        direction_label = 'Right'
        direction_code = 1
    elif direction_code == 3:
        direction_out = 'Continue'
        direction_label = 'Straight'
        direction_flag = 0
        direction_code = 0
    else:
        direction_out = 'Proceed'
        direction_label = 'Straight'
        direction_code = 0
    

    if len(street) > 0:
        if direction_flag == 0:
            append = ' on '
        else:
                append = ' onto '
    else:
        append = ''
    
    return [direction_label, direction_code, direction_out + append + street]
                        

if __name__ == "__main__":
    # Opens html for strava cue-sheets
    txt_test = open('cue-sheet-long.txt').read()
    txt_test = txt_test.split('<script>')[-1].split('</script>')[0]

    # Extracts polyline encoded data
    txt_poly = txt_test.split('polyline')[1:]

    # Condenses all polyline segments
    polyline_segments = [item.split('"data":"')[1].split('"},"')[0].replace('\\\\','\\') for item in txt_test.split('polyline')[1:]]
    # Extracts gps coords from polylines
    polyine_totals = [PolylineCodec().decode(encoding) for encoding in polyline_segments]
    polyine_totals = [item for sublist in polyine_totals for item in sublist]
    # Reencodes for one single polyline through all gps points
    re_encoded_polyline  = PolylineCodec().encode(polyine_totals)

    txt_directions = txt_test.split('"directions":[')
    directions_set = [item.split(']')[0] for item in txt_directions[1:]]

    distance_set_2 = [calc_distance(poly) for poly in polyline_segments]

    direction_set = []
    direction_set_4 = []

    # Constructs list of distances between polyline points, and the net distance
    count = 0
    for item in directions_set:
        count = count + 1

        directions = item.split('}')
        count_2 = 0
        for individual in directions[0:-1]:
            count_2 = count_2 + 1
            dist = individual.split('":')
            direction_set.append(1000*sum(distance_set_2[0:count-1]) + float(dist[1].split(',')[0]))
        
            temp = [dist[3].split(',')[0].strip('"'), direction_translate(dist[2].split(',')[0], dist[3].split(',')[0])]
            direction_set_4.append([temp[0], temp[1][0], temp[1][1], temp[1][2]])

    

    # Opens the tcx file without turn by turn data
    tree = objectify.parse('Old_tcx.tcx')
    root = tree.getroot()

    track = root.Courses.Course.Track.Trackpoint

    direction_set_2 = []
    direction_set_3 = []
    for point in track:
        # Coursepoints will need Name, Time, Position (Lat, Long), Pointtype, Notes
        # Pointtype can take the form "Generic", "Summit", "Valley", "Water", "Food", "Danger", "Left", "Right", "Straight", "First Aid", "4th Category", "3rd Category", "2nd Category", "1st Category", "Hors Category", "Sprint"
        point_time = point.Time.pyval
        point_distance = point.DistanceMeters.pyval
        direction_set_2.append(point_distance)
    
        point_lat = point.Position.LatitudeDegrees.pyval
        point_long = point.Position.LongitudeDegrees.pyval

        direction_set_3.append([point_time, point_distance, point_lat, point_long])


    # Cant just write the output here, have to check for overlaps
    ix = 0
    Loc_data_set = []
    Route_data_set = []
    ix_set = []
    code_set = []
    for point in direction_set:
        find_res = find_closest(point, np.asarray(direction_set_2))
    
        Loc_data = direction_set_3[find_res[1]]
        ix_set.append(find_res[1])
        code_set.append(direction_set_4[ix][2])
        Loc_data = [Loc_data[0], Loc_data[2], Loc_data[3]]
        Loc_data_set.append(Loc_data)
        Route_data_set.append(direction_set_4[ix])

        ix = ix + 1

    # Needs to be functionalised - this loop goes through, finds all the duplicate values in the index set, and then filters thenm out based on if the direction is left, right or straight    
    ix_to_delete = []
    for ix in xrange(len(ix_set)-1):
        if (ix_set[ix+1] - ix_set[ix]) < 0.5:
            if (code_set[ix+1] - code_set[ix]) > 0.5:
                ix_to_delete.append(ix)
            else:
                ix_to_delete.append(ix+1)

    # Removes overlapping points (at the junction of polylines)
    ix_set_new = [i for j, i in enumerate(ix_set) if j not in ix_to_delete]
    ix_set_2 = [(np.abs(ix_set-value)).argmin() for value in ix_set_new]


    # Appends etree construct
    for ix in ix_set_2:
        root.Courses.Course.append(addpoint(Loc_data_set[ix],Route_data_set[ix]))
                
    # Writes to tcx
    string = etree.tostring(root)
    string = '<?xml version="1.0" encoding="UTF-8"?>' + string
    new_tcx = open('New_tcx.tcx','w')
    new_tcx.write(string)
    new_tcx.close()
