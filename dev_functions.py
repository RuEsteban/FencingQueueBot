import os
import json
import random

# event log
# seperate strips queues versus combined strip queues
# Queue UI
# /challenge @Username yourscore, theirscore
# /bout @Username yourscore, theirscore
#   Enter two numbers, your score first, opponent score second, parse input from there, infer winner
#   bot auto updates elo
# scheduled inhouse tourny
# two sep elos, one private, one public for club events
# users have notes on profile to keep track of performance /note @user

from telebot import TeleBot
from itertools import combinations
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import random

 # Dictionary to keep track of how many times each participant has been paired    

def create_participation_dict(participants):
    return {p: 0 for p in participants}

# weighted random pairing WITH CHECKS (you can't go again within x number of bouts, where x is determined by how many strips there are
def weighted_random_pairing(participation_count, bout_history, bout_iterator, rate_limiter):
    def weighted_choice(available_participants):
        """
        Select a participant with weighted randomness based on participation count.
        Participants with fewer participations have a higher probability of being selected.
        """

        total_weight = sum(1 / (1 + participation_count[p]) for p in available_participants)
        rand_val = random.uniform(0, total_weight)
        current_weight = 0
        for p in available_participants:
            weight = 1 / (1 + participation_count[p])
            current_weight += weight
            if current_weight >= rand_val:
                return p

    #THiS DATA TYPE IS A LIST OF PAIRS!!!! THIS IS NOT JUST A TUPLE, BUT A LIST OF TUPLES!!!
    matchup = []

    participants = list(participation_count.keys())
    available_participants = participants.copy()

    p1 = 'def1'
    p2 = 'def2'

    # Select two participants using weighted random choice

    same_bout_marker = False

    #TODO: WE DON"T WANT TO FENCE THE SAME PEOPLE AGAIN UNTIL WE'VE FENCED EVERYONE AT LEAST ONCE
    while(same_bout_marker):
        # SELECT FENCER 1

        #only do this for the first bout
        if len(bout_history) == 0:
            p1 = weighted_choice(available_participants)
            available_participants.remove(p1)
        else:
            while(True):
                #find a potential participant
                temp = weighted_choice(available_participants)
                p1_marker = True

                #iterate through the past x number of bouts to see if they've participated
                for i in range(len(bout_history), len(bout_history) - min(rate_limiter, len(bout_history)), -1):
                    #if they have participated, then flag
                    if check_if_participate(temp,bout_history[i-1]):
                        p1_marker = False
                #if unchanged flag, then we know that this person doesn't show up in the past x bouts
                if p1_marker:
                    break
            p1 = temp
            available_participants.remove(p1)

        # SELECT FENCER 2
        if len(bout_history) == 0:
            p2 = weighted_choice(available_participants)
            available_participants.remove(p2)
        else:
            while(True):
                temp = weighted_choice(available_participants)
                p2_marker = True
                for i in range(len(bout_history), len(bout_history) - min(rate_limiter, len(bout_history)), -1):
                    if check_if_participate(temp,bout_history[i-1]):
                        p2_marker = False
                if p2_marker:
                    break
            p2 = temp
            available_participants.remove(p2)
                
    # Pair them up
    matchup.append((p1, p2))

    # Increment participation count
    participation_count[p1] += 1
    participation_count[p2] += 1

    print("Pair:", matchup)

    return matchup, participation_count

def check_if_participate(participant, matchup):
    if matchup[0][0] == participant or matchup[0][1] == participant:
        return True
    else:
        return False
    
#create on_strip message
def on_strip_message(matchup, match_number):
    message = f"On strip for bout # {match_number}:\n"
    message += f"{matchup[0][0]} vs {matchup[0][1]}"
    return message