# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 24 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Implementation of a simple database class."""

import random


class Database(object):

    """Class containing a database implementation."""

    def __init__(self, db_file):
        self.db_file = db_file
        self.rand = random.Random()
        self.rand.seed()
        #
        # Your code here.
        #
        f = open(db_file, 'r')
        self.db = f.read().split('%')
        f.close()

        #end my code    

    def read(self):
        """Read a random location in the database."""
        #
        # Your code here.
        #
        nr_entries = len(self.db)
        rand_index = self.rand.randint(0, nr_entries-1)
        return self.db[rand_index]

        #end my code

    def write(self, fortune):
        """Write a new fortune to the database."""
        #
        # Your code here.
        #
        self.db.append(fortune)
        f = open(self.db_file, 'a')
        f.write(fortune + "\n%\n")
        f.close()

        #end my code

