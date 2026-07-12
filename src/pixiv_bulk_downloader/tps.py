from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class DownloadPool:

    MAX_WORKERS = 16

    _lock = Lock()
    _executor: ThreadPoolExecutor | None = None

    @classmethod
    def _get_executor(cls) -> ThreadPoolExecutor:

        if cls._executor is not None:
            return cls._executor

        with cls._lock:

            if cls._executor is None:

                cls._executor = ThreadPoolExecutor(
                    max_workers=cls.MAX_WORKERS,
                    thread_name_prefix="PBD-Download",
                )

            return cls._executor

    @classmethod
    def submit(
        cls,
        function: Callable[P, R],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Future[R]:

        executor = cls._get_executor()

        return executor.submit(
            function,
            *args,
            **kwargs,
        )

    @classmethod
    def shutdown(cls) -> None:

        with cls._lock:

            executor = cls._executor
            cls._executor = None

        if executor is not None:

            executor.shutdown(
                wait=True,
                cancel_futures=False,
            )