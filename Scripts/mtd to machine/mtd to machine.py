#Author-
#Description-

import json
import adsk.core, adsk.fusion, adsk.cam, traceback
import os
from xml.etree import ElementTree as ET
import math as Math

def partTreeRecursive(part: adsk.cam.MachinePart):

    for i in range(part.children.count):
        child = part.children.item(i)
        print(child.id)
        print(child.partType)
        partTreeRecursive(child)

def creatrControllerInfo(machineAxis:adsk.cam.MachineAxisConfigurations, machineInfo):
    # remove all axis
    for i in range(machineAxis.count):
        machineAxis.item(0).deleteMe()

    rotList = []
    linList = []
    for infos in machineInfo:
        if 'table' in infos.keys():
            table = infos['table']
            for axis in table:
                if type(axis) == str:
                    continue
                if axis['Type'] == 'Rotary':
                    rotList.append(axis)
                if axis['Type'] == 'Linear':
                    linList.append(axis)
        if 'head' in infos.keys():
            head = infos['head']
            for axis in head:
                if type(axis) == str:
                    continue
                if axis['Type'] == 'Rotary':
                    rotList.append(axis)
                if axis['Type'] == 'Linear':
                    linList.append(axis)

    linList.sort(key=lambda x: x['Axis address'])
    rotList.sort(key=lambda x: x['Axis address'])
    
    combinedInfo = linList + rotList

    for axisinfo in combinedInfo:
        if type(axisinfo) == str:
            continue

        id_ = axisinfo['Axis address']
        coordinate = {  'X': adsk.cam.MachineAxisCoordinates.MachineCoordinate_X_A, 
                        'Y': adsk.cam.MachineAxisCoordinates.MachineCoordinate_Y_B,
                        'Z': adsk.cam.MachineAxisCoordinates.MachineCoordinate_Z_C,
                        'rotary_0': adsk.cam.MachineAxisCoordinates.MachineCoordinate_X_A,
                        'rotary_1': adsk.cam.MachineAxisCoordinates.MachineCoordinate_Y_B,
                        'rotary_2': adsk.cam.MachineAxisCoordinates.MachineCoordinate_Z_C}[id_]

        if axisinfo['Type'] == 'Linear':
            linear:adsk.cam.LinearMachineAxisConfiguration = machineAxis.addLinear(id_)
            linear.coordinate = coordinate

        if axisinfo['Type'] == 'Rotary':
            rotary:adsk.cam.RotaryMachineAxisConfiguration = machineAxis.addRotary(id_)

            rotary.coordinate = coordinate
            rotary.useToolCenterPointControl = True
            rotary.rotaryPreference = adsk.cam.MachineAnglePreferences.MachineAngleNoPreference

            if axisinfo['Min'] is None and axisinfo['Max'] is None:
                rotary.wrapAroundAtRange.createInfinite()
            else:
                rotary.wrapAroundAtRange.create(axisinfo['Min'], axisinfo['Max'])

def createKineMaticElement(machineParts: adsk.cam.MachineParts, machineInfo):
    for i in range(machineParts.count):
        machineParts.item(0).deleteMe()
    
    for infos in machineInfo:
        if 'table' in infos.keys():
            table = infos['table']
            table.append('table')
        if 'head' in infos.keys():
            head = infos['head']
            head.append('head')
    combineInfo = table + head

    part = None
    for k, axisInfo in enumerate(combineInfo):

        if (k == 0) and type(axisInfo) == str:
            if axisInfo == 'table':
                part = createTableMachinePart(machineParts, machineParts)
            if axisInfo == 'head':
                part = createHeadPart(machineParts, machineParts)

        
        if type(axisInfo) == str:
            if axisInfo == 'table':
                part = createTableMachinePart(machineParts, part)
                part = None
            if axisInfo == 'head':
                part = createHeadPart(machineParts, part)
                part = None
        else:
            if (part is None):
                if axisInfo['Type'] == 'Linear' :
                    part = createLinearMachinePart(machineParts, axisInfo)
                if axisInfo['Type'] == 'Rotary':
                    part = createRotaryMachinePart(machineParts, axisInfo)
            else:
                if axisInfo['Type'] == 'Linear' :
                    part = createLinearMachinePart(part, axisInfo)
                if axisInfo['Type'] == 'Rotary':
                    part = createRotaryMachinePart(part, axisInfo)


