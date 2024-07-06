import os
import json

def balls_to_overs(balls):
    overs = balls // 6
    remaining_balls = balls % 6
    return f"{overs}.{remaining_balls}"

def hc_innscore(players, commentary):
    players_scores = {'batting': {}, 'bowling': {}}

    # Split the commentary by 'w' to get individual player scores
    player_innings = commentary.split('w')

    print(players, player_innings, commentary)

    # Ensure the number of players matches the number of innings
    if (len(players) < len(player_innings)) and 'w' in player_innings[-1]:
        raise ValueError("Number of players is more than number of innings in commentary")

    # Assign each player's score
    for i in range(len(player_innings)):
        score_sum = sum(int(char) for char in player_innings[i] if char.isdigit())
        if i < len(players) - 1:
            # Include 'w' in length for all but the last player
            innings_length = len(player_innings[i]) + 1
            player_out = 1
        elif i == len(players) - 1 and commentary[-1] == 'w':
            # Include 'w' in length for the last player if he is out
            innings_length = len(player_innings[i]) + 1
            player_out = 1
        else:
            innings_length = len(player_innings[i])
            player_out = 0
        
        if i == len(player_innings) - 1 and score_sum == 0:
            continue
        else:
            players_scores["batting"][players[i]] = {'runs': score_sum, 'balls': innings_length, 'innings': player_innings[i], 'out': player_out}

    if hctournament_details["tournament_type"] == 'singleplayer':
        players_scores["bowling"] = {'wickets': commentary.count('w'), 'runs': sum(int(char) for char in commentary if char.isdigit()), 'balls': len(commentary)}

    print(players_scores)
    return players_scores

