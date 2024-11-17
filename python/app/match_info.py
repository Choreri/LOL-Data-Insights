
import requests, time
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache
from app.riot_api import get_latest_version,get_riot_id_by_puuid
from app.champions_info import get_champion_info
from config import API_KEY




@lru_cache(maxsize=100)
def get_solo_rank_info(summoner_id):

    url = f"https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    response = requests.get(url, headers={'X-Riot-Token': API_KEY})
    
    if response.status_code == 200:
        rank_data = response.json()
       
        
        for entry in rank_data:
            if entry['queueType'] == "RANKED_SOLO_5x5":
                tier = entry['tier']
                rank = entry['rank']
                lp = entry['leaguePoints']
                wins = entry['wins']
                losses = entry['losses']
                win_rate = round((wins / (wins + losses)) * 100, 1)
                
                tier_lower = tier.lower()
                tier_image_url = f"tier_icons/{tier_lower}.png"
                
                return {
                    'tier': tier,
                    'rank': rank,
                    'lp': lp,
                    'win_rate': win_rate,
                    'wins': wins,
                    'losses': losses,
                    'tier_image_url': tier_image_url
                }
    return None

#####################
# 매치 정보 가져오기 #
#####################
@lru_cache(maxsize=200)
def get_match_details(match_id):
    url = f'https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}'
    response = requests.get(url, headers={'X-Riot-Token': API_KEY})
    if response.status_code == 200:
        match_data = response.json()
        return match_data

    return None
    
@lru_cache(maxsize=50)
def get_recent_ranked_matches(puuid, num_matches=30):
    match_ids_url = f'https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={num_matches}'
    response = requests.get(match_ids_url, headers={'X-Riot-Token': API_KEY})
    
    match_ids = response.json()
    solo_ranked_matches = []

    for i, match_id in enumerate(match_ids):
        if i > 0 and i % 20 == 0:
            time.sleep(2)
        
        match_details = get_match_details(match_id)
        if match_details and match_details['info']['queueId'] == 420:
            solo_ranked_matches.append(match_id)
            
    return solo_ranked_matches

def get_weekly_champion_stats(puuid):
    
    try:
        # 최근 랭크 매치 가져오기
        match_ids = get_recent_ranked_matches(puuid)
        if not match_ids:
            return {}

        # 통계 초기화
        champion_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'kills': 0, 'deaths': 0, 'assists': 0, 'cs': 0})
        one_week_ago = datetime.now() - timedelta(days=7)

        for match_id in match_ids:
            match_details = get_match_details(match_id)
            if not match_details:
                continue

            game_datetime = datetime.fromtimestamp(match_details['info']['gameStartTimestamp'] / 1000)
            if game_datetime < one_week_ago:
                continue

        
            for participant in match_details['info']['participants']:
                if participant['puuid'] == puuid:
                    champion_id = participant['championId']
                    champion_name, _ = get_champion_info(champion_id)

                 
                    champion_stats[champion_name]['games'] += 1
                    if participant['win']:
                        champion_stats[champion_name]['wins'] += 1
                    champion_stats[champion_name]['kills'] += participant['kills']
                    champion_stats[champion_name]['deaths'] += participant['deaths']
                    champion_stats[champion_name]['assists'] += participant['assists']
                    champion_stats[champion_name]['cs'] += participant['totalMinionsKilled'] + participant['neutralMinionsKilled']

        if not champion_stats:
            return {}

        weekly_stats = {}
        for champion, stats in champion_stats.items():
            games = stats['games']
            wins = stats['wins']
            win_rate = round((wins / games) * 100) if games > 0 else 0

            # 평균 KDA 계산
            avg_kills = round(stats['kills'] / games, 1) if games > 0 else 0
            avg_deaths = round(stats['deaths'] / games, 1) if games > 0 else 0
            avg_assists = round(stats['assists'] / games, 1) if games > 0 else 0
            avg_kda = f"{avg_kills} / {avg_deaths} / {avg_assists}"
            kda_ratio = round((avg_kills + avg_assists) / avg_deaths, 2) if avg_deaths > 0 else float('inf')
            
            avg_cs = round(stats['cs'] / games, 1)

            weekly_stats[champion] = {
                'games': games,
                'win_rate': win_rate,
                'avg_kda': avg_kda,
                'avg_cs': avg_cs,
                'kda_ratio': kda_ratio  # 추가된 KDA 비율 값
            }
            
        return weekly_stats

    except Exception as e:
        return {}


