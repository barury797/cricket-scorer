import re
import threading
import traceback
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from helper import update_data, get_matches, get_commentary, get_match_details, get_score, get_head_to_head, get_to_watch, get_quiz, check_quiz
from handcricket import create_hcmatch, get_hcmatch, get_hctable

EMAIL = 'appsrizu@gmail.com'
PASSWORD = ''

live_broadcast_threads, live_match, quiz_dict = [], [], {}

c_commands = {
    '': lambda: data['help_message'],
    'test': lambda:'Tested, I am active now!',
    'help': lambda: data['help_message'],
    'matches': lambda: get_matches()[1],
    'bye': lambda: 'Goodbye!',
    'update data': lambda: update_data()
}

hc_commands = {
    'table': lambda tournament: get_hctable(tournament),
}

match_commands = {
    'best batter': lambda i: get_to_watch(links[i], True),
    'best bowler': lambda i: get_to_watch(links[i], False),
    'head to head': lambda i: get_head_to_head(links[i]),
    'headtohead': lambda i: get_head_to_head(links[i]),
    'live': lambda i: start_live_broadcast(i),
    'umpires': lambda i: get_match_details(links[i], 'Umpires'),
    'tv umpire': lambda i: get_match_details(links[i], 'TV Umpire'),
    'match referee': lambda i: get_match_details(links[i], 'Match Referee'),
    'series': lambda i: get_match_details(links[i], 'Series'),
    'toss': lambda i: get_match_details(links[i], 'Toss')
}

message_css = 'div > div > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div > div.x78zum5.xdt5ytf.x1t2pt76.x1n2onr6.x1ja2u2z.x10cihs4 > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.x2lah0s.x1nhvcw1.x1qjc9v5.xozqiw3.x1q0g3np.xexx8yu.x1dr59a3.x13dmulc.x1bc3s5a.x1hys8i7.x1mj4gcd.x1gryazu.xkrivgy.xh8yej3.xssz1t8 > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x193iq5w.xeuugli.xs83m0k.xjhlixk.xgyuaek > div > div > div.x1ja2u2z.x9f619.x78zum5.xdt5ytf.x193iq5w.x1l7klhg.x1iyjqo2.xs83m0k.x2lwn1j.x6prxxf.x85a59c.x1n2onr6.xjbqb8w.xuce83p.x1bft6iq.xczebs5 > div > div > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2.xs83m0k.x1n2onr6 > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2 > div > div > div > div > div > div > div'
chatbox_css = 'div > div > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div > div.x78zum5.xdt5ytf.x1t2pt76.x1n2onr6.x1ja2u2z.x10cihs4 > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.x2lah0s.x1nhvcw1.x1qjc9v5.xozqiw3.x1q0g3np.xexx8yu.x1dr59a3.x13dmulc.x1bc3s5a.x1hys8i7.x1mj4gcd.x1gryazu.xkrivgy.xh8yej3.xssz1t8 > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x193iq5w.xeuugli.xs83m0k.xjhlixk.xgyuaek > div > div > div.x1ja2u2z.x9f619.x78zum5.xdt5ytf.x193iq5w.x1l7klhg.x1iyjqo2.xs83m0k.x2lwn1j.x6prxxf.x85a59c.x1n2onr6.xjbqb8w.xuce83p.x1bft6iq.xczebs5 > div > div > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2.xs83m0k.x1n2onr6 > div > div > div > div:nth-child(2) > div > div > div.x78zum5.x1iyjqo2.x6q2ic0 > div.x16sw7j7.x107yiy2.xv8uw2v.x1tfwpuw.x2g32xy.x9f619.xlai7qp.x1iyjqo2.xeuugli > div > div.x78zum5.x1iyjqo2.xq8finb.x16n37ib.x1xmf6yo.x1e56ztr.xeuugli.x1n2onr6 > div.xzsf02u.x1a2a7pz.x1n2onr6.x14wi4xw.x1iyjqo2.x1gh3ibb.xisnujt.xeuugli.x1odjw0f.notranslate > p'
chatsend_css ='div > div > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div > div.x78zum5.xdt5ytf.x1t2pt76.x1n2onr6.x1ja2u2z.x10cihs4 > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.x2lah0s.x1nhvcw1.x1qjc9v5.xozqiw3.x1q0g3np.xexx8yu.x1dr59a3.x13dmulc.x1bc3s5a.x1hys8i7.x1mj4gcd.x1gryazu.xkrivgy.xh8yej3.xssz1t8 > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x193iq5w.xeuugli.xs83m0k.xjhlixk.xgyuaek > div > div > div.x1ja2u2z.x9f619.x78zum5.xdt5ytf.x193iq5w.x1l7klhg.x1iyjqo2.xs83m0k.x2lwn1j.x6prxxf.x85a59c.x1n2onr6.xjbqb8w.xuce83p.x1bft6iq.xczebs5 > div > div > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2.xs83m0k.x1n2onr6 > div > div > div > div:nth-child(2) > div > span.x4k7w5x.x1h91t0o.x1h9r5lt.xv2umb2.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1qrby5j.x3nfvp2 > div'

def send_message(text):
    text = str(text).strip()
    if text:
        chatbox = driver.find_element(By.CSS_SELECTOR, chatbox_css)    
        chatbox.click()
        for part in text.split('\n'):
            chatbox.send_keys(part)
            ActionChains(driver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.SHIFT).key_up(Keys.ENTER).perform()
        driver.find_element(By.CSS_SELECTOR, chatsend_css).click()

