import json
import re
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


RESULTS_URL = (
    "https://knasta.cl/results?q=videojuegos&order=asc&"
    "b=2K%2CActivision%2CBandai+Namco%2CCapcom%2CElectronic+Arts%2C"
    "Nintendo%2CPlaystation%2CSega%2CSquare+Enix%2CUbisoft%2CXbox"
)


def currency_to_int(value: Any) -> Optional[int]:
    """Convert values such as '$ 57.990' or 57990 to Chilean pesos."""
    if value is None:
        return None

    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def get_json_ld(driver: webdriver.Chrome, expected_type: str) -> Dict[str, Any]:
    elements = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')

    for element in elements:
        try:
            data = json.loads(element.get_attribute("textContent"))
        except (TypeError, json.JSONDecodeError):
            continue

        if data.get("@type") == expected_type:
            return data

    raise RuntimeError(f"JSON-LD data of type {expected_type!r} was not found")


def find_money(text: str, pattern: str) -> Optional[int]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return currency_to_int(match.group(1)) if match else None


def infer_console(name: str) -> str:
    name_lower = name.lower()

    if "switch" in name_lower:
        return "Switch"
    if "xbox" in name_lower:
        return "Xbox"
    if re.search(r"\bps[245]?\b|\bplaystation\b", name_lower):
        return "PlayStation"

    return ""


def extract_product(driver: webdriver.Chrome, product_id: str) -> Dict[str, Any]:
    product_data = get_json_ld(driver, "Product")
    offers = product_data.get("offers", {})
    name = product_data.get("name", "")
    discount_price = currency_to_int(offers.get("price"))

    page_text = driver.find_element(By.TAG_NAME, "body").text
    savings = find_money(page_text, r"ahorro\s+real\s*:\s*\$?\s*([\d.]+)")
    discount_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*%\s*(?:bajo|de descuento)",
        page_text,
        flags=re.IGNORECASE,
    )
    discount = (
        float(discount_match.group(1).replace(",", "."))
        if discount_match
        else None
    )
    if discount is not None and discount.is_integer():
        discount = int(discount)

    # Knasta presents the current price, the real saving, and the percentage
    # below the usual price in the rendered detail page.
    price = discount_price + savings if discount_price is not None and savings else discount_price
    usual_price = price
    if discount_price is not None and discount is not None and discount < 100:
        usual_price = round(discount_price / (1 - discount / 100))

    best_price = find_money(
        page_text,
        r"(?:mejor\s+precio|precio\s+mínimo|precio\s+más\s+bajo)"
        r"\s*:\s*\$?\s*([\d.]+)",
    )

    return {
        "id": product_id,
        "name": name,
        "price": price,
        "console": infer_console(name),
        "usual_price": usual_price,
        "best_price": best_price,
        "discount": discount,
        "discount_price": discount_price,
        "image": product_data.get("image"),
    }


def get_product_urls(driver: webdriver.Chrome, wait: WebDriverWait) -> List[str]:
    driver.get(RESULTS_URL)
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        )
    )

    search_data = get_json_ld(driver, "SearchResultsPage")
    entries = search_data.get("mainEntity", {}).get("itemListElement", [])

    return [
        entry["item"]["url"]
        for entry in entries
        if entry.get("item", {}).get("url")
    ]


def main() -> None:
    chrome_options = ChromeOptions()
    # Uncomment to run without opening a browser window:
    # chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options,
    )
    wait = WebDriverWait(driver, 15)
    product_urls: List[str] = []
    products: List[Dict[str, Any]] = []

    try:
        product_urls = get_product_urls(driver, wait)
        print(f"Product URLs found: {len(product_urls)}")

        for product_url in product_urls:
            driver.get(product_url)
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                )
            )

            product_id = product_url.rstrip("/").split("/")[-2]
            products.append(extract_product(driver, product_id))

        print(json.dumps(products, indent=2, ensure_ascii=False))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
