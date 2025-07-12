def open_embed_via_proxy(channel, num_viewers, proxies, headless=False):
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    config = load_config()
    embed_url = f"https://player.twitch.tv/?channel={channel}&parent=twitch.tv&autoplay=true"
    web_proxies = [p for p in proxies if p and p.startswith("http")]
    if not web_proxies:
        print("No web proxies available. Exiting.")
        return
    # Use get_chrome_options for consistent window sizing, adblock, and browser-level muting
    options, width, height = get_chrome_options(headless=headless)
    # Ensure headless mode is always set if requested (for undetected_chromedriver compatibility)
    if headless and not any(arg.startswith('--headless') for arg in options.arguments):
        options.add_argument('--headless=new')
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    try:
        driver.set_window_size(width, height)
    except Exception:
        pass
    tabs = []
    for i in range(num_viewers):
        proxy = web_proxies[i % len(web_proxies)]
        if i == 0:
            driver.get(proxy)
            tabs.append(driver.current_window_handle)
        else:
            driver.execute_script(f"window.open('{proxy}','_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            tabs.append(driver.current_window_handle)
        try:
            driver.set_window_size(width, height)
        except Exception:
            pass
        try:
            from urllib.parse import urlparse
            proxy_domain = urlparse(proxy).netloc.replace('www.', '').split('/')[0]
            selectors = config.get("proxy_input_selectors", {}).get(proxy_domain, []) + config.get("input_selectors", [])
            enterurl = None
            for selector in selectors:
                try:
                    el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if el.is_displayed() and el.is_enabled():
                        enterurl = el
                        break
                except Exception:
                    pass
            if not enterurl:
                for inp in driver.find_elements(By.TAG_NAME, "input"):
                    attrs = [
                        inp.get_attribute("placeholder") or "",
                        inp.get_attribute("name") or "",
                        inp.get_attribute("id") or "",
                        inp.get_attribute("aria-label") or "",
                        inp.get_attribute("type") or "",
                    ]
                    attrs = [a.lower() for a in attrs]
                    if any(kw in a for kw in ["url", "link", "website", "address"] for a in attrs):
                        if inp.is_displayed() and inp.is_enabled():
                            enterurl = inp
                            break
            if not enterurl:
                for inp in driver.find_elements(By.TAG_NAME, "input"):
                    if inp.is_displayed() and inp.is_enabled() and (inp.get_attribute("type") in (None, "", "text", "url")):
                        enterurl = inp
                        break
            if not enterurl:
                print(f"[Tab {i+1}] Could not find proxy input field.")
                continue
            try:
                enterurl.clear()
            except Exception:
                pass
            enterurl.send_keys(embed_url)
            enterurl.send_keys(Keys.RETURN)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video"))
            )
            # Removed mute logic; only set quality below
            settings_btn = None
            for sel in [
                '[data-a-target="player-settings-button"]',
                'button[aria-label*="Settings"]',
                'button[aria-label*="settings"]',
                'button[title*="Settings"]',
                'button[title*="settings"]'
            ]:
                try:
                    settings_btn = WebDriverWait(driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, sel))
                    if settings_btn.is_displayed() and settings_btn.is_enabled():
                        break
                except Exception:
                    pass
            if settings_btn:
                settings_btn.click()
                time.sleep(0.5)
                quality_btn = None
                for sel in [
                    '[data-a-target="player-settings-menu-item-quality"]',
                    'button[aria-label*="Quality"]',
                    'button[aria-label*="quality"]',
                    'button[title*="Quality"]',
                    'button[title*="quality"]'
                ]:
                    try:
                        quality_btn = WebDriverWait(driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, sel))
                        if quality_btn.is_displayed() and quality_btn.is_enabled():
                            break
                    except Exception:
                        pass
                if quality_btn:
                    quality_btn.click()
                    time.sleep(0.5)
                    quality_options = []
                    for sel in ['.tw-radio', 'input[type="radio"]', 'button[role="menuitemradio"]', 'div[role="menuitemradio"]']:
                        try:
                            quality_options = WebDriverWait(driver, 3).until(lambda d: d.find_elements(By.CSS_SELECTOR, sel))
                            if quality_options:
                                break
                        except Exception:
                            pass
                    found = False
                    preferred = ["160p", "360p", "480p", "Auto", "144p", "240p"]
                    for label in preferred:
                        for opt in quality_options:
                            try:
                                text = opt.text.strip() if hasattr(opt, 'text') else ''
                                if not text:
                                    text = opt.get_attribute('aria-label') or opt.get_attribute('value') or ''
                                if label.lower() in text.lower():
                                    opt.click()
                                    found = True
                                    break
                            except Exception:
                                pass
                        if found:
                            break
                    if not found and quality_options:
                        try:
                            quality_options[-1].click()
                        except Exception:
                            pass
                # Always print viewer created after video loads, even if quality selection fails
                print(f"Viewer {i+1}/{num_viewers} created")
            else:
                print(f"[EMBED-PROXY] Tab {i+1}: Settings button not found, skipping quality selection.")
                # Still print viewer created after video loads
                print(f"Viewer {i+1}/{num_viewers} created")
        except Exception as e:
            print(f"[EMBED-PROXY] Tab {i+1}: Proxy/embed/quality error: {e}")
    print("All embed-proxy tabs loaded. Press Ctrl+C to close.")
    # --- Sustain and keep all viewers active (anti-idle, anti-timeout) ---
    try:
        while True:
            for tab in tabs:
                try:
                    driver.switch_to.window(tab)
                    # Touch the tab (driver.title)
                    driver.title
                    # Try to interact with the video element if present
                    try:
                        video = driver.find_element(By.CSS_SELECTOR, "video")
                        # Simulate a small mouse move or click to keep it alive
                        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mousemove', {bubbles:true}));", video)
                        # Always mute and set volume to 0 for every tab (robust: set muted property, attribute, and audioTracks)
                        driver.execute_script('''
                            if (arguments[0]) {
                                arguments[0].muted = true;
                                arguments[0].setAttribute('muted', '');
                                arguments[0].volume = 0.0;
                                if (arguments[0].audioTracks && arguments[0].audioTracks.length > 0) {
                                    for (let i = 0; i < arguments[0].audioTracks.length; i++) {
                                        try { arguments[0].audioTracks[i].enabled = false; } catch(e){}
                                    }
                                }
                            }
                        ''', video)
                        # Optionally, play if paused
                        if driver.execute_script("return arguments[0].paused;", video):
                            driver.execute_script("arguments[0].play();", video)
                    except Exception:
                        pass
                    # Optionally, scroll the page a bit to simulate activity
                    try:
                        driver.execute_script("window.scrollBy(0, Math.floor(Math.random()*10));")
                    except Exception:
                        pass
                except Exception:
                    pass
            time.sleep(5)
    except KeyboardInterrupt:
        print("Closing browser...")
        driver.quit()