def create_hcmatch(text):
    global hctournament_details
    errors = []

    text = text.split()
    team1, t1i, team2, t2i = text[-4:]
    if len(text) == 4:
        matchname, tournament = '', 'general'
    elif len(text) == 6:
        matchname, tournament, team1, t1i, team2, t2i = text
    
    #---------------------------------- Check For Errors -----------------------------------#

    details_path = os.path.join(r"D:\cricket-projects\cricket-scorer/hand-cricket", tournament, "details.json")
    if not os.path.exists(details_path):
        return 'Tournament {tournament} has not been created. You may have a spelling mistake. Please type the name of the tournament again.'

    with open(details_path, 'r') as f:
        hctournament_details = json.loads(f.read())

    for inn in [len(text) - 1, len(text) - 3]:
        print(text[inn])
        commentary = ''.join(char for char in text[inn] if char in '0123456w')
        # check if more wickets fell than limit
        if commentary.count('w') > hctournament_details['players_per_match']:
            errors.append(f'There are {commentary.count("w")} wickets. The maximum is {hctournament_details["players_per_match"]} wickets per match. Please send the first innings again.')
        # check if more balls played than limit
        if len(commentary) > hctournament_details['balls_per_match']:
            errors.append(f'There are {len(commentary)} balls. The maximum is {hctournament_details["balls_per_match"]} balls per match. Please send the first innings again.')
    
    if errors:
        return '\n'.join([f"{i+1}. {errors[i]}" for i in range(len(errors))])

   #---------------------------------- Add Match -----------------------------------#
   
    t1n, t2n = team1.replace('.', '').upper(), team2.replace('.', '').upper()
    toss = t1n if '.' in team1 else t2n
    t1r = sum(int(char) for char in t1i if char.isdigit())
    t2r = sum(int(char) for char in t2i if char.isdigit())

    t1s = hc_innscore(hctournament_details['teams'][t1n][1:], t1i)
    t2s = hc_innscore(hctournament_details['teams'][t2n][1:], t2i)

    print(t1s, t2s)

    match = {
        t1n: {'innings': t1i, 'runs': t1r, **t1s},
        t2n: {'innings': t2i, 'runs': t2r, **t2s},
        'details': {'toss': toss}
    }

    # check if first innings was crossed
    if (t1r + 6) < t2r:
        return 'First innings was crossed by too much. Please send the first innings again.'

    tournament_path = os.path.join(r"D:\cricket-projects\Cricket_Bot\Hand_Cricket", tournament)
    matches_path = os.path.join(tournament_path, "matches.json")
    table_path = os.path.join(tournament_path, "table.json")
    stats_path = os.path.join(tournament_path, "stats.json")

    for path in [matches_path, table_path, stats_path]:
        if not os.path.exists(path):
            with open(path, 'w') as newfile:
                json.dump({}, newfile)

    with open(matches_path, 'r+') as f:
        matches = json.load(f)
        if matchname:
            matches[matchname] = match
        else:
            matches[str(len(matches) + 1)] = match
        f.seek(0)
        json.dump(matches, f, indent=4)
        f.truncate()

    if matchname.isnumeric():
        with open(table_path, 'r+') as f:
            table = json.load(f)
            if not table:
                table = {}
            if t1n not in table:
                table[t1n] = {'matches': 0, 'wins': 0, 'losses': 0, 'points': 0, 'runs_scored': 0, 'overs_faced': 0, 'runs_conceded': 0, 'overs_bowled': 0}    
            if t2n not in table:
                table[t2n] = {'matches': 0, 'wins': 0, 'losses': 0, 'points': 0, 'runs_scored': 0, 'overs_faced': 0, 'runs_conceded': 0, 'overs_bowled': 0}

            table[t1n]['matches'] += 1
            table[t1n]['wins'] += 1 if t1r > t2r else 0
            table[t1n]['losses'] += 1 if t1r < t2r else 0
            table[t1n]['points'] += 2 if t1r > t2r else 0
            table[t1n]['runs_scored'] += t1r
            table[t1n]['overs_faced'] += 3
            table[t1n]['runs_conceded'] += t2r
            table[t1n]['overs_bowled'] += len(t2i) / 6 if hctournament_details['players_per_match'] > commentary.count('w') else 3
            
            table[t2n]['matches'] += 1
            table[t2n]['wins'] += 1 if t2r > t1r else 0
            table[t2n]['losses'] += 1 if t2r < t1r else 0
            table[t2n]['points'] += 2 if t2r > t1r else 0
            table[t2n]['runs_scored'] += t2r
            table[t2n]['overs_faced'] += len(t2i) / 6 if hctournament_details['players_per_match'] > commentary.count('w') else 3
            table[t2n]['runs_conceded'] += t1r
            table[t2n]['overs_bowled'] += 3

            f.seek(0)
            json.dump(table, f, indent=4)
            f.truncate()

    with open(stats_path, 'r+') as f:
        stats = json.load(f)

        if not stats:
            stats = {}

        for player in t1s['batting']:
            if player not in stats:
                stats[player] = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, 
                                'batting_runs': 0, 'batting_balls': 0, 'batting_outs': 0,
                                'bowling_runs': 0, 'bowling_balls': 0, 'wickets': 0}

            for digit in '0123456':
                stats[player][digit] += t1s["batting"][player]['innings'].count(digit)

            stats[player]['batting_runs'] += t1s['batting'][player]['runs']
            stats[player]['batting_balls'] += t1s['batting'][player]['balls']
            stats[player]['batting_outs'] += t1s['batting'][player]['out']
            stats[player]['wickets'] += t1s['bowling']['wickets']
            stats[player]['bowling_runs'] += t1s['bowling']['runs']
            stats[player]['bowling_balls'] += t1s['bowling']['balls']
            
        for player in t2s['batting']:
            if player not in stats:
                stats[player] = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, 
                                'batting_runs': 0, 'batting_balls': 0, 'batting_outs': 0,
                                'bowling_runs': 0, 'bowling_balls': 0, 'wickets': 0}

            for digit in '0123456':
                stats[player][digit] += t2s['batting'][player]['innings'].count(digit)

            stats[player]['batting_runs'] += t2s['batting'][player]['runs']
            stats[player]['batting_balls'] += t2s['batting'][player]['balls']
            stats[player]['batting_outs'] += t2s['batting'][player]['out']
            stats[player]['wickets'] += t2s['bowling']['wickets']
            stats[player]['bowling_runs'] += t2s['bowling']['runs']
            stats[player]['bowling_balls'] += t2s['bowling']['balls']

        f.seek(0)
        json.dump(stats, f, indent=4)
        f.truncate()

    return 'Hand Cricket Match Created Successfully'

