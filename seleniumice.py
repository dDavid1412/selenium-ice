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

driver.get("https://knasta.cl/results?q=videojuegos&order=asc&b=2K%2CActivision%2CBandai+Namco%2CCapcom%2CElectronic+Arts%2CNintendo%2CPlaystation%2CSega%2CSquare+Enix%2CUbisoft%2CXbox")



