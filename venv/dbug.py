#%%
import plotly.graph_objs as go
import pandas as pd
import requests
import bs4 as bs
from scipy.stats import ttest_ind
from espn_api.basketball import League
def formatLinks(player_names,year):
    links = []
    special = ['Anthony Davis','Jaren Jackson Jr.']
    

    if type(player_names)==str:
        first_name = player_names.split(" ")[0]
        last_name = player_names.split(" ")[1]
        first_letter = last_name[0].casefold()
        first_five = last_name[0:5].casefold()
        first_two = first_name[0:2].casefold()
        links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'01/gamelog/'+str(year)
        if player_names in special:
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'02/gamelog/'+str(year)
        if player_names == 'Robert Williams III':
            links = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'04/gamelog/'+str(year)

    else:
        for player in player_names:
            first_name = player.split(" ")[0]
            last_name = player.split(" ")[1]
            first_letter = last_name[0].casefold()
            first_five = last_name[0:5].casefold()
            first_two = first_name[0:2].casefold()
            link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'01/gamelog/'+str(year)
            if player in special:
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'02/gamelog/'+str(year)
            if player == 'Robert Williams III':
                link = 'https://www.basketball-reference.com/players/'+str(first_letter)+'/'+str(first_five)+str(first_two)+'04/gamelog/'+str(year)

            links.append(link)
    return(links)


def getPlayerData(link):
    resp = requests.get(link)
    soup = bs.BeautifulSoup(resp.content,'lxml')
    tables = soup.findAll('table')
    html = resp.text
    soup = bs.BeautifulSoup(html, 'lxml')
    links = soup.find_all('img')
    pic = links[1]['src']
    table = tables[-1]
    points = []
    table_headers = []
    for tx in table.findAll('th'):
        table_headers.append(tx.text)
        if len(table_headers)==30:
            break
    table_headers.pop(0)
    player_data = pd.DataFrame(data=None, columns = table_headers)
        
    if table.findParent("table") is None:
        for row in table.findAll('tr')[1:]:
            line = []
            for obs in row.findAll('td'):
                dummy = obs.text
                line.append(dummy)
                if line[-1]=="Did Not Play" or line[-1]=='Inactive' or line[-1]=='Did Not Dress':
                    zeroes = [0]*29
                    zeroes[:len(line)-1] = line[:-1]
                    zeroes[0]=len(player_data)+1
                    [str(i) for i in zeroes]
                    df2 = pd.DataFrame(zeroes).T
                    df2.columns = table_headers
                    player_data = player_data.append(df2)

            if len(line) == len(table_headers):
                df2 = pd.DataFrame(line).T
                df2.columns = table_headers
                player_data = player_data.append(df2)
    player_data = player_data.reset_index()
    player_data = player_data.drop(['index','G'],axis=1)
    player_data = player_data.drop(player_data.columns[3],axis=1)
    return player_data, pic

def getTeams():
    league_id = 18927521

    league = League(league_id=league_id,year=2022)
    teams = []
    for team in league.teams:
        teams.append(team.team_name)

    
    return teams

team_names = getTeams()

def getPlayersFromTeam(team_i):
    league_id = 18927521
    league = League(league_id=league_id,year=2022)
    player_list = []
    for i in range(14):
        player_name = league.teams[team_i].roster[i].name
        player_list.append(player_name)
    return [{'label': i, 'value': i} for i in player_list]

def getFantasyPoints(player_data):
    player_data['FPoints'] = 0
    
    for index, row in player_data.iterrows():
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10) or (int(row['PTS'])>=10 and int(row['AST'])>=10) or (int(row['AST'])>=10 and int(row['TRB'])>=10) or \
        (int(row['PTS'])>=10 and int(row['BLK'])>=10) or (int(row['PTS'])>=10 and int(row['STL'])>=10):
            dd = 1
        else: 
            dd = 0
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10 and int(row['AST'])>=10):
            td=1
        else:
            td=0
        if (int(row['PTS'])>=10 and int(row['TRB'])>=10 and int(row['AST'])>=10) and (int(row['BLK'])>=10 or int(row['STL'])>=10):
            qd = 1
        else: 
            qd=0
        player_data.at[index,'FPoints'] = int(row['FG'])-int(row['FGA'])+int(row['FT'])-int(row['FTA'])+int(row['3P'])+int(row['TRB'])+int(row['AST'])+int(row['STL'])+int(row['BLK']) \
            -int(row['TOV'])+int(row['PTS'])+5*dd+10*td+1000*qd
    return player_data


def getT2(n_clicks,team_i, team_i2):
    team1 = team_i
    team2 = team_i2


    player_names = team1 + team2

    links = formatLinks(player_names, 2022)
    points = []
    for link in links: 
        player_data, pic = getPlayerData(link)
        df = getFantasyPoints(player_data)
        points.append(list(df['FPoints'].values))

    ppp = points[:len(team1)]
    ppp2 = points[len(team1):]
    x = pd.DataFrame(ppp).sum()
    y = pd.DataFrame(ppp2).sum()
    stat, pval = ttest_ind(x, y)
    alpha = 0.10
    if pval < alpha:
        congrats = 'Unfortunately your'
        reject = 'was statistically different.'
        proceed = 'You may still offer the trade but it will not be automatically processed.'
    else:
        congrats = 'Congrats! Your'
        reject = 'was not statistically different.'
        proceed = 'Should your trade be accepted it will be automatically processed.'


    fig = go.Scatter(x=x.index,y=x,name='Points')
    fig2 = go.Scatter(x=x.index,y=x.rolling(5,min_periods=1).mean(),name='Moving Average',line=dict(color='rgba(0,100,80,1)'))
    fig3 = go.Scatter(
        x=list(x.index)+list(x.index)[::-1],
        y=list(x.rolling(5,min_periods=1).mean()+x.std())+list(x.rolling(5,min_periods=1).mean()-x.std()),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0)'),
        hoverinfo="skip",
        showlegend=False)
    line = {'data': [fig,fig2,fig3],
            'layout': {
                'xaxis' :{'title': 'Game'},
                'yaxis' :{'title': 'Fantasy Points'},
                'title' : 'Team 1 Fantasy Points',
                'height':350
            }}
    figure = go.Figure(line)

    fig = go.Scatter(x=y.index,y=y,name='Points')
    fig2 = go.Scatter(x=y.index,y=y.rolling(5,min_periods=1).mean(),name='Moving Average',line=dict(color='rgba(0,100,80,1)'))
    fig3 = go.Scatter(
        x=list(y.index)+list(y.index)[::-1],
        y=list(y.rolling(5,min_periods=1).mean()+y.std())+list(y.rolling(5,min_periods=1).mean()-y.std()),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(0,100,80,0)'),
        hoverinfo="skip",
        showlegend=False)
    line = {'data': [fig,fig2,fig3],
            'layout': {
                'xaxis' :{'title': 'Game'},
                'yaxis' :{'title': 'Fantasy Points'},
                'title' : 'Team 2 Fantasy Points',
                'height':350
            }}
    figure2 = go.Figure(line)


    return '''{} simulated trade of {} for {} {} The pvalue was determined to be {}. {}'''.format(
        congrats,team_i,team_i2,reject,str(round(pval,2)),proceed), figure, figure2



team1 = ['Demar DeRozan', 'Jaren Jackson Jr.']
team2 = ['Robert Williams III','Christian Wood']

text, fig, fig2 = getT2(0,team1,team2)
# %%
