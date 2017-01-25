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

import nsmclient


#QT thead worker
class NsmClientWorker(QObject):
    """Worker for NsmClient, maybe with his own eventloop"""
    
    nsmReadySign = QtCore.pyqtSignal(int)
    ourNsmClientSign= QtCore.pyqtSignal(object)
    exitAppSign = QtCore.pyqtSignal()
    
    def __init__(self, appTitle, thread=None):
        QObject.__init__(self)
        qDebug("Start Init")
        
        if thread is None:
            thread = QThread()
            self.moveToThread(thread)
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
        
        thread.started.connect(lambda:self.run(thread))
        thread.start()
        
        qDebug("Init Finished")


    def saveCallback(self,pathBeginning, clientId):
        pass
        return True, ""
        
    def openOrNewCallback(self,pathBeginning, clientId):
        return True, ""

    def exitCallback(self):
        self.exitAppSign.emit()
        return True

    isRun = False
    def run(self, thread):
        if self.isRun:
            qDebug("Running")
        else:
            self.isRun = True
            qDebug("Worker start in progress")
        
        self.process()
        self.ourNsmClientSign.emit(self.ourNsmClient)
        qDebug("Enter in event loop")
        thread.exec()



### QT main
class Main(QtWidgets.QWidget):
    def __init__(self, qtApp):
        super().__init__()
        
        appTitle = "Non-OSC-NAT"
        
        
        self.qtApp = qtApp
        self.setGeometry(300,300,350,250)
        # Define all elements
        self.wraper = QtWidgets.QVBoxLayout()
        self.wraperBox = QtWidgets.QGroupBox()
        self.peerSelect = QtWidgets.QVBoxLayout()
        self.peersList = QtWidgets.QHBoxLayout()
        self.peersList.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.peerPort = QtWidgets.QSpinBox()
        self.peerPort.setMinimum(1025)
        self.peerPort.setMaximum(65000)
        self.peerPortApply = QtWidgets.QPushButton("Apply")
        self.peerPortForm = QtWidgets.QVBoxLayout()
        self.listHead = QtWidgets.QLabel("NON Clients :")
        self.listSelPeer = QtWidgets.QListWidget()
        #self.spacer = QtWidgets.QSpacerItem()
        
        # Define elements places
        self.setLayout(self.wraper)
        self.wraper.addWidget(self.wraperBox)
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
        
        # Try to thead
        """
        self.threads = []
        nsmClientWorker = NsmClientWorker(appTitle)
        
        nsmClientWorker.nsmReadySign.connect(self.nsmClientRdy)
        nsmClientWorker.exitAppSign.connect(self.quit)
        nsmClientWorker.ourNsmClientSign.connect(self.nsmClientGet)
        self.threads.append(nsmClientWorker)
        #nsmClientWorker.start()
        qDebug("Worker in place, running...")
        """
        self.eventLoop = QtCore.QTimer()
        self.eventLoop.start(100) #10ms-20ms is smooth for "real time" feeling. 100ms is still ok.

    
    
    def nsmClientRdy(self, loops):
        #self.title.setText("<b>" + str(loops) + "</b>")
        pass
    def nsmClientGet(self, ourNsmClient):
        self.ourNsmClient = ourNsmClient
        self.testGui()
        
    
    def quit(self):
        self.title.setText("Quitte")
        exit()

    def testGui(self):
        self.title.setText(str(self.ourNsmClient.states.prettyNSMName))


if __name__ == '__main__':
            
    qtApp = QtWidgets.QApplication(sys.argv)
    nsmOSC = Main(qtApp)
    nsmOSC.show()

    ##################
    #Start everything
    qtApp.exec_()
