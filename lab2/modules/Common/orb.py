# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

import threading
import socket
import json

"""Object Request Broker

This module implements the infrastructure needed to transparently create
objects that communicate via networks. This infrastructure consists of:

--  Stub ::
        Represents the image of a remote object on the local machine.
        Used to connect to remote objects. Also called Proxy.
--  Skeleton ::
        Used to listen to incoming connections and forward them to the
        main object.
--  Peer ::
        Class that implements basic bidirectional (Stub/Skeleton)
        communication. Any object wishing to transparently interact with
        remote objects should extend this class.

"""


class CommunicationError(Exception):
    pass


class Stub(object):

    """ Stub for generic objects distributed over the network.

    This is  wrapper object for a socket.

    """

    def __init__(self, address):
        self.address = tuple(address)

    def _rmi(self, method, *args):
        #
        # Your code here.
        #

        sock = socket.create_connection(self.address) #what if it cant connect?
        conn = sock.makefile(mode="rw")
        
        # make our message and send it
        data = json.dumps({"method":method,"args":args}) + '\n'
    
        conn.write(data)
        conn.flush()

        #read the reply and unpack it
        res = json.loads(conn.readline())
        conn.close()


        if "error" in res:
            # #there has been an exception on the server,
            # #find out which and raise it here on the client
            err = res["error"]
            exc = getattr(globals(), err["name"], None)

            if exc is not None:
                raise exc(*err["args"])

        return res.get("result")

        #end my code

    def __getattr__(self, attr):
        """Forward call to name over the network at the given address."""
        def rmi_call(*args):
            return self._rmi(attr, *args)
        return rmi_call


class Request(threading.Thread):

    """Run the incoming requests on the owner object of the skeleton."""

    def __init__(self, owner, conn, addr):
        threading.Thread.__init__(self)
        self.addr = addr
        self.conn = conn
        self.owner = owner
        self.daemon = True

    def run(self):

        #
        # Your code here.

        try:
            w = self.conn.makefile(mode="rw")
            req = json.loads(w.readline())

            #get the corresponding method of the owner
            method = getattr(self.owner,req["method"])
            
            #invoke the method and send the result
            ret = method(req["args"])

            w.write(json.dumps({"result":ret}) + '\n')
            w.flush()
        except Exception as e:
            w = self.conn.makefile(mode="rw")
            w.write(json.dumps({"error":{"name":e.__class__.__name__,
                                         "args":e.args}}) + '\n')
            w.flush()
        finally:
            self.conn.close()

        #end my code


class Skeleton(threading.Thread):

    """ Skeleton class for a generic owner.

    This is used to listen to an address of the network, manage incoming
    connections and forward calls to the generic owner class.

    """

    def __init__(self, owner, address):
        threading.Thread.__init__(self)
        self.address = address
        self.owner = owner
        self.daemon = True
        #
        # Your code here.

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.address)
        self.server.listen(1)

        # end my code

    def run(self):
        #
        # Your code here.
        
        while True:
            try:
                conn,addr = self.server.accept()
                req = Request(self.owner,conn,addr)
                req.start()
            except socket.error:
                continue

        # end my code
        


class Peer:

    """Class, extended by objects that communicate over the network."""

    def __init__(self, l_address, ns_address, ptype):
        self.type = ptype
        self.hash = ""
        self.id = -1
        self.address = self._get_external_interface(l_address)
        self.skeleton = Skeleton(self, self.address)
        self.name_service_address = self._get_external_interface(ns_address)
        self.name_service = Stub(self.name_service_address)

    # Private methods

    def _get_external_interface(self, address):
        """ Determine the external interface associated with a host name.

        This function translates the machine's host name into its the
        machine's external address, not into '127.0.0.1'.

        """

        addr_name = address[0]
        if addr_name != "":
            addrs = socket.gethostbyname_ex(addr_name)[2]
            if len(addrs) == 0:
                raise ComunicationError("Invalid address to listen to")
            elif len(addrs) == 1:
                addr_name = addrs[0]
            else:
                al = [a for a in addrs if a != "127.0.0.1"]
                addr_name = al[0]
        addr = list(address)
        addr[0] = addr_name
        return tuple(addr)

    # Public methods

    def start(self):
        """Start the communication interface."""

        self.skeleton.start()
        self.id, self.hash = self.name_service.register(self.type,
                                                        self.address)

    def destroy(self):
        """Unregister the object before removal."""
        self.name_service.unregister(self.id, self.type, self.hash)

    def check(self):
        """Checking to see if the object is still alive."""

        return (self.id, self.type)
