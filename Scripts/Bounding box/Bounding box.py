#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        doc = app.activeDocument

        selection = ui.selectEntity('Select a body', 'Bodies') # Select a body

        brepBody: adsk.fusion.BRepBody = selection.entity

        design = doc.products.itemByProductType('DesignProductType')
        rootComp:adsk.fusion.Component = design.rootComponent

        # Create a sketch and project the body onto it
        sketches = rootComp.sketches 
        sketch = sketches.add(rootComp.xYConstructionPlane)
        sketch.project(brepBody) 

        # Get the bounding box of the sketch
        minPoint = sketch.boundingBox.minPoint
        maxPoint = sketch.boundingBox.maxPoint

        # Delete the projected sketch curves
        for i in range(sketch.sketchCurves.count):
            sketch.sketchCurves.item(0).deleteMe()

        # Draw a rectangle using the bounding box
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(minPoint, maxPoint)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
