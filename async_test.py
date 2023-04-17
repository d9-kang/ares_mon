import asyncio

async def foo():
    await asyncio.sleep(1)
    print("foo done")
    await asyncio.ensure_future(bar())

async def bar():
    await asyncio.sleep(2)
    print("bar done")

loop = asyncio.get_event_loop()
task = loop.create_task(foo())
loop.run_until_complete(task)
loop.close()