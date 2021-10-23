from espn_api.basketball import League
league_id = 18927521

league = League(league_id=league_id,year=2022)
player_list = []
for i in range(14):
    player_name = league.teams[0].roster[i].name
    player_list.append(player_name)

print('this is the end')
    