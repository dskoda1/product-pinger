from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from twilio.rest import Client
from dataclasses import dataclass
import time
import os
import logging
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('gpu.inventory.stocker')


def get_current_cards():
    driver = webdriver.Firefox()
    driver.get('https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&qp=chipsetmanufacture_facet%3DChipset%20Manufacturer~NVIDIA%5Ecurrentprice_facet%3DPrice~599%20to%201400&st=gpus')
    cards = []
    try:
        buttons = driver.find_elements(by=By.CLASS_NAME, value='add-to-cart-button')
        titles = driver.find_elements(by=By.CLASS_NAME, value='sku-header')
        cards = list(zip(buttons, titles))
        cards = [
            Card(
                is_enabled=card[0].is_enabled(),
                name=card[1].text.lower(),
                link=card[1].find_element(By.TAG_NAME, 'a').get_attribute('href')
            ) for card in cards
        ]
        blacklist = [
            'single fan',
            '1660',
            '1030',
        ]
        # cards = [card for card in cards if 'nvidia' in card.name]
        cards = [card for card in cards if not any(bl_str in card.name for bl_str in blacklist)]
    except Exception:
        logger.exception("failed loading cards")
    finally:
        driver.quit()
    return cards


@dataclass
class Card:
    is_enabled: bool
    name: str
    link: str


def send_text(message: str):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(to='18456490743', from_='+18632926145', body=message)

if __name__ == '__main__':

    while True:
        logger.info("waking up")
        try:
            cards = get_current_cards()
            for card in cards:
                logger.info(f"Card details: is_enabled={card.is_enabled}, name={card.name}, link={card.link}")
                if card.is_enabled and 'nvidia' in card.name:
                    send_text(f"\n\nA nvidia GPU is in stock:\n\n"
                              f"{card.name}\n\n"
                              f"{card.link}")
        except Exception:
            logger.exception("failed loop")
        logger.info("going to sleep")
        time.sleep(30)