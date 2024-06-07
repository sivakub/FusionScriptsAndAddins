#Author-Boopathi
#Description-

import adsk.core, adsk.fusion, traceback, math, time, tempfile, adsk.cam, json, random
import os.path, sys, os
import tkinter as tk
import json
from datetime import datetime
from sys import platform
from tkinter import Widget, filedialog
import ntpath

app = adsk.core.Application.get()
ui = app.userInterface

def createHolder(fileInfo, comp):  
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        product = app.activeProduct
        
        adsk.doEvents()
        doc = app.activeDocument
        
        products = doc.products
        des = adsk.fusion.Design.cast(products.itemByProductType("DesignProductType"))
        
        jsonOut = {"data": [], "version": 1}
        comp = adsk.fusion.Component.cast(comp)
        for k in range(0, comp.bRepBodies.count):
            sel = comp.bRepBodies.item(k)
            if sel:
                holder = adsk.fusion.BRepBody.cast(sel)
                sections = []
                points = []
                for ed in holder.edges:
                    points.append(round(ed.startVertex.geometry.x, 3))
                
                points.sort()
                ## only allow TWO duplicate points
                currentPoint = 0
                addPoint = True
                newPoints = []
                for point in points:
                    if point == currentPoint:
                        if addPoint:
                            newPoints.append(point + 0.001)
                            newPoints.append(point - 0.001)
                            currentPoint = point
                            addPoint = False
                    else:
                        addPoint = True
                        newPoints.append(point)
                        currentPoint = point
                newPoints.sort(reverse = True)
                normal = adsk.core.Vector3D.create(1,0,0)
                for p in newPoints:
                    if p < 0:
                        continue
                    ## create the plane
                    point = adsk.core.Point3D.create(p,0,0)
                    plane = adsk.core.Plane.create(point, normal)
                    planes = comp.constructionPlanes
                    pInput = planes.createInput()
                    pInput.setByPlane(plane)
                    newPlane = planes.add(pInput)
                    ## put a sketch on it
                    sketches = comp.sketches
                    sketch = sketches.add(newPlane)
                    sketch.projectCutEdges(holder)
                    box = sketch.boundingBox
                    x1 = abs(box.minPoint.x)
                    x2 = abs(box.maxPoint.x)
                    if x1 > x2:
                        sizeX = x1 * 10 * 2
                    else:
                        sizeX = x2 * 10 * 2
                    
                    y1 = abs(box.minPoint.y)
                    y2 = abs(box.maxPoint.y)
                    if y1 > y2:
                        sizeY = y1 * 10 * 2
                    else:
                        sizeY = y2 * 10 * 2
                    maxSize = 0
                    sketch.deleteMe()
                    newPlane.deleteMe()
                    if sizeX > sizeY:
                        maxSize = sizeX
                    else:
                        maxSize = sizeY
                    sections.append((maxSize, p * 10))
                
                first = True
                lastPos = (0, 0)
                guid = "00000000-0000-0000-0000-" + str(random.randint(100000000000, 999999999999))
                ind = 0
                runInd = 0
                desc = fileInfo['Description']
                # desc = desc.replace('"";','placeholderReplace!')
                # desc = desc.replace('"','')
                # desc = desc.replace('placeholderReplace!', '";')
                data = {
                        "description": desc,
                        "guid": guid,
                        "last_modified": 1570310972973,
                        "product-id": fileInfo['ProductID'],
                        "product-link": fileInfo['productLink'],
                        "reference_guid": guid,
                        "segments": [],
                        "type": "holder",
                        "unit": "millimeters",
                        "vendor": 'Haimer'
                        }
                if len(sections) > 5:  
                    for s in range(len(sections)):
                        if not first:
                            cr = round(sections[s][0], 3)
                            if not s == len(sections) - 1:
                                nx = round(sections[s+1][0], 3)
                                if round(lastPos[0],3) == cr and cr == nx :
                                    lp = lastPos[1]
                                    lastPos = (sections[s][0], lp)
                                    continue
                            seg = {
                                "height": round(abs(sections[s][1] - lastPos[1]),3),
                                "lower-diameter": round(lastPos[0],3),
                                "upper-diameter": round(sections[s][0],3)
                            }
                            if abs(sections[s][1] - lastPos[1]) > 0.1:
                                data["segments"].append(seg)
                            lastPos = (sections[s][0], sections[s][1])
                        else:
                            first = False
                            lastPos = (sections[s][0], sections[s][1])
                    return data
            adsk.doEvents()
            
        return ''
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   

def run(context):
    try:
        # Get import manager
        importManager = app.importManager       
        # Get active design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        stTime = datetime.now().strftime("%H:%M:%S")
        if(str(platform) == "win32"):
            folderDlg = ui.createFolderDialog()
            folderDlg.title = 'Select the step file directory'

            folderDlgRes = folderDlg.showDialog()
            if folderDlgRes == adsk.core.DialogResults.DialogOK:
                stepDir = folderDlg.folder
            else:
                return
            
            fileDlg = ui.createFileDialog()
            fileDlg.title = "Select the corresponding JSON file"
            fileDlg.filter = "*.json*"

            fileDlgRes = fileDlg.showOpen()
            if fileDlgRes == adsk.core.DialogResults.DialogOK:
                tsvfile = fileDlg.filename
            else:
                return
        # Get root component
        rootComp = design.rootComponent
        jsonOut = {"data": [], "version": 1}
        filsasave = r'C:\Users\sivakub\Desktop\Heimer\Heimer Holder.json'
        logFile = r'C:\Users\sivakub\Desktop\Heimer\log.txt'
        with open(tsvfile, 'r') as f:
            data = json.load(f)
        ind = 0
        for i in data:
            stpFile = os.path.join(stepDir, i['file'])
            if os.path.isfile(stpFile):
                ind = ind + 1
                stpOptions = importManager.createSTEPImportOptions(stpFile)
                stpOptions.isViewFit = False
                # Import step file to root component
                success = importManager.importToTarget(stpOptions, rootComp)
                adsk.doEvents()
                # Get active design
                product = app.activeProduct
                design = adsk.fusion.Design.cast(product)
                allComps = design.allComponents
                for comp in allComps:
                    if not '.stp' in comp.name and not 'Unsaved' in comp.name:
                        comp.name = ntpath.basename(stpFile)
                        break
                gotStr = createHolder(i, comp)
                if gotStr != '':
                    jsonOut['data'].append(gotStr)
                    #toolLib.write(json.dumps(gotStr) + ',')
                for occ in rootComp.occurrencesByComponent(comp):
                    occ.deleteMe()
            
            else:
                with open (logFile , 'a') as lf:
                    lf.write(i['file'] + ' - '+ i['ProductID']+ str('\n'))

        with open(filsasave, "a") as toolLib:
            toolLib.write(json.dumps(jsonOut))

        endTime = datetime.now().strftime("%H:%M:%S")

        ui.messageBox('Done\nTotal Holders Converted - ' + str(ind) +'\nStart Time - '+ stTime + '\nEnd Time - '+ endTime)
        # Close the new created document
        #doc.close(False)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))