from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import time
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# ==================== FIREFOX ====================
# Automatically manages GeckoDriver version
# firefox_service = FirefoxService(GeckoDriverManager().install())
# firefox_options = FirefoxOptions()
# firefox_options.binary_location = r"C:\Program Files\Waterfox\waterfox.exe"
# driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

# ==================== CHROME ====================
# Automatically manages ChromeDriver version (matches your Chrome browser)
chrome_service = ChromeService(ChromeDriverManager().install())
chrome_options = ChromeOptions()
# Optional: Add Chrome-specific options
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--start-maximized")
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
# Abrir una página

driver.get("https://https://knasta.cl/results?q=videojuegos&order=asc/")


time.sleep(3)


login_button = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/header/div/div/div/div/div/header/div/div[3]/div[5]/span/button")

login_button.click()

time.sleep(1)

login_input = driver.find_element(By.XPATH, "//input[@placeholder='username@example.com']")

time.sleep(1)

login_input.click()

login_input.send_keys("")

time.sleep(1)

submit_login = driver.find_element(By.XPATH, "/html/body/div[3]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div/div/div/div[1]/div/div[2]/button")

submit_login.click()

time.sleep(10)
