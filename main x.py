from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from pystyle import Colors, Center
import os, time, random

created_viewer = 0
selected_list = []
PROXY_SERVERS = {
    1: "https://www.blockaway.net",
    2: "https://www.croxyproxy.com",
    3: "https://www.croxyproxy.rocks",
    4: "https://www.croxy.network",
    5: "https://www.croxy.org",
    6: "https://www.youtubeunblocked.live",
    7: "https://www.croxyproxy.net",
    8: "https://us6.myiphide.com/",
    9: "https://unblockvideos.com/",
    10: "https://www.turbohide.org/",
    11: "https://us7.myiphide.com/",
    12: "https://www.secretbrowser.net/",
    13: "https://www.helpmehide.net/",
    14: "https://www.hideweb.org/",
    15: "https://www.proxysneak.com/",
    
}

def iswatching(driver):
    try:
        all_windows = driver.window_handles
        for window in all_windows:
            driver.switch_to.window(window)
            time.sleep(2)
    except WebDriverException as e:
        print(f"\033[91mError in iswatching: {str(e)}\033[0m")

def proxy_selector(proxy_servers):
    while True:
        selected_server = random.choice(list(proxy_servers.values()))
        if len(selected_list) == len(proxy_servers):
            selected_list.clear()
        if selected_server not in selected_list:
            selected_list.append(selected_server)
            return selected_server

def performance_booster(driver):
    try:
        driver.find_element(By.XPATH, "//button[@data-a-target='player-settings-button']").click()
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//button[@data-a-target='player-settings-menu-item-advanced']").click()
        options = driver.find_elements(By.XPATH, "//div[@data-a-target='player-settings-menu']")
        time.sleep(0.3)
        for x in options:
            x.find_element(By.XPATH, './/div').click()
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//button[@data-test-selector='main-menu']").click()
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//button[@data-a-target='player-settings-menu-item-quality']").click()
        time.sleep(0.3)
        for x in options:
            x.find_elements(By.XPATH, './/div')[-1].click()
    except WebDriverException as e:
        print(f"\033[91mError in performance_booster: {str(e)}\033[0m")

def setup_driver(twitch_name, viewer_count):
    global created_viewer
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument("--lang=en")
    chrome_options.add_argument('--headless')  # Comment out for testing
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    isfirst = 0
    for i in range(viewer_count):
        try:
            proxy = proxy_selector(PROXY_SERVERS)
            if isfirst == 0:
                driver.get(proxy)
                isfirst += 1
            else:
                driver.execute_script("window.open('" + proxy + "')")
                time.sleep(1)  # Prevent resource overload
            driver.switch_to.window(driver.window_handles[-1])

            try:
                enterurl = driver.find_element(By.ID, 'url')
                enterurl.send_keys(f'www.twitch.tv/{twitch_name}')
                enterurl.send_keys(Keys.RETURN)
            except:
                print(f"\033[91mURL input not found on {proxy}\033[0m")
                continue

            videoscreen_xpath = "//div[@data-a-target='player-overlay-click-handler']"
            try:
                wait = WebDriverWait(driver, 30)
                video = wait.until(EC.presence_of_element_located((By.XPATH, videoscreen_xpath)))
            except TimeoutException:
                print(f"\033[91mTimeout waiting for video player on {proxy}\033[0m")
                continue

            actions = ActionChains(driver)
            actions.move_to_element(video).perform()
            performance_booster(driver)
            time.sleep(15)

            created_viewer += 1
            print(f"\033[92mA viewer created {created_viewer}/{viewer_count}. \033[0m")
        except WebDriverException as e:
            print(f"\033[91mAn Error Occurred: {str(e)}\033[0m")
            continue
    print("\033[93mAll viewers created, for exit 'ctrl + c' when done streaming.\033[0m")
    while True:
        time.sleep(30)
        iswatching(driver)

def main():
    os.system("cls")
    print("\n" + Colors.red, Center.XCenter("Made By Eradicationism") + "\n")

    twitch_name = input("\033[93mEnter Twitch Name\n >  \033[0m")
    print(" ")
    viewer_count = int(input("\033[93mEnter Viewer Count\n >  \033[0m"))
    print(" ")

    print("\033[93mViewers creating, please wait..\033[0m")
    setup_driver(twitch_name, viewer_count)

if __name__ == "__main__":
    main()