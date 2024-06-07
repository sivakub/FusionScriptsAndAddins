from ntpath import join
from posixpath import basename

import adsk.core, adsk.fusion, adsk.cam, traceback, os, sys
import xml.etree.ElementTree as ET
import zipfile, shutil
import json , uuid , random , ntpath

#Initialize
libPath = r'C:/Users/sivakub/AppData/Roaming/Autodesk/CAM360/libraries/Local/MachiningCloud'
dir2 = os.path.dirname(os.path.abspath(__file__))
myAddinPath = os.path.join(dir2, 'lib/'+ 'Report.xml')
myFilepath = os.path.join(dir2,'lib')
myHolderpath = os.path.join(myFilepath,'Models')
tool_data = []
holder_data = []
feed_data = []
stepFileName=''
libName = ''

def run(context):
    ui = None
    try:
      global app  , importManager, product, design, libName
      app = adsk.core.Application.get()
      ui  = app.userInterface
      importManager = app.importManager   
      product = app.activeProduct
      design = adsk.fusion.Design.cast(product)
      workspace_ = ui.workspaces.itemById('FusionSolidEnvironment')
      workspace_.activate()

      fileDlg = ui.createFileDialog()
      fileDlg.title = "Select the Zip file form the machining cloud"
      fileDlg.filter = "*.zip*"

      fileDlgRes = fileDlg.showOpen()
      if fileDlgRes == adsk.core.DialogResults.DialogOK:
          zipfile_ = fileDlg.filename
      else:
          return

      with zipfile.ZipFile(zipfile_) as z:
        #Process Dialoug
        processDialog = ui.createProgressDialog()
        processDialog.show('Machining in Cloud to Fusion','Processing...',0,1000)
        processDialog.progressValue = 100
        z.extractall(myFilepath)

      tree = ET.parse(myAddinPath)
      root = tree.getroot()
      xmlstr = ET.tostring(root, encoding='utf-8', method='xml')
      libName = root.attrib['name']
      
      #get Holder data
      get_holder_data(root)

      #get Feed data
      get_feed_data(root)

      tool_object = {}
      for toolType in root.iter('toolItem'):
        #print(toolType.tag)
        # if toolType.tag == 'toolItem':
        isoType_ = toolType.attrib['isoType']
        tool_object['isotype'] = isoType_

        tool_object['product_id'] = toolType.attrib['catalogNumber']
        if 'description' in toolType.attrib:
          desc = (toolType.attrib['description'])
          tool_object['description'] = desc.replace("\u00b0", 'deg')

        isoDesc = (toolType.attrib['isoDescription'])
        tool_object['isoDescription'] = isoDesc.replace("\u00b0", 'deg')
        tool_object['vendor'] = str(toolType.attrib['publisher'])
        tool_object['units'] = toolType.attrib['unitSystem']
        if toolType.attrib['productGroup'] == 'ToolItem':
          for toolProps in toolType.getchildren():
            if toolProps.tag == 'properties':
              isToolType = False
              for props in toolProps.getchildren():
                if props.attrib['name'] == 'DC': 
                  tool_object['diameterDC'] = float(props.text)
                if props.attrib['name'] == 'DCX': 
                  tool_object['diameterDCmax'] = float(props.text)
                if props.attrib['name'] == 'DCONMS':
                  tool_object['shaft_diameter'] = float(props.text)
                if props.attrib['name'] == 'DHUB':
                  tool_object['hub_diameter'] = float(props.text)
                if props.attrib['name'] == 'HAND':
                  tool_object['hand'] = str(props.text)
                if props.attrib['name'] == 'GRADE':
                  tool_object['grade'] = str(props.text)
                if props.attrib['name'] == 'FHA':
                  tool_object['fluteHelixAngle'] = float(props.text)
                if props.attrib['name'] == 'APMX' or props.attrib['name'] == 'LCF' or props.attrib['name'] == "LU":
                  tool_object['flute_length'] = float(props.text)
                if props.attrib['name'] == 'KAPR':
                  tool_object['tip_angle'] = float(props.text)
                if props.attrib['name'] == 'SIG':
                  tool_object['point_angle'] = float(props.text)
                if props.attrib['name'] == 'NOF':
                  tool_object['fluteNos'] = float(props.text)
                if props.attrib['name'] == 'RE':
                  tool_object['corner_radius'] = float(props.text)
                  if (isoType_ == '303_6' and float(props.text) > 0):
                    tool_object['tool_type'] = 'bull nose end mill'
                    isToolType = True
                  else:
                    tool_object['tool_type'] = get_tool_type(isoType_)
                    isToolType = True
                if props.attrib['name'] == 'LUX':
                  tool_object['shoulder_Length'] = float(props.text) 
                if props.attrib['name'] == 'OAL':
                  tool_object['overall_length'] = float(props.text) 
                if props.attrib['name'] == 'LSCMS':
                  tool_object['clamping_Length'] =float(props.text)
                
                if not isToolType:
                  tool_object['tool_type'] = get_tool_type(isoType_)

          tool_data.append(tool_object)
          tool_object ={}

      feed_object = {}
      #combine holder, tool data and feed data
      for n in range(len(tool_data)):
        tool_data[n].update(holder_data[n])
        tool_data[n].update(feed_data[n])

      #print(tool_data)
      # print(tool_data[1].update(holder_object))
      with open(os.path.join(dir2, 'abc.json'), 'w+') as f:
        json.dump(tool_data, f, indent=4)  


      for i in range(1000):
        if processDialog.wasCancelled:
            break
        processDialog.progressValue = i+1 

      convertToToolJson(tool_data)

      #     print(toolType.attrib)
      # for inp in root.iter('measurements'):
      #   # print(child.tag, child.attrib)
      #   for childs in inp.getchildren():
      #     print(childs.tag)
      processDialog.hide()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def getToolInfo(root):
  ui = adsk.fusion
  ui.messageBox("hols")

