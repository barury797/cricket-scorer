import re
import sys
import platform
import traceback
from threading import Thread, Event
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from helper import g_data, give_feedback, g_quiz, check_quiz, calculate
from helper import g_matches, g_commentary, g_match_details, g_score, g_head2head, g_to_watch, g_random
from handcricket import c_hcmatch, c_hcschedule, g_hcmatch, g_hctable, g_hcstats

EMAIL = "appsrizu@gmail.com"
PASSWORD = "RizuRizu&123123"
message_xpath = "/html/body/div[1]/div/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[3]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div/div"
chatbox_xpath = "/html/body/div[1]/div/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[3]/div/div/div/div/div/div/div/div/div[2]/div/div/div/div[2]/div/div/div[4]/div[2]/div/div[1]/div[1]/p"
chatsend_css =  """div > div > div > div > div.x9f619.x1n2onr6.x1ja2u2z > div > div > div.x78zum5.xdt5ytf.x1t2pt76.x1n2onr6.x1ja2u2z.x10cihs4 > div.x9f619.x1n2onr6.x1ja2u2z.__fb-light-mode > 
                div > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x193iq5w.xeuugli.xs83m0k.xjhlixk.xgyuaek > div > div > div.x1ja2u2z.x9f619.x78zum5.xdt5ytf.x193iq5w.x1l7klhg.x1iyjqo2.xs83m0k.x2lwn1j.x6prxxf.x85a59c.x1n2onr6.xjbqb8w.xuce83p.x1bft6iq.xczebs5
                > div > div > div > div > div > div.x78zum5.xdt5ytf.x1iyjqo2.xs83m0k.x1n2onr6 > div > div > div > div:nth-child(2) > div > span.x4k7w5x.x1h91t0o.x1h9r5lt.xv2umb2.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1qrby5j.x3nfvp2 > div > svg"""
live_broadcast_threads, live_match, links, quiz_dict = [], [], [], {}

c_commands = {
    "feedback": lambda text: give_feedback(text),  # feedback
    "help": lambda text: data["help_message"],  # help
    "matches": lambda text: g_matches()[1],  # matches
    "calc": lambda text: calculate(text),  # calculate
    "random": lambda text: g_random(text),  # random
    "refresh": lambda text: refresh(),  # refresh
}

hc_commands = {
    "table": lambda tournament: g_hctable(tournament),
    "createschedule": lambda teams: c_hcschedule(teams),
    "stats": lambda tournament, type: g_hcstats(tournament, type),
}

m_commands = {
    "best batter": lambda i: g_to_watch(links[i], True),
    "best bowler": lambda i: g_to_watch(links[i], False),
    "head to head": lambda i: g_head2head(links[i]),
    "headtohead": lambda i: g_head2head(links[i]),
    "live": lambda i: start_live_broadcast(i),
    "umpires": lambda i: g_match_details(links[i], "Umpires"),
    "tv umpire": lambda i: g_match_details(links[i], "TV Umpire"),
    "match referee": lambda i: g_match_details(links[i], "Match Referee"),
    "series": lambda i: g_match_details(links[i], "Series"),
    "toss": lambda i: g_match_details(links[i], "Toss"),
}

def refresh():
    global data, quizzes
    data, quizzes = g_data()
    return 'Data refreshed'
refresh()

def send_message(text):
    text = str(text).strip()
    if text:
        chatbox = driver.find_element(By.XPATH, chatbox_xpath)
        chatbox.click()
        for part in text.split("\n"):
            chatbox.send_keys(part)
            ActionChains(driver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.SHIFT).key_up(Keys.ENTER).perform()
        driver.find_element(By.CSS_SELECTOR, chatsend_css).click()

def setup():
    global driver, data, links
    if platform.system() == "Windows": 
        service = Service(executable_path="chromedriver.exe")
    else:
        from selenium.webdriver.chrome.service import Service as ChromiumService
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--log-level=1")
    options.add_argument("−−mute−audio")
    options.add_argument("--window-position=-2400,-2400")
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 60)
    print("0% - Started Chrome")

    driver.get(r"https://www.messenger.com")
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginbutton"]')))
    print("20% - Page Loaded")

    driver.find_element(By.XPATH, '//*[@id="email"]').send_keys(EMAIL)
    driver.find_element(By.XPATH, '//*[@id="pass"]').send_keys(PASSWORD)
    driver.find_element(By.XPATH, '//*[@id="loginbutton"]').click()

    wait.until(EC.text_to_be_present_in_element((By.XPATH,
        "//*/div/div/div/div/div[3]/div/div/div[1]/div/div[2]/div/div/div/div/div/div[1]/div[2]/div/div/div/div[2]/span",
    ), "Enter your PIN to sync your chat history",))
    print("40% - Login successful")

    driver.find_element(By.XPATH, '//*[@id="mw-numeric-code-input-prevent-composer-focus-steal"]').send_keys("000000")
    sleep(10)
    print("60% - PIN number entered")

    driver.get(r"https://www.messenger.com/t/6661317790574700")
    print("80% - Group page loaded")

    sleep(5)
    send_message("Hello Everyone, I have been started.")
    print("100% - Bot Ready")

