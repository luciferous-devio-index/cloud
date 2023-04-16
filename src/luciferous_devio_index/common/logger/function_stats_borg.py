import statistics


class FunctionDurationStatsBorg(object):
    _shared_state = {}

    def __new__(cls):
        ob = super().__new__(cls)
        ob.__dict__ = cls._shared_state
        return ob

    def append(self, logger_name: str, function_name: str, duration: float):
        map_logger: dict = self._shared_state.get(logger_name, {})
        list_function: list = map_logger.get(function_name, [])
        list_function.append(duration)
        map_logger[function_name] = list_function
        self._shared_state[logger_name] = map_logger

    def get_stats(self) -> dict:
        return {
            logger_name: {
                function_name: {
                    "len": len(list_function),
                    "max": max(list_function),
                    "min": min(list_function),
                    "avg": statistics.mean(list_function),
                    "med": statistics.median(list_function),
                }
                for function_name, list_function in map_logger.items()
            }
            for logger_name, map_logger in self._shared_state.items()
        }
