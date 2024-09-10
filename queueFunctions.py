import random
from queue import Queue


class Fencer:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.bouts = 0
        self.fenced = set()  # set of names
        self.last = Fencer

    def clear(self):
        # Clears fenced list and re-adds last person fenced to keep repeat from happening
        self.fenced.clear()
        self.fenced.add(self.last)


class StripQueue:
    # Currently pool is a dictionary with keys as number of bouts completed and values as sets of names of fencers
    def __init__(self, strips):
        self.strips = strips
        self.pool = {0: set(), 1: set(), 2: set(), 3: set(), 4: set()}  # dictionary of sets
        self.min_key = 0
        self.num_fencers = 0

    def init_pool(self, fencers):
        # Add each person who voted yes to dictionary in set corresponding to 0 bouts completed
        for fencer in fencers:
            self.pool[0].add(fencer)
            self.num_fencers += 1

    def check_min(self):
        # advances min set counter if set is empty
        if not self.pool[self.min_key]:
            self.min_key += 1

    def add_to_pool(self, fencer):
        # Add new fencer to dictionary in set corresponding to the 1 + the min number of bouts completed
        self.check_min()
        self.pool[self.min_key + 1].add(fencer)

    def rnd_min_fencer(self):
        # Return a random Fencer from the set corresponding to the min number of bouts completed
        self.check_min()
        min_list = list(self.pool[self.min_key])
        return random.choice(min_list)

    def choose_pair(self, left=None, right=None):
        # Returns a pair of Fencers
        # If argument are not given, generate random Fencer(s)
        if left is None:
            left = self.rnd_min_fencer()
        if right is None:
            right = self.rnd_min_fencer()
            while right == left or right.name in left.fenced:
                # if fenced everyone already, clear the fenced list except for the last person fenced
                if left.fenced.len() == self.num_fencers - 1:
                    left.clear()
                right = self.rnd_min_fencer()
        return left, right

    def skip_left(self, pair):
        # Re-calculates pair while keeping the right Fencer
        return self.choose_pair(pair[1])

    def skip_right(self, pair):
        # Re-calculates pair while keeping the left Fencer
        return self.choose_pair(pair[0])

    def push_to_strip(self, pair):
        # Deletes the pair from their respective lists within the dictionary
        self.pool[pair[0].bouts].remove(pair[0])
        self.pool[pair[1].bouts].remove(pair[1])
        # Advances number of bouts completed, adds each other to each fencers fenced set
        pair[0].bouts += 1
        pair[0].last = pair[1]
        pair[1].bouts += 1
        pair[1].last = pair[0]
        # Adds pair to new corresponding lists
        self.pool[pair[0].bouts].add(pair[0])
        self.pool[pair[1].bouts].add(pair[1])