def createLinearMachinePart(machineParts: adsk.cam.MachineParts | adsk.cam.MachinePart, info):
    id_ = info['Axis address']
    name = info['Name']
    min_ = info['Min'] if info['Min'] is not None else None
    max_ = info['Max'] if info['Max'] is not None else None
    home = info['Value'] if info['Value'] is not None else 0

    i_ = float(info['I'])
    j_ = float(info['J'])
    k_ = float(info['K'])

    direction = adsk.core.Vector3D.create(i_, j_, k_)

    if (machineParts.objectType == adsk.cam.MachineParts.classType()):
        machinePartInput = machineParts.createPartInput(adsk.cam.MachinePartTypes.AxisMachinePartType)
    else:
        machinePartInput = machineParts.children.createPartInput(adsk.cam.MachinePartTypes.AxisMachinePartType)

    machinePartInput.id = id_
    # machinePartInput.name = name
    
    axisInput :adsk.cam.LinearMachineAxisInput = machinePartInput.createAxisInput(adsk.cam.MachineAxisTypes.LinearMachineAxisType)

    range_ = axisInput.physicalRange.createInfinite()
    if (min_ != None and max_ != None):
        range_ = adsk.cam.MachineAxisRange.create(min_, max_)

    axisInput.physicalRange = range_
    axisInput.homePosition = home
    axisInput.direction = direction

    machinePartInput.axisInput = axisInput
    machinePart_ = None
    if machineParts.objectType == adsk.cam.MachinePart.classType():
        machinePart_ = machineParts.children.add(machinePartInput)
    else:
        machinePart_ = machineParts.add(machinePartInput)

    machinePart_.axis.name = name

    return machinePart_


def createRotaryMachinePart(machineParts: adsk.cam.MachineParts | adsk.cam.MachinePart, info):
    coord = {'rotary_0': 0, 'rotary_1': 1, 'rotary_2': 2}[info['Axis address']]
    id_ = 'rotary_' + str(coord)

    name = info['Name']
    min_ = info['Min'] if info['Min'] is not None else None
    max_ = info['Max'] if info['Max'] is not None else None
    home = info['Value'] if info['Value'] is not None else 0

    i_ = info['I']
    j_ = info['J']
    k_ = info['K']
    x_ = info['X'] if info['X'] is not None else 0
    y_ = info['Y'] if info['Y'] is not None else 0
    z_ = info['Z'] if info['Z'] is not None else 0

    direction = adsk.core.Vector3D.create(i_, j_, k_)

    if machineParts.objectType == adsk.cam.MachineParts.classType():
        machinePartInput = machineParts.createPartInput(adsk.cam.MachinePartTypes.AxisMachinePartType)
    else:
        machinePartInput = machineParts.children.createPartInput(adsk.cam.MachinePartTypes.AxisMachinePartType)

    machinePartInput.id = id_
    # machineParts. = name

    axisInput :adsk.cam.RotaryMachineAxisInput = machinePartInput.createAxisInput(adsk.cam.MachineAxisTypes.RotaryMachineAxisType)

    range_ = axisInput.physicalRange.createInfinite()
    if (min_ != None and max_ != None):
        range_ = adsk.cam.MachineAxisRange.create(min_, max_)

    axisInput.physicalRange = range_
    axisInput.homePosition = home

    axisInput.rotationAxis =  adsk.core.InfiniteLine3D.create(adsk.core.Point3D.create(x_, y_, z_), direction)

    machinePartInput.axisInput = axisInput

    rotaryMachinePart = None
    if machineParts.objectType == adsk.cam.MachinePart.classType():
        rotaryMachinePart = machineParts.children.add(machinePartInput)
    else:
        rotaryMachinePart = machineParts.add(machinePartInput)

    rotaryMachinePart.axis.name = name

    return rotaryMachinePart

def createTableMachinePart(machineParts: adsk.cam.MachineParts, rootPart: adsk.cam.MachinePart| adsk.cam.MachineParts):
    tablepartInput = machineParts.createPartInput(adsk.cam.MachinePartTypes.FixtureAttachmentMachinePartType)
    tablepartInput.id = 'table'
    tablepartInput.name = 'table'
    
    if rootPart.objectType == adsk.cam.MachinePart.classType():
        return rootPart.children.add(tablepartInput)
    else:
        return rootPart.add(tablepartInput)
        
