import os
import time
import random
import requests
import logging
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pystyle import Colors, Center

# Free, open proxy websites for 2025
PROXY_SERVERS = {
    1: "https://www.blockaway.net",
    2: "https://www.croxyproxy.com",
    3: "https://www.croxyproxy.rocks",
    4: "https://www.croxy.network",
    5: "https://www.croxy.org",
    6: "https://www.youtubeunblocked.live",
    7: "https://www.croxyproxy.net",
    8: "https://myiphide.com/proxy-site.html",
    9: "https://unblockvideos.com/",
    10: "https://www.turbohide.org/",
    11: "https://www.proxysite.com/"
}

selected_proxies = []
valid_proxies = []
MAX_WINDOWS = 10  # Limit concurrent browser windows

# Setup logging
logging.basicConfig(
    filename='twitch_viewer.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clear_console():
    """Clears the console screen"""
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    """Print the banner with creator information"""
    print("\n" + Colors.red + Center.XCenter("Twitch Viewer Script - Free Proxies 2025") + "\n")
    logging.info("Script started")

def check_twitch_channel_status(twitch_name):
    """Check if the Twitch channel is live"""
    try:
        response = requests.get(f"https://www.twitch.tv/{twitch_name}", timeout=10)
        if response.status_code == 200 and "isLiveBroadcast" in response.text:
            print(f"\033[92m{twitch_name} is live!\033[0m")
            logging.info(f"Channel {twitch_name} is live")
            return True
        else:
            print(f"\033[91m{twitch_name} is offline or not found.\033[0m")
            logging.warning(f"Channel {twitch_name} is offline or not found")
            return False
    except requests.RequestException as e:
        print(f"\033[91mError checking channel status: {e}\033[0m")
        logging.error(f"Error checking channel {twitch_name} status: {e}")
        return False

def get_twitch_info():
    """Get user input for Twitch channel, viewer count, and optional login credentials"""
    twitch_name = input("\033[93mEnter Twitch Name (e.g., soothingspaceasmr)\n > \033[0m").strip()
    viewer_count = int(input("\033[93mEnter Viewer Count\n > \033[0m"))
    use_login = input("\033[93mUse Twitch login? (y/n)\n > \033[0m").strip().lower() == 'y'
    username = password = None
    if use_login:
        username = input("\033[93mEnter Twitch Username\n > \033[0m").strip()
        password = input("\033[93mEnter Twitch Password\n > \033[0m").strip()
    print(" ")
    logging.info(f"User input: channel={twitch_name}, viewer_count={viewer_count}, use_login={use_login}")
    return twitch_name, viewer_count, username, password

def login_to_twitch(driver, username, password):
    """Log in to Twitch with provided credentials"""
    try:
        driver.get("https://www.twitch.tv/login")
        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.presence_of_element_located((By.ID, "login-username")))
        password_field = driver.find_element(By.ID, "password-input")
        username_field.send_keys(username)
        password_field.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[data-a-target='passport-login-button']").click()
        time.sleep(random.uniform(3, 5))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='user-menu']")))
            print("\033[92mLogin successful.\033[0m")
            logging.info("Login successful")
        except TimeoutException:
            print("\033[91mLogin failed. Check credentials or solve CAPTCHA manually.\033[0m")
            logging.error("Login failed")
            return False
        return True
    except Exception as e:
        print(f"\033[91mLogin error: {e}\033[0m")
        logging.error(f"Login error: {e}")
        return False

