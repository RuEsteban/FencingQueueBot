import os
import json
import random
import dev_functions
import datetime
import re

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

###### TODOS
## add person to pool
## remove person from pool

from telebot import TeleBot
from itertools import combinations
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
# Set your bot token here
# replace os.environ.get('BOT_TOKEN') with 'paste_bot_token_here'
bot = TeleBot('7286594752:AAHTsA-prAuzXxoxrYx1LatDhsgd1IEcTUI')

# Define the path to the JSON files and the public list
DATA_FILE = 'user_data.json'
VALIDATION_CODE = 'your_secret_code_here'  # Replace with your chosen validation code

chat_polls = {}

pairs_queue = {}

participation_table = {}
participation_count = {}

bout_iterator = 0
bout_history = []

num_strips = 0

def generate_and_shuffle_pairs(names):
    def has_consecutive_repeats(pairs):
        # Check if any name appears within two indices in the list of pairs
        for i in range(len(pairs) - 2):
            if (pairs[i][0] in pairs[i + 1] or pairs[i][1] in pairs[i + 1] or
                pairs[i][0] in pairs[i + 2] or pairs[i][1] in pairs[i + 2] or
                pairs[i + 1][0] in pairs[i + 2] or pairs[i + 1][1] in pairs[i + 2]):
                return True
        return False

    # Generate all unique pairs from the list of names
    pairs = list(combinations(names, 2))

    if len(names) < 100:
        # Shuffle a few times if there are fewer than 8 names
        for _ in range(10):  # Shuffle 10 times, you can adjust this number
            random.shuffle(pairs)
    else:
        # Shuffle the list until no name appears consecutively or within two indices
        while True:
            random.shuffle(pairs)
            if not has_consecutive_repeats(pairs):
                break

    return pairs

def ensure_files_exist():
    """Ensure that the necessary JSON files are created if they don't already exist."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as file:
            json.dump({}, file, indent=4)


def load_data():
    """Load user data from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_data(data):
    """Save user data to the JSON file."""
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)


def clear_yes_voters():
    """Clear the list of 'Yes' voters."""
    global yes_voters
    yes_voters = []


@bot.message_handler(commands=['poll'])
def create_new_poll(message):
    # Define the poll question and options
    poll_question = "Practice?"
    poll_options = ["Yes", "No", "Maybe"]

    # Send the poll and store the poll_id
    sent_poll = bot.send_poll(
        chat_id=message.chat.id,
        question=poll_question,
        options=poll_options,
        is_anonymous=False
    )
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    # Store the poll ID associated with the chat
    chat_polls[message.chat.id] = {
        'poll_id': sent_poll.poll.id,
        'question': poll_question,
        'options': poll_options,
        'yes_voters': []  # Initialize list of users who voted "Yes",
    }

#auto generate poll with filled users for testing
@bot.message_handler(commands=['poll_dev'])
def create_new_poll(message):

    global participation_count, participation_table, bout_history, bout_iterator

    # Define the poll question and options
    poll_question = "Practice?"
    poll_options = ["Yes", "No", "Maybe"]

    # Send the poll and store the poll_id
    sent_poll = bot.send_poll(
        chat_id=message.chat.id,
        question=poll_question,
        options=poll_options,
        is_anonymous=False
    )

    # Store the poll ID associated with the chat
    chat_polls[message.chat.id] = {
        'poll_id': sent_poll.poll.id,
        'question': poll_question,
        'options': poll_options,
        'yes_voters': []  # Initialize list of users who voted "Yes",
    }
    poll_data = chat_polls[message.chat.id]

    #reset globals when you make a new poll
        
    participation_table = {}
    participation_count = {}

    bout_iterator = 0
    bout_history = []

    num_strips = 0


    names_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    for name in names_list:
            # Use a placeholder user ID for the fake users
            fake_user_id = 1000 + len(poll_data['yes_voters']) + 1
            poll_data['yes_voters'].append((name, fake_user_id))


#lists all fencers 
@bot.message_handler(commands=['list_all_fencers'])
def list_all_fencers(message):
    fencers = chat_polls[message.chat.id]['yes_voters']
    print(fencers)
    bot.reply_to(message, fencers)



