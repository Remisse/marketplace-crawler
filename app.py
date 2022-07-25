import apprise
import sys
import time
from colorama import Fore, Style, init
from crawler import BaseCrawler, SubitoCrawler, WallapopCrawler
from datetime import datetime
from threading import Thread, Event

APP_NAME = "Marketplace Crawler"

SLEEP_S = 30

def log_timestamp(message: str):
    time = datetime.now().strftime("%H:%M")
    print(f"[{time}] {message}")

def crawler_callable(crawler: BaseCrawler, new_found_event: Event, keyboard_interrupt_event: Event):
    text_color = None
    if isinstance(crawler, SubitoCrawler):
        text_color = Fore.YELLOW
    elif isinstance(crawler, WallapopCrawler):
        text_color = Fore.LIGHTGREEN_EX

    while not keyboard_interrupt_event.is_set():
        listings = crawler.crawl()

        if len(listings) > 0:
            log_timestamp("")
            for listing in listings:
                print(f"{text_color}    {listing.url}{Fore.WHITE} {str(int(listing.price))}€")
            print(Style.RESET_ALL)

            if not new_found_event.is_set():
                new_found_event.set()

        time.sleep(SLEEP_S)

if __name__ == "__main__":
    # Required on Windows by Colorama
    init()

    # TODO Support more servers?
    apobj = apprise.Apprise()
    apobj.add("dbus://")
    apobj.add("windows://")

    # TODO Improve parsing of launch arguments
    parameters = sys.argv[1:]
    if (len(parameters) != 5):
        print('Usage: python ' + sys.argv[0] + ' "<search_term_1> ... <search_term_n>" <category> <minimum_price> <maximum_price> "<ignore_term_1> ... <ignore_term_n>"')
        exit(1)

    search = parameters[0]
    category = parameters[1]
    min_price = parameters[2]
    max_price = parameters[3]
    ignored = parameters[4].split(sep = " ")

    # Creates a Lock object automatically
    new_found_event = Event()
    keyboard_interrupt_event = Event()

    # TODO Let the user choose which crawlers to enable by providing ad-hoc launch arguments
    crawlers = (
        SubitoCrawler(search, category, min_price, max_price, ignored),
        WallapopCrawler(search, category, min_price, max_price, ignored)
    )

    threads = []
    for crawler in crawlers:
        new_thread = Thread(target = crawler_callable, args = (crawler, new_found_event, keyboard_interrupt_event, ))
        new_thread.start()
        threads.append(new_thread)

    try:
        while True:
            new_found_event.wait()
            apobj.notify(f'New listings for "{search}"!', "Check your terminal.")
            new_found_event.clear()
    except KeyboardInterrupt:
        print(f"\nAttempting to terminate all threads. This can take up to {SLEEP_S} seconds.")
        keyboard_interrupt_event.set()
        for thread in threads:
            thread.join()
        print(f"{APP_NAME}: exited.")