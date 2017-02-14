#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Based on pynsmclient by Nils Gey.
The goal : list all NSM clients and route externals OSC messages to it.
... good luck to myself
"""

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import qDebug, QObject, QThread
import logging
import time

from imports import nsmclient
from imports.pyNonPeer import OurNonClient
from imports.sighandler import SignalWakeupHandler


appTitle = "Non-OSC-NAT"


#QT thead worker
class NsmClientWorker(QObject):
    """Worker for NsmClient, maybe with his own eventloop"""
    ### NSM signals ###
    nsmReadySign = QtCore.pyqtSignal(int)
    ourNsmClientSign= QtCore.pyqtSignal(object)
    
    openSessSign = QtCore.pyqtSignal(str, str)
    saveSessSign = QtCore.pyqtSignal(str, str)
    exitAppSign = QtCore.pyqtSignal()
    
    ### NON signals ###
    updateListSign = QtCore.pyqtSignal(str, object)
    
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
        """ 
        Non-stuffs stuffs 
        
        callbacks should be a dict with the form :
            dict{
                addpeer: addPeerCallback, # retrun the added peer object.
                delpeer: delPeerCallback, 
                addsignal: addSignalCallback, 
                delsignal: delSignalCallback
            }
        """

        ## Displaced in OurNSMClient
        #self.ourNonClient = OurNonClient(self.ourNsmClient, self.nonCallbacks)
        self.ourNsmClient, self.nsmProcess = nsmclient.init(prettyName = appTitle, 
                                                         capabilities = capabilities,
                                                         requiredFunctions = requiredFunctions,
                                                         optionalFunctions = optionalFunctions,
                                                         sleepValueMs = 0
                                                         ) 
        self.ourNsmClientSign.emit(self.ourNsmClient)
        
        
        nonCallbacks = {
            "addpeer" : self.addpeerCallback,
            "delpeer" : self.delpeerCallback
            }
        
        nonPeersParms = {
            "baseport" : 16000, # Start port for externalized client. 16000 by default
        }
        
        self.ourNonPeer = OurNonClient(self.ourNsmClient, nonCallbacks, nonPeersParms)
                
        qDebug("Init Finished")

    ### NSM callbacks ###

    def saveCallback(self,pathBeginning):
        qDebug("Got a SaveCallback")
        returnStr = "\n Not realy implemented \n" + pathBeginning
        return False, returnStr
                
    def openOrNewCallback(self,pathBeginning, clientId):
        qDebug("Got a OpenOrNewCallback")
        self.openSessSign.emit(pathBeginning, clientId)
        self.ourNonPeer.loadSession()
        return True, "Not realy implemented"

    def exitCallback(self):
        qDebug("Got a ExitCallback")
        #self.quit()
        exit()
        return True
        
    ### Non Callbacks ###
    
    def addpeerCallback(self, peer):
        self.updateListSign.emit("add", peer)
    
    def delpeerCallback(self, peerId):
        self.updateListSign.emit("del", peerId)
    

    def run(self):
       
        qDebug("Enter in event loop")
        self.eventLoop = QtCore.QTimer()
        self.eventLoop.start(10) #10ms-20ms is smooth for "real time" feeling. 100ms is still ok.
        self.eventLoop.timeout.connect(self.rolling)

    def rolling(self):
        #qDebug("Looped !")
        self.nsmProcess()
        self.ourNonPeer.process()
        self.ourNsmClientSign.emit(self.ourNsmClient)



### GUI class
class Gui(QtWidgets.QMainWindow):
    def __init__(self, qtApp):
        
        super().__init__()

        self.qtApp = qtApp
        self.setGeometry(300,300,350,250)
        
        # Define some attributs
        self.timers = {}
        
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
        self.status.showMessage("Don't read that !'")  
        
        # Define QT's main widget
        self.mainWidget = QtWidgets.QWidget(self)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        # Connect gui widgets to functions
        self.listSelPeer.currentItemChanged.connect(self.selPeerItem)
        self.peerPortApply.clicked.connect(self.applyPort)
        
        
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
        
    def displayStatus(self, msg):
        self.status.showMessage(str(msg))
        
    def updatePeerList(self, action, peer):
        if action == "add":
            newPeerItem = QtWidgets.QListWidgetItem(peer.clientId)
            newPeerItem.setData(QtCore.Qt.UserRole, peer)
            #self.peerDict[newPeerItem] = peer
            self.listSelPeer.addItem(newPeerItem)
            self.displayStatus("Discovered new peer : " + peer.clientId)
        elif action == "remove":
            pass
    
    def selPeerItem(self, curr, prev):
        nonPeer = curr.data(QtCore.Qt.UserRole)
        print(nonPeer.extPort)
        self.peerPort.setValue(nonPeer.extPort)
    
    def applyPort(self):
        selPeerInList = self.listSelPeer.selectedItems()
        selNonPeer = selPeerInList[0].data(QtCore.Qt.UserRole)
        #selNonPeer = selPeerData.toPyObject()
        selNonPeer.extPort = self.peerPort.value()
    
#    def displayIncomeOsc(self):
#        all_items = self.listSelPeer.findItems('', QtCore.Qt.MatchRegExp)
#        
#        for item in all_items:
#            peer = item.data(QtCore.Qt.UserRole)
#            if peer.oscIncome
    
    
    
    
#    def testGui(self):
#        self.status.addPermanentWidget(QtWidgets.QLabel(self.ourNsmClient.states.clientId))
   
     
     

### QT main
class Main(QObject):
    def __init__(self, qtApp, gui):
        
        self.qtApp = qtApp
        self.gui = gui
        # Try to thead
        self.nsmClientThread = QThread()
        self.nsmClientWorker = NsmClientWorker()
        self.nsmClientWorker.moveToThread(self.nsmClientThread)
        self.gui.displayStatus("Init...")
        ## Connect alls signals
        
        # NSM
        self.nsmClientWorker.nsmReadySign.connect(self.nsmClientRdy)
        self.nsmClientWorker.exitAppSign.connect(self.quit)
        self.nsmClientWorker.ourNsmClientSign.connect(self.nsmClientGet)
        self.nsmClientWorker.openSessSign.connect(gui.showPeersSel)
        
        # NON
        self.nsmClientWorker.updateListSign.connect(gui.updatePeerList)
        self.gui.displayStatus("Worker connected")
        
        
        self.nsmClientThread.started.connect(self.nsmClientWorker.run)

        self.nsmClientThread.finished.connect(self.quit)
        self.nsmClientThread.start()
        self.gui.displayStatus("Worker thread started")
        #self.nsmClientThread.exec()
        self.gui.displayStatus("Worker thread exec")
        qDebug("Worker in place, running...")
        
        


    def nsmClientRdy(self, loops):
        
        #self.title.setText("<b>" + str(loops) + "</b>")
        pass
    
    def nsmClientGet(self, ourNsmClient):
        self.ourNsmClient = ourNsmClient
        gui.testGui()

    
    
    def quit(self):
        qDebug("quit called")
        self.gui.displayStatus("Request to quit")
        #self.nsmClientThread.exit()
        #self.qtApp.exit()
        return "Ready to quit"

        #self.title.setText(str(self.ourNsmClient.states.prettyNSMName))


if __name__ == '__main__':

    qtApp = QtWidgets.QApplication(sys.argv)
    handler = SignalWakeupHandler(qtApp)
    nonNatUi = Gui(qtApp)
    nonNatUi.show()
    nonNat = Main(qtApp, nonNatUi)
    
#    timer = QTimer()
#    timer.start(100)
#    timer.timeout.connect(nonNatUi.showIncomeOsc())

    """
    signal.signal(signal.SIGTERM, Main.quit)
    """
    ##################
    #Start everything
    qtApp.exec_()
