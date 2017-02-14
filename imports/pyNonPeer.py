#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from imports.callback_dict import CallbackDict
import liblo

version = "0.1.1"

"""
    callbacks should be a dict with the form :
        dict{
            addpeer: addPeerCallback, 
            delpeer: delPeerCallback, 
            addsignal: addSignalCallback, 
            delsignal: delSignalCallback
        }
"""
nonCallbacks = {"addpeer" : None,
                "delpeer" : None}

nonParms = {"baseport" : 16000,}




class NonPeer(object):
    """
    Representation of a non-* software, and stock of his controls
    """
    
    def __init__(self, url, name=None, version=None, clientId=None):
        self._url = url
        self._name = name
        self._version = version
        self._clientId = clientId
        self._extPort = 0
        self._oscServer = None
        self._oscIncome = False
         
    @property
    def name(self):
        return self._name
    
    @property
    def clientId(self):
        return str(self._clientId)

    @property
    def extPort(self):
        return int(self._extPort)

    @extPort.setter
    def extPort(self, port):
        if port != self._extPort:
            self._oscServer = liblo.Server(port)
            self._oscServer.add_method(None, None, self.oscForward)
            self._extPort = port
            #print("Assigned port " + str(port) + " to peer " + self._clientId)
    
    @property
    def ocsIncome(self):
        return self._oscIncome
    
    def oscForward(self, path, argList, types): 
        path = self._clientId + path
        #print("Got " + path + " fw to " + self._url)
        i = 0
        m = liblo.Message(path)
        #print(str(path) + " arguments :")
        for a in argList:
            m.add((types[i], a))
            #print(str(types[i]) + " " + str(a))
            i += 1
        self._oscServer.send(self._url, m)
        
    def procOsc(self):
        oscIncome = self._oscServer.recv(0)
        if oscIncome != self._oscIncome:
            self._oscIncome = oscIncome
            return oscIncome
        
    

# External port of a new peer
newExtPort = nonParms["baseport"]

class NonPeers(dict):
    """
    Custom dict for stock all peers instances
    It call alls neededs callbacks when add and delete peer
    """
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

#    def __getitem__(self, key):
#        if self.get_callback:
#            self.get_callback()
#        return dict.__getitem__(self, key)


    # For a new peer : peerId = clientId, val = url
    def __setitem__(self, peerId, *arg, **kargs):
    

        if peerId not in self:
            
            # New peer instance
            dict.__setitem__(self, peerId, NonPeer(arg, kargs, clientId = peerId))
            
            # port assignation
            global newExtPort
            self[peerId].extPort = newExtPort
            print("Got hello from : " + peerId)
            newExtPort += 1
            
            if nonCallbacks["addpeer"]:
                nonCallbacks["addpeer"](self[peerId])

    def __delitem__(self, peerId):
        if self.del_callback:
            self.del_callback()
        dict.__delitem__(self, key)


class OurNonClient(object):
    """
        The non-* client itself.
        Register methods to libloServer, discover & store peers.
    """
    def __init__(self, nsmClient, callbacks, parms):

        
        # Methods to pass to liblo server.
        # Form : "/osc/path" : (Callback, Reply Callback)    
        # OSC::Signal messages from https://github.com/original-male/non/blob/master/nonlib/OSC/Endpoint.C#L216
        # All will be implemented... One Day...

        # Without args types, better intergration with nsmclient.py
        methods = {"/non/hello" : (self.handleHello, None), # Broadcasted Hello message. (osc_url, app_title, version, instance_name)
                   "/signal/hello" : (self.handleHello, None), # Unicast Hello response from app. (Ident, url)
                   "/signal/connect" : (None, None), # Inform about a new control link. (source Ident/path, dest Ident/path)
                   "/signal/disconnect" : (None, None), # Inform about a removed control link. (source Ident/path, dest Ident/path)
                   "/signal/renamed" : (None, None), # TODO
                   "/signal/removed" : (None, None), # TODO
                   "/signal/created" : (None, None), # Inform about a new controlable. (Ident/path, [in|out], min, max, default)
                   "/signal/list" : (None, None), # Ask for possible controls. (reply form = path : /reply. "/signal/list", Ident/path, [in|out], min, max, default)
                   #"/reply" : ("", None), # TODO
                   }

        
    #    # With or without types ??? This is the question...
    #    
    #    methods = {"/non/hello" : ("sssss", None), # Broadcasted Hello message. ("/non/hello", osc_url, app_title, version, instance_name)
    #               "/signal/hello" : ("ss", None), # Unicast Hello response from app. (Ident, url)
    #               "/signal/connect" : ("ss", None), # Inform about a new control link. (source Ident/path, dest Ident/path)
    #               "/signal/disconnect" : ("ss", None), # Inform about a removed control link. (source Ident/path, dest Ident/path)
    #               "/signal/renamed" : ("ss", None), # TODO
    #               "/signal/removed" : ("s", None), # TODO
    #               "/signal/created" : ("ssfff", None), # Inform about a new controlable. (Ident/path, [in|out], min, max, default)
    #               "/signal/list" : ("", None), # Ask for possible controls. (reply form = path : /reply. "/signal/list", Ident/path, [in|out], min, max, default)
    #               #"/reply" : ("", None), # TODO
    #               }
        
        # redefines globals non callbacks
        global nonCallbacks
        nonCallbacks = callbacks

        # 
        global nonParms
        nonParms = parms
        
        self.nsmClient = nsmClient
        self.nsmStates = self.nsmClient.states
        self.libloServer = nsmClient.libloServer
        
        
        nsmClient.methodAdder(methods)
    
    def loadSession(self):
        
        # New peers list instance
        self.nonPeers = NonPeers()
        #self.nonPeers.clear()
        self.nonPeers[self.nsmStates.clientId] = self.nsmStates.ourUrl,self.nsmStates.prettyNSMName, version, self.nsmStates.clientId
        self.sayNonHello()
        
        
    
    def sayNonHello(self):
        """
        Send a broadcast bundle to NSM,
         url : /nsm/server/broadcast
         format : sssss
         "/non/hello", osc_url, app_title, version, instance_name
        """
        msg = liblo.Message("/nsm/server/broadcast")
        msg.add("/non/hello")
        msg.add(str(self.nsmStates.ourUrl))
        msg.add(str(self.nsmStates.prettyNSMName))
        msg.add(str(version))
        msg.add(str(self.nsmStates.clientId))
        bndl = liblo.Bundle(msg)
        
        self.libloServer.send(self.nsmStates.nsmUrl, bndl)
            
    def handleHello(self, path, argList, types):
        """
        Create a NonPeer instance

        """
        print(path)
        if path == "/signal/hello":
            peerId, url = argList
            self.nonPeers[peerId] = url
        
        elif path == "/non/hello":
            url, name, version, peerId = argList
            self.nonPeers[peerId] = url, {"name" : name,
                                         "version" : version} 
        
    def process(self):
        """
        we need to call server.recv on all liblo instances
        """
        for peerId, peerObj in self.nonPeers.items():
            peerObj.procOsc()

        
        
        
        
        
        