def open_twitch_iframe_viewers(channel, num_viewers, headless=False):
    from selenium.webdriver.common.by import By
    import undetected_chromedriver as uc
    # Use get_chrome_options for consistent window sizing
    from random import randint
    from time import sleep
    config = load_config()
    # Use config window size range if available
    ws = config.get("window_size_range", {"min_width": 800, "max_width": 1280, "min_height": 600, "max_height": 720})
    min_width, max_width = ws.get("min_width", 800), ws.get("max_width", 1280)
    min_height, max_height = ws.get("min_height", 600), ws.get("max_height", 720)
    width = randint(min_width, max_width)
    height = randint(min_height, max_height)
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument(f"--window-size={width},{height}")
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    # Explicitly resize window in both headless and non-headless mode
    try:
        driver.set_window_size(width, height)
    except Exception:
        pass
    base_url = f"https://player.twitch.tv/?channel={channel}&parent=twitch.tv&autoplay=true"
    tabs = []
    for i in range(num_viewers):
        if i == 0:
            driver.get(base_url)
            tabs.append(driver.current_window_handle)
        else:
            driver.execute_script(f"window.open('{base_url}','_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            tabs.append(driver.current_window_handle)
        # Explicitly resize each tab's window (for non-headless, but harmless in headless)
        try:
            driver.set_window_size(width, height)
        except Exception:
            pass
        print(f"[IFRAME] Opened tab {i+1}/{num_viewers} (Window size: {width}x{height})")
        # Wait for video and select lowest quality
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video"))
            )
            # Try to open settings and select lowest quality
            settings_btn = None
            for sel in [
                '[data-a-target="player-settings-button"]',
                'button[aria-label*="Settings"]',
                'button[aria-label*="settings"]',
                'button[title*="Settings"]',
                'button[title*="settings"]'
            ]:
                try:
                    settings_btn = WebDriverWait(driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, sel))
                    if settings_btn.is_displayed() and settings_btn.is_enabled():
                        break
                except Exception:
                    continue
            if settings_btn:
                settings_btn.click()
                sleep(0.5)
                # Quality menu
                quality_btn = None
                for sel in [
                    '[data-a-target="player-settings-menu-item-quality"]',
                    'button[aria-label*="Quality"]',
                    'button[aria-label*="quality"]',
                    'button[title*="Quality"]',
                    'button[title*="quality"]'
                ]:
                    try:
                        quality_btn = WebDriverWait(driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, sel))
                        if quality_btn.is_displayed() and quality_btn.is_enabled():
                            break
                    except Exception:
                        continue
                if quality_btn:
                    quality_btn.click()
                    sleep(0.5)
                    # Quality options
                    quality_options = []
                    for sel in ['.tw-radio', 'input[type="radio"]', 'button[role="menuitemradio"]', 'div[role="menuitemradio"]']:
                        try:
                            quality_options = WebDriverWait(driver, 3).until(lambda d: d.find_elements(By.CSS_SELECTOR, sel))
                            if quality_options:
                                break
                        except Exception:
                            continue
                    found = False
                    preferred = ["160p", "360p", "480p", "Auto", "144p", "240p"]
                    for label in preferred:
                        for opt in quality_options:
                            try:
                                text = opt.text.strip() if hasattr(opt, 'text') else ''
                                if not text:
                                    text = opt.get_attribute('aria-label') or opt.get_attribute('value') or ''
                                if label.lower() in text.lower():
                                    opt.click()
                                    found = True
                                    print(f"[IFRAME] Tab {i+1}: Selected quality: {label}")
                                    break
                            except Exception:
                                continue
                        if found:
                            break
                    if not found and quality_options:
                        try:
                            quality_options[-1].click()
                            print(f"[IFRAME] Tab {i+1}: Fallback: selected last quality option.")
                        except Exception:
                            print(f"[IFRAME] Tab {i+1}: Could not select any quality option.")
            else:
                print(f"[IFRAME] Tab {i+1}: Settings button not found, skipping quality selection.")
        except Exception as e:
            print(f"[IFRAME] Tab {i+1}: Error selecting quality: {e}")
    print("All iframe tabs loaded. Press Ctrl+C to close.")
    try:
        while True:
            for tab in tabs:
                try:
                    driver.switch_to.window(tab)
                    driver.title
                except Exception:
                    pass
            sleep(5)
    except KeyboardInterrupt:
        print("Closing browser...")
        driver.quit()