def get_hcmatch(tournament, matchname):
    details_path = os.path.join(r"D:\cricket-projects\Cricket_Bot\Hand_Cricket", tournament.lower(), "details.json")
    if not os.path.exists(details_path):
        return f'Tournament {tournament.lower()} has not been created. You may have a spelling mistake. Please type the name of the tournament again.'
    
    with open(details_path, 'r') as f:
        tournament_details = json.loads(f.read())

    file_path = os.path.join(r"D:\cricket-projects\Cricket_Bot\Hand_Cricket", tournament, "matches.json")
    with open(file_path, 'r') as f:
        hc_match = json.loads(f.read())[matchname]

    t1n, t2n = list(hc_match)[0], list(hc_match)[1]

    print(t1n, t2n)

    t1i, t1r, t1bt, t1bs = hc_match[t1n]['innings'], hc_match[t1n]['runs'], hc_match[t1n]['batting'], hc_match[t1n]['bowling']
    t2i, t2r, t2bt, t2bs = hc_match[t2n]['innings'], hc_match[t2n]['runs'], hc_match[t2n]['batting'], hc_match[t2n]['bowling']

    t1w, t2w = t1i.count('w'), t2i.count('w')

    winning_team = t1n if t1r > t2r else t2n
    winning_margin = abs(t1r - t2r) if t1r > t2r else abs(t2w - tournament_details['players_per_match'])
    result_type = 'runs' if t1r > t2r else f'wickets ({6 - t2w} balls remaining)'

    result = f"{winning_team} won by {winning_margin} {result_type}\n"

    print(t1bt, t2bt)

    t1_scores = "".join([f"{player}: {t1bt[player]['runs']} ({t1bt[player]['balls']}b)\n" for player in t1bt])
    t2_scores = "".join([f"{player}: {t2bt[player]['runs']} ({t2bt[player]['balls']}b)\n" for player in t2bt])

    t1bs = f'{balls_to_overs(t1bs['wickets'])}-{t1bs['runs']}-{t1bs['balls']}'
    t2bs = f'{balls_to_overs(t2bs['wickets'])}-{t2bs['runs']}-{t2bs['balls']}'

    match_details = (f'{tournament.upper()} Match {matchname}\n\n'
                     f'{t1n} {t1r}/{t1w}\n'
                     f'{t1_scores}'
                     f'Bowling: {t1bs}\n\n'
                     f'{t2n} {t2r}/{t2w}\n'
                     f'{t2_scores}'
                     f'Bowling: {t2bs}\n\n'
                     f'{result}')

    return match_details
    
def get_hctable(tournament):
    file_path = r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\\" + tournament + r"\table.json"  

    with open(file_path, 'r') as f:
        table = json.loads(f.read())

    for item in table:
        table[item]['NRR'] = round((table[item]['runs_scored'] / table[item]['overs_faced']) - (table[item]['runs_conceded'] / table[item]['overs_bowled']), 3)

    sorted_table = sorted(table.items(), key=lambda x: (x[1]['points'], x[1]['NRR']), reverse=True)

    table_string = f"{'T':<3} | {'M':<2} | {'W':<2} | {'L':<2} | {'PT':<2} | {'NRR':<6}\n"

    for team, stats in sorted_table:
        table_string += f"{team:<3} | {stats['matches']:<2} | {stats['wins']:<2} | {stats['losses']:<2} | {stats['points']:<2} | {stats['NRR']:<6.2f}\n"

    return table_string

if __name__ == '__main__':
    for path in [r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\test\matches.json", r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\test\stats.json", r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\test\table.json",
            r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\general\matches.json", r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\general\stats.json", r"D:\cricket-projects\Cricket_Bot\Hand_Cricket\general\table.json"]:
        if os.path.exists(path):
            os.remove(path)

    print(create_hcmatch('2 test rt. 16253446w125342 jg 312653w513265123w'))
    print(create_hcmatch('5 test su. 1234121321265ww jg 1245125135136'))
    print(create_hcmatch('eliminator test rt. 641642624624565566 su ww'))

    print(create_hcmatch('su. 1234121321265ww jg 1245125135136'))


    print(get_hcmatch('test', '5'))
    print(get_hcmatch('test', 'eliminator'))
    print(get_hctable('test'))