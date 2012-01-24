# Copyright 2011 Antoine Bertin <diaoulael@gmail.com>
#
# This file is part of Dobby.
#
# Dobby is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dobby is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dobby.  If not, see <http://www.gnu.org/licenses/>.
from ..app import Application as Dobby
from PySide.QtCore import *
from PySide.QtGui import *
from dobby.qt.dialogs.weather import ActionWeatherForm
from dobby.qt.models import ScenarioModel, ScenarioCommandModel, \
    ScenarioActionModel, ActionModel
from ui.main_ui import Ui_MainWindow
import os.path
import pyjulius.exceptions
import time


class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        locale = QLocale.system().name()
        translator = QTranslator()
        translator.load(os.path.join('ts', locale))
        translator.load('qt_' + locale, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        self.installTranslator(translator)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.dobby = DobbyApplication()
        self.session = self.dobby.dobby.Session()
        self.qaStop.setVisible(False)

        # Scenario Models
        self.scenarioModel = ScenarioModel(self.session)
        self.qlvScenarios.setModel(self.scenarioModel)
        self.scenarioCommandModel = ScenarioCommandModel(self.session)
        self.qlvScenarioCommands.setModel(self.scenarioCommandModel)
        self.scenarioActionsModel = ScenarioActionModel(self.session)
        self.qlvScenarioActions.setModel(self.scenarioActionsModel)

        # Action Model
        self.actionModel = ActionModel(self.session)
        self.qlvActions.setModel(self.actionModel)

        # Scenario Signals
        self.qpbScenarioAdd.clicked.connect(self.addScenario)
        self.qpbScenarioRemove.clicked.connect(self.removeScenario)
        self.qpbScenarioCommandAdd.clicked.connect(self.addScenarioCommand)
        self.qpbScenarioCommandRemove.clicked.connect(self.removeScenarioCommand)
        self.qlvScenarios.selectionModel().selectionChanged.connect(self.changeScenario)

        # Action Signals
        self.qpbActionAdd.clicked.connect(self.addAction)
#        self.qpbActionRemove.clicked.connect(self.removeAction)

        # Dobby Signals
        self.qaStart.triggered.connect(self.startDobby)
        self.qaStop.triggered.connect(self.stopDobby)

    @Slot(QModelIndex, QModelIndex)
    def changeScenario(self, selected, deselected):
        self.scenarioCommandModel.commands = self.scenarioModel.scenarios[selected.indexes()[0].row()].commands
        self.qlvScenarioCommands.reset()

    @Slot()
    def addScenario(self):
        text = self.qleScenario.text()
        if not text:
            return 
        self.scenarioModel.addScenario(text)
        self.qleScenario.clear()

    @Slot()
    def removeScenario(self):
        self.scenarioModel.removeScenario(self.qlvScenarios.currentIndex().row())

    @Slot()
    def addScenarioCommand(self):
        text = self.qleScenarioCommand.text()
        if not text:
            return
        self.scenarioCommandModel.addCommand(text)
        self.qleScenarioCommand.clear()

    @Slot()
    def removeScenarioCommand(self):
        self.scenarioCommandModel.removeCommand(self.qlvScenarioCommands.currentIndex().row())

    @Slot()
    def addAction(self):
        dialog = ActionWeatherForm(self)
        result = dialog.exec_()
        if result != QDialog.Accepted:
            return
        print dialog.qleName.text()
#        self.actionModel.addAction(self.)

    def startDobby(self):
        try:
            self.dobby.start()
        #TODO: Check for the recognizer in dobby before 'run'
        except pyjulius.exceptions.ConnectionError:
            QMessageBox.question(self, 'Error', 'Did you start the recognizer?', QMessageBox.Ok)
        except:
            raise
        self.qaStart.setVisible(False)
        self.qaStop.setVisible(True)
 
    def stopDobby(self):
        self.dobby.stop()
        self.qaStop.setVisible(False)
        self.qaStart.setVisible(True)

    def closeEvent(self, event):
        #FIXME
        self.hide()
        self.quit()
        event.accept()
        return
        reply = QMessageBox.question(self, 'Message', 'Are you sure to quit?',
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.hide()
            self.quit()
            event.accept()
        else:
            event.ignore()

    def quit(self):
        self.stopDobby()
        qApp.quit


class DobbyApplication(QThread):
    #TODO: Make a real application instead of using Dobby like this... /!\ http://labs.qt.nokia.com/2010/06/17/youre-doing-it-wrong/
    #TODO: Inherit Dobby as well as QThread instead of encapsulate the Dobby (poor Dobby...)
    #TODO: Choose between the two options above.
    def __init__(self, parent=None):
        super(DobbyApplication, self).__init__(parent)
        self.dobby = Dobby(os.path.abspath('data'), quiet=False, verbose=False, use_signal=False)
        self.running = False

    def stop(self):
        if not self.running:
            return
        self.dobby.stop()
        self.running = False
        self.wait()

    def run(self):
        self.running = True
        self.dobby.start()
        while self.running:
            time.sleep(1)