def createHeadPart(machineParts: adsk.cam.MachineParts, rootPart: adsk.cam.MachinePart| adsk.cam.MachineParts):
    headPartInput = machineParts.createPartInput(adsk.cam.MachinePartTypes.ToolAttachmentMachinePartType)
    headPartInput.id = 'head'
    headPartInput.name = 'head'

    if rootPart.objectType == adsk.cam.MachinePart.classType():
        return rootPart.children.add(headPartInput)
    else:
        return rootPart.add(headPartInput)
    
def formatHierarchy(hirarchy):
    formatedHierarchy = []
    tableAxis = []
    headAxis = []
    for i in hirarchy:
        allAxis = None
        isTable = i.get('table',  None)
        isHead = i.get('head',  None)

        if isTable is not None and isHead is None:
            allAxis = isTable

        if isHead is not None and isTable is None:
            allAxis = isHead


        for axis in allAxis:
            id_ = axis['Axis address']
            name = axis['Axis address']
            min_, max_, home = None, None, None
            min_ = float(axis['Min'])/10 if axis['Min'] is not None else None
            max_ = float(axis['Max'])/10 if axis['Max'] is not None else None
            home = float(axis['Value'])/10 if axis['Value'] is not None else 0
            
            
            i_ = abs(float(axis['I'])) * -1 if isTable is not None else abs(float(axis['I']))
            j_ = abs(float(axis['J'])) * -1 if isTable is not None else abs(float(axis['J']))
            k_ = abs(float(axis['K'])) * -1 if isTable is not None else abs(float(axis['K']))

            x_, y_, z_ = 0, 0, 0
            if axis['Type'] == 'Rotary':
                x_ = float(axis['X']) if axis['X'] is not None else 0
                y_ = float(axis['Y']) if axis['Y'] is not None else 0
                z_ = float(axis['Z']) if axis['Z'] is not None else 0

                min_ = float(axis['Min']) if axis['Min'] is not None else None
                max_ = float(axis['Max']) if axis['Max'] is not None else None
                home = float(axis['Value']) if axis['Value'] is not None else 0

                min_ = Math.radians(min_) if min_ is not None else None
                max_ = Math.radians(max_) if max_ is not None else None
                home = Math.radians(home) if home is not None else 0

                i_ = float(axis['I'])
                j_ = float(axis['J'])
                k_ = float(axis['K'])

                x_ /= 10
                z_ /= 10
                y_ /= 10
                coord = {'A': 0, 'B': 1, 'C': 2}[axis['Axis address']]
                id_ = 'rotary_' + str(coord)

            axisInfo = {}
            axisInfo['Axis address'] = id_
            axisInfo['Name'] = name
            axisInfo['Type'] = axis['Type']
            axisInfo['Min'] = min_
            axisInfo['Max'] = max_
            axisInfo['Value'] = home
            axisInfo['I'] = i_
            axisInfo['J'] = j_
            axisInfo['K'] = k_

            if axis['Type'] == 'Rotary':
                axisInfo['X'] = x_
                axisInfo['Y'] = y_
                axisInfo['Z'] = z_

            if isTable is not None:
                tableAxis.append(axisInfo)
            if isHead is not None:
                headAxis.append(axisInfo)

    formatedHierarchy.append({'table': tableAxis})
    formatedHierarchy.append({'head': headAxis})

    return formatedHierarchy

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface


        fileDlg = ui.createFileDialog()
        fileDlg.isMultiSelectEnabled = True
        fileDlg.title = 'Open MTD File'
        fileDlg.filter = '*.mtd*'
        fileDlg.isMultiSelectEnabled = False

        dlgResult = fileDlg.showOpen()
        mtdFile = None
        if dlgResult == adsk.core.DialogResults.DialogOK:
            mtdFile = fileDlg.filename
        else:
            return     


        # xmlFilePath = os.path.join(os.path.dirname(__file__), 'head-head.mtd')

        filePath = os.path.join(os.path.dirname(__file__), 'GenericMachine.mch')

        name = os.path.basename(mtdFile).split('.')[0]
        # Read the XML file
        with open(mtdFile, 'r') as file:
            tree = ET.parse(file)
            element_name = '{*}machine_part'
            root = tree.getroot()

            elements = root.findall(element_name)

            list_ = []
            getMachineAxis(elements, list=list_)

            formatedHierarchy = formatHierarchy(finalHierarchy)
            machineTemplate = getMachineTemplate(finalHierarchy)

            camManager: adsk.cam.CAMManager = adsk.cam.CAMManager.get()
            libraryManager: adsk.cam.CAMLibraryManager = camManager.libraryManager
            machineLibrary: adsk.cam.MachineLibrary = libraryManager.machineLibrary

            location = machineLibrary.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)

            #machineInput = adsk.cam.MachineFromTemplateInput.create(machineTemplate)\
            machineInput = adsk.cam.MachineFromFileInput.create(filePath)
            machine = adsk.cam.Machine.create(machineInput)

            # query= machineLibrary.createQuery(adsk.cam.LibraryLocations.LocalLibraryLocation)
            # query.vendor = 'API'
            # machines = query.execute()
            # machine = machines[0]

            kinematicElement : adsk.cam.KinematicsMachineElement = machine.elements.itemsByType('kinematics')[0]
            createKineMaticElement(kinematicElement.parts, formatedHierarchy)

            # for part in kinematicElement.parts:
            #     if part.partType == adsk.cam.MachinePartTypes.AxisMachinePartType:
            #         axis = part.axis


            controller: adsk.cam.ControllerConfigurationMachineElement = machine.elements.itemsByType('controller')[0]
            creatrControllerInfo(controller.axisConfigurations, formatedHierarchy)

            machine.description = name
            machine.vendor = name


            location = machineLibrary.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)

            # url = adsk.core.URL.create('user://MTD Import')

            locations = machineLibrary.childFolderURLs(location)

            mtdFolder = None
            for folder in locations:
                if folder.leafName == "MTD Import":
                    mtdFolder = folder
                    break
            if mtdFolder is None:
                mtdFolder = machineLibrary.createFolder(location, "MTD Import")


            machineLibrary.importMachine(machine, mtdFolder, name)

            ui.messageBox('Machine Created Successfully')
            return
        # print(finalHierarchy)
        
        machineTemplate = getMachineTemplate(finalHierarchy)

        camManager: adsk.cam.CAMManager = adsk.cam.CAMManager.get()
        libraryManager: adsk.cam.CAMLibraryManager = camManager.libraryManager
        machineLibrary: adsk.cam.MachineLibrary = libraryManager.machineLibrary

        location = machineLibrary.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)

        machineInput = adsk.cam.MachineFromTemplateInput.create(machineTemplate)
        machine = adsk.cam.Machine.create(machineInput)

        query= machineLibrary.createQuery(adsk.cam.LibraryLocations.LocalLibraryLocation)
        query.vendor = 'API'
        machines = query.execute()
        machine = machines[0] 

        url = adsk.core.URL.create('user://api/api_machine.mch')
        url_list = machineLibrary.childAssetURLs(adsk.core.URL.create('user://api'))

        # for i in url_list:
        #     print(machineLibrary.machineAtURL(i).id)
        # print(url_list)

        machineLocation = url
        # print(machineLocation)

        # machine.description = name
        # machine.vendor = 'Autodesk'

        # for i in machine.elements:
        #     print(i.typeId)

        controller: adsk.cam.ControllerConfigurationMachineElement = machine.elements.itemsByType('controller')[0]

        print(controller.axisConfigurations)
        for i in controller.axisConfigurations:
            print(i)


        return

        kinematicElement : adsk.cam.KinematicsMachineElement = machine.elements.itemsByType('kinematics')[0]
        machineParts = kinematicElement.parts
        
        # for part in machineParts:
        #     print(part.id)

        # return
        Apart = machineParts.itemById('rotary_0')

        headPart = Apart.children.item(0)

        Apart.deleteMe()

        #YaxisPart = createLinearMachinePart(machineParts, {'Axis address': 'Y', 'Value': None, 'min': 0, 'max': 90, 'I': 0, 'J': 1, 'K': 0})
        AaxisPart = createRotaryMachinePart(machineParts, {'Axis address': 'A', 'Value': None, 'min': -180, 'max': 180, 'I': 1, 'J': 0, 'K': 0, 'X': '57', 'Y': 0, 'Z': '86.7'})

        headPartInput = machineParts.createPartInput(adsk.cam.MachinePartTypes.ToolAttachmentMachinePartType)
        headPartInput.id = 'head'
        headPartInput.name = 'head'
        # headPartInput.spindleInput.

        headPart = AaxisPart.children.add(headPartInput)

        # tablepartInput = machineParts.createPartInput(adsk.cam.MachinePartTypes.FixtureAttachmentMachinePartType)
        # tablepartInput.id = 'table'
        # tablepartInput.name = 'table'

        # tablePart = machineParts.add(tablepartInput)

        # YaxisPart.children.add(tablepartInput)



        machineLibrary.updateMachine(machineLocation, machine)

        for part in kinematicElement.parts:
            if part.partType == adsk.cam.MachinePartTypes.AxisMachinePartType:
                
                # print(part.axis.direction)
                partTreeRecursive(part)
                

        # input = kinematicElement.parts.createPartInput(adsk.cam.MachinePartTypes.AxisMachinePartType)
        # input.id = 'X1'
        # input.name = 'X1'
        # axis = input.createAxisInput(adsk.cam.MachineAxisTypes.LinearMachineAxisType)
        # input.axisInput = axis

        # kinematicElement.parts.add(input)
        # for part in kinematicElement.parts:
        #     if part.partType == adsk.cam.MachinePartTypes.AxisMachinePartType:
        #         axis = part.axis
        #         print(axis.axisType)
        #         print(part.axis.name)


        # location = machineLibrary.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)

        # machineLibrary.importMachine(machine, location, "Test")
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def getMachineTemplate(hierarchy):
    rotaryConfig = {
        'table' : [],
        'head' : []
    }

    for i in hierarchy:
        if 'table' in i.keys():
            table = i['table']

            for axis in table:
                if axis['Type'] == 'Rotary':
                    rotaryConfig['table'].append(axis['Axis address'])
        if 'head' in i.keys():
            head = i['head']

            for axis in head:
                if axis['Type'] == 'Rotary':
                    rotaryConfig['head'].append(axis['Axis address'])

    tableAxis = rotaryConfig['table']
    headAxis = rotaryConfig['head']

    if len(tableAxis) == 0 and len(headAxis) == 0:
        return adsk.cam.MachineTemplate.Generic3Axis
    elif ((len(tableAxis) == 1 and len(headAxis) == 0) or (len(tableAxis) == 0 and len(headAxis) == 1)):
        return adsk.cam.MachineTemplate.Generic4Axis
    elif len(tableAxis) == 2 and len(headAxis) == 0:
        return adsk.cam.MachineTemplate.Generic5AxisTableTable
    elif len(tableAxis) == 0 and len(headAxis) == 2:
        return adsk.cam.MachineTemplate.Generic5AxisHeadHead
    elif len(tableAxis) == 1 and len(headAxis) == 1:
        return adsk.cam.MachineTemplate.Generic5AxisTableHead
    else:
        return None