import os, sys, time, random, json, threading, glob, requests, re
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
try:
    import undetected_chromedriver as uc
except ImportError as e:
    print(f"\033[91mMissing dependency: {str(e)}. Install with: pip install undetected-chromedriver requests selenium\033[0m"); sys.exit(1)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    clear()


# ================== Timing/Wait Settings (EVB-Optimized) ==================
# These values are tuned for best performance and reliability (EVB style)
WAIT_PROXY_LOAD = 1.2           # Time to wait after loading a proxy page (seconds)
WAIT_AFTER_URL_SUBMIT = 1.2     # Time to wait after submitting Twitch URL in proxy (seconds)
WAIT_AFTER_TWITCH_LOAD = 5      # Time to wait after loading Twitch page (for resolution change/manual interaction)
WAIT_BETWEEN_TABS = (0.15, 0.35) # Min/max random wait between opening tabs (seconds)
WAIT_BETWEEN_VIEWERS = (0.2, 0.5) # Min/max random wait after viewer loads (seconds)
WAIT_BETWEEN_THREADS = (0.1, 0.3) # If using threads, min/max random wait between starts
WAIT_SUSTAIN_LOOP = 1           # Time to wait in sustain loop per tick (seconds)
# ========================================================================
# --- Robust Config and Proxy Management ---
DEFAULT_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    ],
    "proxies": [
        "https://www.croxyproxy.com",
        "https://www.croxyproxy.rocks",
        "https://www.croxy.network",
        "https://www.croxy.org",
        "https://www.croxyproxy.net"
    ],
    "activity_interval": 30,
    "failure_threshold": 5,
    "window_size_range": {"min_width": 800, "max_width": 1280, "min_height": 600, "max_height": 720},
    "retry_attempts": 3,
    "reconnect_delay": 5,
    "proxy_input_selectors": {
        "croxyproxy.com": ["input#url", "input[name='url']", "input[id='url']", "input[type='url']"],
        "croxyproxy.rocks": ["input#url", "input[name='url']", "input[id='url']", "input[type='url']"],
        "croxy.network": ["input#url", "input[name='url']", "input[id='url']", "input[type='url']"],
        "croxy.org": ["input#url", "input[name='url']", "input[id='url']", "input[type='url']"],
        "croxyproxy.net": ["input#url", "input[name='url']", "input[id='url']", "input[type='url']"],
    },
    "input_selectors": [
        "input#url", "input[name='url']", "input[id='url']", "input[type='url']",
        "input[name*='url']", "input[id*='url']", "input[placeholder*='url']",
        "input[placeholder*='URL']", "input[placeholder*='link']", "input[placeholder*='website']",
        "input[placeholder*='address']", "input[type='text']", "input[autocomplete*='url']",
        "input[class*='url']", "input[aria-label*='url']"
    ],
}

