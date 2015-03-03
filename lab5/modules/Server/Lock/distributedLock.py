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

import time

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
            if len(self.peer_list.get_peers()) == 0:
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
            if(self.state == TOKEN_PRESENT or self.state == TOKEN_HELD):
                if not self.release():
                    peerid = self.peer_list.peer(0) #get the first peer in que
                    self.peer_list.peer(peerid).obtain_token()
        finally:
            self.peer_list.lock.release()

    def register_peer(self, pid):
        """Called when a new peer joins the system."""
        #
        # Your code here.
        #
        
        print("register: ", pid)

        #self.peer_list.lock.acquire()
        #try:
        if self.token:
            self.token[pid] = 0
        
        self.request[pid] = 0
        #finally:
        #    self.peer_list.lock.release()

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

        print("acquire that token")
        
        self.time = self.time + 1
        
        if self.state == TOKEN_PRESENT:
            print("I already have that token!")
            self.state = TOKEN_HELD
            return
            
        for pid in self.peer_list.get_peers():
            self.peer_list.peer(pid).request_token(self.time, self.owner.id)

        while(self.state == NO_TOKEN):
            print("still waiting...")
            time.sleep(1)

        self.state = TOKEN_HELD
        print("Got the token!")

    def release(self):
        """Called when this object releases the lock."""
        print("Releasing the lock...")
        #
        # Your code here.
        #

        self.peer_list.lock.acquire()
        try:
            
            #self.state == TOKEN_PRESENT 
        
            #build a list of the the request dict
            req_list = sorted(self.request.items())
            req_len = len(req_list)

            #print("Req len: ", req_len)
            #print("Req List: ", req_list)

            #find the correct index of my ID in the new list
            index = 0
            

            for i in range(0, req_len):
                print("Looking for index... ", i)
                print("Key: ", req_list[i][0])
                print("Owner id: ", self.owner.id)
                if req_list[i][0] == self.owner.id:
                    index = i
                    #print("Index found at ", index)
                    break
                    
            #iterate through the requests
            #starting from the process ID above
            #this peers ID, wrapping around
            #until we reach this peers ID again  
            i = (index + 1) % req_len
            #print("I starting at ", i)
            while i != index:

                print(i)

                pid = req_list[i][0] #the id of the peer currently looked at
                req_t = req_list[i][1] #the time this peer last requested the token
                token_t = self.token[pid] #the latest time this peer had the token
                
                #print("Pid: ", pid)
                #print("Req time: ", req_t)

                #if the peer has requested the
                #token and not yet got it
                if req_t > token_t: 
                    #print("inside shit lol")
                    print(self.peer_list.peer(pid))
                    self.peer_list.peer(pid).obtain_token(self._prepare(self.token))
                    self.state = NO_TOKEN
                    self.token = None
                    return True
                
                i = (i + 1) % req_len
        
        finally:
            self.peer_list.lock.release()

        return False

    def request_token(self, time, pid):
        """Called when some other object requests the token from us."""
        #
        # Your code here.
        #

        print("Token requested by", pid)

        self.peer_list.lock.acquire()
        try:
            self.request[pid] = max(self.request[pid], time)
            self.time = max(time, self.time)

            if self.state == TOKEN_PRESENT:
                print("Im  the one with the token so i will release it")
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
        
        unpacked_token = self._unprepare(token)
        self.token = unpacked_token
        self.token[self.owner.id] = self.time
        self.state = TOKEN_PRESENT
        
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
