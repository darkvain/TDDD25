# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Module for the distributed mutual exclusion implementation.

This implementation is based on the second Rikard-Agravara algorithm.
The implementation should satisfy the following requests:
    --  when starting, the peer with the smallest id in the peer list
        should get the token.
    --  access to the state of each peer (dictinaries: request, token,
        and peer_list) should be protected.
    --  the implementation should gratiously handle situations when a
        peer dies unexpectedly. All exceptions comming from calling
        peers that have died, should be handled such as the rest of the
        peers in the system are still working. Whenever a peer has been
        detected as dead, the token, request, and peer_list
        dictionaries should be updated acordingly.
    --  when the peer that has the token (either TOKEN_PRESENT or
        TOKEN_HELD) quits, it should pass the token to some other peer.
    --  For simplicity, we shall not handle the case when the peer
        holding the token dies unexpectedly.

"""

from threading import Event

NO_TOKEN = 0
TOKEN_PRESENT = 1
TOKEN_HELD = 2




class DistributedLock(object):

    """Implementation of distributed mutual exclusion for a list of peers.

    Public methods:
        --  __init__(owner, peer_list)
        --  initialize()
        --  destroy()
        --  register_peer(pid)
        --  unregister_peer(pid)
        --  acquire()
        --  release()
        --  request_token(time, pid)
        --  obtain_token(token)
        --  display_status()

    """

    def __init__(self, owner, peer_list):
        self.peer_list = peer_list
        self.owner = owner
        self.time = 0
        self.token = None
        self.request = {}
        self.state = NO_TOKEN
        self.wait_event = Event()

    def _prepare(self, token):
        """Prepare the token to be sent as a JSON message.

        This step is necessary because in the JSON standard, the key to
        a dictionary must be a string whild in the token the key is
        integer.
        """
        return list(token.items())

    def _unprepare(self, token):
        """The reverse operation to the one above."""
        return dict(token)

    # Public methods

    def initialize(self):
        """ Initialize the state, request, and token dicts of the lock.

        Since the state of the distributed lock is linked with the
        number of peers among which the lock is distributed, we can
        utilize the lock of peer_list to protect the state of the
        distributed lock (strongly suggested).

        NOTE: peer_list must already be populated when this
        function is called.

        """
        #
        # Your code here.
        #

        self.peer_list.lock.acquire()
        try:
            peers = sorted(self.peer_list.peers.keys())

            # If I'm alone, or have the smallest id I get to start with the token
            if len(peers) == 0 or peers[0] > self.owner.id:
                self.token = {}
                self.token[self.owner.id] = 0
                self.state = TOKEN_PRESENT
            else:
                for pid in self.peer_list.get_peers():
                    self.request[pid] = 0

            self.request[self.owner.id] = 0
        finally:
            self.peer_list.lock.release()

        #end my code

    def destroy(self):
        """ The object is being destroyed.

        If we have the token (TOKEN_PRESENT or TOKEN_HELD), we must
        give it to someone else.

        """
        #
        # Your code here.
        self.peer_list.lock.acquire()
        try:
            #if I have the token I must give it to someone else
            if(self.state == TOKEN_PRESENT or self.state == TOKEN_HELD):
                
                #try to release
                if not self.release():
                    #If nobody wanted the token, send it to the whoever is first in the peer list
                    #( in a rather awkward way I might add )
                    for pid in self.peer_list.get_peers():
                        self.peer_list.peer(pid).obtain_token(self._prepare(self.token))
                        break
        finally:
            self.peer_list.lock.release()

    def register_peer(self, pid):
        """Called when a new peer joins the system."""
        #
        # Your code here.
        #
        self.peer_list.lock.acquire()
        try:
            print("register: ", pid)
            if self.token:
                self.token[pid] = 0
        
            self.request[pid] = 0

        finally:
            self.peer_list.lock.release()
        #end my code

    def unregister_peer(self, pid):
        """Called when a peer leaves the system."""
        #
        # Your code here.
        #
        self.peer_list.lock.acquire()
        try:
            del self.request[pid]
            if self.token:
                del self.token[pid]

        finally:
            self.peer_list.lock.release()

    def acquire(self):
        """Called when this object tries to acquire the lock."""
        print("Trying to acquire the lock...")
        #
        # Your code here.
        #

        self.peer_list.lock.acquire()
        try:
            self.time = self.time + 1
        
            if self.state == TOKEN_PRESENT:
                #we already have the token so no need to request it
                self.state = TOKEN_HELD
                return

        finally:
            self.peer_list.lock.release()

        for pid in self.peer_list.get_peers():
            self.peer_list.peer(pid).request_token(self.time, self.owner.id)

        #print("wait for the flag")
        #self.wait_event.wait()
        #print("clear the flag")
        #self.wait_event.clear()

        print("waiting for token...")
        #TODO: use something better than a spinlock
        while self.state == NO_TOKEN:
            pass

        self.peer_list.lock.acquire()
        try:
            self.state = TOKEN_HELD
            print("Got the token!")
        finally:
            self.peer_list.lock.release()

    def release(self):
        """Called when this object releases the lock."""
        print("Releasing the lock...")
        #
        # Your code here.
        #

        

        self.peer_list.lock.acquire()
        try:
            #this is a rather complicated way of
            #finding the next process to obtain the
            #token

            #build a list of the the request dict
            req_list = sorted(self.request.items())
            req_len = len(req_list)

            #find the correct index of my ID in the new list
            index = 0
            for i in range(0, req_len):
                if req_list[i][0] == self.owner.id:
                    index = i
                    break
                    
            #iterate through the requests
            #starting from the process ID above
            #this peers ID, wrapping around
            #until we reach this peers ID again  
            i = (index + 1) % req_len
            while i != index:

                pid = req_list[i][0] #the id of the peer currently looked at
                req_t = req_list[i][1] #the time this peer last requested the token
                token_t = self.token[pid] #the last time this peer had the token
        
                if req_t > token_t: 
                    #the peer has a pending request for the token,
                    #send the token to the waiting peer

                    self.peer_list.lock.release()

                    #what happens if the peer we decide to give the token to has left?
                    self.peer_list.peer(pid).obtain_token(self._prepare(self.token))
            
                    self.peer_list.lock.acquire()
                    self.state = NO_TOKEN
                    self.token = None

                    return True
                
                i = (i + 1) % req_len
            #end while
        
            #nobody needs the token right now, hang on to it for now
            self.state = TOKEN_PRESENT
            return False

        finally:
            self.peer_list.lock.release()

    def request_token(self, time, pid):
        """Called when some other object requests the token from us."""
        #
        # Your code here.
        #
        self.peer_list.lock.acquire()
        try:
            self.request[pid] = max(self.request[pid], time)
            self.time = max(time, self.time)

            if self.state == TOKEN_PRESENT:
                self.release()

        finally:
            self.peer_list.lock.release()

        #end my code

    def obtain_token(self, token):
        """Called when some other object is giving us the token."""
        print("Receiving the token...")
        #
        # Your code here.
        #

        self.peer_list.lock.acquire()
        try:
            self.token = self._unprepare(token)
            self.token[self.owner.id] = self.time
            self.state = TOKEN_PRESENT
            #print("set the flag")
            #self.wait_event.set()
            #print("the flag has been set")
        finally:
            self.peer_list.lock.release()
        #end my code

    def display_status(self):
        """Print the status of this peer."""
        self.peer_list.lock.acquire()
        try:
            nt = self.state == NO_TOKEN
            tp = self.state == TOKEN_PRESENT
            th = self.state == TOKEN_HELD
            print("State   :: no token      : {0}".format(nt))
            print("           token present : {0}".format(tp))
            print("           token held    : {0}".format(th))
            print("Request :: {0}".format(self.request))
            print("Token   :: {0}".format(self.token))
            print("Time    :: {0}".format(self.time))
        finally:
            self.peer_list.lock.release()
