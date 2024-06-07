import os
import shutil
import json
import uuid

libPath = os.path.join(os.getenv('APPDATA'),'Autodesk','CAM360','libraries','Local') 

def isEndMill(tsyc):
    endmill = ["82-01", "303-01", "303-02", "82-02", "303-06"]

    if tsyc in endmill:
        return True

    return False


def getFusionToolType(toolData):
    isoType = toolData.get("ToolIsoType")
    tsyc = toolData.get("TSYC")
    if isoType is not None and tsyc is not None:
        if isEndMill(tsyc):
            dc = toolData.get("DC", 0)
            re = toolData.get("RE", 0)
            if re == 0:
                return "flat end mill"
            elif dc > 0 and re == dc/2:
                return "ball end mill"
            elif dc > 0 and re < dc/2:
                return "bull nose end mill"

def getFusionToolGeometry(tooldata):
    geometry = {}
    isoType = tooldata.get("ToolIsoType")
    tsyc = tooldata.get("TSYC")
    if isoType is not None and tsyc is not None:
        isoType = isoType.split("-")[0]
        if isoType == "mil":
            if isEndMill(tsyc):
                dc = tooldata.get("DC", 0)
                lcf = tooldata.get("APMX", 0)
                sfdm = tooldata.get("DCON", 0)
                hand = True if tooldata.get("HAND", "R") == "R" else False
                csp = True if tooldata.get("CSP", "1") == "1" else False
                oal = tooldata.get("OAL", 0)
                nof = tooldata.get("NOF", 1)
                lb = tooldata.get("LPR", tooldata.get("LF", oal))
                usbLen = tooldata.get("LU", tooldata.get("LUX", 0))
                calLen = oal - tooldata.get("LS", 0)
                shdl = usbLen if usbLen > 0 else calLen if calLen > 0 else lcf
                re = tooldata.get("RE", 0)

        geometry["DC"] = dc
        geometry["LCF"] = lcf
        geometry["HAND"] = hand
        geometry["CSP"] = csp
        geometry["SFDM"] = sfdm
        geometry["NOF"] = nof
        geometry["LB"] = lb
        geometry["OAL"] = oal
        geometry["shoulder-length"] = shdl
        if re > 0:
            geometry["RE"] = re

    return geometry


def convertToToolJson(converted_data, dir):
  output_data = {"data":[], "version":1}
  with open(os.path.join(dir, 'abcfinal.json'), 'w+') as tool_output:
    input_data = converted_data

    tool_instance = {}
    tool_instance['BMC'] = 'unspecified'
    tool_instance['GRADE'] = 'generic'

    desp_ = input_data.get('ToolDescription', 'UnNamed')

    tool_instance['description'] = desp_
    
    tool_instance['geometry'] = getFusionToolGeometry(input_data)

    tool_instance['guid'] = '{'+str(uuid.uuid4())+'}'
    
    # fileInfo = []
    # holder_ = {}
    # filename = os.path.join(myHolderpath, i['holder_file_name'])

    # stpOptions = importManager.createSTEPImportOptions(filename)
    # stpOptions.isViewFit = False
    # success = importManager.importToTarget(stpOptions, rootComp)
    # adsk.doEvents()
    # allComps = design.allComponents
    # fileInfo.append(holder_data[count])
    # for comp in allComps:
    #   if not '.stp' in comp.name and not 'Unsaved' in comp.name:
    #     comp.name = ntpath.basename(filename)
    #     break
    # gotStr = createHolder(fileInfo, comp)

    # for occ in rootComp.occurrencesByComponent(comp):
    #     occ.deleteMe()
    #doc.close(False)

    # holder_ = gotStr
    # tool_instance['holder'] = holder_
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

    tool_instance['product-id'] = ''
    tool_instance['product-link'] = ''

    start_values = {
        "presets": [
            {
            "description": "unNamed",
            "f_n": 0,
            "f_z": 0,
            "guid": str(uuid.uuid4()),
            "n": 0,
            "n_ramp": 0,
            "name": 'Default Preset',
            "tool-coolant": "flood",
            "use-stepdown": "false",
            "use-stepover": "false",
            "stepdown": 0,
            "stepover": 0,
            "v_c": 0,
            "v_f": 0,
            "v_f_leadIn": 0,
            "v_f_leadOut": 0,
            "v_f_plunge": 0,
            "v_f_ramp":  0,
            "v_f_retract":  0
            }
        ]
        }

    tool_instance['start-values'] = start_values

    tool_instance['type'] = getFusionToolType(input_data)
    tool_instance['unit'] = 'millimeters' if input_data.get("UST", "M") == 'M' else 'inches'
    tool_instance['vendor'] = input_data.get("OrgName", "")

    # if isHolder:
    #   tool_instance={}
    #   tool_instance = holder_
    #   isHolder = False

    output_data['data'].append(tool_instance)
      # print(output_data)
    json.dump(output_data, tool_output, indent=4)
    srcFile = os.path.join(dir, 'abcfinal.json')
    copyFile = os.path.join(libPath, (str(input_data.get("ToolName")).replace(".", "")+'.json'))
    tool_output.close()

  shutil.copyfile(srcFile,copyFile)