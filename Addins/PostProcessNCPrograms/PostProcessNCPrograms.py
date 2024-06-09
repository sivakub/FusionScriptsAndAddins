#Author-Boopathi Sivakumar
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

        onMarkingMenuDisplaying = MarkingMenuHandler()                   
        handlers.append(onMarkingMenuDisplaying)                     
        ui.markingMenuDisplaying.add(onMarkingMenuDisplaying)
        
        addinDefnition = cmdDefs.addButtonDefinition(ADDIN_ID, ADDIN_ID_NAME, '', 'resources')
        addinDefnition.tooltip = 'Post Process the operations in the selected NC Program individually.'
        
        clickAddins = ExportPostCommandCreatedHandler()
        addinDefnition.commandCreated.add(clickAddins)
        handlers.append(clickAddins)
        
        # Get the ADD-INS panel in the model workspace. 
        # addInsPanel = ui.allToolbarPanels.itemById(ADDIN_PANEL)

        # # Add the button to the bottom of the panel.
        # buttonControl = addInsPanel.controls.addCommand(addinDefnition)

        # buttonControl.isPromotedByDefault = True
        # buttonControl.isPromoted = True
       
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MarkingMenuHandler(adsk.core.MarkingMenuEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:                    
            eventArgs = adsk.core.MarkingMenuEventArgs.cast(args)
            linearMarkingMenu = eventArgs.linearMarkingMenu.controls
            ncSingleCommnad = ui.commandDefinitions.itemById(ADDIN_ID)
            if ncSingleCommnad is None or ui.activeSelections.count != 1:
                return
            
            activeSelection = ui.activeSelections.item(0).entity
            if activeSelection is None:
                return
            
            if activeSelection.objectType == adsk.cam.NCProgram.classType():
                if linearMarkingMenu.itemById(ADDIN_ID) is None:
                    buttonControl = linearMarkingMenu.addCommand(ncSingleCommnad, 'IronPostProcess', False)
                    buttonControl.isVisible = True
                else:
                    linearMarkingMenu.itemById(ADDIN_ID).isVisible = True

            else:
                if linearMarkingMenu.itemById(ADDIN_ID) is not None:
                    linearMarkingMenu.itemById(ADDIN_ID).isVisible = False

        except:
            if ui:
                ui.messageBox('Marking Menu Displaying event failed: {}'.format(traceback.format_exc()))

def addTextCommandInput(inputs:adsk.core.CommandInputs , id, name, value,isReadOnly ,isVisible, rows = 1):
    textBox = inputs.addTextBoxCommandInput(id, name, value, rows, isReadOnly)
    textBox.isVisible = isVisible
    return textBox

class ExportPostCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command

            cmd.setDialogMinimumSize(300, 300)
            inputs = cmd.commandInputs
            #Create Selection button
            selections =  inputs.addSelectionInput('ncSelection','Select NC Program','Select the NC program to post process')
            selections.setSelectionLimits(1)

            pgmGroup = inputs.addGroupCommandInput('pgmGroup', 'Program Name/Number')
            pgmGroup.isVisible = False
            pgmGroupInput = pgmGroup.children

            addPgmName = addTextCommandInput(pgmGroupInput, 'programName', 'Program Name/Number', '', False, False)
            addPgmName.tooltip = 'NC Program Name or Number'
            addPgmInc = pgmGroupInput.addBoolValueInput('addPgmNameIncrement', 'Increment Program Name', True, '', False)
            addPgmInc.isVisible = False
            pgmInc = addTextCommandInput(pgmGroupInput, 'pgmNameIncrement', 'Increment Value', '1', False, False)
            pgmInc.tooltip = 'Increment value for the program name. Should be a integer.'
            addTextCommandInput(pgmGroupInput, 'programNamePreview', 'Preview', '', True, False, 2)

            fileGroup = inputs.addGroupCommandInput('fileGroup', 'File Name')
            fileGroup.isVisible = False
            fileGroupInput = fileGroup.children

            addUseOpName = fileGroupInput.addBoolValueInput('useOpName', 'Use Operation Name', True, '', False)
            addUseOpName.isVisible = False
            addUseOpName.tooltip = 'Use the operation name as the file name.'

            addFileName = addTextCommandInput(fileGroupInput, 'fileName', 'File Name', '', False, False)
            addFileName.tooltip = 'File Name for the NC Program'

            addTextCommandInput(fileGroupInput, 'fileNamePrefix', 'File Name Prefix', '', False, False)
            fileIncrement = addTextCommandInput(fileGroupInput, 'fileNameIncrement', 'FileName Increment Value', '1', False, False)
            fileIncrement.tooltip = 'Increment value for the file name. Should be a integer.'

            addTextCommandInput(fileGroupInput, 'fileNamePreview', 'Preview', '', True, False, 2)

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
            initialPgmName = ncProgram.parameters.itemByName('nc_program_name').value.value

            filename_ = adsk.core.TextBoxCommandInput.cast(inputs.itemById('fileName')).text
            fileNamePrefix_ = adsk.core.TextBoxCommandInput.cast(inputs.itemById('fileNamePrefix')).text
            fileNameIncrement_ = int(adsk.core.TextBoxCommandInput.cast(inputs.itemById('fileNameIncrement')).text)
            isUseOpName_ = inputs.itemById('useOpName').value

            pgmName_ = adsk.core.TextBoxCommandInput.cast(inputs.itemById('programName')).text
            isPgmNameIncrement = inputs.itemById('addPgmNameIncrement').value
            pgmNameIncrement_ = int(adsk.core.TextBoxCommandInput.cast(inputs.itemById('pgmNameIncrement')).text)

            if len(selectedOperations) < 1:
                criticalError("No operations found in the selected NC Program", "Post Process Error")
                return

            fileIncVal = 0
            pgmIncVal = 0
            opIds = []
            for count, i in enumerate(selectedOperations):
                if i.operationId in opIds:
                    criticalError('Pattern operations found. Currently the addin does not support patterned operations', 'Post Process Error')
                    return
                opIds.append(i.operationId)
                
            for count, i in enumerate(selectedOperations):

                if isUseOpName_:
                    fileName = getProgramName(i.name, '', '')
                else:
                    fileName = getProgramName(filename_, fileIncVal, fileNamePrefix_)

                fileIncVal = fileIncVal + fileNameIncrement_


                pgmName = getProgramName(pgmName_, 0, '')
                if isPgmNameIncrement:
                    pgmName = getProgramName(pgmName_, pgmIncVal, '')
                    pgmIncVal = pgmIncVal + pgmNameIncrement_

                ncProgram.operations = [i]

                postOptions = adsk.cam.NCProgramPostProcessOptions.create()
                ncProgram.parameters.itemByName('nc_program_filename').value.value = str(fileName)
                ncProgram.parameters.itemByName('nc_program_name').value.value = str(pgmName)

                postOptions.postProcessExecutionBehavior = adsk.cam.PostProcessExecutionBehaviors.PostProcessExecutionBehavior_Fail
                isSuccess = False
                try:
                    isSuccess = ncProgram.postProcess(postOptions)
                except:
                    isSuccess = False

                if not isSuccess:
                    criticalError(f"Failed to post process the operation {i.name}", "Post Process Error")
                    ncProgram.parameters.itemByName('nc_program_name').value.value = str(pgmName_)
                    ncProgram.parameters.itemByName('nc_program_filename').value.value = str(filename_)
                    ncProgram.operations = originalSelected
                    return

            ncProgram.parameters.itemByName('nc_program_name').value.value = str(initialPgmName)
            ncProgram.parameters.itemByName('nc_program_filename').value.value = str(initialName)
            ncProgram.operations = originalSelected

        except:
         if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def getProgramName(pgName, incVal, prefix):
    try:
        pgName = int(pgName)
    except:
        pgName = str(pgName)

    if (isinstance(pgName, int)) and prefix == '':
        pgmName = str(pgName + incVal)
    else:
        prefix_ = ('_' + str(prefix)) if str(prefix) != '' else ''
        incVal = incVal + 1 if incVal != '' else ''
        pgmName = str(pgName) + prefix_ + str(incVal)

    return pgmName

# Event handler for the inputChanged event.
class ncInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
        self.InternalCommands = ['programName', 'fileName', 'pgmNameIncrement', 'fileNameIncrement', 'useOpName',
                        'fileNamePrefix', 'programNamePreview', 'fileNamePreview', 'addPgmNameIncrement', 'ncSelection', 'pgmGroup', 'fileGroup']
        
        self.fileName = ""
        self.programName = ""
        self.ncProgram = None

    def updatePreview(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            if not changedInput.id in self.InternalCommands:
                return
            commandInputs = changedInput.parentCommand.commandInputs
            programName = commandInputs.itemById('programName').text
            fileName = commandInputs.itemById('fileName').text

            useOpName = commandInputs.itemById('useOpName').value

            programNameCount = 0
            fileNameCount = 0
            try:
                programNameCount = int(commandInputs.itemById('pgmNameIncrement').text)
            except:
                programNameCount = 0
                commandInputs.itemById('pgmNameIncrement').text = '1'
            
            try:
                fileNameCount = int(commandInputs.itemById('fileNameIncrement').text)
            except:
                commandInputs.itemById('fileNameIncrement').text = '1'
                fileNameCount = 0

            fileInitialVal = 0
            fileNamePrefix = commandInputs.itemById('fileNamePrefix').text

            if programName == "":
                programName = self.programName
                commandInputs.itemById('programName').text = str(programName)
            if fileName == '':
                fileName = self.fileName
                commandInputs.itemById('fileName').text = str(fileName)

            programNameList = ""
            fileNameList = ""
            pgmInitialVal = 0

            incPrgName = commandInputs.itemById('addPgmNameIncrement').value
            if incPrgName:
                for i in range(4):
                    pgName = getProgramName(programName, pgmInitialVal, '')
                    pgmInitialVal = pgmInitialVal + programNameCount
                    programNameList = programNameList + str(pgName) + ', '
            else:
                programNameList = str(programName)

            for i in range(4):
                if useOpName:
                    oP = self.ncProgram.filteredOperations
                    if len(oP) < 1:
                        criticalError("No operations found in the selected NC Program", "Post Process Error")
                        return

                    if len(oP) <= i:
                        break

                    fileName_ = getProgramName(oP[i].name, '', '')
                else:
                    fileName_ = getProgramName(fileName, fileInitialVal, fileNamePrefix)

                fileInitialVal = fileInitialVal + fileNameCount
                fileNameList = fileNameList + str(fileName_) + ', '


            commandInputs.itemById('programNamePreview').text = programNameList if len(programNameList) < 35 else programNameList[:35] + '...'
            commandInputs.itemById('fileNamePreview').text =  fileNameList if len(fileNameList) < 35 else fileNameList[:35] + '...'

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
                    self.ncProgram = ncProgram

                    try:
                        self.programName = int(programName)
                    except:
                        self.programName = str(programName)

                    commandInputs.itemById('programName').text = str(self.programName)
                    commandInputs.itemById('fileName').text = str(self.fileName)

            if changedInput.id == 'addPgmNameIncrement':
                pgmNameIncrement = changedInput.parentCommand.commandInputs.itemById('pgmNameIncrement')
                pgmNameIncrement.isVisible = changedInput.value

            if changedInput.id == 'useOpName':
                isVisbile = not changedInput.value
                changedInput.parentCommand.commandInputs.itemById('fileName').isVisible = isVisbile
                changedInput.parentCommand.commandInputs.itemById('fileNamePrefix').isVisible = isVisbile
                changedInput.parentCommand.commandInputs.itemById('fileNameIncrement').isVisible = isVisbile
            
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

def criticalError(message , title):
    ui.messageBox(message,title,
        adsk.core.MessageBoxButtonTypes.OKButtonType,
        adsk.core.MessageBoxIconTypes.CriticalIconType)
    return

def WarningMessage(message , title):
    ui.messageBox(message,title,
        adsk.core.MessageBoxButtonTypes.OKButtonType,
        adsk.core.MessageBoxIconTypes.WarningIconType)
    return