def load_config(path="settings.txt"):
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception:
            pass
    return config

def load_proxies():
    # Always include hardcoded proxies from config
    config = load_config()
    proxies = list(config.get("proxies", []))
    seen = set(proxies)
    for fname in ["proxies.txt"] + glob.glob("proxies_*.txt"):
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and line not in seen:
                        proxies.append(line)
                        seen.add(line)
    return proxies

# --- Proxy Health Tracking ---
PROXY_HEALTH = {}
FAILED_PROXIES = set()
proxy_health_lock = threading.Lock()
def update_proxy_health(proxy, success):
    with proxy_health_lock:
        d = PROXY_HEALTH.setdefault(proxy, {'success': 0, 'fail': 0})
        d['success' if success else 'fail'] += 1
        if d['fail'] > 5:
            FAILED_PROXIES.add(proxy)

def get_best_proxy(valid_proxies):
    with proxy_health_lock:
        available = [p for p in valid_proxies if p not in FAILED_PROXIES]
        if not available:
            FAILED_PROXIES.clear()
            available = valid_proxies
        return min(available, key=lambda p: PROXY_HEALTH.get(p, {'fail': 0})['fail'])

def check_proxy_health(proxy):
    # EVB-style: Only check HTTP(S) proxies, skip CroxyProxy URLs
    if proxy.startswith("http://") or proxy.startswith("https://"):
        # If it's a CroxyProxy or similar, treat as always healthy (let browser handle failures)
        croxy_domains = [
            "croxyproxy.com", "croxyproxy.rocks", "croxy.network", "croxy.org", "croxyproxy.net"
        ]
        from urllib.parse import urlparse
        domain = urlparse(proxy).netloc.replace('www.', '').split('/')[0]
        if any(domain.endswith(croxy) for croxy in croxy_domains):
            return True
        try:
            resp = requests.get("http://example.com", proxies={"http": proxy, "https": proxy}, timeout=8)
            return resp.status_code == 200
        except Exception:
            return False
    return False

# --- Chrome Options ---
def get_chrome_options(proxy=None, user_agent=None, headless=False):
    options = uc.ChromeOptions()
    # Add adblock extension if present
    adblock_path = os.path.join(os.path.dirname(__file__), 'adblock.crx')
    if os.path.exists(adblock_path):
        try:
            options.add_extension(adblock_path)
            print("[DEBUG] Loaded adblock.crx extension.")
        except Exception as e:
            print(f"[DEBUG] Failed to load adblock.crx: {e}")
    # Optimized window size for performance but large enough for Twitch quality selector
    min_width, max_width = 480, 720
    min_height, max_height = 320, 480
    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)
    for arg in [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        # Do NOT disable extensions, so adblock can load
        # "--disable-extensions",
        "--mute-audio",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        f"--window-size={width},{height}",
        "--lang=en-US"
    ]:
        options.add_argument(arg)
    # Instead of storing on options, return width and height for explicit resize
    return options, width, height