def test_proxy(proxy_url):
    """Test if a proxy website is running and can access Twitch"""
    logging.info(f"Testing proxy: {proxy_url}")
    try:
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            print(f"\033[91mProxy {proxy_url} is down (HTTP {response.status_code}).\033[0m")
            logging.warning(f"Proxy {proxy_url} is down (HTTP {response.status_code})")
            return False
    except requests.RequestException as e:
        print(f"\033[91mProxy {proxy_url} failed HTTP check: {e}\033[0m")
        logging.error(f"Proxy {proxy_url} failed HTTP check: {e}")
        return False

    driver = None
    try:
        driver = setup_driver()
        driver.set_page_load_timeout(10)
        driver.get(proxy_url)
        time.sleep(random.uniform(1, 3))

        input_selectors = [
            "input[type='url']",
            "input[name='url']",
            "input[id='url']",
            "input[placeholder*='URL']",
            "input[placeholder*='url']",
            "input[placeholder*='http']",
            "input[placeholder*='website']",
            "input[type='text']"
        ]
        url_input = None
        for selector in input_selectors:
            try:
                url_input = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue

        if not url_input:
            print(f"\033[91mProxy {proxy_url} has no URL input field.\033[0m")
            logging.warning(f"Proxy {proxy_url} has no URL input field")
            return False

        url_input.clear()
        url_input.send_keys("https://www.twitch.tv")
        url_input.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2, 4))
        wait = WebDriverWait(driver, 10)

        # Check for CAPTCHA
        try:
            captcha = driver.find_element(By.CSS_SELECTOR, "div[class*='captcha'], iframe[src*='captcha'], div[data-sitekey]")
            print(f"\033[91mCAPTCHA detected on {proxy_url}. Disable headless mode to solve manually.\033[0m")
            logging.warning(f"CAPTCHA detected on {proxy_url}")
            return False
        except NoSuchElementException:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='root']")))
                print(f"\033[92mProxy {proxy_url} can access Twitch.\033[0m")
                logging.info(f"Proxy {proxy_url} is valid and can access Twitch")
                return True
            except TimeoutException:
                print(f"\033[91mProxy {proxy_url} cannot access Twitch.\033[0m")
                logging.warning(f"Proxy {proxy_url} cannot access Twitch")
                return False
    except (WebDriverException, TimeoutException) as e:
        print(f"\033[91mProxy {proxy_url} failed Selenium check: {e}\033[0m")
        logging.error(f"Proxy {proxy_url} failed Selenium check: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def proxy_selector(proxy_servers):
    """Select a running proxy server with a functional URL input field"""
    global selected_proxies, valid_proxies
    max_attempts = len(proxy_servers) * 2
    attempts = 0

    available_proxies = [p for p in valid_proxies if p not in selected_proxies]
    if available_proxies:
        proxy = random.choice(available_proxies)
        selected_proxies.append(proxy)
        return proxy

    while attempts < max_attempts:
        selected_server = random.choice(list(proxy_servers.values()))
        if len(selected_proxies) == len(proxy_servers):
            selected_proxies.clear()
        if selected_server not in selected_proxies:
            if test_proxy(selected_server):
                valid_proxies.append(selected_server)
                selected_proxies.append(selected_server)
                return selected_server
            attempts += 1
    print("\033[91mNo running proxies found. Please update PROXY_SERVERS with active proxies.\033[0m")
    logging.error("No running proxies found")
    return None

def handle_mature_warning(driver):
    """Auto-accept mature audience warning"""
    try:
        wait = WebDriverWait(driver, 5)
        mature_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-a-target='player-overlay-mature-accept'], button[class*='mature-accept'], button[class*='start-watching']")))
        mature_button.click()
        time.sleep(random.uniform(1, 2))
        print("\033[92mMature audience warning accepted.\033[0m")
        logging.info("Mature audience warning accepted")
        return True
    except (NoSuchElementException, TimeoutException) as e:
        print(f"\033[93mNo mature audience warning found or failed to accept: {e}\033[0m")
        logging.info(f"No mature audience warning found or failed to accept: {e}")
        return False

def performance_booster(driver):
    """Optimize player settings for better performance"""
    try:
        wait = WebDriverWait(driver, 5)
        settings_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-a-target='player-settings-button'], button[class*='player-settings']")))
        settings_button.click()
        time.sleep(random.uniform(0.5, 1.5))

        quality_button = driver.find_element(By.CSS_SELECTOR, "button[data-a-target='player-settings-menu-item-quality'], button[class*='quality']")
        quality_button.click()
        time.sleep(random.uniform(0.5, 1.5))

        quality_options = driver.find_elements(By.CSS_SELECTOR, "div[data-a-target='player-settings-menu'] div, div[class*='quality-option']")
        if quality_options:
            quality_options[-1].click()
            print("\033[92mSet to lowest quality.\033[0m")
            logging.info("Set stream to lowest quality")
        else:
            print("\033[91mNo quality options found.\033[0m")
            logging.warning("No quality options found")
    except (NoSuchElementException, TimeoutException) as e:
        print(f"\033[91mPerformance booster failed: {e}\033[0m")
        logging.error(f"Performance booster failed: {e}")

def is_watching(driver):
    """Check if viewers are still watching the stream"""
    try:
        all_windows = driver.window_handles
        for window in all_windows:
            driver.switch_to.window(window)
            wait = WebDriverWait(driver, 5)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
            time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(f"\033[91mError checking viewer status: {e}\033[0m")
        logging.error(f"Error checking viewer status: {e}")

