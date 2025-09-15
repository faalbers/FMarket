import logging
import logging.handlers
import multiprocessing
import time
from random import choice

# --- Configuration ---
LOG_FILE_NAME = "multiprocess_session.log"
LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(processName)s] %(message)s"
SENTINEL = None # Special message to stop the listener


def setup_worker_logger(queue):
    """Sets up the QueueHandler for a worker process."""
    # This logger is only for the worker process and sends records to the queue.
    handler = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def listener_process(queue, configurer):
    """
    Listens for log messages from the queue and writes them to a file.
    Runs in a dedicated process.
    """
    configurer() # Set up the actual file handler here
    while True:
        try:
            record = queue.get()
            if record is SENTINEL:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception as e:
            print(f"Error handling log record: {e}", file=sys.stderr)
            break
    # Flush and close the file handler before exiting
    for handler in logging.getLogger().handlers:
        handler.close()


def worker_task(queue, worker_id):
    """
    The function executed by each worker process.
    Logs messages using the queue handler.
    """
    setup_worker_logger(queue)
    logger = logging.getLogger(f"Worker-{worker_id}")

    for _ in range(5):
        logger.info(f"Task message from worker {worker_id}")
        time.sleep(choice([0.1, 0.2, 0.3]))


def run_logging_session(worker_count=3):
    """
    Sets up and runs a complete logging session.
    """
    print(f"--- Starting new logging session ---")
    print(f"Logs will be written to {LOG_FILE_NAME}")

    # 1. Create the queue and listener process
    queue = multiprocessing.Queue(-1)
    listener = multiprocessing.Process(
        target=listener_process,
        args=(queue, lambda: setup_file_handler(LOG_FILE_NAME)),
    )
    listener.start()

    # 2. Start the worker processes
    workers = []
    for i in range(worker_count):
        worker = multiprocessing.Process(
            target=worker_task, args=(queue, i + 1)
        )
        workers.append(worker)
        worker.start()

    # 3. Wait for all workers to finish
    for worker in workers:
        worker.join()
    
    # 4. Shut down the listener gracefully
    queue.put(SENTINEL)
    listener.join()
    
    print("--- Logging session finished ---")


def setup_file_handler(log_file):
    """
    Configures the file handler for the listener process.
    This function is only called inside the listener process.
    """
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setFormatter(formatter)

    # Apply the handler to the root logger in this specific process
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    

if __name__ == "__main__":
    import sys

    # Multiple sessions can be run sequentially
    run_logging_session(worker_count=2)
    time.sleep(2)
    run_logging_session(worker_count=3)