import json
import os

import adsk.core

from ... import config
from ...lib import fusion360utils as futil
from .modules import isolib
from .modules import mapping
from .modules.steputils import p21

app = adsk.core.Application.get()
ui = app.userInterface


from pathlib import Path

# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'Import P21'
CMD_Description = 'Import P21 File into Fusion tool'

PALETTE_ID = "tools"
PALETTE_NAME = "Tools Palette"
PALETTE_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tool.html')
PALETTE_URL = PALETTE_URL.replace('\\', '/')
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight

scriptPath = os.path.dirname(os.path.abspath(__file__))
gtcPath = os.path.join(Path(__file__).parent.absolute(), "gtc_package_Kennametal")
toolPngPath = os.path.join(Path(__file__).parent.absolute(),"tool1.html")
toolPath = os.path.join(Path(__file__).parent.absolute(),"tool.json")
p21FilePath = os.path.join(gtcPath, "product_data_files", "6754975.p21")


# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'CAMEnvironment'
PANEL_ID = 'CAMManagePanel'
COMMAND_BESIDE_ID = 'importP21'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    futil.add_handler(cmd_def.commandCreated, command_created)

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    control.isPromoted = IS_PROMOTED

# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    global toolItem, inputs
    inputs = args.command.commandInputs

    fileDlg = ui.createFileDialog()
    fileDlg.title = "Select the P21 File"
    fileDlg.filter = "*.p21*"

    fileDlgRes = fileDlg.showOpen()
    if fileDlgRes == adsk.core.DialogResults.DialogOK:
        p21FilePath = fileDlg.filename
    else:
        return


    toolItem = readData(p21FilePath)

    writeTool(toolItem)

    createInfo(inputs, toolItem)


    showPal = inputs.addBoolValueInput("palTools", "Show Palette", True, "", False)

    palettes = ui.palettes
    palette = palettes.itemById(PALETTE_ID)

    if palette is None:
        palette = palettes.add(
            id=PALETTE_ID,
            name=PALETTE_NAME,
            htmlFileURL=PALETTE_URL,
            isVisible=True,
            showCloseButton=True,
            isResizable=True,
            width=650,
            height=600,
            useNewWebBrowser=True
        )

        palette.isVisible = False
        palette.dockingState = PALETTE_DOCKING

    # if os.path.exists(toolPngPath):
    #     print(toolPngPath)
    #     txt = '<img src="C:/Users/sivakub/AppData/Roaming/Autodesk/Autodesk%20Fusion%20360/API/AddIns/Import%20P21/commands/commandDialog/gtc_package_Kennametal/product_family_drawings/100150355_ArtCallout.png" alt="Tool Image" width="150" height="50"></body>'

    #     png = inputs.addTextBoxCommandInput('toolPng', '',txt,10, True)
        # print(png.htmlFileURL)

        # resizeImg(pngFileLocation)

    # # Create a simple text box input.
    # 

    # # Create a value input field and set the default using 1 unit of the default length unit.
    # defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    # default_value = adsk.core.ValueInput.createByString('1')
    # inputs.addValueInput('value_input', 'Some Value', defaultLengthUnits, default_value)




    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(palette.incomingFromHTML, palette_incoming)
    # futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    # futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def readData(p21FilePath):
    stpFile = p21.readfile(p21FilePath)

    paramList = p21.ParameterList(stpFile)

    plibPropRef = isolib.getPlibPropertyRef(paramList)

    allProps = isolib.getallPropRefISOcode(plibPropRef)

    org = isolib.getOrganization(paramList)

    data = stpFile.data[0]

    isoType = isolib.getISOType(paramList)
    toolItem = {}

    toolDescription = isolib.getStringValue(data, isolib.getItemInfo(paramList)[0])
    toolName = isolib.getStringValue(data, isolib.getItemInfo(paramList)[1])

    toolItem["File Name"] = os.path.basename(p21FilePath)
    toolItem["Tool Name"] = toolName.replace("'", "")
    toolItem["Tool Description"] = toolDescription.replace("'", '')
    toolItem["Org Name"] = isolib.getCompanyName(org)


    tltype = isolib.getToolType(isoType)

    if tltype is not None:
        toolItem["Tool IsoType"] = isolib.getToolType(isoType)
        # isTyp = inputs.addStringValueInput('isoType','Tool type', tltype)
        # isTyp.isReadOnly = True

    for i in allProps:
        propKey = isolib.getPropKey(paramList, i[0])

        propRefKey = isolib.getPropValueRepKey(paramList, propKey)

        isoMapData = isolib.mapIsoData(i[1])

        if isoMapData:
            toolItem[isoMapData] = isolib.getPropertyValue(data, propRefKey)


    digiFiles = isolib.getAllDigitalFile(paramList)

    pngKey = isolib.getToolPngKey(digiFiles, data)
    if not pngKey is None:
        pngLoc = isolib.getToolLocation(pngKey, data)

        pngFolder = os.path.join(gtcPath, pngLoc[1])
        pngFileLocation = os.path.join(pngFolder, pngLoc[0])

        if os.path.exists(pngFileLocation):
            createHtmlFile(pngFileLocation)
            toolItem["pngLocation"] = pngFileLocation

    toolKey = isolib.getToolItemKey(digiFiles, data)

    if not toolKey is None:
        toolLoc = isolib.getToolLocation(toolKey, data)
        toolFolder = os.path.join(gtcPath, toolLoc[1])
        toolFileLocation = os.path.join(toolFolder, pngLoc[0])
        if os.path.exists(toolFileLocation):
            createHtmlFile(toolFileLocation)
            toolItem["toolLocation"] = toolFileLocation
    
    return toolItem