def setup_driver():
    """Initialize the WebDriver with Chrome options"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--lang=en')
#    chrome_options.add_argument('--headless')  # Comment out for debugging/CAPTCHA solving
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def create_viewer(driver, twitch_name, viewer_count, username, password):
    """Create viewers by opening Twitch streams"""
    created_viewer = 0
    for i in range(viewer_count):
        if len(driver.window_handles) >= MAX_WINDOWS:
            print(f"\033[91mMaximum window limit ({MAX_WINDOWS}) reached. Skipping viewer {i+1}.\033[0m")
            logging.warning(f"Maximum window limit ({MAX_WINDOWS}) reached")
            continue

        try:
            print(f"\033[93mAttempting viewer {i+1}/{viewer_count}...\033[0m")
            logging.info(f"Attempting viewer {i+1}/{viewer_count}")
            proxy = proxy_selector(PROXY_SERVERS)
            if not proxy:
                print(f"\033[91mSkipping viewer {i+1} due to no available proxies.\033[0m")
                logging.warning(f"Skipping viewer {i+1} due to no available proxies")
                continue

            print(f"\033[93mUsing proxy: {proxy}\033[0m")
            logging.info(f"Using proxy: {proxy}")

            if i == 0:
                driver.get(proxy)
            else:
                driver.execute_script(f"window.open('{proxy}')")
            driver.switch_to.window(driver.window_handles[-1])
            print(f"\033[93mSwitched to window {driver.current_window_handle}\033[0m")
            logging.info(f"Switched to window {driver.current_window_handle}")

            # Optional login
            if username and password:
                if not login_to_twitch(driver, username, password):
                    driver.close()
                    driver.switch_to.window(driver.window_handles[-1])
                    continue

            wait = WebDriverWait(driver, 10)
            input_selectors = [
                "input[type='url']",
                "input[name='url']",
                "input[id='url']",
                "input[placeholder*='URL']",
                "input[placeholder*='url']",
                "input[placeholder*='http']",
                "input[placeholder*='website']",
                "input[type='text']"
            ]
            url_input = None
            for selector in input_selectors:
                try:
                    url_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue

            if not url_input:
                print(f"\033[91mNo URL input field found on {proxy}.\033[0m")
                logging.error(f"No URL input field found on {proxy}")
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])
                continue

            url_input.clear()
            url_input.send_keys(f'https://www.twitch.tv/{twitch_name}')
            url_input.send_keys(Keys.RETURN)
            print(f"\033[93mNavigated to {twitch_name}\033[0m")
            logging.info(f"Navigated to {twitch_name}")

            # Check for CAPTCHA
            try:
                captcha = driver.find_element(By.CSS_SELECTOR, "div[class*='captcha'], iframe[src*='captcha'], div[data-sitekey]")
                print(f"\033[91mCAPTCHA detected on {proxy}. Disable headless mode to solve manually by commenting out '--headless' in setup_driver().\033[0m")
                logging.warning(f"CAPTCHA detected on {proxy}")
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])
                continue
            except NoSuchElementException:
                pass

            # Handle mature audience warning
            handle_mature_warning(driver)

            # Wait until video player is loaded
            videoscreen_css = "div[data-a-target*='player-overlay'], div[class*='player-overlay']"
            wait = WebDriverWait(driver, 30)
            video = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, videoscreen_css)))
            print(f"\033[93mVideo player loaded\033[0m")
            logging.info("Video player loaded")

            # Check for login or subscriber-only prompt
            try:
                restriction = driver.find_element(By.CSS_SELECTOR, "button[data-a-target='login-button'], div[class*='subscriber-only'], div[class*='age-restriction']")
                print(f"\033[91mLogin, subscriber-only, or age-restriction detected for {twitch_name}. Skipping viewer.\033[0m")
                logging.warning(f"Restriction detected for {twitch_name}")
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])
                continue
            except NoSuchElementException:
                pass

            actions = ActionChains(driver)
            actions.move_to_element(video).perform()
            performance_booster(driver)
            time.sleep(random.uniform(8, 12))

            created_viewer += 1
            print(f"\033[92mViewer created {created_viewer}/{viewer_count}.\033[0m")
            logging.info(f"Viewer created {created_viewer}/{viewer_count}")

        except (WebDriverException, TimeoutException) as e:
            print(f"\033[91mError for viewer {i+1}: {e}\033[0m")
            logging.error(f"Error for viewer {i+1}: {e}")
            try:
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])
            except:
                pass
            continue

    print(f"\033[92mViewer creation complete: {created_viewer}/{viewer_count} viewers created.\033[0m")
    logging.info(f"Viewer creation complete: {created_viewer}/{viewer_count} viewers created")
    return created_viewer

def main():
    """Main execution function"""
    clear_console()
    print_banner()

    twitch_name, viewer_count, username, password = get_twitch_info()

    if not check_twitch_channel_status(twitch_name):
        print("\033[91mExiting due to channel not being live.\033[0m")
        logging.error("Exiting due to channel not being live")
        return

    print("\033[93mCreating viewers, please wait...\033[0m")
    logging.info("Creating viewers")

    driver = setup_driver()

    try:
        created = create_viewer(driver, twitch_name, viewer_count, username, password)
        if created == 0:
            print("\033[91mNo viewers created. Check proxies or channel settings.\033[0m")
            logging.error("No viewers created")
            return

        print("\033[93mAll viewers created. Press 'Ctrl + C' to exit when done.\033[0m")
        logging.info("All viewers created")

        while True:
            is_watching(driver)
            time.sleep(random.uniform(60, 90))

    except KeyboardInterrupt:
        print("\033[93mShutting down viewers...\033[0m")
        logging.info("Shutting down viewers")
    finally:
        driver.quit()
        logging.info("Driver quit")

if __name__ == "__main__":
    main()