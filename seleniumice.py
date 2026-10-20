import json
import re
from typing import Any, Dict, List, Optional

from config import database, models
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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
BEST_PRICE_TIMEOUT_SECONDS = 0.5


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

    if "xbox" in name_lower:
            return "xbox"
    elif "switch" in name_lower:
        return "switch"
    elif re.search(r"\bps[245]?\b|\bplaystation\b", name_lower):
        return "playstation"
    else:
        return ""


def first_image_url(image: Any) -> Optional[str]:
        if isinstance(image, str):
            return image
        if isinstance(image, list):
            return next((item for item in image if isinstance(item, str)), None)
        return None


def get_previous_price(driver: webdriver.Chrome) -> Optional[int]:
    previous_price_xpath = (
        '//*[@id="body-principal"]/main/article/div[2]/section/div[2]/'
        "div[2]/div/span[2]"
    )
    previous_price_elements = driver.find_elements(By.XPATH, previous_price_xpath)
    if not previous_price_elements:
        return None

    return currency_to_int(previous_price_elements[0].text)


def get_best_price(driver: webdriver.Chrome) -> Optional[int]:
    history_tab = driver.find_elements(By.ID, "price-history-tab")
    if history_tab:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            history_tab[0],
        )
        if history_tab[0].get_attribute("aria-selected") != "true":
            history_tab[0].click()

    best_price_xpath = (
        '//*[@id="price-history-panel"]/div/div[2]/div/div/div[1]/'
        "div/div[4]/div[1]/div[2]/div[2]"
    )
    try:
        best_price_text = WebDriverWait(
            driver, BEST_PRICE_TIMEOUT_SECONDS
        ).until(
            lambda current_driver: next(
                (
                    text
                    for element in current_driver.find_elements(
                        By.XPATH, best_price_xpath
                    )
                    for text in [element.get_attribute("textContent").strip()]
                    if text
                ),
                False,
            )
        )
    except TimeoutException:
        return None

    best_price = currency_to_int(best_price_text)
    return best_price


def extract_product(driver: webdriver.Chrome, product_id: str) -> Dict[str, Any]:
    product_data = get_json_ld(driver, "Product")
    offers = product_data.get("offers", {})
    name = product_data.get("name", "")
    discount_price = currency_to_int(offers.get("price"))

    price = get_previous_price(driver)
    best_price = get_best_price(driver)
    page_text = driver.find_element(By.TAG_NAME, "body").text
    discount_match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*%\s*(?:bajo|de descuento)",
        page_text,
        flags=re.IGNORECASE,
    )
    discount: Optional[float] = (
        float(discount_match.group(1).replace(",", "."))
        if discount_match
        else None
    )
    if discount is not None and discount.is_integer():
        discount = int(discount)

    usual_price = find_money(
        page_text,
        r"precio\s+habitual\s*\$?\s*(\d[\d.]*)",
    )
    if (
        usual_price is None
        and discount_price is not None
        and discount is not None
        and discount < 100
    ):
        usual_price = round(discount_price / (1 - discount / 100))
    if usual_price is None:
        usual_price = None

    return {
        "id": product_id,
        "name": name,
        "price": price,
        "console": infer_console(name),
        "usual_price": usual_price,
        "best_price": best_price,
        "discount": discount,
        "discount_price": discount_price,
        "image": first_image_url(product_data.get("image")),
    }


def save_products(products: List[Dict[str, Any]]) -> None:
    database.Base.metadata.create_all(bind=database.engine)
    with database.engine.begin() as connection:
        connection.exec_driver_sql(
            "ALTER TABLE games "
            "MODIFY COLUMN id BIGINT NOT NULL AUTO_INCREMENT"
        )

    db = database.SessionLocal()

    try:
        for product in products:
            product_id = currency_to_int(product.get("id"))
            if product_id is None:
                raise ValueError(f"Invalid product id: {product.get('id')!r}")

            game = db.get(models.Game, product_id)
            values = {
                "id": product_id,
                "name": product["name"],
                "price": product["price"],
                "platform": product["console"],
                "usual_price": product["usual_price"],
                "best_price": product["best_price"],
                "discount": product["discount"],
                "discount_price": product["discount_price"],
                "image": first_image_url(product.get("image")),
            }

            if game is None:
                db.add(models.Game(**values))
            else:
                for field, value in values.items():
                    setattr(game, field, value)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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
    chrome_options.page_load_strategy = "eager"
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

        save_products(products)
        print(f"Products saved to database: {len(products)}")
        print(json.dumps(products, indent=2, ensure_ascii=False))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