def createInfo(inputs, toolItem):
    stringType = ["File Name", "Tool Name", "Tool Description", "Org Name"]
    for i in toolItem:
        if i == "pngLocation" or i == "toolLocation":
            continue
        
        if i in stringType:
            fnName = inputs.addStringValueInput('iso_{}'.format(i), i,  str(toolItem.get(i)))
            fnName.isReadOnly = True
            continue

        inputs.addTextBoxCommandInput('iso_{}'.format(i), i, str(toolItem.get(i)), 1, True)

def removeItem(inputs, toolItem):

    for i in toolItem:
        if i == "pngLocation":
            continue
        
        rem = inputs.itemById('iso_{}'.format(i))
        rem.deleteMe()

def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    # General logging for debug.
    # futil.log(f'{CMD_NAME}: Palette incoming event.')

    message_data: dict = json.loads(html_args.data)
    message_action = html_args.action

    if message_action == 'send':
        arg1 = message_data.get('arg1', 'arg1 not sent')
        arg2 = message_data.get('arg2', 'arg2 not sent')

        # msg = 'An event has been fired from the html to Fusion with the following data:<br/>'
        # msg += f'<b>Action</b>: {message_action}<br/><b>arg1</b>: {arg1}<br/><b>arg2</b>: {arg2}'               
        loc = toolItem.get("toolLocation", None)
        if loc is not None:
            product = app.activeProduct
            # design.designType = adsk.fusion.DesignTypes.DirectDesignType
            impMgr = app.importManager
            stp = impMgr.createSTEPImportOptions(loc)
            impMgr.importToNewDocument(stp)

    if message_action == 'request':
        arg = message_data.get("Req")
        # removeItem(inputs, toolItem)

        fileDlg = ui.createFileDialog()
        fileDlg.title = "Select the P21 File"
        fileDlg.filter = "*.p21*"

        fileDlgRes = fileDlg.showOpen()
        if fileDlgRes == adsk.core.DialogResults.DialogOK:
            p21FilePath = fileDlg.filename
        else:
            return

        tlIt = readData(p21FilePath)
        palette = ui.palettes.itemById(PALETTE_ID)
        if palette:
            string = json.dumps(tlIt)
            palette.sendInfoToHTML("contentUpdate", string)
            
        # createInfo(inputs, tlIt)


def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Palette was closed.')
    palette = ui.palettes.itemById(PALETTE_ID)
    # Delete the Palette
    if palette:
        palette.deleteMe()


def createHtmlFile(fileLocation):
    # htmlPath = os.path.join(os.path.dirname(fileLocation), "tool.html")
    with open(toolPngPath, "w") as html:
        txt = "<!DOCTYPE html>\n<html>\n<body>\n"
        txt  += '<img src="{}" alt="Tool Image" width="150" height="50">'.format(fileLocation)
        txt += '</body>\n</html>'
        html.write(txt)
        html.close()

def writeTool(tool):
    with open(toolPath, "w") as toolJson:
        data = json.dumps(tool)

        toolJson.write(data)
        toolJson.close

def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    
    mapping.convertToToolJson(toolItem, scriptPath )
    ui.messageBox("Tool Has been written to {}".format(toolPath))


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    if changed_input.id == "palTools":
        palette = ui.palettes.itemById(PALETTE_ID)
        if inputs.itemById(changed_input.id).value:
            palette.isVisible = True
            string = json.dumps(toolItem)
            palette.sendInfoToHTML("update", string)
        else:
            palette.isVisible = False

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

    palette = ui.palettes.itemById(PALETTE_ID)
    # Delete the Palette
    if palette:
        palette.deleteMe()