def get_spell_name_by_id(spell_id):

    version = get_latest_version()
    spells_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/summoner.json"
    response = requests.get(spells_url)
    if response.status_code == 200:
        spell_data = response.json()['data']
        for spell_key, spell_info in spell_data.items():
            if int(spell_info['key']) == spell_id:
                return spell_key

    return None

def get_rune_icon_by_id(rune_id):
    runes_url = "https://ddragon.leagueoflegends.com/cdn/13.15.1/data/en_US/runesReforged.json"
    response = requests.get(runes_url)
    if response.status_code == 200:
        runes_data = response.json()
        for rune_tree in runes_data:
            if rune_tree['id'] == rune_id:
                return rune_tree['icon']
            for slot in rune_tree['slots']:
                for rune in slot['runes']:
                    if rune['id'] == rune_id:
                        return rune['icon']
 
    return None


def get_match_info(match_id, summoner_id):
    match_details = get_match_details(match_id)
    if not match_details:
        return None

    our_team = []
    enemy_team = []

    stats = None

    for participant in match_details['info']['participants']:

        champion_name, english_name = get_champion_info(participant['championId'])
        champion_image_url = f"https://ddragon.leagueoflegends.com/cdn/{get_latest_version()}/img/champion/{english_name}.png" if english_name else None

        spell1_id = participant['summoner1Id']
        spell2_id = participant['summoner2Id']
        spell1_url = f"https://ddragon.leagueoflegends.com/cdn/{get_latest_version()}/img/spell/{get_spell_name_by_id(spell1_id)}.png"
        spell2_url = f"https://ddragon.leagueoflegends.com/cdn/{get_latest_version()}/img/spell/{get_spell_name_by_id(spell2_id)}.png"

       
        primary_perk_id = participant['perks']['styles'][0]['selections'][0]['perk']
        primary_perk_icon = get_rune_icon_by_id(primary_perk_id)
        rune_primary_url = f"https://ddragon.leagueoflegends.com/cdn/img/{primary_perk_icon}" if primary_perk_icon else None

        
        rune_sub_id = participant['perks']['styles'][1]['style']
        rune_sub_icon = get_rune_icon_by_id(rune_sub_id)
        rune2_url = f"https://ddragon.leagueoflegends.com/cdn/img/{rune_sub_icon}" if rune_sub_icon else None

      
        puuid = participant['puuid']
        riot_id = get_riot_id_by_puuid(puuid)

        player_info = {
            'champion_image_url': champion_image_url,
            'summoner_name': participant['summonerName'],
            'riot_id': riot_id if riot_id else participant['summonerName'],
            'spell1_url': spell1_url,
            'spell2_url': spell2_url,
            'rune_primary_url': rune_primary_url,  
            'rune2_url': rune2_url
        }

        if participant['teamId'] == 100: 
            our_team.append(player_info)
        elif participant['teamId'] == 200: 
            enemy_team.append(player_info)

        if participant['summonerId'] == summoner_id:
            stats = {
                'kills': participant['kills'],
                'deaths': participant['deaths'],
                'assists': participant['assists'],
                'win': participant['win'],
                'total_damage': participant.get('totalDamageDealtToChampions', 0),
                'gold_earned': participant.get('goldEarned', 0),
                'champ_level': participant.get('champLevel', 1),
                'cs': participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0),
                'vision_score': participant.get('visionScore', 0),
                'champion': champion_name,
                'champion_image_url': champion_image_url,
                'inventory': [
                    f"https://ddragon.leagueoflegends.com/cdn/{get_latest_version()}/img/item/{participant.get(f'item{i}')}.png"
                    if participant.get(f'item{i}') else None for i in range(7)
                ],
                'spell1_url': spell1_url,
                'spell2_url': spell2_url,
                'rune_primary_url': rune_primary_url,
                'rune2_url': rune2_url
            }

    if stats is None:
        stats = {}

    stats.update({'our_team': our_team, 'enemy_team': enemy_team})

    return stats
