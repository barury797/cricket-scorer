import os
import json
import random

def balls_to_overs(balls):
    overs = balls // 6
    remaining_balls = balls % 6
    return f"{overs}.{remaining_balls}"

def hc_parse_commentary(batters, bowlers, commentary, info):
    innings_data = {'batting': {}, 'bowling': {}}

    if info["type"] == 'oneplayer':
        player_innings = commentary.split('w')  # Split the commentary by 'w' to get individual player scores
        played_batters = range(len(player_innings)) if player_innings[-1] != '' else range(len(player_innings) - 1)

        # Ensure the number of wickets matches the number of innings
        if (len(batters) < len(player_innings)) and 'w' in player_innings[-1]:
            return "Number of wickets is more than number of innings"

        # Assign each player's score
        for i in played_batters:
            runs = sum(int(char) for char in player_innings[i] if char.isdigit())
            if i < (len(batters) - 1) or (i == (len(batters) - 1) and commentary[-1] == 'w'):
                # Include 'w' in length for all but the last player and for the last player if he is out
                balls = len(player_innings[i]) + 1
                out = True
            else:
                balls = len(player_innings[i])
                out = False

            innings_data["batting"][batters[i]] = {'runs': runs, 'balls': balls, 'innings': player_innings[i], 'out': out}

        innings_data["bowling"] = {
            'wickets': commentary.count('w'),
            'runs': sum(int(char) for char in commentary if char.isdigit()),
            'balls': len(commentary)
        }

    elif info["type"] == 'twoplayer':
        empty_batter = {'runs': 0, 'balls': 0, 'innings': '', 'out': False}
        
        # Initialize batters
        striker = batters[0]
        non_striker = batters[1] if len(batters) > 1 else None
        current_bowler = bowlers[0]
        bowler_index = 0

        innings_data['batting'][striker] = empty_batter.copy()
        if non_striker:
            innings_data['batting'][non_striker] = empty_batter.copy()

        # Initialize bowling data
        for bowler in bowlers:
            innings_data['bowling'][bowler] = {'runs': 0, 'balls': 0, 'wickets': 0}

        ball_count = 0
        wicket_count = 0

        for ball in commentary:
            ball_count += 1
            innings_data['batting'][striker]['balls'] += 1
            innings_data['bowling'][current_bowler]['balls'] += 1

            if ball == 'w':
                innings_data['batting'][striker]['out'] = True
                innings_data['bowling'][current_bowler]['wickets'] += 1
                wicket_count += 1

                if len(batters) > 2:
                    batters.pop(0)  # Remove the striker from the batters list
                    if len(batters) > 0:
                        striker = batters[0]
                        innings_data['batting'][striker] = empty_batter.copy()
                else:
                    break  # No more batters left

                if wicket_count == len(batters):
                    striker = None
                    break

                # If only one batter remains
                if wicket_count == len(batters) - 1:
                    non_striker = None  # Only one wicket left, no non-striker

            else:
                runs = int(ball)
                innings_data['batting'][striker]['runs'] += runs
                innings_data['batting'][striker]['innings'] += ball
                innings_data['bowling'][current_bowler]['runs'] += runs

                if runs % 2 != 0 and non_striker is not None:  # Odd runs, change strike
                    striker, non_striker = non_striker, striker

            if ball_count % 6 == 0:  # End of over
                bowler_index = (bowler_index + 1) % len(bowlers)
                current_bowler = bowlers[bowler_index]
                if non_striker is not None:
                    striker, non_striker = non_striker, striker

            # Handle single-player situation when only one wicket left
            if non_striker is None and wicket_count < len(batters) - 1:
                striker = batters[wicket_count]

        # Ensure the last player is marked out if all players are out
        if striker and wicket_count == len(batters) - 1:
            innings_data['batting'][striker]['out'] = True

        innings_data["bowling"]['wickets'] = wicket_count
        innings_data["bowling"]['runs'] = sum(int(char) for char in commentary if char.isdigit())
        innings_data["bowling"]['balls'] = ball_count

    return innings_data