def get_tool_type(isoType):
  if isoType == '303_6' or isoType == '303_5':
    return 'flat end mill'
  if isoType == '303-03':
    return 'tapered mill'
  if isoType == '303-04':
    return 'dovetail mill'
  if isoType == '302_5':
    return 'drill'
  if isoType == '303_10':
    return 'ball end mill'
  if isoType == '303_12':
    return 'radius mill'
  if isoType == '303_7':
    return 'radius mil'
  if isoType == '303-09':
    return 'thread mill'
  if isoType == '307_6' or isoType == '308_5':
    return 'face mill'
  # if isoType == '303-10':
  #   return 'Cutting Sylus TODO'

def get_holder_data(root):
  holder_object = {}
  for assembly in root.iter('toolItem'):
    #print(assembly.tag)
    if assembly.attrib['productGroup'] == 'AdaptiveItem':
      holder_object['holder_id'] = str(assembly.attrib['catalogNumber'])
      if 'description' in assembly.attrib:
        holder_object['holder_description'] = str(assembly.attrib['description'])
      holder_object['iso_holder_description'] = str(assembly.attrib['isoDescription'])
      holder_object['holder_vendor'] = str(assembly.attrib['publisher'])
      holder_object['holder_orderNumber'] = str(assembly.attrib['orderNumber'])
      holder_object['holder_unit'] = str(assembly.attrib['unitSystem'])
      
      for holder in assembly.getchildren():
        if holder.tag == 'graphics':
          for model in holder.getchildren():
            if model.tag == 'model':
              if model.attrib['complexity'] == 'AntiCollision':
                tr_name = str(model.text)
                holder_object['holder_file_name']= os.path.basename(tr_name)
    if assembly.attrib['productGroup'] == 'ToolItem':
      holder_data.append(holder_object)
      holder_object = {}

def get_feed_data(root):
  feed_Object = {}
  for performance in root.iter('performance'):
    for toolFeeds in performance.getchildren():
      if toolFeeds.attrib['name'] == 'Operation':
        feed_Object['preset_name'] = str(toolFeeds.text)
      if toolFeeds.attrib['name'] == 'Axial Depth of Cut':
        feed_Object['axial_depth_cut'] = float(toolFeeds.text)
      if toolFeeds.attrib['name'] == 'Radial Width of Cut':
        feed_Object['radial_width_cut'] = float(toolFeeds.text)
      if toolFeeds.attrib['name'] == 'Feed Rate':
        feed_Object['feed_rate'] = float(toolFeeds.text)
      if toolFeeds.attrib['name'] == 'Spindle Speed':
        feed_Object['spindle_speed'] = float(toolFeeds.text)
      if toolFeeds.attrib['name'] == 'Feed Per Tooth':
        feed_Object['feed_per_tooth'] = float(toolFeeds.text)
      if toolFeeds.attrib['name'] == 'Cutting Speed':
        feed_Object['cutting_speed'] = float(toolFeeds.text)
    feed_data.append(feed_Object)
    feed_Object = {}

