#!/usr/bin/env python3
# -*- coding: utf-8 -*-

version = 0.1

class NonPeer(object):
    """
    Representation of a non-* software, and stock of his controls
    """
    def __init__(self, url, name, version, ident):
        self.url = url
        self.name = name
        self.version = version
        self.ident = ident
        
        

class OurNonClient(object):
    
    # OSC::Signal messages from https://github.com/original-male/non/blob/master/nonlib/OSC/Endpoint.C#L216
    # All will be implemented... One Day...
    methods = {"/non/hello" : ("ssss", None), # Broadcasted Hello message. (osc_url, app_title, version, instance_name)
               "/signal/hello" : ("ss", None), # Unicast Hello response from app. (Ident, url)
               "/signal/connect" : ("ss", None), # Inform about a new control link. (source Ident/path, dest Ident/path)
               "/signal/disconnect" : ("ss", None), # Inform about a removed control link. (source Ident/path, dest Ident/path)
               "/signal/renamed" : ("ss", None), # TODO
               "/signal/removed" : ("s", None), # TODO
               "/signal/created" : ("ssfff", None), # Inform about a new controlable. (Ident/path, [in|out], min, max, default)
               "/signal/list" : ("", None), # Ask for possible controls. (reply form = path : /reply. "/signal/list", Ident/path, [in|out], min, max, default)
               #"/reply" : ("", None), # TODO
               }
    # Dict of all peers as Id : nonPeerObj
    nonPeers = {}               
    
    def __init__(self, nsmClient):
        nsmClient = nsmClient
        self.nsmStates = nsmClient.states
        
        nsmClient.methodAdder(self.methods)
        self.nonPeers[self.nsmStates.ourUrl] = NonPeer(self.nsmtates.ourUrl, version, self.nsmStates.clientId)
        
    
    def sayHello(self):
        """
        Send a broadcast bundle to NSM,
         url : /nsm/server/broadcast
         format : sssss
         "/non/hello", osc_url, app_title, version, instance_name
        """
        pass
        
    def handleHello(self):
        """
        Create a NonPeer instance

        """
        pass
