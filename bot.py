import json
import random
from Crypto.PublicKey import ECC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Dizionario per memorizzare i portafogli degli utenti
user_wallets = {}

# Percorso del file per salvare le chiavi di sicurezza
KEYS_FILE = "wallet_keys.json"

# Funzione per generare un indirizzo di portafoglio BTC
def generate_btc_address():
    prefix = "bc1"
    suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=39 - len(prefix)))
    return prefix + suffix

# Funzione per generare un indirizzo di portafoglio BNB
def generate_bnb_address():
    prefix = "bnb"
    suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=38 - len(prefix)))
    return prefix + suffix

# Funzione per generare un indirizzo di portafoglio ETH
def generate_eth_address():
    prefix = "0x"
    suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=40 - len(prefix)))
    return prefix + suffix

# Funzione per generare una chiave privata ECC
def generate_ecc_private_key():
    key = ECC.generate(curve='P-256')
    return key.export_key(format='PEM')

# Funzione per creare un wallet principale e salvare le chiavi di sicurezza
def create_main_wallet():
    btc_address = generate_btc_address()
    bnb_address = generate_bnb_address()
    eth_address = generate_eth_address()

    # Genera una chiave privata ECC per ciascuna criptovaluta
    btc_private_key = generate_ecc_private_key()
    bnb_private_key = generate_ecc_private_key()
    eth_private_key = generate_ecc_private_key()

    keys_data = {
        "BTC": {"address": btc_address, "private_key": btc_private_key},
        "BNB": {"address": bnb_address, "private_key": bnb_private_key},
        "ETH": {"address": eth_address, "private_key": eth_private_key}
    }

    with open(KEYS_FILE, 'w') as f:
        json.dump(keys_data, f)

# Funzione per caricare le chiavi di sicurezza dal file
def load_keys():
    with open(KEYS_FILE) as f:
        return json.load(f)

# Funzione per creare un portafoglio con la configurazione di rete specificata
def create_wallet_with_network(update, context, coin, network):
    user_id = update.effective_user.id
    if user_id not in user_wallets:
        if coin.lower() == 'btc':
            btc_address = load_keys()["BTC"]["address"]
            user_wallets[user_id] = {'BTC': {'address': btc_address, 'network': network}}
        elif coin.lower() == 'bnb':
            bnb_address = load_keys()["BNB"]["address"]
            user_wallets[user_id] = {'BNB': {'address': bnb_address, 'network': network}}
        elif coin.lower() == 'eth':
            eth_address = load_keys()["ETH"]["address"]
            user_wallets[user_id] = {'ETH': {'address': eth_address, 'network': network}}
        update.message.reply_text("Il tuo portafoglio è stato creato con successo!")
    else:
        update.message.reply_text("Hai già un portafoglio creato.")

# Funzione per gestire il comando /deposit
def deposit(update, context):
    user_id = update.effective_user.id
    if user_id not in user_wallets:
        update.message.reply_text("Prima di depositare, devi creare un portafoglio usando /create_wallet.")
        return
    else:
        wallet_info = user_wallets[user_id]
        coin = context.args[0].upper()
        if coin in wallet_info:
            address = wallet_info[coin]['address']
            update.message.reply_text(f"Invia {coin} a questo indirizzo per depositare: {address}")
        else:
            update.message.reply_text("Non hai un portafoglio per questa criptovaluta nel tuo account.")

# Gestisce il comando /start
def start(update, context):
    update.message.reply_text("Benvenuto! Usa /create_wallet per creare un nuovo portafoglio.")

# Gestisce il comando /create_wallet
def create_wallet(update, context):
    update.message.reply_text("Quale criptovaluta vuoi aggiungere al tuo portafoglio? (BTC, BNB, ETH)")

# Gestisce i messaggi contenenti la criptovaluta scelta
def handle_crypto_choice(update, context):
    coin = update.message.text.strip().upper()
    if coin in ['BTC', 'BNB', 'ETH']:
        update.message.reply_text(f"Per quale rete desideri configurare il portafoglio {coin}? (Mainnet, Testnet)",
                                  reply_markup=generate_network_keyboard())
        context.user_data['coin'] = coin
        return 'NETWORK'
    else:
        update.message.reply_text("Criptovaluta non valida. Scegli tra BTC, BNB o ETH.")
        return

# Gestisce la selezione della rete tramite il pulsante di menu
def handle_network_choice(update, context):
    query = update.callback_query
    network = query.data
    coin = context.user_data.get('coin')
    create_wallet_with_network(query.message, context, coin, network)
    query.message.reply_text(f"Portafoglio {coin} creato con successo sulla rete {network}!")

# Genera la tastiera personalizzata per la selezione della rete
def generate_network_keyboard():
    keyboard = [[InlineKeyboardButton("Mainnet", callback_data='Mainnet'),
                 InlineKeyboardButton("Testnet", callback_data='Testnet')]]
    return InlineKeyboardMarkup(keyboard)

# Funzione principale per avviare il bot
def main():
    # Crea il wallet principale all'avvio del bot
    create_main_wallet()

    updater = Updater("TOKEN", use_context=True)  # Inserisci il tuo token di accesso al bot Telegram qui
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_wallet", create_wallet))
    dp.add_handler(MessageHandler(Filters.regex(r'(BTC|BNB|ETH)'), handle_crypto_choice, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(handle_network_choice))
    dp.add_handler(CommandHandler("deposit", deposit, pass_args=True))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
