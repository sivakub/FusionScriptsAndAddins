import json
import os
from pathlib import Path
import re

toolHierachy = os.path.join(Path(__file__).parent.absolute(), "toolHierachy.json")
toolPropsFile = os.path.join(Path(__file__).parent.absolute(), "ISO13399 item properties.json")


def getToolType(isoType):
    try:
        mappedIso = getMappedIso(isoType)

        if mappedIso is not None:
            return mappedIso.get("hierachy")
    
    except:
        return None


def getToolPropertyFile(file):
    with open(file, 'r') as f:
        data = json.loads(f.read())

    return data


def getToolProperty(bsuName):
    data = getToolPropertyFile("ISO13399 item properties.json")
    for i in data.get("ToolProperties"):
        if i.get("BSU") == bsuName:
            return i.get("PropertyName")

    return None

def mapIsoData(isoProp):

    with open(toolPropsFile, 'r') as file:
        toolPropData = json.load(file)

    toolProps = toolPropData.get('ToolProperties')
    for i in toolProps:
        if i.get("BSU") == isoProp:
            return i.get("Symbol")
    return None


def formatString(txt):
    return str(txt.replace('"', "").replace("'", ""))


def getPlibPropertyRef(pramList):
    plib = [ ]
    for i in pramList:
        txt = re.findall("PLIB_PROPERTY_REFERENCE", str(i))
        if len(txt) > 0:
            plib.append(str(i))

    return plib


def getISOType(pramList):
    iso = [ ]
    for i in pramList:
        txt = re.findall("PLIB_CLASS_REFERENCE", str(i))
        if len(txt) > 0:
            ab = re.findall("'.{13}'", str(i))
            iso.append(formatString(ab[ 0 ]))
    return iso

def getMappedIso(isoType):
    with open(toolHierachy, 'r') as th:
        toolHiedata = json.load(th)

    for i in isoType:
        for tlH in toolHiedata:
            if tlH.get(i) is not None:
                return tlH.get(i)

    return None

def getallPropRefISOcode(plibRef) -> tuple():
    allProp = [ ]
    for i in plibRef:
        key = i.split("=")[ 0 ]
        ab = formatString(re.findall("'.{13}'", i)[ 0 ])
        obj = (key, ab)
        allProp.append(obj)

    return allProp


def getPropKey(pramList, key):
    for i in pramList:
        txt = re.findall('PROPERTY\(\(', str(i))
        if len(txt) > 0:
            if str(i).split(",")[ 3 ] == key:
                return str(i).split("=")[ 0 ]

    return None


def getPropValueRepKey(pramList, key):
    for i in pramList:
        txt = re.findall(r'\bPROPERTY_VALUE_REPRESENTATION\(', str(i))
        if len(txt) > 0:
            temp = str(i).split("PROPERTY_VALUE_REPRESENTATION(")[ 1 ].split(");")[ 0 ].split(",")
            if temp[ 0 ] == key:
                return temp[ 3 ]
    return None


def getDataEntity(data, key):
    return data.get(key)


def getPropValueType(data, key):
    val = str(getDataEntity(data, key)).split("=")[ 1 ].split("(")
    return val[ 0 ]


def getPropItem(data, refKey):
    valType = getPropValueType(data, refKey) + "("
    val = str(getDataEntity(data, refKey)).split(valType)[ 1 ].split(");")[ 0 ].split(",")
    return val


def getStringValue(data, valKey):
    valKey = str(getDataEntity(data, valKey)).split("MULTI_LANGUAGE_STRING(")[ 1 ].split(");")[ 0 ].split(",")[ 1 ]
    stringVal = str(getDataEntity(data, valKey)).split("STRING_WITH_LANGUAGE(")[ 1 ].split(");")[ 0 ].split(",")
    return stringVal[ 0 ]


def getPropertyName(data, propRefKey):
    return str(getPropItem(data, propRefKey)[0]).replace("'", "")


def getPropertyValue(data, propRefKey):
    if getPropValueType(data, propRefKey) == "NUMERICAL_VALUE":
        return float((getPropItem(data, propRefKey))[ 3 ].replace("'", ""))
    elif getPropValueType(data, propRefKey) == "STRING_VALUE":
        return getStringValue(data, getPropItem(data, propRefKey)[ 1 ]).replace("'", "")
    else:
        return ""

def getItemInfo(paramList):
    for i in paramList:
        txt = re.findall(r'\bITEM\(', str(i))
        if len(txt) > 0:
            temp = str(i).split("ITEM(")[1].split(");")[0].split(",")
            return (temp[0], temp[2])
    return None

def getAllDigitalFile(paramList):
    digiFiles = []
    for i in paramList:
        txt = re.findall(r'\bDIGITAL_FILE\(', str(i))
        if len(txt) > 0:
            temp = str(i).split("DIGITAL_FILE(")[1].split(");")[0].split(",")
            digiFiles.append((temp[3].replace("(", "").replace(")", ""), temp[4]))

    return digiFiles

def getToolPngKey(digiFiles, data):
    for i in digiFiles:
        txt = getDataEntity(data, i[1])
        temp = str(txt).split("DOCUMENT_FORMAT_PROPERTY(")[1].split(");")[0].split(",")
        if temp[1].replace("'", "").upper() == "PNG":
            return i[0]

def getToolItemKey(digiFiles, data):
    for i in digiFiles:
        txt = getDataEntity(data, i[1])
        temp = str(txt).split("DOCUMENT_FORMAT_PROPERTY(")[1].split(");")[0].split(",")
        if temp[1].replace("'", "").upper() == "ISO 10303-203":
            return i[0]

def getToolLocation(key, data):
    txt = getDataEntity(data, key)
    temp = str(txt).split("EXTERNAL_FILE_ID_AND_LOCATION(")[1].split(");")[0].split(",")
    fileName = formatString(temp[0])
    txt1 = getDataEntity(data, temp[1])
    temp1 = str(txt1).split("DOCUMENT_LOCATION_PROPERTY(")[1].split(");")[0].split(",")
    location = formatString(temp1[0])
    return fileName, location

def getOrganization(paramList):
    for i in paramList:
        txt = re.findall(r'\bORGANIZATION\(', str(i))
        if len(txt) > 0:
            temp = str(i).split("ORGANIZATION(")[1].split(");")[0]
            st = re.findall("'(.*?)'", str(temp))

            return st

def getCompanyName(orgInfo):
    return orgInfo[2]

            