def setup():
    global driver, data, quizzes, links

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    print('0% - Started Chrome')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    driver.get(r'https://www.messenger.com')
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginbutton"]')))
    print('20% - Page Loaded')

    driver.find_element(By.XPATH, '//*[@id="email"]').send_keys(EMAIL)
    driver.find_element(By.XPATH, '//*[@id="pass"]').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//*[@id="loginbutton"]').click()

    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'div > div > div > div:nth-child(3) > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div:nth-child(2) > div > div > div > div > div > div.x9f619.x1ja2u2z.x1k90msu.x6o7n8i.x1qfuztq.x10l6tqk.x17qophe.x13vifvy.x1hc1fzr.x71s49j.xh8yej3 > div.html-div.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd > div > div > div > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x2lah0s.x193iq5w.x6s0dn4.x1swvt13.x1pi30zi.xyamay9.x1l90r2v > span'),'Enter your PIN to sync your chat history'))
    print('40% - Login successful')
    
    driver.find_element(By.XPATH, '//*[@id="mw-numeric-code-input-prevent-composer-focus-steal"]').send_keys("000000")
    sleep(10)
    print('60% - PIN number entered')
    
    driver.get(r'https://www.messenger.com/t/6661317790574700')
    print('80% - Group page loaded')
    
    sleep(10)    
    data = update_data()[1]
    quizzes = update_data()[2]

    matches = get_matches()
    links = matches[0]
    send_message(matches[1])

    print('100% - Bot Ready')

def monitor_commands(): 
    while True:
        try:
            messages = driver.find_elements(By.CSS_SELECTOR, message_css)
            messages.reverse()

            for message in messages:
                message_lines = message.text.lower().split("\n")
                if 'you sent' in message_lines:
                    break

                if not 'replied' in message_lines[0] and len(message_lines) > 2:
                    text = message_lines[1]
                    if text.startswith('.c ') or text.startswith('.cs ') or text.startswith('@cricket scorer '): 
                        send_message(command(message_lines[0], 'c', text.replace('.c ', '').replace('.cs ', '').replace('@cricket scorer ', '')))
                        break
                    if text.startswith('.hc'):
                        send_message(command(message_lines[0], 'hc', text.replace('.hc', '')))
                        break
                    print(message_lines)
                    sleep(0.2)
        except Exception as e:
            if not 'stale element not found in the current frame' in str(e):
                traceback.print_exc()
                send_message(f"Error in monitor_commands: {str(e)}")
            else:
                print('STALE ERROR')


def live_score(link):
    previous_ball = 0
    while True:
        try:
            match = next((m for m in live_match if m['link'] == link), None)
            if match and match['active']:
                balls = get_commentary(link, previous_ball)
                if balls is not None:
                    previous_ball = balls[1]
                    for ball in balls[0]:
                        send_message(ball[1])
                        digit_after_decimal = int(ball[0] * 10) % 10
                        if digit_after_decimal == 6:
                            send_message(get_score(link))
                            break
                sleep(20)
            else:
                break
        except Exception as e:
            traceback.print_exc()
            send_message(f"Error in live_score: {str(e)}")
            sleep(20)


def start_live_broadcast(i):
    if i < len(links):
        live_match.append({'link': links[i], 'active': True})
        thread = threading.Thread(target=live_score, args=(links[i],), daemon=True)
        live_broadcast_threads.append(thread)
        thread.start()
        return f'Started Live Broadcast for match {i} every 60 seconds.'

def stop_live_broadcast(i):
    if i < len(live_match):
        live_match[i]['active'] = False
        return f'Stopped Live Broadcast for match {i}.'

def command(sender, type, text):
    global quiz_dict, live_match
    text = text.replace('quiz', 'q').strip()  # Strip leading and trailing whitespace
    print("Command received:", sender, type, text)  # Debugging print statement

    if type in ('c', 'cs'):
        if text in c_commands:
            return c_commands[text]()
        
        if text.startswith('q') or text.startswith('quiz'):
            if len(text.split()) <= 1:
                return data['quiz_message']
            if not quiz_dict:
                quiz = get_quiz(text.split()[1])
                quiz_dict = quiz[0]
                return quiz[1]

        if text.startswith('feedback '):
            feedback_text = text[len('feedback '):].strip()
            with open('feedbacks.txt', 'a') as f:
                f.write(feedback_text + '\n')
            return 'Thank you for your feedback! It has been recorded.'

        if text in 'abcd':
            answer_index = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
            if quiz_dict:
                try:
                    return check_quiz(sender, quiz_dict['o'][answer_index[text]])
                finally:
                    quiz_dict = ''

            return 'I did not ask any question\nPlease remember that to prevent cheating, one question can only be answered once'

        else:
            for i in range(1, len(links) + 1):
                if text.startswith(f'm{i}') or text.startswith(f'match {i}'):
                    text = text.replace(f'm{i} ', '').replace(f'match {i} ', '')
                    if text == f'm{i}' or text == f'match {i}':
                        return data['match_message']
                    if text in match_commands:
                        return match_commands[text](i)
                    if text == 'stop live':
                        return stop_live_broadcast(i)
                    
                    return get_score(links[i])

    elif type == 'hc':
        match = re.match(r'^(\w+)\s+m(\d+)$', text)

        if text.split()[1] in hc_commands:
            text = text.split()
            return hc_commands[text[1]](text[0])

        elif text.startswith('n '):
            if sender == 'rizu titans (cv,gt,ms)':
                return create_hcmatch(text.replace('n', ''))
            else:
                return 'Sorry, you are not authorized to do that. Please contact the tournament captain if you think this is an error.'
                
        elif match:
            tournament = match.group(1)
            match_id = int(match.group(2))
            return get_hcmatch(tournament, match_id)
        
        else:
            return'Invalid format. Please provide the text in the format "tournament mN", where N is the match ID.'

    else:
        return 'Invalid command. Please send a correct command and try again.'

if __name__ == '__main__':
    setup()
    threading.Thread(target=monitor_commands, daemon=True).start()
    input()
