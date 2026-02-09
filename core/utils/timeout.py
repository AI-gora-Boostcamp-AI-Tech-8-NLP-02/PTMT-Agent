import asyncio
from functools import wraps

def async_timeout(seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"TimeoutError: {func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator

@async_timeout(3)
async def slow_async_function():
    await asyncio.sleep(5)
    return "완료"

if __name__ == "__main__":
    try:
        result = asyncio.run(slow_async_function())
    except TimeoutError as e:
        print(e)