
from flask import Blueprint, render_template, request
import requests
from app.riot_api import get_puuid_by_riot_id, get_summoner_id_by_puuid
from app.match_info import (
    get_recent_ranked_matches,
    get_match_info,
    get_solo_rank_info,
    get_weekly_champion_stats
)


main = Blueprint('main', __name__)

def get_latest_version():
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url)  
    if response.status_code == 200:
        return response.json()[0]  
    return "14.15.1"  

@main.route('/')
def index():
    return render_template('home.html')

@main.route('/search', methods=['POST'])
def search():
    
    game_name = request.form.get('game_name')
    tag_line = request.form.get('tag_line')
    
    if not game_name or not tag_line:
        return render_template('home.html', error_message="게임 이름과 태그 라인을 모두 입력해 주세요.")
    

    puuid = get_puuid_by_riot_id(game_name, tag_line)
    if not puuid:
        return render_template('home.html', error_message="PUUID를 가져올 수 없습니다.")

    summoner_id = get_summoner_id_by_puuid(puuid)
    if not summoner_id:
        return render_template('home.html', error_message="소환사 ID를 가져올 수 없습니다.")

    solo_rank_info = get_solo_rank_info(summoner_id)

    match_ids = get_recent_ranked_matches(puuid)
    if not match_ids:
        return render_template('home.html', error_message="랭크 게임 기록을 가져올 수 없습니다.")

    match_infos = []
    for match_id in match_ids:
        match_info = get_match_info(match_id, summoner_id)
        if match_info:
            match_infos.append(match_info)

    weekly_champion_stats = get_weekly_champion_stats(puuid)

    # 결과 페이지 렌더링
    return render_template(
        'search_results.html',
        matches=match_infos,
        solo_rank_info=solo_rank_info,
        weekly_champion_stats=weekly_champion_stats
    )
