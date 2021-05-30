import json
import datetime
from concurrent import futures
from requests.exceptions import ReadTimeout
import time
from itertools import combinations
from woocommerce import API


with open("credentials.json", "r") as file:
    creds = json.loads(file.read())["WC"]
    shops = {}
    for shop in creds:
        shops[shop] = API(
            url=creds[shop]["url"],
            consumer_key=creds[shop]["consumer_key"],
            consumer_secret=creds[shop]["consumer_secret"],
            wp_api=True,
            version="wc/v3",
            timeout=20
            )


class get_all_orders():
    def __init__(self, shop, *args, **kwargs):
        """
        Gets all available orders from a shop and saves them in a json file. 
        Every order object gets a new field called "website", in which the URL
        to the shop is saved.

        Parameters:

        - `shops`: A list of woocommerce API objects is expected.
        """
        self.orders = []

        self.shop = shop
        self.response = shops[self.shop].get("orders?after=2020-05-31T23:59:00Z&per_page=100").headers
        self.pages = int(self.response["X-WP-TotalPages"])
        print(f"Retrieving {self.pages} pages from {shop}")

        self.request_all_orders()
        
        self.save()

    def get_page(self, page):
        while True:
            try:
                response = shops[self.shop].get(f"orders?per_page=100&page={page}")
                print(f"Page {page}: {response}, {len(response.json())} Orders")
                return response.json()

            except ReadTimeout:
                print(f"Page {page} timed out")

    def request_all_orders(self):
        with futures.ThreadPoolExecutor(max_workers=6) as executor:
            self.results = executor.map(self.get_page, range(1, self.pages + 1))

        requested_orders = []
        for result in self.results:
            for i in range(len(result)):
                result[i]["website"] = self.shop
            requested_orders.extend(result)

        self.orders.extend(requested_orders)

    def save(self):
        print(f"Retrieved {len(self.orders)} orders")

        with open(f"orders-{self.shop}.json", "w") as jsonfile:
            jsonfile.write(json.dumps(self.orders))

taxrates = {}
for shop in shops:
    get_all_orders(shop)
    tax_response = shops[shop].get("taxes?per_page=100").json()
    taxrates[shops[shop].url] = {tax["id"]: tax for tax in tax_response}

with open("taxrates.json", "w+") as file:
    file.write(json.dumps(taxrates))