def monitor_commands():
    while True:
        try:
            messages = driver.find_elements(By.XPATH, message_xpath)
            messages.reverse()
            for message in messages:
                message_lines = message.text.lower().split("\n")
                if "you sent" in message_lines: break
                if not "replied" in message_lines[0] and len(message_lines) > 2:
                    text = message_lines[1]
                    if (text.startswith(".c") or text.startswith(".cs") or text.startswith("@cricket scorer")):
                        send_message(command(message_lines[0],"c",text.replace(".c ", "").replace(".cs ", "").replace("@cricket scorer ", "")))
                        break
                    elif text.startswith(".hc"):
                        send_message(command(message_lines[0], "hc", text.replace(".hc ", "")))
                        break
            sleep(0.5)

        except Exception as e:
            if "stale element not found in the current frame" in str(e):
                print("STALE ERROR")
            else:
                traceback.print_exc()
                send_message(f"Error in monitor_commands: {str(e)}")
                sleep(1)

def live_score(link, stop_event):
    previous_ball = 0
    while not stop_event.is_set():
        try:
            match = next((m for m in live_match if m["link"] == link), None)
            if match and match["active"]:
                balls = g_commentary(link, previous_ball)
                if balls is not None:
                    previous_ball = balls[1]
                    for ball in balls[0]:
                        send_message(ball[1])
                        digit_after_decimal = int(ball[0] * 10) % 10
                        if digit_after_decimal == 6:
                            send_message(g_score(link))
                            break
                if stop_event.is_set():
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
        stop_event = Event()
        live_match.append({"link": links[i], "active": True, "stop_event": stop_event})
        thread = Thread(target=live_score, args=(links[i], stop_event), daemon=True)
        live_broadcast_threads.append(thread)
        thread.start()
        return f"Started Live Broadcast for match {i} every 60 seconds."

def stop_live_broadcast(i):
    if i < len(live_match):
        live_match[i]["active"] = False
        live_match[i]["stop_event"].set()
        return f"Stopped Live Broadcast for match {i}."

def command(sender, type, text):
    global quiz_dict, live_match
    print("Command received:", [sender, type, text])

    if type == "c":
        if text == "":
            return data["help_message"]
        elif text.split()[0] in c_commands:
            return c_commands[text.split()[0]](text.replace(text.split()[0]+" ",""))

        elif text in data["chat_commands"]:
            return data["chat_commands"][text]

        elif text.startswith("q") or text.startswith("quiz"):
            if len(text.split()) <= 1:
                return data["quiz_message"]
            elif not quiz_dict:
                quiz = g_quiz(text.split()[1])
                quiz_dict = quiz[0]
                return quiz[1]

        elif text in "abcd":
            if quiz_dict:
                try: return check_quiz(sender, quiz_dict["o"]["abcd".index(text)])
                finally: quiz_dict = ""
            return "I did not ask any question.\nPlease remember that to prevent cheating, one question can only be answered once. If anyone already answered the question, you will see this message."

        elif text.startswith(f"m") or text.startswith(f"match "):
            for i in range(1, len(links) + 1):
                if text.startswith(f"m{i}") or text.startswith(f"match {i}"):
                    text = text.replace(f"m{i} ", "").replace(f"match {i} ", "")

                    if text == f"m{i}" or text == f"match {i}": return data["match_message"]
                    elif text in m_commands: return m_commands[text](i)
                    elif text == "stop": return stop_live_broadcast(i)
                    else: return g_score(links[i])

    elif type == "hc":
        if text == "": return data["hc_message"]
        match = re.match(r"^(\w+)\s+m(\d+)$", text)

        if len(text.split()) == 2 and text.split()[1] in hc_commands:
            return hc_commands[text.split()[1]](text.split()[0])
        elif len(text.split()) == 3 and text.split()[1] in hc_commands:
            return hc_commands[text.split()[1]](text.split()[0], text.split()[2])

        elif text.startswith("n "):
            if sender == "rizu titans ⚔️":
                return c_hcmatch(text.replace("n ", ""))
            return "Sorry, you are not authorized to do that. Please contact the tournament captain if you think this is an error."

        elif match:
            tournament = match.group(1)
            match_id = int(match.group(2))
            return g_hcmatch(tournament, match_id)
        return 'Invalid format. Please provide the text in the format "tournament mN", where N is the match ID.'
    return "Invalid command. Please send a correct command and try again."

if __name__ == "__main__":
    matches = g_matches()
    links = matches[0]
    setup()
    Thread(target=monitor_commands, daemon=True).start()
    input("Press enter to exit.\n\n")
    send_message("Goodbye Everyone.")
    driver.quit()
    sys.exit()