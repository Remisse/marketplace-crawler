class Listing(object):
    def __init__(self, url, price, is_not_sold, is_not_pinned):
        self.url = url
        self.price = price
        self.is_not_sold = is_not_sold
        self.is_not_pinned = is_not_pinned

    def __eq__(self, other):
        if isinstance(other, Listing):
            return self.url == other.url
        return False