# --- Viewer Thread Logic ---
def create_viewer(viewer_id, url, proxy=None, user_agent=None, headless=False, sustain_time=None):
    try:
        options, width, height = get_chrome_options(proxy, user_agent, headless)
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        # If using a proxy URL, go to the proxy first, then input the Twitch URL
        if proxy and proxy.startswith("http"):
            driver.get(proxy)
            time.sleep(2)
            from urllib.parse import urlparse
            config = load_config()
            proxy_domain = urlparse(proxy).netloc.replace('www.', '').split('/')[0]
            selectors = config.get("proxy_input_selectors", {}).get(proxy_domain, []) + config.get("input_selectors", [])
            enterurl = None
            # Try proxy-specific selectors first, then generic
            for selector in selectors:
                try:
                    el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if el.is_displayed() and el.is_enabled():
                        enterurl = el
                        break
                except Exception:
                    continue
            # Smart scan if not found
            if not enterurl:
                for inp in driver.find_elements(By.TAG_NAME, "input"):
                    attrs = [
                        inp.get_attribute("placeholder") or "",
                        inp.get_attribute("name") or "",
                        inp.get_attribute("id") or "",
                        inp.get_attribute("aria-label") or "",
                        inp.get_attribute("type") or "",
                    ]
                    attrs = [a.lower() for a in attrs]
                    if any(kw in a for kw in ["url", "link", "website", "address"] for a in attrs):
                        if inp.is_displayed() and inp.is_enabled():
                            enterurl = inp
                            break
            if not enterurl:
                # Fallback: try to find the first visible text input
                for inp in driver.find_elements(By.TAG_NAME, "input"):
                    if inp.is_displayed() and inp.is_enabled() and (inp.get_attribute("type") in (None, "", "text", "url")):
                        enterurl = inp
                        break
            if not enterurl:
                raise Exception("Could not find proxy input field")
            # Input the Twitch URL and submit
            try:
                enterurl.clear()
            except Exception:
                pass
            enterurl.send_keys(url)
            enterurl.send_keys(Keys.RETURN)
            time.sleep(2)
        else:
            driver.get(url)
        # Wait for Twitch video to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "video"))
        )
        print(f"[Viewer {viewer_id}] Watching {url} (Proxy: {proxy if proxy else 'None'})")
        sustain_time = sustain_time or random.randint(300, 600)
        for _ in range(sustain_time):
            try:
                driver.title
            except (WebDriverException, NoSuchWindowException, AttributeError):
                break
            time.sleep(1)
        driver.quit()
        if proxy:
            update_proxy_health(proxy, True)
    except Exception as e:
        print(f"[Viewer {viewer_id}] Error: {e}")
        if proxy:
            update_proxy_health(proxy, False)

