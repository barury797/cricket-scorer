import re
import math
import json
import random
from requests import get, RequestException
from bs4 import BeautifulSoup

status_selector = r'#main-container > div.ds-relative > div.lg\:ds-container.lg\:ds-mx-auto.lg\:ds-px-5.lg\:ds-pt-4 > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line > div > div:nth-child(1) > div.ds-flex > div > div > div > p > span'
matches_selector = r'.ds-max-w-\[918px\] > div:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div'
hcmatch_data, links = [], ['']

def g_match_status(status):
    if "yet to begin" in status: return 1
    elif "chose" in status: return 2
    elif "need" in status: return 3
    elif "won" in status: return 4
    return 0

def text(soup, selector):
    element = soup.select_one(selector)
    return element.text if element else ""

def g_soup(link):
    response = get(link)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html5lib")
    return soup

def g_data():
    global data, quizzes
    with open(r'./data.json', encoding="utf8") as f: data = json.loads(f.read())
    with open(r'./quiz.json') as f: quizzes = json.loads(f.read())
    return data, quizzes
g_data()

def g_matches():
    try:
        soup = g_soup("https://www.espncricinfo.com/live-cricket-score")
        matches = soup.select(matches_selector)
        mnames = []

        for i, match in enumerate(matches, 1):
            text = (f"{i} - {match.text}"
                .replace("RESULT", "Result, ").replace("LIVE", "Live, ").replace("Series Home", "")
                .replace("Preview", "").replace("Report", "").replace("Photos", "").replace("Videos", "")
                .replace("News", "").replace("Summary", "").replace('AM', 'AM, ').replace('PM', 'PM, '))
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            mnames.append(text)

            link = (soup.select(f"{matches_selector}:nth-child({i}) > div > div.ds-px-4.ds-py-3 > a")[0]['href'])
            links.append(f'https://www.espncricinfo.com{link}'.replace("/match-preview", "/live-cricket-score").replace("/full-scorecard", "/live-cricket-score"))
            
        return [links, '\n\n'.join(mnames)]
    except RequestException as e:
        return [f'Error fetching matches: {e}']