@bot.poll_answer_handler(func=lambda poll_answer: True)
def handle_poll_answer(poll_answer):
    poll_id = poll_answer.poll_id
    selected_option_ids = poll_answer.option_ids  # This is a list of selected option IDs
    user_id = poll_answer.user.id

    # Find the chat that has this poll ID
    for chat_id, poll_data in chat_polls.items():
        if poll_data['poll_id'] == poll_id:
            # Track users who voted "Yes"
            if 0 in selected_option_ids:  # Assuming "Yes" is at index 0
                # Check if user has already voted "Yes"
                if not any(user_id == _user_id for _, _user_id in poll_data['yes_voters']):
                    # Get user info
                    user = bot.get_chat_member(chat_id, user_id)
                    first_name = user.user.first_name
                    poll_data['yes_voters'].append((first_name, user_id))
            break


@bot.message_handler(commands=['queue'])
def create_queue(message):
    # Retrieve the latest poll data for the chat
    if message.chat.id in chat_polls:

        if len(chat_polls[message.chat.id]['yes_voters']) < 2:
                bot.reply_to(message, "Not enough yes voters")

        poll_data = chat_polls[message.chat.id]

        # Get the list of first names who voted "Yes"
        first_names = [first_name for first_name, _ in poll_data['yes_voters']]

        # Generate unique pairs only if the pairs_queue is empty, which occurs when you make a new poll
        if pairs_queue is None:
            pairs_queue = generate_and_shuffle_pairs(first_names)

        #TODO handle no poll data?

        # Format the pairs into a string
        queue_string = queue_format_long(pairs_queue=pairs_queue)

        bot.reply_to(message, queue_string)
    else:
        bot.reply_to(message, "No poll data available for this chat.")

def queue_format_long(pairs_queue):
    queue_string = "Queue:\n"
    for pair in pairs_queue:
        queue_string += f"{pair[0]} vs {pair[1]}\n"
    return queue_string

#return a match up given the participation table (which is global)
def weighted_matchup_generate(participation_table, num_of_strips):
    global participation_count
    global bout_history
    matchup, participation_count = dev_functions.weighted_random_pairing(participation_count=participation_table, bout_history=bout_history, bout_iterator=bout_iterator, rate_limiter=num_of_strips)
    bout_history.insert(len(bout_history),matchup)

    return matchup

#syntax: /weighted_queue [@param]
#@param = number of strips 
#example: when two strips -> /weighted_queue 2
@bot.message_handler(commands=['weighted_queue'])
def create_weighted_queue(message):
    global participation_table
    global num_strips
    # Retrieve the latest poll data for the chat

    strips_arg = message.text.split(maxsplit=1)

    if len(strips_arg) < 2:
        bot.reply_to(message, "Please provide an argument for the number of strips")
        return
    
    num_strips = int(strips_arg[1])
    
    if message.chat.id in chat_polls:
        poll_data = chat_polls[message.chat.id]

        # Get the list of first names who voted "Yes"
        first_names = [first_name for first_name, _ in poll_data['yes_voters']]
        
        #when a new poll is made, the participant table is cleared, so we'll need to make a new one if we see that its empty
        if not participation_table:
            participation_table = dev_functions.create_participation_dict(first_names)

        #generate a match up
        matchup = weighted_matchup_generate(participation_table=participation_table, num_of_strips=num_strips)

        print("\nFinal Matchups:", matchup)
        print("\nParticipation Counts:", participation_count)
        
        on_strip_message = dev_functions.on_strip_message(matchup=matchup, match_number=bout_iterator)

        bot.reply_to(message, on_strip_message, reply_markup=gen_markup())
    else:
        bot.reply_to(message, "No poll data available for this chat.")


