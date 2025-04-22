import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import gspread
import json
import base64
import os
from oauth2client.service_account import ServiceAccountCredentials

PRODUCT_URL = "https://www.amazon.com.br/dp/B009UKJ5RK"
TARGET_VARIANT_ALT = "30ml"
PRICE_SELECTOR = ".a-price .a-offscreen"
AVAILABILITY_SELECTOR = "span#twisterAvailability"
SHEET_ID = "1jD-7a2mBkyXWOxE0KE3aCA7FJAbPBaUmxCrv0YOkCJU"
SHEET_NAME = "Página1"

def append_to_google_sheets(timestamp, price_found):
    print("Saving to Google Sheets")

    creds_json = base64.b64decode(os.environ["GOOGLE_CREDENTIALS_BASE64"]).decode("utf-8")
    creds_dict = json.loads(creds_json)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    sheet.append_row([timestamp, price_found])

    print(f"Salvo: {timestamp}, {price_found}")

async def scraper():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Getting product page")
        await page.goto(PRODUCT_URL, wait_until="load", timeout=60000)
        await page.set_viewport_size({"width": 1280, "height": 800})

        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
        except TimeoutError:
            print("Timeout")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_found = "N/A"

        variant_img = page.locator(f'img[alt="{TARGET_VARIANT_ALT}"]')

        if await variant_img.count() == 0:
            print(f"'{TARGET_VARIANT_ALT}' not found")
        else:
            parent_li = variant_img.locator("xpath=ancestor::li")
            availability = await parent_li.locator(AVAILABILITY_SELECTOR).inner_text()

            if "Não disponível" in availability:
                print("Product unavailable.")
            else:
                try:
                    await page.wait_for_selector(PRICE_SELECTOR, timeout=10000)
                    price_text = await page.locator(PRICE_SELECTOR).first.inner_text()
                    price_found = price_text
                    print(f"Price found: {price_text}")
                except Exception as e:
                    print("Error", e)

        await browser.close()
        append_to_google_sheets(timestamp, price_found)

if __name__ == "__main__":
    asyncio.run(scraper())