def g_score(link):
    soup = g_soup(link)
    sselect = r'#main-container > div.ds-relative > div.lg\:ds-container.lg\:ds-mx-auto.lg\:ds-px-5.lg\:ds-pt-4 > div > div.ds-flex.ds-space-x-5 > div.ds-grow > '
    mstatus = text(soup, sselect + r'div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line > div > div:nth-child(1) > div.ds-px-4.ds-py-3.ds-border-b.ds-border-line > div > div.ds-grow > div.ds-text-raw-red > strong')
    
    status = text(soup, status_selector)
    match_status = g_match_status(status)

    tinfo = sselect + 'div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line > div > div:nth-child(1) > div.ds-flex > div > div > div > div:nth-child(2) > div > div:nth-child('

    t1n = replace_team_names(text(soup, tinfo + '1) > div.ds-flex.ds-items-center.ds-min-w-0.ds-mr-1 > a'))
    t1s = text(soup, tinfo + '1) > div.ds-text-compact-m')
    t2n = replace_team_names(text(soup, tinfo + '2) > div.ds-flex.ds-items-center.ds-min-w-0.ds-mr-1 > a'))

    winperc = text(soup, sselect + r'div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line > div > div.ds-text-tight-s.ds-font-regular.ds-overflow-x-auto.ds-scrollbar-hide.ds-whitespace-nowrap.ds-mt-1.md\:ds-mt-0.lg\:ds-flex.lg\:ds-items-center.lg\:ds-justify-between.lg\:ds-px-4.lg\:ds-py-2.lg\:ds-bg-fill-content-alternate.ds-text-typo-mid3.md\:ds-text-typo-mid2 > div:nth-child(2) > div').replace(" Probability:", ": ").replace(" Forecast:", " Forecast: ")
    crr = text(soup, sselect + r'div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line > div > div.ds-text-tight-s.ds-font-regular.ds-overflow-x-auto.ds-scrollbar-hide.ds-whitespace-nowrap.ds-mt-1.md\:ds-mt-0.lg\:ds-flex.lg\:ds-items-center.lg\:ds-justify-between.lg\:ds-px-4.lg\:ds-py-2.lg\:ds-bg-fill-content-alternate.ds-text-typo-mid3.md\:ds-text-typo-mid2 > div.ds-flex > div:nth-child(1) > span:nth-child(2)')
    winperc = winperc + "\n" if winperc else ""
    crr = "\n\nCRR: " + crr if crr else ""
    
    if match_status == 3:
        t2s = text(soup, tinfo + '2) > div.ds-text-compact-m')
        rrr = text(soup, sselect + r'div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line > div > div.ds-text-tight-s.ds-font-regular.ds-overflow-x-auto.ds-scrollbar-hide.ds-whitespace-nowrap.ds-mt-1.md\:ds-mt-0.lg\:ds-flex.lg\:ds-items-center.lg\:ds-justify-between.lg\:ds-px-4.lg\:ds-py-2.lg\:ds-bg-fill-content-alternate.ds-text-typo-mid3.md\:ds-text-typo-mid2 > div.ds-flex > div:nth-child(2) > span:nth-child(3)')
        rrr = ", RRR: " + rrr if rrr else ""

    bt1 = sselect + r'div.ds-mt-3 > div.ds-mb-2 > div.ds-w-full.ds-bg-fill-content-prime > div > div:nth-child(2) > div > table > tbody:nth-child(2) > tr:nth-child(1) > '
    bt2 = sselect + r'div.ds-mt-3 > div.ds-mb-2 > div.ds-w-full.ds-bg-fill-content-prime > div > div:nth-child(2) > div > table > tbody:nth-child(2) > tr:nth-child(2) > '
    bwl = sselect + r'div.ds-mt-3 > div.ds-mb-2 > div.ds-w-full.ds-bg-fill-content-prime > div > div:nth-child(2) > div > table > tbody:nth-child(4) > tr:nth-child(1) > td'

    bt1n = text(soup, bt1 + 'td.ds-min-w-max.ds-text-left.ds-flex.ds-items-center').split("(")[0]
    bt1r = text(soup, bt1 + 'td.ds-min-w-max.ds-text-typo')
    bt1b = text(soup, bt1 + 'td:nth-child(3)')
    bt1sr = text(soup, bt1 + 'td:nth-child(6)')

    bt2n = text(soup, bt2 + 'td.ds-min-w-max.ds-text-left.ds-flex.ds-items-center').split("(")[0]
    bt2r = text(soup, bt2 + 'td.ds-min-w-max.ds-text-typo')
    bt2b = text(soup, bt2 + 'td:nth-child(5)')
    bt2sr = text(soup, bt2 + 'td:nth-child(6)')

    bt1b = "(" + bt1b + "b)" if bt1b != "" else ""
    bt2b = "(" + bt2b + "b)" if bt2b != "" else ""

    bwln = text(soup, bwl + '.ds-min-w-max.ds-text-left.ds-flex.ds-items-center').split("(")[0]
    bwlo, bwlr = text(soup, bwl + ':nth-child(2)'), text(soup, bwl + ':nth-child(4)')
    bwlw, bwle = text(soup, bwl + ':nth-child(5)'), text(soup, bwl + ':nth-child(6)')

    bwlo = bwlo + "-" if bwlo != "" else ""
    bwlr = bwlr + "-" if bwlr != "" else ""
    bwlw = bwlw + "-" if bwlw != "" else ""

    status = status if crr != "" else "\n" + status

    if match_status == 3:
        return  (f"{mstatus}\n{t1n} {t1s}\n{t2n} {t2s}{crr}{rrr}\n{winperc}{status}\n\n{bt1n}{bt1r} {bt1b} {bt1sr}\n{bt2n}{bt2r} {bt2b} {bt2sr}\n{bwln}{bwlo}{bwlr}{bwlw}{bwle}")
    else:
        return (f"{mstatus}\n{t1n} {t1s}\n{t2n}{crr}\n{winperc}{status}\n\n{bt1n}{bt1r} {bt1b} {bt1sr}\n{bt2n}{bt2r} {bt2b} {bt2sr}\n{bwln}{bwlo}{bwlr}{bwlw}{bwle}")