def createHolder(fileInfo, comp):  
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        product = app.activeProduct
        
        adsk.doEvents()
        doc = app.activeDocument
        products = doc.products
        des = adsk.fusion.Design.cast(products.itemByProductType("DesignProductType"))
        
        #jsonOut = {"data": [], "version": 1}
        comp = adsk.fusion.Component.cast(comp)
        rootComp = des.rootComponent
        model = des.activeComponent
        fet  =model.features
        combineFeat= fet.combineFeatures
        bodyColl = adsk.core.ObjectCollection.create()
        sel = comp.bRepBodies.item(0)
        for bodies in comp.bRepBodies:
          if not bodies == sel:
            bodyColl.add(bodies)
            combineFeatureInput = combineFeat.createInput(sel, bodyColl)
            combineFeatureInput.operation = 0
            combineFeatureInput.isKeepToolBodies = False
            combineFeatureInput.isNewComponent = False
            combineFeat.add(combineFeatureInput)
         
        sel = comp.bRepBodies.item(0)
        if sel:
            holder = adsk.fusion.BRepBody.cast(sel)
            sections = []
            points = []
            for ed in holder.edges:
                points.append(round(ed.startVertex.geometry.z, 3))
            
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
            newPoints.sort()
            normal = adsk.core.Vector3D.create(0,0,1)
            for p in newPoints:
              ## create the plane
              point = adsk.core.Point3D.create(0,0,p)
              plane = adsk.core.Plane.create(point, normal)
              planes = rootComp.constructionPlanes
              pInput = planes.createInput()
              pInput.setByPlane(plane)
              newPlane = planes.add(pInput)
              ## put a sketch on it
              sketches = rootComp.sketches
              sketch = sketches.add(newPlane)
              sketch.projectCutEdges(holder)
              box = sketch.boundingBox
              sizeX = abs(box.minPoint.x - box.maxPoint.x) * 10
              sizeY = abs(box.minPoint.y - box.maxPoint.y) * 10
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
            data = {
                    "description": fileInfo[0]['holder_description'] if 'holder_description' in fileInfo[0] else 'Untitled' ,
                    "guid": guid,
                    "last_modified": 1570310972973,
                    "product-id": fileInfo[0]['holder_id'],
                    "product-link": '',
                    "reference_guid": guid,
                    "segments": [],
                    "type": "holder",
                    "unit": 'millimeters' if fileInfo[0]['holder_unit'] == 'Metric' else 'inches',
                    "vendor": fileInfo[0]['holder_vendor']
                    }
            for s in sections:
              if not first:
                  seg = {
                      "height": round(abs(s[1] - lastPos[1]),3),
                      "lower-diameter": round(lastPos[0],3),
                      "upper-diameter": round(s[0],3)
                  }
                  if abs(s[1] - lastPos[1]) > 0.1:
                        data["segments"].append(seg)
                  lastPos = (s[0], s[1])
              else:
                  first = False
                  lastPos = (s[0], s[1])        
            return data
        adsk.doEvents()
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   

