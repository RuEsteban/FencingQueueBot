import os
import json
import random

from telebot import TeleBot
from itertools import combinations

# Set your bot token here
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = TeleBot(BOT_TOKEN)

# Define the path to the JSON files and the public list
DATA_FILE = 'user_data.json'
VALIDATION_CODE = 'your_secret_code_here'  # Replace with your chosen validation code
chat_polls = {}

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

    # Store the poll ID associated with the chat
    chat_polls[message.chat.id] = {
        'poll_id': sent_poll.poll.id,
        'question': poll_question,
        'options': poll_options,
        'yes_voters': []  # Initialize list of users who voted "Yes"
    }


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
        poll_data = chat_polls[message.chat.id]

        # Get the list of first names who voted "Yes"
        first_names = [first_name for first_name, _ in poll_data['yes_voters']]

        # Generate unique pairs
        pairs_queue = generate_and_shuffle_pairs(first_names)

        if pairs_queue is None:
            bot.reply_to(message, "Could not generate a valid queue. Please try again later.")
            return

        # Format the pairs into a string
        queue_string = "Queue:\n"
        for pair in pairs_queue:
            queue_string += f"{pair[0]} vs {pair[1]}\n"

        bot.reply_to(message, queue_string)
    else:
        bot.reply_to(message, "No poll data available for this chat.")


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

        bot.reply_to(message, f"Added names: {', '.join(names_list)}.")
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
            'indicator': 1
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

    bot.send_message(message.from_user.id, stats_message)


@bot.message_handler(commands=['clear'])
def clear_command(message):
    """Initiate the clear data process."""
    bot.send_message(message.from_user.id, "Please send the validation code to proceed with data clearance.")


@bot.message_handler(func=lambda message: message.text == VALIDATION_CODE, content_types=['text'])
def clear_data(message):
    """Clear data after validation code is received."""
    with open(DATA_FILE, 'w') as file:
        json.dump({}, file, indent=4)
    bot.send_message(message.from_user.id, "Data cleared successfully.")


# Ensure necessary files exist at startup
ensure_files_exist()

# Start polling
bot.infinity_polling()
