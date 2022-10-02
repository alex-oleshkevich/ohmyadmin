async def api_function_one():
    print("hi from af one()")
    await api_function_two()
    return "result"


async def api_function_two():
    print("hi from af two()")


def sync_api_function_one():
    coro = api_function_one()
    try:
        coro.send(None)
    except StopIteration as err:
        return err.value


print(sync_api_function_one())
