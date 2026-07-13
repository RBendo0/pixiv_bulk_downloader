from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import BoundedSemaphore
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class ThreadPoolSystem:

    def __init__(
        self,
        *,
        workers: int = 8,
        queue: int = 8,
        thread_name_prefix: str = "PBD-TPS",
    ) -> None:

        workers = max(workers, 8)
        queue = max(queue, 8)

        self.max_workers = workers
        self.max_tasks = workers + queue

        self._executor = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix=thread_name_prefix,
        )

        self._semaphore = BoundedSemaphore(
            self.max_tasks
        )

    def _release_capacity(
        self,
        future: Future[Any],
    ) -> None:

        self._semaphore.release()

    def submit(
        self,
        function: Callable[P, R],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Future[R]:

        self._semaphore.acquire()

        try:

            future = self._executor.submit(
                function,
                *args,
                **kwargs,
            )

        except BaseException:

            self._semaphore.release()

            raise

        future.add_done_callback(
            self._release_capacity
        )

        return future

    def shutdown(
        self,
        *,
        wait: bool = True,
        cancel_futures: bool = False,
    ) -> None:

        self._executor.shutdown(
            wait=wait,
            cancel_futures=cancel_futures,
        )


# Alias della classe Thread Pool System.
TPS = ThreadPoolSystem