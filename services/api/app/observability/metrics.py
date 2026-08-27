from time import perf_counter

class Timer:
    def __init__(self) -> None:
        self.started_at = perf_counter()

    @property
    def elapsed_ms(self) -> float:
        return (perf_counter() - self.started_at) * 1000
