import requests
from app.riot_api import get_latest_version

def get_champion_info(champion_id):
    url = f'https://ddragon.leagueoflegends.com/cdn/{get_latest_version()}/data/ko_KR/champion.json'
    response = requests.get(url)
    if response.status_code == 200:
        champions = response.json().get('data')
        for champion in champions.values():
            if int(champion['key']) == champion_id:
                english_name = champion['id']
                korean_name = champion['name']
                return korean_name, english_name
    return f'알 수 없는 챔피언 ID {champion_id}', None