#Author-Boopathi Sivakumar
#Description-Dumper Export and CNC file export
import adsk.core, adsk.fusion, adsk.cam, traceback, os

#Common Calls
app = adsk.core.Application.cast(None)
ui = adsk.core.UserInterface.cast(None)

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []
ADDIN_ID = 'singleNC'
ADDIN_ID_NAME = "Post Process Single"
ADDIN_PANEL = 'CAMActionPanel'

def run(context):
    global ui
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions
        
        addinDefnition = cmdDefs.addButtonDefinition(ADDIN_ID, ADDIN_ID_NAME, 'Post Process the individual operations in the selcted NC program', 'resources') 

        clickAddins = ExportPostCommandCreatedHandler()
        addinDefnition.commandCreated.add(clickAddins)
        handlers.append(clickAddins)
        
        # Get the ADD-INS panel in the model workspace. 
        addInsPanel = ui.allToolbarPanels.itemById(ADDIN_PANEL)

        # Add the button to the bottom of the panel.
        buttonControl = addInsPanel.controls.addCommand(addinDefnition)

        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True
       
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def addTextCommandInput(inputs, id, name, value,isReadOnly ,isVisible):
    textBox = inputs.addTextBoxCommandInput(id, name, value, 1, isReadOnly)
    textBox.isVisible = isVisible
    return textBox

class ExportPostCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs
            #Create Selection button
            selections =  inputs.addSelectionInput('ncSelection','Select NC Program','Select the NC program to post process')
            selections.setSelectionLimits(1)

            addTextCommandInput(inputs, 'programName', 'Program Name/Number', '', False, False)
            addPgmInc = inputs.addBoolValueInput('addPgmNameIncrement', 'Increment Program Name', True, '', False)
            addPgmInc.isVisible = False
            addTextCommandInput(inputs, 'pgmNameIncrement', 'Increment Value', '1', False, False)
            addTextCommandInput(inputs, 'programNamePreview', 'Preview', '', True, False)

            addTextCommandInput(inputs, 'fileName', 'File Name', '', False, False)
            addTextCommandInput(inputs, 'fileNamePrefix', 'File Name Prefix', '', False, False)
            addTextCommandInput(inputs, 'fileNameIncrement', 'FileName Increment Value', '1', False, False)
            addTextCommandInput(inputs, 'fileNamePreview', 'Preview', '', True, False)

            onExecuteNC= ncCommandExcuteHandler()
            cmd.execute.add(onExecuteNC)
            handlers.append(onExecuteNC)

            onInputChanged = ncInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

        except:
         if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class ncCommandExcuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            doc = app.activeDocument
            products = doc.products
            product = products.itemByProductType('CAMProductType')
            cam = adsk.cam.CAM.cast(product)

            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            selection: adsk.core.SelectionCommandInput = inputs.itemById('ncSelection')
            ncProgram: adsk.cam.NCProgram = selection.selection(0).entity

            selectedOperations = ncProgram.filteredOperations
            originalSelected = selectedOperations
            initialName = ncProgram.parameters.itemByName('nc_program_filename').value.value
            try:
                initialName = int(initialName)
            except:
                initialName = str(initialName)

            pgmName = initialName
            for count, i in enumerate(selectedOperations):

                ncProgram.operations = [i]

                if isinstance(pgmName, str):
                    pgmName = initialName +'_'+ str(count+1)
                else:
                    pgmName = pgmName + 1

                postOptions = adsk.cam.NCProgramPostProcessOptions.create()

                ncProgram.parameters.itemByName('nc_program_filename').value.value = str(pgmName)
                try:
                    isSuccess = ncProgram.postProcess(postOptions)
                except:
                    criticalError("Failed to post process the operation", "Post Process Failed")
                    return

            ncProgram.parameters.itemByName('nc_program_filename').value.value = str(initialName)
            ncProgram.operations = originalSelected

        except:
         if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the inputChanged event.
class ncInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
        self.InternalCommands = ['programName', 'fileName', 'pgmNameIncrement', 'fileNameIncrement', 
                        'fileNamePrefix', 'programNamePreview', 'fileNamePreview', 'addPgmNameIncrement', 'ncSelection']
        
        self.fileName = ""
        self.programName = ""

    def updatePreview(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            if not changedInput.id in self.InternalCommands:
                return
            commandInputs = changedInput.parentCommand.commandInputs
            programName = commandInputs.itemById('programName').text
            fileName = commandInputs.itemById('fileName').text
            programNameCount = 0
            fileNameCount = 0
            try:
                programNameCount = int(commandInputs.itemById('pgmNameIncrement').text)
            except:
                programNameCount = 0
            
            try:
                fileNameCount = int(commandInputs.itemById('fileNameIncrement').text)
            except:
                fileNameCount = 0
            fileNamePrefix = commandInputs.itemById('fileNamePrefix').text

            incPrgName = commandInputs.itemById('addPgmNameIncrement').value

            if programName == "":
                programName = self.programName
            if fileName == '':
                fileName = self.fileName

            programNameList = ""
            fileNameList = ""
            pgmInitialVal = programNameCount
            fileInitialVal = fileNameCount

            if incPrgName:
                try:
                    programName = int(programName)
                except:
                    programName = str(programName)

                for i in range(4):
                    if isinstance(programName, int):
                        pgmName = str(programName + int(pgmInitialVal))
                    else:
                        pgmName = str(programName) + '_' + str(pgmInitialVal)

                    pgmInitialVal = pgmInitialVal + programNameCount
                    programNameList = programNameList + str(pgmName) + ', '
            else:
                programNameList = str(programName)

            for i in range(4):
                if fileNamePrefix != '':
                    fileName_ = str(fileName) + '_' + str(fileNamePrefix) + '_' + str(fileInitialVal)
                else:
                    fileName_ = str(fileName) + '_' + str(fileInitialVal)

                fileInitialVal = fileInitialVal + fileNameCount
                fileNameList = fileNameList + str(fileName_) + ', '


            commandInputs.itemById('programNamePreview').text = programNameList if len(programNameList) < 25 else programNameList[:25] + '...'
            commandInputs.itemById('fileNamePreview').text =  fileNameList if len(fileNameList) < 25 else fileNameList[:25] + '...'

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    def showCommands(self, args, show):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            commandInputs = changedInput.parentCommand.commandInputs
            for command in self.InternalCommands:
                if command == 'ncSelection':
                    continue
                if command == 'pgmNameIncrement':
                    commandInputs.itemById(command).isVisible = commandInputs.itemById('addPgmNameIncrement').value and show
                    continue
                    
                commandInputs.itemById(command).isVisible = show
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            if changedInput.id == 'ncSelection':
                commandInputs = changedInput.parentCommand.commandInputs         
                selection :adsk.core.SelectionCommandInput = changedInput
                if selection.selectionCount == 0:
                    self.showCommands(args, False)
                    return
                selectedEntity = selection.selection(0).entity

                if selectedEntity.objectType != adsk.cam.NCProgram.classType():
                    selection.clearSelection()
                    self.showCommands(args, False)
                else:
                    self.showCommands(args, True)
                    ncProgram = adsk.cam.NCProgram.cast(selectedEntity)
                    self.fileName = ncProgram.parameters.itemByName('nc_program_filename').value.value
                    programName = ncProgram.parameters.itemByName('nc_program_name').value.value
                    try:
                        self.programName = int(programName)
                    except:
                        self.programName = str(programName)

                    commandInputs.itemById('programName').text = str(self.programName)
                    commandInputs.itemById('fileName').text = str(self.fileName)
                    self.updatePreview(args)

            if changedInput.id == 'addPgmNameIncrement':
                pgmNameIncrement = changedInput.parentCommand.commandInputs.itemById('pgmNameIncrement')
                pgmNameIncrement.isVisible = changedInput.value
                self.updatePreview(args)
            
            self.updatePreview(args)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        # Clean up the UI.
        cmdDef = ui.commandDefinitions.itemById(ADDIN_ID)
        if cmdDef:
            cmdDef.deleteMe()

        addinsPanel = ui.allToolbarPanels.itemById(ADDIN_PANEL)
        cntrl = addinsPanel.controls.itemById(ADDIN_ID)
        if cntrl:
            cntrl.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	


def errorMsg():
    ui.messageBox("Select valid toolpaths", "Post Process Error",0,4)

def criticalError(message , title):
    ui.messageBox(message,title,
        adsk.core.MessageBoxButtonTypes.OKButtonType,
        adsk.core.MessageBoxIconTypes.CriticalIconType)
    return
