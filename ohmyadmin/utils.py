import inspect
import typing
from starlette.concurrency import run_in_threadpool


async def run_async(fn: typing.Callable, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
    """
    Awaits a function.

    Will convert sync to async callable if needed.
    """
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    return await run_in_threadpool(fn, *args, **kwargs)
