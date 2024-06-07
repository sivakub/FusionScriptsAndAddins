
#Author-Boopathi
#Description-Import Tools from machiningcloud




# if not myAddinPath in sys.path:
#     sys.path.append(myAddinPath)

# import xmltodict

# print(myAddinPath)


def run(context):
  ui = None
  try:
    app = adsk.core.Application.get()
    ui  = app.userInterface

    with zipfile.ZipFile(zipfile) as zf:
      for name in zf.namelist():
        if (name.endswith("Report.xml")):

  except:
    if ui:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
    


def get_tool_type(tool):
    if False:
        return 'drill'
    elif tool['corner_radius'] == tool['diameter']/2:
        print(tool['ISYC'])
        return 'ball end mill'
    elif tool['corner_radius'] > 0:
        return 'bull nose end mill'
    elif ('chamfer' in tool) and tool['chamfer'] > 0:
        return 'chamfer mill'
    else:
        return 'flat end mill'

def get_tool_type(tool):
  if 'ISYC' in tool:
    if tool['ISYC'] == '303-01':
      return 'flat end mill'
    if tool['ISYC'] == '303-02':
      return 'flat end mill'
    if tool['ISYC'] == '303-03':
      return 'tapered mill'
    if tool['ISYC'] == '303-04':
      return 'dovetail mill'
    if tool['ISYC'] == '303-05':
      return 'slot mill'
    if tool['ISYC'] == '303-06':
      return 'ball end mill'
    # if tool['ISYC'] == '303-07':
    #   return 'tapered mill TODO'
    # if tool['ISYC'] == '303-08':
    #   return 'Rounded Profile Concave TODO'
    if tool['ISYC'] == '303-09':
      return 'thread mill'
    # if tool['ISYC'] == '303-10':
    #   return 'Cutting Sylus TODO'
    return 'tool error'
  return 'tool error'

tool_data = []

for path in Path('Iscar').rglob('*.xml'):
    # print(path)

    tree = ET.parse(Path(path))
    xml_data = tree.getroot()
    #here you can change the encoding type to be able to set it to the one you need
    xmlstr = ET.tostring(xml_data, encoding='utf-8', method='xml')

    data_dict = dict(xmltodict.parse(xmlstr))

    tool_data.append(data_dict)

with open(Path('Iscar/tool_data.json'), 'w+') as f:
  json.dump(tool_data, f, indent=4)

converted_data = []
missing_parameters = []

