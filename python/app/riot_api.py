import requests
from config import API_KEY

BASE_URL = "https://kr.api.riotgames.com"
ACCOUNT_BASE_URL = 'https://asia.api.riotgames.com/riot/account/v1'
CACHE_VERSION = None 

def get_puuid_by_riot_id(gameName, tagLine):
    url = f'{ACCOUNT_BASE_URL}/accounts/by-riot-id/{gameName}/{tagLine}'
    response = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if response.status_code == 200:
        return response.json()['puuid']
    else:
        print("PUUID 요청 실패:", response.status_code)
        return None


def get_summoner_id_by_puuid(puuid):
    url = f'{BASE_URL}/lol/summoner/v4/summoners/by-puuid/{puuid}'
    response = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if response.status_code == 200:
        return response.json()['id']
    else:
        print("소환사 ID 요청 실패:", response.status_code)
        return None

def get_latest_version():
    global CACHE_VERSION
    if CACHE_VERSION:
        return CACHE_VERSION
    
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url)
    if response.status_code == 200:
        CACHE_VERSION = response.json()[0]
        return CACHE_VERSION
    else:
        return "13.15.1"

def get_riot_id_by_puuid(puuid):
    url = f'{ACCOUNT_BASE_URL}/accounts/by-puuid/{puuid}'
    response = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if response.status_code == 200:
        account_info = response.json()
        return f"{account_info['gameName']}#{account_info['tagLine']}"
    else:
        return None