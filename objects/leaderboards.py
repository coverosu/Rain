from helpers import remove_duplicates
from objects.player import Player
from objects.const import Mods
from aiotinydb import AIOTinyDB
import config
import os

"""
rankedstatus|false|beatmapid|setid|howmanyscoresonthemap \n
0 \n
[bold:0,size:20]artist unicode|title unicode \n
7.27 \n
(put personal score here) \n 
(rest of lb goes under) \n
scoreID|username|score|combo|n50s|n100s|n300s|misses|katu(green)|geki(blue)|
perfect|mods(int)|rankofscoreonlb|time(Epoch time)|1 if it has replay 0 if it doesn't
"""

class Leaderboard:
    def __init__(self) -> None:
        self.md5 = ''
        self.mapid: int = None
        self.lb: list = [
            "{rankedstatus}|false|{mapid}|{setid}|{howmanyscoresonthemap}",
            "0",
            "[bold:0,size:20]{artist_unicode}|{title_unicode}",
            "10.0"
        ]
        self.layout: str = ("{scoreID}|{username}|{Score}|"
                            "{combo}|{n50}|{n100}|"
                            "{n300}|{nmiss}|{nkatus}|"
                            "{ngeki}|{perfect}|{mods}|{userid}|"
                            "{rankofscoreonlb}|{time}|{has_replay}")
        self.mods: Mods = None
        self.userids: tuple = None
        self.user: Player = None
        self.country: str = None
    
    async def formatLB(self, Skey, scoring):
        def check(s):
            if Skey(s) and s['userid'] == self.user.userid:
                return True
        md5 = self.md5
        async with AIOTinyDB(config.beatamp_path) as db:
            beatmap = db.get(lambda x: True if x['md5'] == md5 else False)
            if not beatmap:
                return
        async with AIOTinyDB(config.scores_path) as db:
            scores = db.search(Skey)
            if not scores: # no scores found
                return
            userscores = db.get(check)
        
        scores = sorted(remove_duplicates(scores), key = scoring, reverse = True)

        self.lb[0] = self.lb[0].format(
            **beatmap, howmanyscoresonthemap = len(scores)
        )
        if beatmap['title_unicode']:
            title_unicode = beatmap['title_unicode']
        else:
            title_unicode = beatmap['title']
        
        if beatmap['artist_unicode']:
            artist_unicode = beatmap['artist_unicode']
        else:
            artist_unicode = beatmap['artist']
        
        self.lb[2] = self.lb[2].format(
            title_unicode = title_unicode,
            artist_unicode = artist_unicode
        )

        index = 1
        for s in scores:
            s['rankOnLB'] = index
            scores[index - 1] = s
            index += 1
        
        if userscores:
            for x in scores:
                xx = x.copy()
                del xx['rankOnLB']
                if xx == userscores:
                    userscores = x
                    break
            if os.path.exists(f'./data/replays/{userscores["scoreID"]}.osr'):
                has_r = 1
            else:
                has_r = 0
            self.lb.append(
                self.layout.format(
                    **userscores, username = userscores['player_name'],
                    Score = round(userscores['score' if not self.mods & Mods.RELAX and not self.mods & Mods.AUTOPILOT else 'pp']),
                    combo = userscores['max_combo'],
                    rankofscoreonlb = userscores['rankOnLB'],
                    time = userscores['playtime'],
                    has_replay = has_r
                )
            )
        else:
            self.lb.append('')
        
        scores = scores[-50:]
        
        for r, row in enumerate(scores):
            r += 1
            if os.path.exists(f'./data/replays/{row["scoreID"]}.osr'):
                has_r = 1
            else:
                has_r = 0
            self.lb.append(
                self.layout.format(
                    **row, 
                    Score = round(row['score' if not self.mods & Mods.RELAX and not self.mods & Mods.AUTOPILOT else 'pp']), 
                    username = row['player_name'],
                    combo = row['max_combo'],
                    rankofscoreonlb = r,
                    time = row['playtime'],
                    has_replay = has_r
                )
            )

    def __repr__(self) -> str:
        return '\n'.join(self.lb)