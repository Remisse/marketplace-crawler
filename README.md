# marketplace-crawler

Simple bot that monitors marketplaces available in Europe and notifies you of new listings as they are published.

## Supported marketplaces

- Ebay
- Subito (IT)
- Wallapop (ES, IT)
- Vinted

## Dependencies

- [Apprise](https://github.com/caronc/apprise)
- [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/)
- [Colorama](https://github.com/tartley/colorama)
- [jsonpickle](https://jsonpickle.github.io/)
- [requests](https://requests.readthedocs.io/en/latest/)

## TODO

- [ ] More categories
- [ ] Improve parsing of launch arguments
- [ ] Let the user choose which crawlers to enable by providing ad-hoc launch arguments
- [ ] Config file
- [ ] Read Apprise configuration from file
- [x] Vinted support
