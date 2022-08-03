import jsonpickle
import requests
import util
from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup
from datetime import datetime
from listing import Listing

class BaseCrawler(object, metaclass = ABCMeta):
    MAX_HISTORY = 500

    HEADERS = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    @abstractmethod
    def __init__(self, query, category, min_price, max_price, ignored):
        self.query = query
        self.category = category
        self.min_price = min_price
        self.max_price = max_price
        self.ignored = ignored
        self.__saved_listings = []
        self.__saved_pinned = []

    """Internal method. Do not use."""
    @abstractmethod
    def category_adapter(self, cat: str) -> str:
        pass

    """Internal method. Do not use."""
    @abstractmethod
    def pinned_link_callable(self, link):
        pass

    @abstractmethod
    def retrieve_listings(self) -> list[Listing]:
        pass

    """
    Template method.
    """
    def crawl(self) -> list[Listing]:
        listings = self.retrieve_listings()
        # TODO Delegate filtering to the caller?
        filtered_listings = [
            listing for listing in listings 
            if listing.is_not_sold and ("" in self.ignored or not any(term in listing.url for term in self.ignored))
        ]

        new_listings = util.difference(filtered_listings, self.__saved_listings)
        self.__saved_listings += new_listings
        self.__saved_listings = util.trim(self.__saved_listings, self.MAX_HISTORY)

        return new_listings

class SubitoCrawler(BaseCrawler):
    URL_PART1 = "https://www.subito.it/annunci-italia/vendita/"
    URL_QUERY = "/?q="
    URL_MIN_PRICE = "&ps="
    URL_MAX_PRICE = "&pe="

    CATEGORIES = {
        "games": "videogiochi"
    }

    ITEM_CARD_CLASS = ".item-card"
    LINK_CLASS = ".link"
    PRICE_CLASS = ".price"
    PINNED_CLASS = ".PostingTimeAndPlace-module_vetrina-badge__XWWCm"
    SOLD_CLASS = ".item-sold-badge"
    PINNED_TIME_CLASS = ".index-module_insertion-date__MU4AZ"

    def __init__(self, query, category, min_price, max_price, ignored):
        super().__init__(query, category, min_price, max_price, ignored)
        self.url: str = (
            self.URL_PART1 + 
            self.category_adapter(self.category) + 
            self.URL_QUERY + self.query.replace(" ", "+") + 
            self.URL_MIN_PRICE + self.min_price + 
            self.URL_MAX_PRICE + self.max_price
        )

    # TODO
    def pinned_link_callable(link):
        pass
    
    def category_adapter(self, cat):
        return self.CATEGORIES[cat]

    def retrieve_listings(self):
        page = requests.get(self.url, headers = self.HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")

        item_cards = soup.select(self.ITEM_CARD_CLASS)
        return [
            Listing(
                url = card.select_one(self.LINK_CLASS)['href'], 
                price = card.select_one(self.PRICE_CLASS).text.split("€")[0], 
                is_not_sold = card.select_one(self.SOLD_CLASS) is None,
                is_not_pinned = card.select_one(self.PINNED_CLASS) is None
            )
            for card in item_cards
            if card.select_one(self.PINNED_CLASS) is None # TODO Handle pinned listings in a proper way
        ]

class WallapopCrawler(BaseCrawler):
    URL_BASE = "https://api.wallapop.com/api/v3/general/search"
    URL_QUERY = "?keywords="
    URL_CATEGORY = "&category_ids="
    URL_MID = "&filters_source=quick_filters"
    URL_MIN_PRICE = "&min_sale_price="
    URL_MAX_PRICE = "&max_sale_price="
    URL_SORT_NEWEST = "&order_by=newest"

    LISTING_BASE_URL = "https://wallapop.com/item/"

    CATEGORIES = {
        "games": "12900"
    }

    LISTING_MAX_AGE_S = 10800.0

    def __init__(self, query, category, min_price, max_price, ignored):
        super().__init__(query, category, min_price, max_price, ignored)
        self.url: str = (
            self.URL_BASE + 
            self.URL_QUERY + self.query.replace(" ", "+") + 
            self.URL_CATEGORY + self.category_adapter(self.category) + 
            self.URL_MID +
            self.URL_MIN_PRICE + self.min_price + 
            self.URL_MAX_PRICE + self.max_price +
            self.URL_SORT_NEWEST
        )

    def pinned_link_callable(link):
        pass

    def category_adapter(self, cat):
        return self.CATEGORIES[cat]

    def retrieve_listings(self):
        page = requests.get(self.url, headers = self.HEADERS)
        search_objects = jsonpickle.decode(page.content)["search_objects"]

        return [
            Listing(
                url = self.LISTING_BASE_URL + item["web_slug"], 
                price = item["price"],
                is_not_sold = not bool(item["flags"]["sold"]), 
                is_not_pinned = True
            ) 
            for item in search_objects
            if (datetime.now().timestamp() - float(item["modification_date"]) / 1000) <= self.LISTING_MAX_AGE_S
        ]

class EbayCrawler(BaseCrawler):
    URL_PART1 = "https://www.ebay."
    URL_PART2 = "/sch/"
    URL_PART3 = "i.html"
    URL_QUERY = "?_nkw="
    URL_MIN_PRICE = "&_udlo="
    URL_MAX_PRICE = "&_udhi="
    URL_BUY_NOW_ONLY = "&LH_BIN=1"
    URL_NEWEST = "&_sop=10"
    URL_EU_ONLY = "&LH_PrefLoc=3"

    CATEGORIES = {
        "games": "1249/",
        "": ""
    }

    ITEM_CARD_CLASS = ".s-item"
    LINK_CLASS = ".s-item__link"
    PRICE_CLASS = ".s-item__price"
    TITLE_CLASS = ".s-item__title"
    SHIPPING_CLASS = ".s-item__shipping"
    HIGHLIGHT_CLASS = ".LIGHT_HIGHLIGHT"

    def __init__(self, query, category, min_price, max_price, ignored, locale: str):
        super().__init__(query, category, min_price, max_price, ignored)

        ignored_keywords = "+-" + "+-".join(ignored)

        self.url: str = (
            self.URL_PART1 + locale + 
            self.URL_PART2 + 
            self.category_adapter(self.category) + 
            self.URL_PART3 + 
            self.URL_QUERY + self.query.replace(" ", "+") + ignored_keywords + 
            self.URL_MIN_PRICE + self.min_price + 
            self.URL_MAX_PRICE + self.max_price + 
            self.URL_BUY_NOW_ONLY + 
            self.URL_NEWEST + 
            self.URL_EU_ONLY
        )

    def pinned_link_callable(link):
        pass
    
    def category_adapter(self, cat):
        return self.CATEGORIES[cat]

    def retrieve_listings(self):
        page = requests.get(self.url, headers = self.HEADERS)
        soup = BeautifulSoup(page.content, "html.parser")

        item_cards = soup.select(self.ITEM_CARD_CLASS)
        return [
            Listing(
                url = card.select_one(self.LINK_CLASS)['href'].split("?")[0],
                # We want to strip the "New listing" tag from all the titles, if present.
                title = card.select_one(self.TITLE_CLASS).text[len(util.tag_coalesce(card.select_one(self.HIGHLIGHT_CLASS), "")):],
                price = card.select_one(self.PRICE_CLASS).text.split("€")[0],
                shipping_cost = util.tag_coalesce(card.select_one(self.SHIPPING_CLASS), ""),
                is_not_sold = True,
                is_not_pinned = True
            )
            for card in item_cards
        ]
