import os
import re
import logging
import json
import cv2
import pytesseract
import requests
from PIL import Image
from mnemonic import Mnemonic
from eth_account import Account
from web3 import Web3
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from colorama import init, Fore, Style

init(autoreset=True)

Account.enable_unaudited_hdwallet_features()

ETH_RPC_URL = "https://eth.llamarpc.com"      
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"  
POLYGON_RPC_URL = "https://polygon-rpc.com"      
BITCOIN_BALANCE_API = "https://blockchain.info/q/addressbalance/"
SCREENSHOT_FOLDER = os.path.join(os.getcwd(), "screenshots")

# Log
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#OCR
def extract_seed_phrase(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            logging.error(f"Unable to read image: {image_path}")
            return None
        _, thresh = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(thresh, lang="eng")

        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if len(words) in [12, 24]:
            seed_phrase = " ".join(words)
            logging.info(f"Extracted seed phrase: {seed_phrase}")
            return seed_phrase
        else:
            logging.error(f"Invalid seed phrase extracted from {image_path} ({len(words)} words): {words}")
            return None
    except Exception as e:
        logging.error(f"OCR extraction error for {image_path}: {e}")
        return None

#Validation
def is_valid_seed(seed_phrase):
    try:
        mnemo = Mnemonic("english")
        valid = mnemo.check(seed_phrase)
        if not valid:
            logging.error("Seed phrase is invalid per BIP-39.")
        return valid
    except Exception as e:
        logging.error(f"Error validating seed phrase: {e}")
        return False

def generate_wallet_addresses(seed_phrase):
    try:
        if not is_valid_seed(seed_phrase):
            return None
        seed_bytes = Bip39SeedGenerator(seed_phrase).Generate()
        # Derive eth address using BIP-44
        bip44_eth = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        eth_addr = bip44_eth.PublicKey().ToAddress()
        # Derive bit address using BIP-44
        bip44_btc = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        btc_addr = bip44_btc.PublicKey().ToAddress()
        addresses = {
            "bitcoin": btc_addr,
            "ethereum": eth_addr,
            "binance_smart_chain": eth_addr,
            "polygon": eth_addr,
            "solana": None,
            "cardano": None,
        }
        logging.info(f"Derived wallet addresses: {addresses}")
        return addresses
    except Exception as e:
        logging.error(f"Error generating wallet addresses: {e}")
        return None

def get_bitcoin_balance(address):
    try:
        url = f"{BITCOIN_BALANCE_API}{address}?format=json"
        r = requests.get(url)
        if r.status_code == 200:
            balance = int(r.text) / 1e8  #satoshis to BTC
            logging.info(f"Bitcoin balance for {address}: {balance} BTC")
            return balance
        else:
            logging.error(f"Bitcoin API error: {r.status_code}")
            return 0
    except Exception as e:
        logging.error(f"Error fetching Bitcoin balance: {e}")
        return 0

def get_eth_balance(address, rpc_url):
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        bal = w3.eth.get_balance(address)

        balance = float(Web3.from_wei(bal, 'ether'))
        logging.info(f"Balance for {address} on {rpc_url}: {balance} ETH equivalent")
        return balance
    except Exception as e:
        logging.error(f"Error fetching balance from {rpc_url}: {e}")
        return 0

def get_solana_balance(address):

    return 0

def get_cardano_balance(address):

    return 0

def get_usd_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,binancecoin,matic-network",
            "vs_currencies": "usd"
        }
        r = requests.get(url, params=params)
        data = r.json()
        prices = {
            "bitcoin": data.get("bitcoin", {}).get("usd", 0),
            "ethereum": data.get("ethereum", {}).get("usd", 0),
            "binance_smart_chain": data.get("binancecoin", {}).get("usd", 0),
            "polygon": data.get("matic-network", {}).get("usd", 0)
        }
        logging.info(f"Fetched USD prices: {prices}")
        return prices
    except Exception as e:
        logging.error(f"Error fetching USD prices: {e}")
        return {"bitcoin":0, "ethereum":0, "binance_smart_chain":0, "polygon":0}

def process_screenshots():
    wallet_data = []
    for fname in os.listdir(SCREENSHOT_FOLDER):
        if fname.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(SCREENSHOT_FOLDER, fname)
            logging.info(f"Processing image: {fname}")
            seed = extract_seed_phrase(img_path)
            if not seed:
                continue
            addresses = generate_wallet_addresses(seed)
            if not addresses:
                continue
            balances = {
                "bitcoin": get_bitcoin_balance(addresses["bitcoin"]),
                "ethereum": get_eth_balance(addresses["ethereum"], ETH_RPC_URL),
                "binance_smart_chain": get_eth_balance(addresses["binance_smart_chain"], BSC_RPC_URL),
                "polygon": get_eth_balance(addresses["polygon"], POLYGON_RPC_URL),
                "solana": get_solana_balance(addresses["solana"]) if addresses["solana"] else 0,
                "cardano": get_cardano_balance(addresses["cardano"]) if addresses["cardano"] else 0,
            }
            total = sum(balances.values())
            wallet_data.append({
                "filename": fname,
                "addresses": addresses,
                "balances": balances,
                "total": total
            })

    wallet_data.sort(key=lambda x: x["total"], reverse=True)
    prices = get_usd_prices()
    for wallet in wallet_data:
        usd_value = (
            wallet["balances"]["bitcoin"] * prices["bitcoin"] +
            wallet["balances"]["ethereum"] * prices["ethereum"] +
            wallet["balances"]["binance_smart_chain"] * prices["binance_smart_chain"] +
            wallet["balances"]["polygon"] * prices["polygon"]
        )
        wallet["usd"] = usd_value
    display_wallet_data(wallet_data)

#Display
def display_wallet_data(wallet_data):
    header = f"{Fore.CYAN}{'Screenshot':20s} {'BTC':>10s} {'ETH':>10s} {'BNB':>10s} {'MATIC':>10s} {'Total':>10s} {'USD':>12s}{Style.RESET_ALL}"
    print(header)
    print(Fore.CYAN + "-" * 90 + Style.RESET_ALL)
    for data in wallet_data:
        fname = data["filename"]
        btc = data["balances"]["bitcoin"]
        eth = data["balances"]["ethereum"]
        bsc = data["balances"]["binance_smart_chain"]
        poly = data["balances"]["polygon"]
        total = data["total"]
        usd = data["usd"]
        line = (f"{Fore.YELLOW}{fname:20s}"
                f"{Fore.GREEN}{btc:10.4f}"
                f"{eth:10.4f}"
                f"{bsc:10.4f}"
                f"{poly:10.4f}"
                f"{Fore.MAGENTA}{total:10.4f}"
                f"{Fore.BLUE}{usd:12.2f}{Style.RESET_ALL}")
        print(line)
    print()

if __name__ == "__main__":
    process_screenshots()