#adds buttons for the queue message
def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 5
    markup.add(InlineKeyboardButton("prev", callback_data="cb_prev"),
                InlineKeyboardButton("skip left", callback_data="cb_skip_left"),
                InlineKeyboardButton("skip right", callback_data="cb_skip_right"),
                InlineKeyboardButton("next", callback_data="cb_next"),
                InlineKeyboardButton("force", callback_data="cb_force"))

    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cb_prev":
        global bout_iterator
        if bout_iterator == 0:
            return
        bout_iterator -= 1
        print(bout_history)
        on_strip_message = dev_functions.on_strip_message(matchup=bout_history[bout_iterator], match_number=bout_iterator)

        bot.edit_message_text(on_strip_message, call.message.chat.id, call.message.message_id, reply_markup=gen_markup())

    elif call.data == "cb_next":
        global participation_table
        if bout_iterator == (len(bout_history) - 1):
            weighted_matchup_generate(participation_table=participation_table, num_of_strips=num_strips)
        bout_iterator += 1
        print(bout_history)
        on_strip_message = dev_functions.on_strip_message(matchup=bout_history[bout_iterator], match_number=bout_iterator)
        
        bot.edit_message_text(on_strip_message, call.message.chat.id, call.message.message_id, reply_markup=gen_markup())

@bot.message_handler(commands=['add'])
def add_voters(message):
    # Extract names from the message
    names = message.text.split(maxsplit=1)

    if len(names) < 2:
        bot.reply_to(message, "Please provide a list of names after the /add command.")
        return

    # Strip leading /add and whitespace
    names_list = names[1].strip().split(',')

    # Remove extra spaces around names
    names_list = [name.strip() for name in names_list]

    # Retrieve the latest poll data for the chat
    if message.chat.id in chat_polls:
        poll_data = chat_polls[message.chat.id]

        # Add names to the yes_voters list
        for name in names_list:
            if not any(name == _name for _name, _user_id in poll_data['yes_voters']):
                # Use a placeholder user ID for the fake users
                fake_user_id = 1000 + len(poll_data['yes_voters']) + 1
                poll_data['yes_voters'].append((name, fake_user_id))

        bot.reply_to(message, f"Added names: {', '.join(names_list)}")
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    else:
        bot.reply_to(message, "No poll data available for this chat.")


@bot.message_handler(commands=['win'])
def update_wins(message):
    """Handle the /win command to increment wins for the user."""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name

    data = load_data()

    if user_id in data:
        data[user_id]['wins'] += 1
    else:
        data[user_id] = {
            'name': user_name,
            'wins': 1,
            'losses': 0,
            'indicator': 1,
            'elo': 0,
            'notes': ""
        }

    # Update the indicator
    data[user_id]['indicator'] = data[user_id]['wins'] - data[user_id]['losses']

    save_data(data)

    # Send a confirmation message
    reply_message = bot.reply_to(message, f"Added a win to {user_name}.")

    # Delete the original message and confirmation message
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)


@bot.message_handler(commands=['minuswin'])
def subtract_wins(message):
    """Handle the /subtract_wins command to decrement wins for the user."""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name

    data = load_data()

    if user_id in data:
        if data[user_id]['wins'] > 0:
            data[user_id]['wins'] -= 1
        else:
            bot.reply_to(message, f"{user_name} does not have any wins to subtract.")
            return
    else:
        bot.reply_to(message, f"No record found for {user_name}.")
        return

    # Update the indicator
    data[user_id]['indicator'] = data[user_id]['wins'] - data[user_id]['losses']

    save_data(data)

    # Send a confirmation message
    reply_message = bot.reply_to(message, f"Subtracted a win from {user_name}'s win count.")

    # Delete the original message and confirmation message
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)


@bot.message_handler(commands=['minusloss'])
def minus_losses(message):
    """Handle the /minus_losses command to decrement losses for the user."""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name

    data = load_data()

    if user_id in data:
        if data[user_id]['losses'] > 0:
            data[user_id]['losses'] -= 1
        else:
            bot.reply_to(message, f"{user_name} does not have any losses to subtract.")
            return
    else:
        bot.reply_to(message, f"No record found for {user_name}.")
        return

    # Update the indicator
    data[user_id]['indicator'] = data[user_id]['wins'] - data[user_id]['losses']

    save_data(data)

    # Send a confirmation message
    reply_message = bot.reply_to(message, f"Subtracted a loss from {user_name}'s loss count.")

    # Delete the original message and confirmation message
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)


