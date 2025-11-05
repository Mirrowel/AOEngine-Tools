import logging
from queue import Queue

log_queue: "Queue[str]" = Queue()
log_history: list[str] = []


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")

    class QueueHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            message = self.format(record)
            log_queue.put(message)
            log_history.append(message)

    handler = QueueHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(handler)
