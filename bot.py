import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# This is the order of people's turns
ROTATION_ORDER = [
    "Zhandos",
    "Azamat",
    "Salamat",
    "Duman",
    "Bekasyl",
    "Meyirman",
    "Ospan"
]

# Path to the data file to store the state
DATA_FILE = "water_bot_data.json"

# Initialize or load the state
def load_state():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    else:
        # Default state - starting with the first person in the rotation
        return {
            "last_person": "Azamat",  # Last person who got water
            "last_updated": None
        }

# Save the current state
def save_state(state):
    with open(DATA_FILE, 'w') as file:
        json.dump(state, file)

# Get the next person in the rotation
def get_next_person(last_person):
    # Find the position of the last person who got water
    try:
        last_person_index = ROTATION_ORDER.index(last_person)
        
        # Get the next person in the rotation
        next_index = (last_person_index + 1) % len(ROTATION_ORDER)
        return ROTATION_ORDER[next_index]
    except ValueError:
        # If person not found, return the first person in rotation
        logging.error(f"Person {last_person} not found in rotation, defaulting to first person")
        return ROTATION_ORDER[0]

# Command handler for /turn
async def turn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    last_person = state["last_person"]
    next_person = get_next_person(last_person)
    
    message = f"🚰 *Су бөтелкелерін алу кезегі* 🚰\n\n"
    message += f"*Соңғы рет барған*: {last_person}\n"
    message += f"*Келесі баратын*: {next_person}\n\n"
    message += "Есіңізде болсын: Әр адам 2 бөтелке әкелуге жауапты!"
    
    # Create buttons for updating with different options
    keyboard = [
        [
            InlineKeyboardButton("Жалғыз бару", callback_data=f"single_{next_person}"),
            InlineKeyboardButton("Досымен бару", callback_data=f"friend_{next_person}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# Callback handler for button presses
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Parse the callback data
    data = query.data.split('_', 1)  # Split only on first underscore
    action_type = data[0]  # "single" or "friend"
    person = data[1]  # The name of the person
    
    # Debug logging
    logging.info(f"Button callback: action_type={action_type}, person={person}")
    
    state = load_state()
    
    if action_type == "single":
        # Update the state with just the one person
        state["last_person"] = person
        state["last_updated"] = str(query.message.date)
        save_state(state)
        
        next_person = get_next_person(person)
        
        message = f"✅ *Су алу кезегі жаңартылды* ✅\n\n"
        message += f"*Осы жолы кезек*: {person} (жалғыз)\n"
        message += f"*Келесі кезек*: {next_person}\n"
        
    elif action_type == "friend":
        # Find the person in the rotation
        try:
            person_index = ROTATION_ORDER.index(person)
            # Get the next person as the friend
            friend_index = (person_index + 1) % len(ROTATION_ORDER)
            friend = ROTATION_ORDER[friend_index]
            
            # Update the state to the friend (since both went)
            state["last_person"] = friend
            state["last_updated"] = str(query.message.date)
            save_state(state)
            
            next_person = get_next_person(friend)
            
            message = f"✅ *Су алу кезегі жаңартылды* ✅\n\n"
            message += f"*Осы жолы кезек*: {person} және {friend} (екеуі бірге)\n"
            message += f"*Келесі кезек*: {next_person}\n"
        except ValueError:
            message = f"❌ *Қате*: {person} кезек тізімінде табылмады"
    else:
        message = "❌ *Қате*: Белгісіз әрекет түрі"
    
    await query.edit_message_text(text=message, parse_mode='Markdown')

# Manual update command for admins
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    last_person = state["last_person"]
    next_person = get_next_person(last_person)
    
    # Create buttons for updating with different options
    keyboard = [
        [
            InlineKeyboardButton("Жалғыз бару", callback_data=f"single_{next_person}"),
            InlineKeyboardButton("Досымен бару", callback_data=f"friend_{next_person}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"🔄 *Кезекті жаңарту* 🔄\n\n"
    message += f"*Қазіргі кезек*: {next_person}\n"
    message += "Келесі адам жалғыз барады ма, әлде досымен бірге ме?"
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🚰 *Су бөтелкелерін алу кезегі ботына қош келдіңіз!* 🚰\n\n"
    message += "Бұл бот су бөтелкелерін алуға кімнің кезегі келгенін қадағалауға көмектеседі.\n\n"
    message += "*Командалар*:\n"
    message += "/turn - Соңғы жауапты адамды және келесі кезекті тексеру\n"
    # message += "/update - Келесі адамдарға кезекті жаңарту\n"
    # message += "/order - Толық кезек тәртібін көру\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# Command handler for /order
async def order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🔄 *Кезек тәртібі* 🔄\n\n"
    for i, name in enumerate(ROTATION_ORDER, 1):
        message += f"{i}. {name}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# Command to debug the current state
async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    message = f"*Debug інформация*:\n"
    message += f"Соңғы адам: {state['last_person']}\n"
    message += f"Келесі адам: {get_next_person(state['last_person'])}\n"
    message += f"Соңғы жаңарту: {state.get('last_updated', 'Жоқ')}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

def main():
    # Get the bot token from environment variable or .env file
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Log the token status (but not the actual token)
    if token:
        logging.info("Токен сәтті жүктелді")
    else:
        logging.error("Токен берілмеген! .env файлын немесе ортаның айнымалыларын тексеріңіз.")
        return
    
    # Create the application
    application = ApplicationBuilder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("turn", turn_command))
    # application.add_handler(CommandHandler("update", update_command))
    # application.add_handler(CommandHandler("order", order_command))
    # application.add_handler(CommandHandler("debug", debug_command))
    
    # Add callback handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logging.info("Бот іске қосылуда...")
    application.run_polling()

if __name__ == "__main__":
    main()