for i in tool_data:
    tool_object={}
    tool_object['product_id'] = i['TechPubInstSimpleObject']['Item']['itemNumber']
    tool_object['description'] = i['TechPubInstSimpleObject']['Item']['isoDescription']
    for p in i['TechPubInstSimpleObject']['TechPubInst']['branchList'][0]['Branch']['branchList']['Branch']['propertyList']['Property']:
      if p['symbol'] == "DC":
        tool_object['diameterDC'] = float(p['value'])
      if p['symbol'] == "DCX":
        tool_object['diameterDCX'] = float(p['value'])
      if p['symbol'] == 'NOF':
        tool_object['flutes'] = float(p['value'])
      if p['symbol'] == 'KAPR':
        tool_object['tip_angle'] = float(p['value'])
      if p['symbol'] == 'APMX':
        tool_object['flute_length'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'CW':
        tool_object['slot_flute_length'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'OAL':
        tool_object['overall_length'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'RE':
        tool_object['corner_radius'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'CHW':
        tool_object['chamfer'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'DCONMS':
        tool_object['shaft_diameter'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'LU':
        tool_object['reach_length'] = float(p['value']) if p['unit'] == 'inch' else float(p['value'])*25.4
      if p['symbol'] == 'ISYC':
        tool_object['ISYC'] = p['value']
    if 'ISYC' in tool_object and tool_object['ISYC'] == '303-03':
      tool_object['diameter'] = min(tool_object['diameterDC'] if 'diameterDC' in tool_object else 0,tool_object['diameterDCX'] if 'diameterDCX' in tool_object else 0)
    # if 'ISYC' in tool_object and tool_object['ISYC'] == '303-04':
    #   tool_object['tip_angle'] = (180-float(tool_object['tip_angle']))/2
    if 'ISYC' in tool_object and tool_object['ISYC'] == '303-05':
      tool_object['flute_length'] = tool_object['slot_flute_length']
    else:
      tool_object['diameter'] = max(tool_object['diameterDC'] if 'diameterDC' in tool_object else 0,tool_object['diameterDCX'] if 'diameterDCX' in tool_object else 0)

    for i in ['diameter', 'flutes', 'flute_length', 'overall_length', 'corner_radius', 'chamfer', 'shaft_diameter', 'reach_length']:
      if i not in tool_object:
        if i == 'diameter':
          # print(tool_object['product_id'] + ': DC')
          missing_parameters.append(tool_object['product_id'] + ': DC')
          tool_object[i] = 0
        if i == 'flutes':
          # print(tool_object['product_id'] + ': NOF')
          missing_parameters.append(tool_object['product_id'] + ': NOF')
          tool_object[i] = 0
        if i == 'flute_length':
          # print(tool_object['product_id'] + ': APMX')
          missing_parameters.append(tool_object['product_id'] + ': APMX')
          tool_object[i] = 0
        if i == 'overall_length':
          # print(tool_object['product_id'] + ': OAL')
          missing_parameters.append(tool_object['product_id'] + ': OAL')
          tool_object[i] = 0
        if i == 'corner_radius':
          # print(tool_object['product_id'] + ': RE')
          # missing_parameters.append(tool_object['product_id'] + ': RE')
          tool_object[i] = 0
        if i == 'chamfer':
          # print(tool_object['product_id'] + ': CHW')
          # missing_parameters.append(tool_object['product_id'] + ': CHW')
          tool_object[i] = 0
        if i == 'shaft_diameter':
          # print(tool_object['product_id'] + ': DCONMS')
          missing_parameters.append(tool_object['product_id'] + ': DCONMS')
          tool_object[i] = 0
        if i == 'reach_length':
          # print(tool_object['product_id'] + ': LU')
          missing_parameters.append(tool_object['product_id'] + ': LU')
          tool_object[i] = 0

    converted_data.append(tool_object)

f = open(Path('Iscar/missing_parameters.txt'), "w")
for i in missing_parameters:
  f.write(i+'\n')
f.close()

with open(Path('Iscar/data_conversion.json'), 'w+') as f:
  json.dump(converted_data, f, indent=4)

with open(Path('Iscar/Iscar.json'), 'w+') as tool_output:
    input_data = converted_data
    output_data = {"data":[], "version":1}

    for i in input_data:

        tool_instance = {}

        tool_instance['BMC'] = 'unspecified'
        tool_instance['GRADE'] = 'generic'
        tool_instance['description'] = i['description']
            
        tool_geometry = {}
        tool_geometry['CSP'] = False
        tool_geometry['DC'] = i['diameter']
        tool_geometry['HAND'] = True
        tool_geometry['LB'] = i['reach_length'] + 0.1 if i['reach_length'] > i['flute_length'] else i['flute_length'] + 0.1
        tool_geometry['LCF'] = i['flute_length']
        tool_geometry['NOF'] = max(i['flutes'], 1)
        tool_geometry['NT'] = 0
        tool_geometry['OAL'] = max(i['overall_length'], tool_geometry['LB'])
        tool_geometry['RE'] = i['corner_radius']
        tool_geometry['SFDM'] = i['shaft_diameter']
        tool_geometry['SIG'] = 0
        tool_geometry['TA'] = i['tip angle'] if 'tip angle' in i else 0
        tool_geometry['TP'] = 0
        tool_geometry['shoulder-diameter'] = i['diameter']*0.9 if i['reach_length'] > i['flute_length'] else i['diameter']
        tool_geometry['shoulder-length'] = i['reach_length'] if i['reach_length'] > i['flute_length'] else i['flute_length']
        tool_geometry['tip-diameter'] = 0
        tool_geometry['tip-length'] = 0
        tool_geometry['tip-offset'] = 0
        tool_instance['geometry'] = tool_geometry

        tool_instance['guid'] = '{'+str(uuid.uuid4())+'}'

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

        start_values = {
                "presets": [
                    {
                        "description": "",
                        "f_n": 0,
                        "f_z": 0,
                        "guid": str(uuid.uuid4()),
                        "n": 0,
                        "n_ramp": 0,
                        "name": "Default Preset",
                        "tool-coolant": "flood",
                        "v_c": 0,
                        "v_f": 0,
                        "v_f_leadIn": 0,
                        "v_f_leadOut": 0,
                        "v_f_plunge": 0,
                        "v_f_ramp": 0,
                        "v_f_retract": 0
                    }
                ]
            }

        tool_instance['start-values'] = start_values

        tool_instance['type'] = get_tool_type(i)
        tool_instance['unit'] = 'inches'
        tool_instance['vendor'] = 'Iscar'

        if get_tool_type(i) == 'tool error':
          continue
        
        output_data['data'].append(tool_instance)

    json.dump(output_data, tool_output, indent=4)