import os
import re
from time import sleep
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import json

def extract_price(product_price):
    price_match = re.match(r'([A-Z]+)?[\s$€£¥]*([\d,.]+)', product_price)

    if price_match:
        currency_code = price_match.group(1) if price_match.group(1) else "USD"
        numerical_value = float(price_match.group(2).replace(',', ''))

        return currency_code, numerical_value
    else:
        print("Error: Unable to extract price information.")
        return None, None


def clean_filename(filename):
    invalid_chars = r'\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def download_image(url, save_path):
    if not url.startswith('http'):
        url = 'https:' + url
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        os.makedirs("images", exist_ok=True)        
        image_filename = clean_filename(os.path.basename(urlparse(url).path))
        save_path = os.path.join("images", image_filename)
        with open(save_path, 'wb') as image_file:
            for chunk in response.iter_content(chunk_size=128):
                image_file.write(chunk)
    else:
        print(f"Failed to download image from {url}")

def scrape_category(url, download_images=True):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')

    category_data = []
    li_elements = soup.select('.subcategory-view-icons.subcategory-list.grid-list li')[:5]

    for li in li_elements:
        category_url = li.select_one("a")['href']
        category_img_url = li.select_one('img')['src']
        category_name = li.select_one('.subcategory-name').text
        print(category_name)

        subcategories = scrape_subcategories("https://almeera.online/" + category_url, download_images)

        category_data.append({
            "CategoryTitle": category_name,
            "CategoryImageURL": category_img_url,
            "Subcategories": subcategories
        })

        sleep(5)

    return category_data

def scrape_subcategories(url, download_images=True):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')

    subcategory_data = []
    li_elements = soup.select('.subcategory-view-icons.subcategory-list.grid-list li')

    for sub_li in li_elements:
        sub_url = sub_li.select_one("a")['href']
        subcategory_name = sub_li.select_one('.subcategory-name').text
        print(subcategory_name)

        products = scrape_products("https://almeera.online/" + sub_url, download_images)

        subcategory_data.append({
            "SubcategoryTitle": subcategory_name,
            "Products": products
        })

        sleep(5)

    return subcategory_data

def scrape_products(url, download_images=True):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')

    products_data = []
    li_elements = soup.select('.products-grid li.product-cell')[:5]

    for pro_li in li_elements:
        product_name_tag = pro_li.find('h5', class_='product-name')
        product_name = product_name_tag.text.strip() if product_name_tag else None

        product_image_tag = pro_li.find('img', class_='photo')
        product_image_url = product_image_tag['src'] if product_image_tag and 'src' in product_image_tag.attrs else None

        product_price_tag = pro_li.find('li', class_='product-price-base')
        if product_price_tag:
            product_price = product_price_tag.text.strip()
            currency_code, numerical_value = extract_price(product_price)

            if currency_code is not None and numerical_value is not None:
                products_data.append({
                    "ItemTitle": product_name,
                    "ItemImageURL": product_image_url,
                    "ItemPrice": str(numerical_value),
                    "ItemBarcode": currency_code
                })

                if download_images and product_image_url:
                    image_filename = f"{product_name}.jpg"  
                    download_image(product_image_url, image_filename)

        else:
            print("Error: Product price not found on the webpage.")

    return products_data

URL = "https://almeera.online/"
json_data = scrape_category(URL, download_images=True)

with open('output.json', 'w') as json_file:
    json.dump(json_data, json_file, indent=2)
