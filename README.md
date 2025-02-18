# ocr-multichainwallets-screenshot
Multi-Chain Wallet Balance Checker via OCR

script that automates the process of extracting wallet seed phrases from screenshots, deriving wallet addresses, and fetching real-time balances across multiple blockchain networks. This tool is especially useful if you have a collection of seed phrase screenshots and want to quickly verify your crypto assets without manually importing each wallet.

Features
OCR-Based Seed Extraction: Uses OpenCV and pytesseract to extract and clean seed phrases from images.
Wallet Address Derivation: Utilizes BIP-39/BIP-44 standards
Real-Time Balance Checking: usign public RPC endpoints
convert crypto balances into USD value.
Wallets are sorted from highest to lowest total value.
Extensible & Open-Source: The script is designed to be easy to understand and extend, making it a great starting point for further blockchain or OCR-related projects.
How It Works:
script processes all images in a specified “screenshots” folder. Each image is preprocessed for OCR to accurately extract the seed phrase.
Seed Validation
Address Derivation: Wallet addresses are derived using standard derivation paths (e.g., m/44'/60'/0'/0/0 for Ethereum and m/44'/0'/0'/0/0 for Bitcoin).
Balance Retrieval: The script queries public endpoints to fetch current balances for btc, Eth, Binance Smart Chain and Polygon.
USD Valuation: Crypto balances are converted to USD using current prices from CoinGecko.

use:

Clone the repository from GitHub.
Ensure you have your screenshots (with wallet seed phrases) in a folder named “screenshots” in the project directory.
Install the required dependencies:

pip install opencv-python pytesseract pillow mnemonic web3 bip-utils requests colorama

Run the script:

python seed.py
![Screenshot 2025-02-18 at 12 25 55](https://github.com/user-attachments/assets/7ad33412-a74b-46fc-900a-fe093082d6ae)
