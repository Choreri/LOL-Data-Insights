
from flask import Flask, render_template, request
from app.riot_api import get_puuid_by_riot_id, get_summoner_id_by_puuid
from app.match_info import (get_match_info,
                            get_recent_ranked_matches,
                            get_solo_rank_info,
                            get_weekly_champion_stats)
import time

# Flask 애플리케이션 초기화
app = Flask(__name__)

@app.route('/')
def index():
   
    return render_template('home.html')

@app.route('/search', methods=['POST'])
def search():
  
    game_name = request.form['game_name']
    tag_line = request.form['tag_line']
 

    # PUUID 가져오기
    puuid = get_puuid_by_riot_id(game_name, tag_line)
    if not puuid:
        return render_template('home.html', message="PUUID를 가져올 수 없습니다.")

    # 소환사 ID 가져오기
    summoner_id = get_summoner_id_by_puuid(puuid)
    if not summoner_id:
        return render_template('home.html', message="소환사 ID를 가져올 수 없습니다.")

    # 솔로 랭크 정보 가져오기
    solo_rank_info = get_solo_rank_info(summoner_id) or {}

    # 최근 랭크 매치 가져오기
    match_ids = get_recent_ranked_matches(puuid) or []

    # 각 매치의 세부 정보를 가져오기
    match_infos = []
    for match_id in match_ids:
        match_info = get_match_info(match_id, summoner_id)
        if match_info:
            match_infos.append(match_info)
        time.sleep(1)  


   # 주간 챔피언 통계 가져오기
    weekly_champion_stats = get_weekly_champion_stats(puuid) or {}

    # 결과 페이지 렌더링
    return render_template('search_results.html',
                        matches=match_infos,
                        solo_rank_info=solo_rank_info,
                        weekly_champion_stats=weekly_champion_stats)

if __name__ == '__main__':
    app.run(debug=True)