@bot.message_handler(commands=['loss'])
def add_loss(message):
    """Handle the /loss command to increment losses for the user."""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name

    data = load_data()

    if user_id in data:
        data[user_id]['losses'] += 1
    else:
        data[user_id] = {
            'name': user_name,
            'wins': 0,
            'losses': 1,
            'indicator': -1
        }

    # Update the indicator
    data[user_id]['indicator'] = data[user_id]['wins'] - data[user_id]['losses']

    save_data(data)

    # Send a confirmation message
    reply_message = bot.reply_to(message, f"Added a loss to {user_name}.")

    # Delete the original message and confirmation message
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)


@bot.message_handler(commands=['secret'])
def send_stats(message):
    """Send private stats to the user."""
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id in data:
        user_stats = data[user_id]
        stats_message = (f"Name: {user_stats['name']}\n"
                         f"Wins: {user_stats['wins']}\n"
                         f"Losses: {user_stats['losses']}\n"
                         f"Indicator: {user_stats['indicator']}")
    else:
        stats_message = "No stats found for you."

    try:
        # Attempt to send the message to the user's DM
        bot.send_message(message.from_user.id, stats_message)
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        # If sending fails, notify them in the group chat to start a private chat
        bot.reply_to(message, f"Please start a private conversation with the bot and try again.")


pending_validation_users = {}  # To track users awaiting validation
VALIDATION_CODE = '1234'  # Replace with your chosen validation code


@bot.message_handler(commands=['clear'])
def clear_command(message):
    """Initiate the clear data process."""
    user_id = message.from_user.id
    pending_validation_users[user_id] = True  # Mark the user as waiting for validation
    bot.send_message(user_id, "Please send the validation code to proceed with data clearance.")
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@bot.message_handler(func=lambda message: message.from_user.id in pending_validation_users, content_types=['text'])
def validate_clearance(message):
    """Validate the clearance request with the validation code."""
    if message.text == VALIDATION_CODE:
        user_id = message.from_user.id

        # Clear the data
        with open(DATA_FILE, 'w') as file:
            json.dump({}, file, indent=4)

        bot.send_message(user_id, "Data cleared successfully.")
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        # Remove the user from the pending validation list
        pending_validation_users.pop(user_id, None)
    else:
        bot.send_message(message.from_user.id, "Invalid validation code. Try again.")


from datetime import datetime

@bot.message_handler(commands=['note'])
def add_note_to_profile(message):
    """Handle the /note command to add a note to a user's profile."""
    # Parse the message to extract username and note
    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Usage: /note username note here")
        return

    username = parts[1].strip()
    note = parts[2].strip()

    data = load_data()

    # Find the user profile by username
    user_id = None
    for uid, profile in data.items():
        if profile['name'].lower() == username.lower():
            user_id = uid
            break

    if not user_id:
        bot.reply_to(message, f"No profile found for user '{username}'.")
        return

    # Append the note to the user's profile with the current date
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if 'notes' in data[user_id]:
        data[user_id]['notes'] += f"\n{note} (Date: {date_str})"
    else:
        data[user_id]['notes'] = f"{note} (Date: {date_str})"

    save_data(data)
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@bot.message_handler(commands=['mynotes'])
def send_my_notes(message):
    """Handle the /mynotes command to send the user's notes as a DM."""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name

    data = load_data()

    if user_id in data:
        user_notes = data[user_id].get('notes', 'No notes available.')
        notes_message = f"Notes for {user_name}:\n{user_notes}"
    else:
        notes_message = "No profile found for you. Please create a profile first using /profile."

    try:
        # Send the notes as a direct message to the user
        bot.send_message(user_id, notes_message)
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        # If sending fails, notify them in the group chat to start a private chat
        bot.reply_to(message, "Please start a private conversation with the bot and try again.")


@bot.message_handler(commands=['profile'])
def create_or_update_profile(message):
    """Handle the /profile command to create or update a user's profile."""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name

    data = load_data()

    if user_id not in data:
        # Create a new profile with empty stats and notes
        data[user_id] = {
            'name': user_name,
            'wins': 0,
            'losses': 0,
            'indicator': 0,
            'elo': 0,
            'notes': ""
        }
        save_data(data)
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    else:
        bot.reply_to(message, f"Profile already exists for you, {user_name}.")

# Ensure necessary files exist at startup
ensure_files_exist()

# Start polling
bot.infinity_polling()