def g_match_details(link, type):
    try:
        soup = g_soup(link)
        details = soup.select(r'#main-container > div.ds-relative > div.lg\:ds-container.lg\:ds-mx-auto.lg\:ds-px-5.lg\:ds-pt-4 > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line.ds-mb-4 > div > div:nth-child(2) > div.lg\:ds-w-\[36\%\] > div > table > tbody > tr')

        data = 'Toss was not conducted.' if type == 'Toss' else 'Not found' 

        for item in details:
            if type in item.text:
                if type == 'Umpires':
                    data = f"{item.find_all('div')[0].text}\n{item.find_all('div')[2].text}"
                else:
                    data = item.text.replace(type, '')

        return f'{type.title()}:\n{data}'
    except RequestException as e:
        return f'Error fetching match details: {e}'

def replace_team_names(text):
    return re.sub('|'.join(re.escape(team) for team in data['team_abbreviations']), lambda m: data['team_abbreviations'][m.group(0)], text, flags=re.IGNORECASE)

def g_to_watch(link, batter):
    best_players = ''
    soup = g_soup(link)
    match_status = g_match_status(soup.select(status_selector)[0].text)

    if match_status == 2 or match_status == 3:
        return "Match has already started. Best bowlers / batters can only be got before a match starts"
    elif match_status == 4:
        return "Match has already ended. Best bowlers / batters can only be got before a match starts"
    elif match_status == "Not Started":
        if batter:
            players = soup.select(r'div.ds-bg-fill-content-prime.lg\:ds-w-\[64\%\].lg\:ds-border-r.lg\:ds-border-line > div.lg\:ds-grid.lg\:ds-grid-cols-2 > div.lg\:ds-border-r.ds-border-line.ds-rounded-xl > div:nth-child(2) > div')
        else:
            players = soup.select(r'#main-container > div.ds-relative > div.lg\:ds-container.lg\:ds-mx-auto.lg\:ds-px-5.lg\:ds-pt-4 > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line.ds-mb-4 > div > div:nth-child(2) > div.ds-bg-fill-content-prime.lg\:ds-w-\[64\%\].lg\:ds-border-r.lg\:ds-border-line > div.lg\:ds-grid.lg\:ds-grid-cols-2 > div:nth-child(2) > div:nth-child(2) > div')
        for player in players:
            name = player.find('span', class_='ds-text-tight-m').text
            team = player.find('span', class_='ds-text-tight-s').text
            stats = player.find('span', class_='ds-text-tight-xs').text.replace(' • ', ', ')

            best_players += f'{name} {team}\n{stats}\n\n'

    return best_players

def g_head2head(link):
    best_players = []
    soup = g_soup(link)
    match_status = g_match_status(soup.select(status_selector)[0].text)

    if match_status == 2 or match_status == 3:
        return "Match has already started. Best bowlers / batters can only be got before a match starts"
    elif match_status == 4:
        return "Match has already ended. Best bowlers / batters can only be got before a match starts"
    elif match_status == "Not Started":
        head_to_heads = soup.select('#main-container > div.ds-relative > div.lg\\:ds-container.lg\\:ds-mx-auto.lg\\:ds-px-5.lg\\:ds-pt-4 > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div.ds-w-full.ds-bg-fill-content-prime.ds-overflow-hidden.ds-rounded-xl.ds-border.ds-border-line.ds-mb-4 > div > div:nth-child(2) > div.ds-bg-fill-content-prime.lg\\:ds-w-\\[64\\%\\].lg\\:ds-border-r.lg\\:ds-border-line > div.ds-mb-3 > div:nth-child(2) > a')
        for head_to_head in head_to_heads:
            best_players.append(head_to_head.find('div').g_text(strip=True))

        formatted_results = [f"{(len(best_players) - i) + 1}. {result}" for i, result in enumerate(reversed(best_players), start=1)]
    return 'Head to head\n' + '\n'.join(formatted_results)
    
def g_quiz(type):
    global quiz_dict
    category = type if type != 'random' else random.choice(list(quizzes.keys()))
    subcategory = random.choice(list(quizzes[category].keys()))
    quiz_dict = random.choice(quizzes[category][subcategory])
    return [quiz_dict, f"{subcategory} Quiz:\n• {quiz_dict['q']}\na) {quiz_dict['o'][0]}\nb) {quiz_dict['o'][1]}\nc) {quiz_dict['o'][2]}\nd) {quiz_dict['o'][3]}"]

