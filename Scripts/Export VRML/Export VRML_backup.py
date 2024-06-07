#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
import struct, os

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        sel = ui.selectEntity('Select a component', 'Occurrences')


        selItem : adsk.fusion.Occurrence = sel.entity

        colorCode = getColorCode(selItem.component)


        design : adsk.fusion.Design = app.activeDocument.products.itemByProductType("DesignProductType")
        exportMgr = adsk.fusion.ExportManager.cast(design.exportManager)
        stlOptions = exportMgr.createSTLExportOptions(selItem.component)
        stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium

        filePath = os.path.join(r'C:\Users\sivakub\Desktop', selItem.component.name + ".stl")
        stlOptions.filename =  filePath
        suc = exportMgr.execute(stlOptions)

        if not suc:
            ui.messageBox('Failed to export STL')
            return



        # fileDlg = ui.createFileDialog()
        # fileDlg.isMultiSelectEnabled = False
        # fileDlg.title = 'Select STL file'

        # dialog = fileDlg.showOpen()
        # if dialog != adsk.core.DialogResults.DialogOK:
        #     return
        
        file_ = open(filePath, 'rb')

        # print(fileDlg.filename)

        vrmlData = convertSTLtoVRML(file_.read(), colorCode)


        exportFileName = os.path.splitext(filePath)[0] + ".vrml"

        print(exportFileName)
        with open(exportFileName, 'w') as f:
            f.write(vrmlData)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def getColorCode(component : adsk.fusion.Component):
    
    brepBody = None
    if (component.bRepBodies.count > 0) :
        brepBody = component.bRepBodies.item(0)

    color = brepBody.faces.item(0).appearance.appearanceProperties

    for c in color:
        print(c.id)

    bodyColorProp: adsk.core.ColorProperty = color.itemById('metal_f0')

    if bodyColorProp is None:
        bodyColorProp = color.itemById('opaque_albedo')


    (done, r, g, b, a) = bodyColorProp.value.getColor()
    colorCode = "0.623 0.623 0.623"

    if done:
        colorCode = f"{r/255} {g/255} {b/255}"
        
    print(colorCode)
    return colorCode

def convertSTLtoVRML(inputBuffer, colorcode = '1 1 1'):
    color = f"""
        Material{{
        ambientColor  0 0 0
        diffuseColor  {colorcode}
        specularColor 0 0 0
        emissiveColor 0 0 0
        shininess     1
        transparency  0
        }}
    """
    vrmlStr = f"#VRML V1.0 ascii\nSeparator {{{color}   Coordinate3 {{\n        point [\n"
    numTriangles = struct.unpack_from('<I', inputBuffer, 80)[0]
    indexData = "    IndexedFaceSet {\n        coordIndex [\n"
    offset = 84

    vertices = []
    indices = []

    for i in range(numTriangles):
        for j in range(3): 
            valx = struct.unpack_from('<f', inputBuffer, offset + j * 12)[0]
            print(valx)
            vertex = [
                
                f"             {struct.unpack_from('<f', inputBuffer, offset + 12 + j * 12)[0]}",
                f"{struct.unpack_from('<f', inputBuffer, offset + 12 + j * 12 + 4)[0]}",
                f"{struct.unpack_from('<f', inputBuffer, offset + 12 + j * 12 + 8)[0]}"
            ]
            vertices.append(' '.join(vertex))
            indices.append(str(i * 3 + j))

        indices.append("-1") 
        offset += 50 

    vrmlStr += ',\n'.join(vertices) + "\n        ]\n    }\n" 
    indexData += ', '.join(indices) + "\n]\n    }\n}\n"
    vrmlStr += indexData

    return vrmlStr