def sustain_viewers(num_viewers, url, proxies, user_agents, headless, activity_interval):
    # --- EVB/ETVBA-style: Use one browser, multiple tabs, maximize proxy diversity ---
    if proxies:
        valid_proxies = [p for p in proxies if check_proxy_health(p)]
        if not valid_proxies:
            print("No healthy proxies found. Running without proxies.")
            valid_proxies = [None]*num_viewers
        print(f"Loaded {len(proxies)} proxies. {len(valid_proxies) if valid_proxies[0] else 0} healthy.")
    else:
        valid_proxies = [None]*num_viewers
        print("No proxies loaded. Running without proxies.")

    # Separate web proxies (CroxyProxy etc) from HTTP/SOCKS proxies
    web_proxies = [p for p in valid_proxies if p and p.startswith("http")]
    socks_http_proxies = [p for p in valid_proxies if p and not p.startswith("http")]

    # If we have HTTP/SOCKS proxies, use the first one for the whole browser
    browser_proxy = socks_http_proxies[0] if socks_http_proxies else None
    user_agent = random.choice(user_agents)
    # Get options, width, height
    options, width, height = get_chrome_options(browser_proxy, user_agent, headless)
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    # Explicitly resize window in non-headless mode
    if not headless:
        try:
            driver.set_window_size(width, height)
        except Exception:
            pass

    # For each tab, assign a web proxy if available, else use direct or browser-level proxy
    tabs = []
    tab_proxies = []
    for i in range(num_viewers):
        if i == 0:
            driver.switch_to.window(driver.current_window_handle)
        else:
            driver.execute_script("window.open('about:blank','_blank');")
            driver.switch_to.window(driver.window_handles[-1])
        tabs.append(driver.current_window_handle)
        # Assign a web proxy to this tab if available
        tab_proxy = web_proxies[i % len(web_proxies)] if web_proxies else browser_proxy
        tab_proxies.append(tab_proxy)
        print(f"[DEBUG] Opened tab {i+1}/{num_viewers} (Proxy: {tab_proxy})")
        time.sleep(random.uniform(*WAIT_BETWEEN_TABS))

    # For each tab, open the proxy (if web proxy) and input Twitch URL, else go direct
    success_count = 0
    for i, tab in enumerate(tabs):
        try:
            driver.switch_to.window(tab)
            proxy = tab_proxies[i]
            viewer_ok = False
            # Step 1: Open proxy or Twitch page
            if proxy and proxy.startswith("http"):
                driver.get(proxy)
                time.sleep(WAIT_PROXY_LOAD)
                from urllib.parse import urlparse
                config = load_config()
                proxy_domain = urlparse(proxy).netloc.replace('www.', '').split('/')[0]
                selectors = config.get("proxy_input_selectors", {}).get(proxy_domain, []) + config.get("input_selectors", [])
                enterurl = None
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                debug_inputs = []
                for inp in all_inputs:
                    attrs = {
                        "placeholder": inp.get_attribute("placeholder"),
                        "name": inp.get_attribute("name"),
                        "id": inp.get_attribute("id"),
                        "aria-label": inp.get_attribute("aria-label"),
                        "type": inp.get_attribute("type"),
                        "class": inp.get_attribute("class"),
                        "displayed": inp.is_displayed(),
                        "enabled": inp.is_enabled(),
                    }
                    debug_inputs.append(attrs)
                for selector in selectors:
                    try:
                        el = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if el.is_displayed() and el.is_enabled():
                            enterurl = el
                            break
                    except Exception:
                        continue
                if not enterurl:
                    for inp in all_inputs:
                        attrs = [
                            (inp.get_attribute("placeholder") or "").lower(),
                            (inp.get_attribute("name") or "").lower(),
                            (inp.get_attribute("id") or "").lower(),
                            (inp.get_attribute("aria-label") or "").lower(),
                            (inp.get_attribute("type") or "").lower(),
                            (inp.get_attribute("class") or "").lower(),
                        ]
                        if any(kw in a for kw in ["url", "link", "website", "address"] for a in attrs):
                            if inp.is_displayed() and inp.is_enabled():
                                enterurl = inp
                                break
                if not enterurl:
                    for inp in all_inputs:
                        if inp.is_displayed() and inp.is_enabled() and (inp.get_attribute("type") in (None, "", "text", "url")):
                            enterurl = inp
                            break
                if not enterurl:
                    print(f"[Tab {i+1}] Could not find proxy input field. Inputs found:")
                    for idx, attrs in enumerate(debug_inputs):
                        print(f"  Input {idx+1}: {attrs}")
                    # Still count this viewer as created, but warn
                    success_count += 1
                    print(f"\033[93mViewer {success_count}/{num_viewers} created (NO INPUT FIELD)\033[0m")
                    continue
                # Step 2: Input Twitch URL and submit
                try:
                    enterurl.clear()
                except Exception:
                    pass
                enterurl.send_keys(url)
                enterurl.send_keys(Keys.RETURN)
                time.sleep(WAIT_AFTER_URL_SUBMIT)
                # Step 3: Wait for Twitch to load for manual/auto resolution change
                time.sleep(WAIT_AFTER_TWITCH_LOAD)
            else:
                driver.get(url)
                # Step 2: Wait for Twitch to load for manual/auto resolution change
                time.sleep(WAIT_AFTER_TWITCH_LOAD)
            # Step 4: Accept cookies popup if present before waiting for video
            try:
                # Try common Twitch cookie consent selectors
                cookie_btns = driver.find_elements(By.CSS_SELECTOR, '[data-a-target="consent-banner-accept"]')
                if not cookie_btns:
                    # Try alternate selectors (EU/other regions)
                    cookie_btns = driver.find_elements(By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'agree') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'proceed')]")
                # Try new fallback: region-specific or deeply nested button (user provided selector)
                if not cookie_btns:
                    try:
                        extra_btn = driver.find_element(By.CSS_SELECTOR, "#root > div > div.Layout-sc-1xcs6mc-0.hodpZn > div.Layout-sc-1xcs6mc-0.eLLosC > div > div > div > div.Layout-sc-1xcs6mc-0.qgmNh > div:nth-child(2) > div > button")
                        if extra_btn.is_displayed() and extra_btn.is_enabled():
                            cookie_btns = [extra_btn]
                    except Exception:
                        pass
                # Try clicking all found buttons, with extra debug
                clicked = False
                for btn in cookie_btns:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            print(f"[Tab {i+1}] Cookie/consent candidate button: '{btn.text}' (class: {btn.get_attribute('class')})")
                            btn.click()
                            print(f"[Tab {i+1}] Clicked cookies/proceed button: {btn.text}")
                            time.sleep(0.5)
                            clicked = True
                            break
                    except Exception as e:
                        print(f"[Tab {i+1}] Error clicking cookie/proceed button: {e}")
                if not clicked:
                    print(f"[Tab {i+1}] No cookie/proceed button clicked. Buttons found: {[btn.text for btn in cookie_btns]}")
            except Exception as e:
                print(f"[Tab {i+1}] Cookie/proceed button error: {e}")
            # Step 5: Wait for Twitch video to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "video"))
                )
                # --- Robust auto-select of lowest quality (EVB-style improved) ---
                try:
                    # 1. Wait for and click the settings button (try multiple selectors)
                    settings_btn = None
                    for sel in [
                        '[data-a-target="player-settings-button"]',
                        'button[aria-label*="Settings"]',
                        'button[aria-label*="settings"]',
                        'button[title*="Settings"]',
                        'button[title*="settings"]'
                    ]:
                        try:
                            settings_btn = WebDriverWait(driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, sel))
                            if settings_btn.is_displayed() and settings_btn.is_enabled():
                                print(f"[Tab {i+1}] Found settings button: {sel}")
                                break
                        except Exception:
                            continue
                    if not settings_btn:
                        # Print all clickable buttons for debug
                        all_btns = driver.find_elements(By.TAG_NAME, 'button')
                        print(f"[Tab {i+1}] No settings button found. Clickable buttons: {[btn.get_attribute('aria-label') for btn in all_btns]}")
                        raise Exception("Settings button not found")
                    settings_btn.click()
                    time.sleep(0.5)
                    # 2. Wait for and click the quality menu item (try multiple selectors)
                    quality_btn = None
                    for sel in [
                        '[data-a-target="player-settings-menu-item-quality"]',
                        'button[aria-label*="Quality"]',
                        'button[aria-label*="quality"]',
                        'button[title*="Quality"]',
                        'button[title*="quality"]'
                    ]:
                        try:
                            quality_btn = WebDriverWait(driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, sel))
                            if quality_btn.is_displayed() and quality_btn.is_enabled():
                                print(f"[Tab {i+1}] Found quality menu item: {sel}")
                                break
                        except Exception:
                            continue
                    if not quality_btn:
                        # Print all menu items for debug
                        menu_items = driver.find_elements(By.CSS_SELECTOR, 'button,div')
                        print(f"[Tab {i+1}] No quality menu item found. Menu items: {[item.text for item in menu_items if item.is_displayed()]}")
                        raise Exception("Quality menu item not found")
                    quality_btn.click()
                    time.sleep(0.5)
                    # 3. Wait for quality options to appear (try multiple selectors)
                    quality_options = []
                    for sel in ['.tw-radio', 'input[type="radio"]', 'button[role="menuitemradio"]', 'div[role="menuitemradio"]']:
                        try:
                            quality_options = WebDriverWait(driver, 3).until(lambda d: d.find_elements(By.CSS_SELECTOR, sel))
                            if quality_options:
                                print(f"[Tab {i+1}] Found quality options with selector: {sel}")
                                break
                        except Exception:
                            continue
                    # 4. Try to select the lowest available quality by text
                    found = False
                    preferred = ["160p", "360p", "480p", "Auto", "144p", "240p"]
                    for label in preferred:
                        for opt in quality_options:
                            try:
                                text = opt.text.strip() if hasattr(opt, 'text') else ''
                                if not text:
                                    # Try aria-label or value
                                    text = opt.get_attribute('aria-label') or opt.get_attribute('value') or ''
                                if label.lower() in text.lower():
                                    opt.click()
                                    found = True
                                    print(f"[Tab {i+1}] Selected quality: {label}")
                                    break
                            except Exception as e:
                                print(f"[Tab {i+1}] Error clicking quality option: {e}")
                        if found:
                            break
                    # 5. Fallback: select the last option (usually lowest quality)
                    if not found and quality_options:
                        try:
                            quality_options[-1].click()
                            found = True
                            print(f"[Tab {i+1}] Fallback: selected last quality option.")
                        except Exception as e:
                            print(f"[Tab {i+1}] Error clicking fallback quality option: {e}")
                    time.sleep(0.5)
                    if not found:
                        print(f"[Tab {i+1}] Could not auto-select quality. Options found: {[opt.text for opt in quality_options]}")
                except Exception as e:
                    print(f"[Tab {i+1}] Quality selection error: {e}")
                # --- Wait for manual/auto quality selection before counting viewer ---
                if not headless:
                    input(f"[Tab {i+1}] Video loaded. Please select quality (if needed), then press Enter to continue...")
                success_count += 1
                print(f"\033[92mViewer {success_count}/{num_viewers} created\033[0m")
                viewer_ok = True
            except Exception as e:
                # Count as created, but warn
                success_count += 1
                print(f"\033[93mViewer {success_count}/{num_viewers} created (NO VIDEO)\033[0m")
            # Step 6: Only after all above, open the next tab
            time.sleep(random.uniform(*WAIT_BETWEEN_VIEWERS))
        except Exception as e:
            print(f"[Tab {i+1}] Exception: {e}")
            continue

    # --- Improved logic to keep viewers active (EVB/ETVBA style) ---
    sustain_time = activity_interval or random.randint(300, 600)
    try:
        for sec in range(sustain_time):
            for i, tab in enumerate(tabs):
                try:
                    driver.switch_to.window(tab)
                    # Try to keep the tab/video alive with activity:
                    # 1. Touch the tab (driver.title)
                    driver.title
                    # 2. Try to interact with the video element if present
                    try:
                        video = driver.find_element(By.CSS_SELECTOR, "video")
                        # Simulate a small mouse move or click to keep it alive
                        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mousemove', {bubbles:true}));", video)
                        # Always mute and set volume to 0 for every tab (robust: set muted property, attribute, and audioTracks)
                        driver.execute_script('''
                            if (arguments[0]) {
                                arguments[0].muted = true;
                                arguments[0].setAttribute('muted', '');
                                arguments[0].volume = 0.0;
                                if (arguments[0].audioTracks && arguments[0].audioTracks.length > 0) {
                                    for (let i = 0; i < arguments[0].audioTracks.length; i++) {
                                        try { arguments[0].audioTracks[i].enabled = false; } catch(e){}
                                    }
                                }
                            }
                        ''', video)
                        # Optionally, play if paused
                        if driver.execute_script("return arguments[0].paused;", video):
                            driver.execute_script("arguments[0].play();", video)
                    except Exception:
                        pass
                    # 3. Optionally, scroll the page a bit to simulate activity
                    try:
                        driver.execute_script("window.scrollBy(0, Math.floor(Math.random()*10));")
                    except Exception:
                        pass
                except Exception:
                    pass
            time.sleep(WAIT_SUSTAIN_LOOP)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        driver.quit()
        # Mark all proxies as healthy (web proxies always healthy, HTTP/SOCKS only if used)
        for proxy in set(tab_proxies):
            if proxy:
                update_proxy_health(proxy, True)

