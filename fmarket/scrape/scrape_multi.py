import logging.handlers
import multiprocessing, logging, sys
from .scrapers import *
from pprint import pp

class Scrape_Multi():
    def __init__(self, scrapers):
        scraper_classes_data = {FMP: [], Polygon: []}
        for scraper in scrapers:
            scraper_class = scraper[0]
            key_values = scraper[1]
            for sub_class, scraper_class_data in scraper_classes_data.items():
                if issubclass(scraper_class, sub_class):
                    scraper_class_data.append((scraper_class, key_values))

        # create multi chunks for pool
        multi_chunks = []
        for sub_class, scraper_classes in scraper_classes_data.items():
            # creat multi chunk per sub_class
            update_scrapers = []
            for scraper_class, key_values in scraper_classes:
                if not scraper_class in update_scrapers:
                    update_scrapers.append(scraper_class)
            if len(update_scrapers) > 0:
                multi_chunks.append((sub_class.__name__, update_scrapers, key_values))

        # start logger queue process for multi chunks
        self.queue = multiprocessing.Queue(-1)
        listener = multiprocessing.Process(target=self.queue_process, args=(len(multi_chunks),))
        listener.start()

        # run scrapes in multi thread
        if len(multi_chunks) == 0: return
        processes = []
        for chunk in multi_chunks:
            p = multiprocessing.Process(target=self.update_scrapers, args=chunk)
            processes.append(p)
            p.start()
        for p in processes:
            p.join()

        # stop logger queue process
        self.queue.put(None)
        listener.join()

    def queue_process(self, threads):
        formatter = logging.Formatter('%(asctime)s: %(name)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler = logging.FileHandler('scrape.log', mode='w')
        file_handler.setFormatter(formatter)

        # Apply the handler to the root logger in this specific process
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(file_handler)
        root.info('Run scrapes in %s threads' % threads)
        while True:
            try:
                record = self.queue.get()
                if record is None:
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except Exception as e:
                print(f"Error handling log record: {e}", file=sys.stderr)
                break
        # Flush and close the file handler before exiting
        root.info('End scrapes')
        for handler in logging.getLogger().handlers:
            handler.close()
    
    def update_scrapers(self, sub_class, update_scrapers, key_values):
        handler = logging.handlers.QueueHandler(self.queue)
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.INFO)

        for scraper_class in update_scrapers:
            scraper_class().scrape_data(key_values=key_values)