def convertToToolJson(converted_data):
  app = adsk.core.Application.get()
  importManager = app.importManager  
  #doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType) 
  product = app.activeProduct
  design = adsk.fusion.Design.cast(product)
  design.designType = adsk.fusion.DesignTypes.DirectDesignType
  doc = app.activeDocument
  rootComp = design.rootComponent
  count = 0
  fileInfo =[]
  output_data = {"data":[], "version":1}
  with open(os.path.join(dir2, 'abcfinal.json'), 'w+') as tool_output:
    input_data = converted_data

    for i in input_data:
      tool_instance = {}
      tool_instance['BMC'] = 'unspecified'
      tool_instance['GRADE'] = 'generic'
      if 'description' in i:
        desp_ = i['description']
      elif 'iso_description' in i :
        desp_ = i['iso_Description']
      else:
        desp_ = 'Unnamed'

      tool_instance['description'] = desp_
      
      lb_ = i['overall_length'] - (i['clamping_Length'] if 'clamping_Length' in i else float(0))
      shL_ = i['shoulder_Length'] if 'shoulder_Length' in i else i['flute_length']

      tool_geometry = {}
      tool_geometry['CSP'] = False
      tool_geometry['DC'] = i['diameterDCmax'] if 'diameterDCmax' in i else i['diameterDC']
      tool_geometry['HAND'] = True if i['hand'] == 'R' else False
      if lb_ < shL_:
        lb_ = shL_
      tool_geometry['LB'] = lb_
      tool_geometry['LCF'] = i['flute_length']
      tool_geometry['NOF'] = i['fluteNos']
      tool_geometry['NT'] = 0
      tool_geometry['OAL'] = i['overall_length']
      tool_geometry['RE'] = i['corner_radius'] if 'corner_radius' in i else float(0)

      sfdm_ = i['hub_diameter'] if 'hub_diameter' in i else i['shaft_diameter']
      tool_geometry['SFDM'] = sfdm_

      ta_ =  i['point_angle'] if 'point_angle' in i else float(180)
      tool_geometry['SIG'] = ta_ if i['tool_type'] == 'drill' else 0

      if 'tip_angle' in i:
        if i['tool_type'] == 'face mill':
          ta_ = 90 - i['tip_angle']
        else:
          ta_ = 0
        tool_geometry['TA'] = ta_

      tool_geometry['TP'] = 0
      tool_geometry['shoulder-diameter'] = 0
      tool_geometry['shoulder-length'] = shL_
      tool_geometry['tip-diameter'] = 0
      tool_geometry['tip-length'] = 0
      tool_geometry['tip-offset'] = 0
      tool_instance['geometry'] = tool_geometry

      tool_instance['guid'] = '{'+str(uuid.uuid4())+'}'
      
      if 'holder_file_name' in i:
        fileInfo = []
        holder_ = {}
        filename = os.path.join(myHolderpath, i['holder_file_name'])

        stpOptions = importManager.createSTEPImportOptions(filename)
        stpOptions.isViewFit = False
        success = importManager.importToTarget(stpOptions, rootComp)
        adsk.doEvents()
        allComps = design.allComponents
        fileInfo.append(holder_data[count])
        for comp in allComps:
          if not '.stp' in comp.name and not 'Unsaved' in comp.name:
            comp.name = ntpath.basename(filename)
            break
        gotStr = createHolder(fileInfo, comp)

        for occ in rootComp.occurrencesByComponent(comp):
            occ.deleteMe()
        #doc.close(False)

        holder_ = gotStr
        tool_instance['holder'] = holder_
      post_process = {}
      post_process['break-control'] = False
      post_process['comment'] = ''
      post_process['diameter-offset'] = 0
      post_process['length-offset'] = 0
      post_process['live'] = True
      post_process['manual-tool-change'] = False
      post_process['number'] = 0
      post_process['turret'] = 0
      tool_instance['post-process'] = post_process

      tool_instance['product-id'] = str(i['product_id'])
      tool_instance['product-link'] = ''
      fee = i['feed_rate'] if 'feed_rate' in i else 0
      start_values = {
            "presets": [
              {
                "description": "",
                "f_n": 0,
                "f_z": 0,
                "guid": str(uuid.uuid4()),
                "n": i['spindle_speed'] if 'spindle_speed' in i else 0,
                "n_ramp": i['spindle_speed'] if 'spindle_speed' in i else 0,
                "name": 'MC-Cloud-' + i['preset_name'] if 'preset_name' in i else 'Default Preset',
                "tool-coolant": "flood",
                "use-stepdown": "true",
                "use-stepover": "true",
                "stepdown":i['axial_depth_cut'] if 'axial_depth_cut' in i else 0,
                "stepover":i['radial_width_cut'] if 'radial_width_cut' in i else 0,
                "v_c": 0,
                "v_f": fee,
                "v_f_leadIn": fee / 2,
                "v_f_leadOut": fee,
                "v_f_plunge": fee / 2,
                "v_f_ramp":  fee / 2,
                "v_f_retract":  fee
              }
            ]
          }

      tool_instance['start-values'] = start_values

      tool_instance['type'] = i['tool_type']
      tool_instance['unit'] = 'millimeters' if i['units'] == 'Metric' else 'inches'
      tool_instance['vendor'] = i['vendor'] 

      # if isHolder:
      #   tool_instance={}
      #   tool_instance = holder_
      #   isHolder = False

      output_data['data'].append(tool_instance)
      count = count + 1
      # print(output_data)
    json.dump(output_data, tool_output, indent=4)
  shutil.copyfile(os.path.join(dir2, 'abcfinal.json'),os.path.join(libPath, (str(libName)+'.json'))) 