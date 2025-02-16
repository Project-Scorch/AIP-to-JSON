from pypdf import PdfReader
import re
import pandas as pdr
import json


def DMStoDD(coward):

    # Example input format: ['523317.60S', '1685732.30E']
    lat_str = coward[0]  # '523317.60S'
    lng_str = coward[1]  # '1685732.30E'

    if(lat_str == "null" or lat_str == None):
        return coward

    # Extract direction indicators (last character)
    NSindicator = lat_str[-1]  # 'S' or 'N'
    EWindicator = lng_str[-1]  # 'E' or 'W'

    # Remove the direction character to extract the numeric part
    lat_value = float(lat_str[:-1])  # Convert '523317.60' to float
    lng_value = float(lng_str[:-1])  # Convert '1685732.30' to float

    # Convert to decimal degrees (assuming input is in DMS format)
    lat_degrees = int(lat_value / 10000)  # Extract degrees
    lat_minutes = int((lat_value % 10000) / 100)  # Extract minutes
    lat_seconds = (lat_value % 100)  # Extract seconds

    lng_degrees = int(lng_value / 10000)
    lng_minutes = int((lng_value % 10000) / 100)
    lng_seconds = (lng_value % 100)

    # Convert to decimal degrees
    lat_dd = round(lat_degrees + (lat_minutes / 60) + (lat_seconds / 3600),4)
    lng_dd = round(lng_degrees + (lng_minutes / 60) + (lng_seconds / 3600),4)

    # Apply negative sign for South and West
    if NSindicator == 'W':
        lat_dd *= -1
    if EWindicator == 'S':
        lng_dd *= -1
 
    return [lat_dd, lng_dd]  # Return in Decimal Degrees format



reader = PdfReader("testing\/1_10_NZANR_Part_71_Danger_Areas_D.pdf")

pdfText = ""


pattern = re.compile(
    r"(?P<identifier>NZR\d{3,})\s+"            # Captures NZRxxx
    r"(?P<name>[\w\s]+?)\s+"                   # Captures Name (Non-greedy)
    r"(?P<altitude>\d{3,5}\sFT)\s+"            # Captures Altitude (allows 13500 FT)
    r"\[Activity or Purpose:\]\s(?P<purpose>.*?)\s+"  # Capture full Activity/Purpose (non-greedy)
    r"\[Organisation or Authority:\]\s(?P<authority>[^\n]+)",  # Capture full authority name
    re.DOTALL
)

pattern_boundary = re.compile(
r"(?P<identifier>[A-Za-z0-9]+)\s(?P<sequence>\d+)\s(?P<latitude1>-?\d{6,7}\.\d{2}[NS])\s(?P<longitude1>-?\d{6,7}\.\d{2}[EW])\s(?P<type>[A-Za-z]+)(?:\s(?P<latitude2>-?\d{6,7}\.\d{2}[NS])\s(?P<longitude2>-?\d{6,7}\.\d{2}[EW])\s(?P<distance>[\d\.]+)\s?(?P<units>[A-Za-z]+)?)?",

    re.DOTALL
)


for i in range(len(reader.pages)):
    page = reader.pages[i]
    pdfText += page.extract_text()

matches = [m.groupdict() for m in pattern_boundary.finditer(pdfText)]




pdfjsonformat = ""

pdfjsonformat += "["

for i in range(len(matches)):

    matchestring = str(matches[i])
    matchestring = matchestring.replace("'",'"')
    matchestring = matchestring.replace("None","null")

    pdfjsonformat += matchestring

    if(i < len(matches) - 1):
        pdfjsonformat += ","


pdfjsonformat += "]"


##print(pdfjsonformat)

jsonBoundingPoints = json.loads(pdfjsonformat)

consolidatedPoints = []


for entry in jsonBoundingPoints:
    identifier = entry['identifier']
    sequance = int(entry['sequence'])
    latitude1 = entry['latitude1']
    longitude1 = entry['longitude1']
    distance = entry['distance']
    typejs = entry['type']
    latitude2 = entry['latitude2']
    longitude2 = entry['longitude2']

    consolidatedPoints.append([identifier,sequance,DMStoDD([longitude1,latitude1]), distance, typejs, DMStoDD([longitude2,latitude2])])


refactoredPoints = []
innerlist = []


for i in range(len(consolidatedPoints)):
    if(consolidatedPoints[i][1] == 1):
        if(i > 0):
            refactoredPoints.append(innerlist)
        innerlist = []
        innerlist.append(consolidatedPoints[i][0])
    innerlist.append(consolidatedPoints[i][1:8])
refactoredPoints.append(innerlist)




RefactoredJson = {
    "type": "FeatureCollection",
    "features": []
}


for i in range(len(refactoredPoints)):
    points = []
    if(len(refactoredPoints[i]) > 2):
        geomatarytype = "Polygon"
    else:
        geomatarytype = "Point"

    for k in range(len(refactoredPoints[i]) - 1):
        points.append(refactoredPoints[i][k + 1][1])
  
    if(geomatarytype == "Polygon"):
        points.append(refactoredPoints[i][1][1])

        feature = {
            "type": "Feature",
            "geometry": {
                "type": geomatarytype,
                "coordinates": [points[::-1]]
            },
            "properties": {
                "Name": refactoredPoints[i][0]
            }
        }
    else:
        feature = {
        "type": "Feature",
        "geometry": {
            "type": geomatarytype,
            "coordinates": points[0]
        },
        "properties": {
            "Name": refactoredPoints[i][0]
        }
    }
        
    RefactoredJson["features"].append(feature)

    
savefile = open("output/extracteddata.json","w")


RefactoredJson = str(RefactoredJson)
RefactoredJson = RefactoredJson.replace("'",'"')
RefactoredJson = RefactoredJson.replace("None","null")

savefile.write(RefactoredJson)

print(RefactoredJson)