finalHierarchy = []
def getMachineAxis(elements, list):
    for element in elements:
        axisElements = element.findall('{*}axis')
        machineParts = element.findall('{*}machine_part')

        if len(axisElements) > 0:
            for axisElement in axisElements:
                controlInfo = axisElement.find('{*}control_info')
                info = {}
                if controlInfo is not None:
                    address = controlInfo.get('ADDRESS')
                    value = controlInfo.get('VALUE')
                    min_val = controlInfo.get('MIN')
                    max_val = controlInfo.get('MAX')
                    info = {'Axis address': address, 'Value': value,'Min': min_val, 'Max': max_val}

                linearInfo = axisElement.find('{*}simple_linear')
                if linearInfo is not None:
                    info.update({'Type': 'Linear'})
                    i_val = linearInfo.get('I')
                    j_val = linearInfo.get('J')
                    k_val = linearInfo.get('K')
                    info.update({'I': i_val, 'J': j_val, 'K': k_val})
                
                rotaryInfo = axisElement.find('{*}simple_rotary')
                if rotaryInfo is not None:
                    info.update({'Type': 'Rotary'})
                    i_val = rotaryInfo.get('I')
                    j_val = rotaryInfo.get('J')
                    k_val = rotaryInfo.get('K')
                    x_off = rotaryInfo.get('X')
                    y_off = rotaryInfo.get('Y')
                    z_off = rotaryInfo.get('Z')
                    info.update({'I': i_val, 'J': j_val, 'K': k_val, 'X': x_off, 'Y': y_off, 'Z': z_off})
                list.append(info)

        if len(machineParts) > 0:
            for machinePart in machineParts:
                partName = machinePart.get('NAME')
                if partName is not None:
                    if partName == 'table' or partName =='head':
                        temp = {partName: []}
                        for i in list:
                            temp[partName].append(i)
                        finalHierarchy.append(temp)
                        list.clear()
        
        getMachineAxis(machineParts, list)
