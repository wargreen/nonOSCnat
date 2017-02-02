#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Based on pynsmclient2 by Nils Gey.
The goal : list all NSM clients and route externals OSC messages to it.
... good luck to myself
"""

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import qDebug, QObject, QThread
import logging

from imports import nsmclient
from imports.pyNonPeer import OurNonClient


appTitle = "Non-OSC-NAT"


#QT thead worker
class NsmClientWorker(QObject):
    """Worker for NsmClient, maybe with his own eventloop"""
    
    nsmReadySign = QtCore.pyqtSignal(int)
    ourNsmClientSign= QtCore.pyqtSignal(object)
    
    openSessSign = QtCore.pyqtSignal(str, str)
    saveSessSign = QtCore.pyqtSignal(str, str)
    exitAppSign = QtCore.pyqtSignal()
    
    def __init__(self):
        QObject.__init__(self)
        qDebug("Start Init")
        
#        if thread is None:
#            thread = QThread()
#            self.moveToThread(thread)


        """ NSM stuffs """        
        #All capabilities default to False. Just change one value to True if you program can do that.
        capabilities = {
            "switch" : False,		#client is capable of responding to multiple `open` messages without restarting
            "dirty" : False, 		#client knows when it has unsaved changes
            "progress" : False,		#client can send progress updates during time-consuming operations
            "message" : False, 		#client can send textual status updates
            "optional-gui" : False,	#client has an optional GUI	
            }

        requiredFunctions = {
            "function_open" : self.openOrNewCallback, #Accept two parameters. Return two values. A bool and a status string. Otherwise you'll get a message that does not help at all: "Exception TypeError: "'NoneType' object is not iterable" in 'liblo._callback' ignored"
            "function_save" : self.saveCallback, #Accept one parameter. Return two values. A bool and a status string. Otherwise you'll get a message that does not help at all: "Exception TypeError: "'NoneType' object is not iterable" in 'liblo._callback' ignored"					
            }

        optionalFunctions = {
            "function_quit" : self.exitCallback,  #Accept zero parameters. Return True or False
            "function_showGui" : None, #Accept zero parameters. Return True or False
            "function_hideGui" : None, #Accept zero parameters. Return True or False
            "function_sessionIsLoaded" : None, #No return value needed.
            }
        self.ourNsmClient, self.process = nsmclient.init(prettyName = appTitle, capabilities = capabilities, requiredFunctions = requiredFunctions, optionalFunctions = optionalFunctions,  sleepValueMs = 0) 
        self.ourNsmClientSign.emit(self.ourNsmClient)
        
#        thread.started.connect(lambda:self.run(thread))
#        thread.start()
        
        qDebug("Init Finished")


    def saveCallback(self,pathBeginning, clientId):
        qDebug("Got a SaveCallback")
        return False, "Not realy implemented"
                
    def openOrNewCallback(self,pathBeginning, clientId):
        self.openSessSign.emit(pathBeginning, clientId)
        return True, "Not realy implemented"

    def exitCallback(self):
        self.exitAppSign.emit()
        return True

    def run(self, thread=None):
#        self.isRun = False
#        if self.isRun:
#            qDebug("Running")
#        else:
#            self.isRun = True
#            qDebug("Worker start in progress")
        
        qDebug("Enter in event loop")
        #thread.exec()
        self.eventLoop = QtCore.QTimer()
        self.eventLoop.start(500) #10ms-20ms is smooth for "real time" feeling. 100ms is still ok.
        self.eventLoop.timeout.connect(self.rolling)

    def rolling(self):
        qDebug("Looped !")
        self.process()
        self.ourNsmClientSign.emit(self.ourNsmClient)



### GUI class
class Gui(QtWidgets.QMainWindow):
    def __init__(self, qtApp):
        
        super().__init__()

        self.qtApp = qtApp
        self.setGeometry(300,300,350,250)
        
        # Define all GUI elements
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.wraperBox = QtWidgets.QGroupBox()
        self.peerSelect = QtWidgets.QVBoxLayout()
        self.peersList = QtWidgets.QHBoxLayout()
        self.peersList.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.peerPort = QtWidgets.QSpinBox()
        self.peerPort.setMinimum(1025)
        self.peerPort.setMaximum(65000)
        self.peerPort.setValue(16000)
        self.peerPortApply = QtWidgets.QPushButton("Apply")
        self.peerPortForm = QtWidgets.QVBoxLayout()
        self.listHead = QtWidgets.QLabel("NON Clients :")
        self.listSelPeer = QtWidgets.QListWidget()
        #self.infoAppId = QtWidgets.QLabel
        #self.spacer = QtWidgets.QSpacerItem()
        
        self.status = QtWidgets.QMainWindow.statusBar(self)
        self.status.showMessage('Init...')  
        
        # Define QT's main widget
        self.mainWidget = QtWidgets.QWidget(self)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        
    def showPeersSel(self):
        # Define elements places
        #self.setLayout(self.wraper)
        self.mainLayout.addWidget(self.wraperBox)
        self.wraperBox.setLayout(self.peersList)
        self.peersList.addLayout(self.peerSelect)
        self.peersList.addStretch(50)
        self.peersList.addLayout(self.peerPortForm)
        
        # Define widgets in peerSelect
        self.peerSelect.addWidget(self.listHead)
        self.peerSelect.addWidget(self.listSelPeer)
        # Define widgets in peerPortForm
        self.peerPortForm.addWidget(self.peerPort)
        self.peerPortForm.addWidget(self.peerPortApply)     
        
    def testGui(self):
        self.status.addPermanentWidget(QtWidgets.QLabel(self.ourNsmClient.states.clientId))
   
     
     

### QT main
class Main(QObject):
    def __init__(self, qtApp, gui):
        
        self.qtApp = qtApp
        self.gui = gui
        # Try to thead
        self.nsmClientThread = QThread()
        self.nsmClientWorker = NsmClientWorker()
        self.nsmClientWorker.moveToThread(self.nsmClientThread)
        
        self.nsmClientWorker.nsmReadySign.connect(self.nsmClientRdy)
        self.nsmClientWorker.exitAppSign.connect(self.quit)
        self.nsmClientWorker.ourNsmClientSign.connect(self.nsmClientGet)
        self.nsmClientWorker.openSessSign.connect(gui.showPeersSel)
        
        self.nsmClientThread.started.connect(self.nsmClientWorker.run)
        
        self.nsmClientThread.start()
        self.nsmClientThread.exec()
        qDebug("Worker in place, running...")
        
        


    def nsmClientRdy(self, loops):
        
        #self.title.setText("<b>" + str(loops) + "</b>")
        pass
    
    def nsmClientGet(self, ourNsmClient):
        self.ourNsmClient = ourNsmClient
        gui.testGui()
    
    def applyPort(self):
        pass
    
    
    def quit(self):
        self.title.setText("Quitte")
        exit()

        #self.title.setText(str(self.ourNsmClient.states.prettyNSMName))


if __name__ == '__main__':
            
    qtApp = QtWidgets.QApplication(sys.argv)
    nonNatUi = Gui(qtApp)
    nonNatUi.show()
    nonNat = Main(qtApp, nonNatUi)

    ##################
    #Start everything
    qtApp.exec_()
