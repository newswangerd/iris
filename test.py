import asyncio

async def async_func1():
    await asyncio.sleep(2)  # Simulate a delay
    return 'Result from func1'

async def async_func2():
    await asyncio.sleep(1)  # Simulate a shorter delay
    return 'Result from func2'

async def main():
    for i in range(10):
        tasks = [asyncio.create_task(async_func1()), asyncio.create_task(async_func2())]

        # Wait for the first task to complete
        # done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        done, pending = await asyncio.gather(*tasks)

        print(done)
        print(pending)

        # Get the result of the first completed task
        # for task in done:
        #     print(task)
            # result = await task
            # print(f'Task result: {result}')
            # break  # We only care about the first completed task

# Run the main function
asyncio.run(main())