# --- Interactive Menu and Main Logic ---
def main():
    banner()
    print("WARNING: Viewbots may violate Twitch ToS (https://www.twitch.tv/p/en/legal/terms-of-service/). Use responsibly.")
    confirm = input("Type 'I AGREE' to confirm you understand the risks and ToS implications:\n > ").strip()
    if confirm.lower() != "i agree":
        print("You must type 'I AGREE' to continue. Exiting.")
        return
    config = load_config()
    twitch_name = input("Twitch Channel Name\n > ").strip()
    if not twitch_name or not re.match(r'^[a-zA-Z0-9_]{4,25}$', twitch_name):
        print("Invalid Twitch channel name. Exiting.")
        return
    try:
        num_viewers = int(input("Viewer Count\n > "))
        if num_viewers <= 0:
            raise ValueError
    except Exception:
        print("Invalid viewer count. Exiting.")
        return
    headless_input = input("Headless mode? (y/n)\n > ").strip().lower()
    headless = headless_input in ("y", "yes")
    print("Select mode:")
    print("1. Full bot (proxy, quality, cookies, etc)")
    print("2. Iframe only (no proxy)")
    print("3. Embed via proxy (proxy + embed)")
    mode = input("Enter 1, 2, or 3:\n > ").strip()
    if mode == "2":
        open_twitch_iframe_viewers(twitch_name, num_viewers, headless)
    elif mode == "3":
        proxies = load_proxies()
        open_embed_via_proxy(twitch_name, num_viewers, proxies, headless)
    else:
        proxies = load_proxies()
        user_agents = config.get("user_agents", DEFAULT_CONFIG["user_agents"])
        activity_interval = config.get("activity_interval", 30)
        url = f"https://www.twitch.tv/{twitch_name}"
        sustain_viewers(num_viewers, url, proxies, user_agents, headless, activity_interval)

if __name__ == "__main__":
    main()
