import os
import time
import random
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pystyle import Colors, Center


# Proxy list is now global and used for proxy selection
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

selected_list = []


def clear_console():
    """Clears the console screen"""
    os.system("cls")


def print_banner():
    """Print the banner with creator information"""
    print("\n" + Colors.red, Center.XCenter("Made By Eradicationism") + "\n")


def get_twitch_info():
    """Get user input for Twitch channel and viewer count"""
    twitch_name = input("\033[93mEnter Twitch Name\n >  \033[0m")
    viewer_count = int(input("\033[93mEnter Viewer Count\n >  \033[0m"))
    print(" ")
    return twitch_name, viewer_count


def proxy_selector(proxy_servers):
    """Randomly select an unused proxy server"""
    global selected_list
    while True:
        selected_server = random.choice(list(proxy_servers.values()))
        if len(selected_list) == len(proxy_servers):  # Clear the list when all proxies are used
            selected_list.clear()

        if selected_server not in selected_list:  # Ensure proxy isn't used yet
            selected_list.append(selected_server)
            return selected_server


def performance_booster(driver):
    """Optimize the player settings for better performance"""
    driver.find_element(By.XPATH, "//button[@data-a-target='player-settings-button']").click()
    time.sleep(0.3)

    driver.find_element(By.XPATH, "//button[@data-a-target='player-settings-menu-item-advanced']").click()
    options = driver.find_elements(By.XPATH, "//div[@data-a-target='player-settings-menu']")
    time.sleep(0.3)

    for option in options:
        option.find_element(By.XPATH, './/div').click()

    time.sleep(0.3)

    driver.find_element(By.XPATH, "//button[@data-test-selector='main-menu']").click()
    time.sleep(0.3)

    driver.find_element(By.XPATH, "//button[@data-a-target='player-settings-menu-item-quality']").click()
    time.sleep(0.3)

    for option in options:
        option.find_elements(By.XPATH, './/div')[-1].click()


def is_watching(driver):
    """Check if the viewer is still watching the stream"""
    all_windows = driver.window_handles
    for window in all_windows:
        driver.switch_to.window(window)
        time.sleep(2)


def setup_driver():
    """Initialize the WebDriver with Chrome options"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument("--lang=en")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument('--disable-dev-shm-usage')

    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def create_viewer(driver, twitch_name, viewer_count):
    """Create viewers by opening Twitch streams"""
    created_viewer = 0
    for i in range(viewer_count):
        try:
            proxy = proxy_selector(PROXY_SERVERS)

            # Open a new window for each viewer
            if i == 0:
                driver.get(proxy)
            else:
                driver.execute_script(f"window.open('{proxy}')")
            driver.switch_to.window(driver.window_handles[-1])

            enterurl = driver.find_element(By.ID, 'url')
            enterurl.send_keys(f'www.twitch.tv/{twitch_name}')
            enterurl.send_keys(Keys.RETURN)

            # Wait until video is loaded
            videoscreen_xpath = "//div[@data-a-target='player-overlay-click-handler']"
            wait = WebDriverWait(driver, 30)
            video = wait.until(EC.presence_of_element_located((By.XPATH, videoscreen_xpath)))

            # Boost performance settings
            actions = ActionChains(driver)
            actions.move_to_element(video).perform()
            performance_booster(driver)
            time.sleep(15)

            created_viewer += 1
            print(f"\033[92mA viewer created {created_viewer}/{viewer_count}. \033[0m")

        except WebDriverException:
            print("\033[91mAn Error Occurred!\033[0m")


def main():
    """Main execution function"""
    clear_console()
    print_banner()

    # Get user input
    twitch_name, viewer_count = get_twitch_info()

    print("\033[93mViewers creating, please wait..\033[0m")

    # Setup the WebDriver
    driver = setup_driver()

    # Create viewers
    create_viewer(driver, twitch_name, viewer_count)

    print("\033[93mAll viewers created, for exit 'ctrl + c' when done streaming.\033[0m")

    # Keep the driver running and checking for viewing status
    while True:
        time.sleep(30)
        is_watching(driver)


if __name__ == "__main__":
    main()