def c_hcmatch(text):
    text = text.replace('-', '').strip()    
    errors = []
    text = text.split()
    team1, t1i, team2, t2i = text[-4:]
    if len(text) == 4: matchname, tournament = '','general'
    elif len(text) == 6: tournament, matchname = text[0:2]
    else: return f'Too many values given (only 4 or 6 are allowed). Given {len(text)}'
    
    # -------------------------------------------- Check For Errors -------------------------------------------- #
    tournament_file = os.path.join('hand-cricket', f'{tournament}.json')           

    if not os.path.exists(tournament_file):
        return f'Tournament {tournament.lower()} has not been created. You may have a spelling mistake. Please type the name of the tournament again.'
        
    with open(tournament_file,'r+') as f:
        tournament_data = json.load(f)

        for data in ['table', 'stats', 'matches']:
            if data not in list(tournament_data.keys()): tournament_data[data] = {}

        info = tournament_data['info']
        table = tournament_data['table']
        stats = tournament_data['stats']
        matches = tournament_data['matches']

        if not info:
            return f'Tournament {tournament.lower()} has not been created. You may have a spelling mistake. Please type the name of the tournament again.'

        for inn in [len(text) - 1, len(text) - 3]:
            commentary = ''.join(char for char in text[inn] if char in '0123456w')
            
            if commentary.count('w') > info['wickets']: # if more wickets fell than limit
                errors.append(f'There are {commentary.count("w")} wickets. The maximum is {info["wickets"]} wickets per match. Please send the first innings again.')
            
            if len(commentary) > info['balls']: # if more balls played than limit
                errors.append(f'There are {len(commentary)} balls. The maximum is {info["balls"]} balls per match. Please send the first innings again.')
        
        if errors: return '\n'.join([f"{i+1}. {errors[i]}" for i in range(len(errors))])

    # ------------------------------------------------ Add Match ------------------------------------------------ #
        t1n = team1.replace('.','').upper()
        t2n = team2.replace('.','').upper()
        t1r = sum(int(char) for char in t1i if char.isdigit())
        t2r = sum(int(char) for char in t2i if char.isdigit())
        t1s = hc_parse_commentary(info['teams'][t1n][1:], info['teams'][t2n][1:], t1i, info)
        t2s = hc_parse_commentary(info['teams'][t2n][1:], info['teams'][t1n][1:], t2i, info)

        match = {t1n: {'innings': t1i,'runs': t1r, **t1s}, t2n: {'innings': t2i,'runs': t2r, **t2s}, 'info': {'toss': t1n if '.' in team1 else t2n}}

        # check if first innings was crossed by more than 6 runs
        if (t1r + 6) < t2r: return 'First innings was crossed by too much. Please send the first innings again.'

        if not matchname: 
            matchname = str(len(matches) + 1)
        matches[matchname] = match

    # -------------------------------------------------- Table -------------------------------------------------- #
        if matchname.isnumeric():
            if t1n not in table: table[t1n] = {'matches':0,'wins':0,'losses':0,'points':0,'runs_scored':0,'overs_faced':0,'runs_conceded':0,'overs_bowled':0}    
            if t2n not in table: table[t2n] = {'matches':0,'wins':0,'losses':0,'points':0,'runs_scored':0,'overs_faced':0,'runs_conceded':0,'overs_bowled':0}

            table[t1n]['matches'] += 1
            table[t1n]['wins'] += 1 if t1r > t2r else 0
            table[t1n]['losses'] += 1 if t1r < t2r else 0
            table[t1n]['points'] += 2 if t1r > t2r else 0
            table[t1n]['runs_scored'] += t1r
            table[t1n]['overs_faced'] += 3
            table[t1n]['runs_conceded'] += t2r
            table[t1n]['overs_bowled'] += len(t2i) / 6 if info['wickets'] > t2i.count('w') else 3
            
            table[t2n]['matches'] += 1
            table[t2n]['wins'] += 1 if t2r > t1r else 0
            table[t2n]['losses'] += 1 if t2r < t1r else 0
            table[t2n]['points'] += 2 if t2r > t1r else 0
            table[t2n]['runs_scored'] += t2r
            table[t2n]['overs_faced'] += len(t2i) / 6 if info['wickets'] > t2i.count('w') else 3
            table[t2n]['runs_conceded'] += t1r
            table[t2n]['overs_bowled'] += 3

        # -------------------------------------------------- Stats -------------------------------------------------- #
        empty_stats = {'matches':0,'0':0,'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'runs':0,'balls':0,'outs':0,'b_runs':0,'b_balls':0,'wickets':0}

        if info["type"] == 'oneplayer':
            if t1n not in stats: stats[t1n] = empty_stats
            for digit in '0123456': stats[t1n][digit] += t1i.count(digit)
            stats[t1n]['matches'] += 1
            stats[t1n]['runs'] += t1r
            stats[t1n]['balls'] += len(t1i)
            stats[t1n]['outs'] += t1i.count('w')
            stats[t1n]['wickets'] += t2i.count('w')
            stats[t1n]['b_runs'] += t2r
            stats[t1n]['b_balls'] += len(t2i)

            if t2n not in stats: stats[t2n] = empty_stats
            for digit in '0123456': stats[t2n][digit] += t2i.count(digit)
            stats[t2n]['matches'] += 1
            stats[t2n]['runs'] += t2r
            stats[t2n]['balls'] += len(t2i)
            stats[t2n]['outs'] += t2i.count('w')
            stats[t2n]['wickets'] += t1i.count('w')
            stats[t2n]['b_runs'] += t1r
            stats[t2n]['b_balls'] += len(t1i)

        elif info["type"] == 'twoplayer':
            for player in t1s['batting']:
                if player not in stats: stats[player] = empty_stats
                for digit in '0123456': stats[player][digit] += t1s["batting"][player]['innings'].count(digit)
                stats[player]['runs'] += t1s['batting'][player]['runs']
                stats[player]['balls'] += t1s['batting'][player]['balls']
                stats[player]['outs'] += t1s['batting'][player]['out']
                stats[player]['wickets'] += t2s['bowling'][player]['wickets']
                stats[player]['b_runs'] += t2s['bowling'][player]['runs']
                stats[player]['b_balls'] += t2s['bowling'][player]['balls']

            for player in t2s['batting']:
                if player not in stats: stats[player] = empty_stats
                for digit in '0123456': stats[player][digit] += t2s["batting"][player]['innings'].count(digit)
                stats[player]['runs'] += t2s['batting'][player]['runs']
                stats[player]['balls'] += t2s['batting'][player]['balls']
                stats[player]['outs'] += t2s['batting'][player]['out']
                stats[player]['wickets'] += t1s['bowling'][player]['wickets']
                stats[player]['b_runs'] += t1s['bowling'][player]['runs']
                stats[player]['b_balls'] += t1s['bowling'][player]['balls']
                    
        f.seek(0)
        json.dump(tournament_data, f, indent=4)
        f.truncate()

    winning_team = t1n if t1r > t2r else t2n
    winning_margin = abs(t1r - t2r) if t1r > t2r else abs(t2i.count('w') - info['wickets'])
    result_type = 'runs' if t1r > t2r else f'wickets ({6 - t2i.count('w')} balls remaining)'

    return f'\n{t1n} scored {t1r} runs. {t2n} scored {t2r} runs.\n{winning_team} won by {winning_margin} {result_type}\n'

def g_hcmatch(tournament, matchname):       
    if not os.path.exists(os.path.join('hand-cricket', f'{tournament}.json')):
        return f'Tournament {tournament.lower()} has not been created. You may have a spelling mistake. Please type the name of the tournament again.'

    with open(os.path.join('hand-cricket', f'{tournament}.json'), 'r') as f:
        tournament_data = json.load(f)
        info = tournament_data['info']
        hc_match = tournament_data['matches'][matchname]

    t1n, t2n = list(hc_match)[0], list(hc_match)[1]

    t1i, t1r, t1bt, t1bs = hc_match[t1n]['innings'], hc_match[t1n]['runs'], hc_match[t1n]['batting'], hc_match[t1n]['bowling']
    t2i, t2r, t2bt, t2bs = hc_match[t2n]['innings'], hc_match[t2n]['runs'], hc_match[t2n]['batting'], hc_match[t2n]['bowling']

    t1w, t2w = t1i.count('w'), t2i.count('w')

    winning_team = t1n if t1r > t2r else t2n
    winning_margin = abs(t1r - t2r) if t1r > t2r else abs(t2w - info['wickets'])
    result_type = 'runs' if t1r > t2r else f'wickets ({6 - t2w} balls remaining)'

    result = f"{winning_team} won by {winning_margin} {result_type}\n"

    t1_scores = "".join([f"{player}: {t1bt[player]['runs']} ({t1bt[player]['balls']}b)\n" for player in t1bt])
    t2_scores = "".join([f"{player}: {t2bt[player]['runs']} ({t2bt[player]['balls']}b)\n" for player in t2bt])

    t1bs = f'{balls_to_overs(t1bs['wickets'])}-{t1bs['runs']}-{t1bs['balls']}'
    t2bs = f'{balls_to_overs(t2bs['wickets'])}-{t2bs['runs']}-{t2bs['balls']}'

    match_info = (f'{tournament.upper()} Match {matchname}\n\n'
                     f'{t1n} {t1r}-{t1w}\n'
                     f'{t1_scores}'
                     f'Bowling: {t1bs}\n\n'
                     f'{t2n} {t2r}-{t2w}\n'
                     f'{t2_scores}'
                     f'Bowling: {t2bs}\n\n'
                     f'{result}')

    return match_info
    
def g_hctable(tournament):
    if not os.path.exists(os.path.join('hand-cricket', f'{tournament}.json')):
        return f'Tournament {tournament.lower()} has not been created. You may have a spelling mistake. Please type the name of the tournament again.'
    
    with open(os.path.join('hand-cricket', f'{tournament}.json'), 'r') as f:
        tournament_data = json.load(f)
        table = tournament_data['table']
    for item in table:
        table[item]['NRR'] = round((table[item]['runs_scored'] / table[item]['overs_faced']) - (table[item]['runs_conceded'] / table[item]['overs_bowled']), 3)

    sorted_table = sorted(table.items(), key=lambda x: (x[1]['points'], x[1]['NRR']), reverse=True)
    table_string = " TM  | M  | W  | L  | PT | NRR\n"

    for team, stats in sorted_table:
        table_string += f"{team:<3} | {stats['matches']:<2} | {stats['wins']:<2} | {stats['losses']:<2} | {stats['points']:<2} | {stats['NRR']:.2f}\n"

    return table_string.strip()

STAT_TYPES = {
    'wickets': ('Wickets', lambda data: data['wickets']),
    'runs': ('Runs', lambda data: data['runs']),
    'batting_average': ('Batting Average', lambda data: round(data['runs'] / data['outs'], 2) if data['outs'] else data['runs']),
    'economy': ('Economy', lambda data: round(data['b_runs'] / (data['b_balls'] / 6), 2) if data['b_balls'] else 0),
    'bowling_average': ('Bowling Average', lambda data: round(data['b_runs'] / data['wickets'], 2) if data['wickets'] else 0),
    'strike_rate': ('Strike Rate', lambda data: round(data['runs'] / data['balls'] * 100, 2) if data['balls'] else 0),
    '4s': ('4s', lambda data: data['4']),
    '6s': ('6s', lambda data: data['6']),
    'bowling_strike_rate': ('Bowling Strike Rate', lambda data: round(data['b_balls'] / data['wickets'], 2) if data['wickets'] else 0),
    'run_rate': ('Run Rate', lambda data: round(data['runs'] / (data['balls'] / 6), 2) if data['balls'] else 0)
}

def g_hcstats(tournament, stat_type):
    path = os.path.join('hand-cricket', f'{tournament}.json')
    if not os.path.exists(path):
        return f"Tournament '{tournament}' not found. Please check the name."

    with open(path, 'r') as f:
        stats = json.load(f)['stats']

    if stat_type not in STAT_TYPES:
        return f"Invalid stat type '{stat_type}'. Choose from {', '.join(STAT_TYPES.keys())}."

    stat_label, stat_func = STAT_TYPES[stat_type]
    header = f"Player | M  | {stat_label}" if stat_type in ['wickets', 'runs'] else f"Player | {stat_label}"
    return header + "\n" + "\n".join(
        f"{player:<6} | {data['matches']:<2} | {stat_func(data):<4}" if stat_type in ['wickets', 'runs'] else 
        f"{player:<6} | {stat_func(data):<4}" for player, data in sorted(stats.items(), key=lambda x: stat_func(x[1]), reverse=True))

def c_hcschedule(teams, lottery=False):
    teams = teams.split(',')
    schedule = []
    for teama in teams:
        for teamb in teams:
            if teams.index(teama) < teams.index(teamb):
                schedule.append(teama + ' vs ' + teamb)

    if lottery:
        random.shuffle(schedule)
    return schedule

if __name__ == '__main__':
    print(g_hcstats('hcpl2', 'batting_average'))

    # for tournament in ['test']:
    #     with open(os.path.join('hand-cricket', f'{tournament}.json'), 'r+') as f:
    #         tournament_data = json.load(f)
    #         tournament_data['stats'] = {}
    #         tournament_data['table'] = {}
    #         tournament_data['matches'] = {}
    #         f.seek(0); json.dump(tournament_data, f, indent=4); f.truncate()
            
    # print(create_hcmatch('test 1 rt. 666666000000 su 124ww'))
    # print(hcmatch('test', '1'))
    # print(hctable('test'))