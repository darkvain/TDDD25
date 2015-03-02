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
            if len(self.peer_list.get_peers() == 0):
                self.token = {}
                self.state = TOKEN_PRESENT
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

        if(self.state == TOKEN_PRESENT or self.state == TOKEN_HELD):
            pass


    def register_peer(self, pid):
        """Called when a new peer joins the system."""
        #
        # Your code here.
        #

        self.token[pid] = 0
        self.request[pid] = -1


        #end my code

    def unregister_peer(self, pid):
        """Called when a peer leaves the system."""
        #
        # Your code here.
        #
        pass

    def acquire(self):
        """Called when this object tries to acquire the lock."""
        print("Trying to acquire the lock...")
        #
        # Your code here.
        #

        for peer in self.peer_list.get_peers():
            peer.request_token(self.time, self.owner.id)

        wait_for(self.state == TOKEN_PRESENT)
        self.state = TOKEN_HELD

    def release(self):
        """Called when this object releases the lock."""
        print("Releasing the lock...")
        #
        # Your code here.
        #

        self.state == TOKEN_PRESENT 
        
        #build a list of the the request dict
        req_list = sorted(self.request.items())
        req_len = len(req_list)


        #find the correct index of my ID in the new list
        index = 0
        for( i=0; i<req_len; ++i):
            if req_list[i].key == self.owner.id:
                index = i
        
        #iterate through the requests
        #starting from the process ID above
        #this peers ID, wrapping around
        #until we reach this peers ID again  
        i = (index + 1) % req_len
        while i != self.owner_id:

            pid = req_list[i].key #the id of the peer currently looked at
            req_t = req_list[i].value #the time this peer last requested the token
            token_t = token[pid] #the latest time this peer had the token
            
            #if the peer has requested the
            #token and not yet got it
            if req_t > token_t: 
                self.peer_list.peer().obtain_token(token) 
                self.state = NO_TOKEN
                self.token = None

            i = (index + 1) % req_len

    def request_token(self, time, pid):
        """Called when some other object requests the token from us."""
        #
        # Your code here.
        #


        self.request[pid] = max(self.request[pid], time)
        self.time = max(time, self.time)

        if self.state == TOKEN_PRESENT:
            self.release()

        #end my code

    def obtain_token(self, token):
        """Called when some other object is giving us the token."""
        print("Receiving the token...")
        #
        # Your code here.
        #

        self.token = token
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