def check_quiz(sender, choice):
    options = ['a', 'b', 'c', 'd']
    chosen_option_index = quiz_dict['o'].index(choice)
    correct_option_index = quiz_dict['o'].index(quiz_dict['a'])

    chosen_option = f"{options[chosen_option_index]}) {quiz_dict['o'][chosen_option_index]}"
    correct_option = f"{options[correct_option_index]}) {quiz_dict['o'][correct_option_index]}"

    if choice == quiz_dict['a']:
        return f"{sender} gave the correct answer!\nChosen answer: {chosen_option}\nGreat Job!!"
    else:
        return f"{sender} gave the incorrect Answer\nChosen answer: {chosen_option}\nCorrect Answer: {correct_option}"
    
def g_commentary(link, previous_ball):
    commentary_selector = ('#' + link.lower().replace('/', r'\/').replace('.', r'\.') + ' > div').replace(':', r'\:')
    bowler_to_batter = r' > div > div > div:nth-child(1) > div > div > div.xl\:ds-w-\[400px\] > div > div > div.ds-leading-none.ds-mb-0\.5 > span'
    ball_comment1 = r' > div > div > div:nth-child(1) > div.lg\:hover\:ds-bg-ui-fill-translucent.ds-hover-parent.ds-relative > div > div.xl\:ds-w-\[400px\] > div > div > div.first-letter\:ds-capitalize > p'
    ball_comment2 = r' > div > div > div:nth-child(1) > div.lg\:hover\:ds-bg-ui-fill-translucent.ds-hover-parent.ds-relative > div > div.xl\:ds-w-\[400px\] > div > div > div > span'
    ball_no = r' > div > div > div:nth-child(1) > div > div > div.lg\:ds-flex.lg\:ds-items-center.lg\:ds-px-2 > span'
    
    balls = []
    soup = g_soup(link)
    last_ball = float(soup.select(commentary_selector + ':nth-child(10)' + ball_no)[0].text)
    
    if previous_ball < last_ball:
        for i in range(10, 30):
            btb = soup.select(commentary_selector + ':nth-child(' + str(i) + ')' + bowler_to_batter)
            btb = btb[0].text.replace('<!-- -->, ', ',') + '\n' if btb else ''

            bc = soup.select(commentary_selector + ':nth-child(' + str(i) + ')' + ball_comment1)
            if not bc: bc = soup.select(commentary_selector + ':nth-child(' + str(i) + ')' + ball_comment2)
            bc = bc[0].text

            bn = soup.select(commentary_selector + ':nth-child(' + str(i) + ')' + ball_no)
            bn = bn[0].text if bn else ''

            balls.append([float(bn), f'{bn}\n{btb}{bc}'])

            if last_ball >= float(bn):
                break
        print([balls, last_ball])
        return [balls, last_ball]
    else:
        print('CHECKED LIVE')

def give_feedback(text):
    print(text)
    with open('feedbacks.txt', 'a') as f:
        f.write(text[1:].strip() + '\n' if text.startswith('f') else text[8:].strip() + '\n')
    return 'Thank you for your feedback! It has been recorded.'

def calculate(text):
    text = text.replace('×', '*').replace('÷', '/').strip()
    text = re.sub(r'(\d+)%', lambda m: str(int(m.group(1)) / 100), text)
    text = re.sub(r'√(\d+)', lambda m: str(math.sqrt(int(m.group(1)))), text)
    text = text.replace('{', '(').replace('}', ')').replace('[', '(').replace(']', ')')

    def eval_simple_expr(expr):
        expr = re.sub(r'--', '+', expr)
        try:
            return eval(re.sub(r'\^', '**', expr))
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception:
            return "Error: Invalid expression"

    def eval_expr_with_brackets(expr):
        while '(' in expr:
            expr = re.sub(r'\(([^()]+)\)', lambda x: str(eval_simple_expr(x.group(1))), expr)
        return eval_simple_expr(expr)

    if re.search(r'[^\d\s\+\-\*/\^%√().]', text): return "Error: Invalid characters in expression"

    return eval_expr_with_brackets(text)

def g_random(text):
    text = text.split()
    return random.choice(text)