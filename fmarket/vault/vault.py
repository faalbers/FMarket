from .catalog import Catalog

from pprint import pp

class Vault():
    def __init__(self):
        self.catalog = Catalog()

    def get_data(self, catalog, key_values=[]):
        catalog = self.catalog.get(catalog)

        data = {}
        for scraper_class, scraper_data in catalog.items():
            scraper = scraper_class()
            for data_name, columns in scraper_data.items():
                data[scraper_class.__name__+':'+data_name] = scraper.get_vault_data(data_name, columns, key_values)
        return data
    