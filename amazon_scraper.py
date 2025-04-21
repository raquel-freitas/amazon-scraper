import asyncio
from playwright.async_api import async_playwright
import boto3
import os
import csv
from io import StringIO
from datetime import datetime

BUCKET_NAME = os.environ.get("BUCKET_NAME")
S3_FILE_KEY = os.environ.get("S3_FILE_KEY", "product_prices.csv")

PRODUCT_URL = "https://www.amazon.com.br/dp/B009UKJ5RK"
TARGET_VARIANT_ALT = "30ml"
PRICE_SELECTOR = ".a-price .a-offscreen"
AVAILABILITY_SELECTOR = "span#twisterAvailability"

from playwright.async_api import async_playwright
import asyncio
import csv
from datetime import datetime
from io import StringIO
import boto3

# Configuration
BUCKET_NAME = "amazon-price-tracker-estagio"
S3_FILE_KEY = "product_prices.csv"
PRODUCT_URL = "https://www.amazon.com.br/dp/B009UKJ5RK"
TARGET_VARIANT_ALT = "30ml"
PRICE_SELECTOR = ".a-price .a-offscreen"
AVAILABILITY_SELECTOR = "span#twisterAvailability"

async def scraper():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to product page...")
        await page.goto(PRODUCT_URL, wait_until="load", timeout=60000)
        await page.set_viewport_size({"width": 1280, "height": 800})

        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
        except TimeoutError:
            print("Timeout while waiting for network idle. Proceeding anyway.")

        # Initialize default values
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_found = "N/A"

        # Locate product variant by image alt text
        variant_img = page.locator(f'img[alt="{TARGET_VARIANT_ALT}"]')

        if await variant_img.count() == 0:
            print(f"Variant '{TARGET_VARIANT_ALT}' not found.")
        else:
            parent_li = variant_img.locator("xpath=ancestor::li")
            availability = await parent_li.locator(AVAILABILITY_SELECTOR).inner_text()

            if "Não disponível" in availability:
                print("Product is not available.")
            else:
                try:
                    await page.wait_for_selector(PRICE_SELECTOR, timeout=10000)
                    price_text = await page.locator(PRICE_SELECTOR).first.inner_text()
                    price_found = price_text
                    print(f"Product price found: {price_text}")
                except Exception as e:
                    print("Failed to retrieve price:", e)

        await browser.close()

        # # Upload or update CSV in S3
        # s3 = boto3.client("s3")
        # print("Saving price to S3...")

        # try:
        #     response = s3.get_object(Bucket=BUCKET_NAME, Key=S3_FILE_KEY)
        #     csv_content = response["Body"].read().decode("utf-8")
        #     price_rows = list(csv.reader(StringIO(csv_content)))
        # except s3.exceptions.NoSuchKey:
        #     price_rows = [["timestamp", "price"]]  # Initialize CSV header

        # price_rows.append([timestamp, price_found])

        # csv_buffer = StringIO()
        # writer = csv.writer(csv_buffer)
        # writer.writerows(price_rows)

        # s3.put_object(Bucket=BUCKET_NAME, Key=S3_FILE_KEY, Body=csv_buffer.getvalue())
        # print(f"Saved: {timestamp}, {price_found}")

if __name__ == "__main__":
    asyncio.run(scraper())
