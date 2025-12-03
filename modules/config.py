import os
from dotenv import load_dotenv

load_dotenv()

TINY_API_TOKEN = os.getenv('TINY_API_TOKEN','')
SHOPEE_PARTNER_ID = os.getenv('SHOPEE_PARTNER_ID','')
SHOPEE_PARTNER_KEY = os.getenv('SHOPEE_PARTNER_KEY','')
SHOPEE_SHOP_ID = os.getenv('SHOPEE_SHOP_ID','')
SHOPEE_ACCESS_TOKEN = os.getenv('SHOPEE_ACCESS_TOKEN','')
SHOPEE_REFRESH_TOKEN = os.getenv('SHOPEE_REFRESH_TOKEN','')
SHOPEE_REDIRECT_URL = os.getenv('SHOPEE_REDIRECT_URL','http://localhost:8000/callback')
DATABASE_URL = os.getenv('DATABASE_URL','sqlite:///hub_financeiro.db')

def get_env():
	"""Retorna todas as variáveis de ambiente relevantes como dict."""
	return {
		"TINY_API_TOKEN": TINY_API_TOKEN,
		"SHOPEE_PARTNER_ID": SHOPEE_PARTNER_ID,
		"SHOPEE_PARTNER_KEY": SHOPEE_PARTNER_KEY,
		"SHOPEE_SHOP_ID": SHOPEE_SHOP_ID,
		"SHOPEE_ACCESS_TOKEN": SHOPEE_ACCESS_TOKEN,
		"SHOPEE_REFRESH_TOKEN": SHOPEE_REFRESH_TOKEN,
		"SHOPEE_REDIRECT_URL": SHOPEE_REDIRECT_URL,
		"DATABASE_URL": DATABASE_URL,
	}
