import asyncio
from collections import defaultdict
from threading import Thread


class Event:
    def __init__(self, type, data):
        self.type = type
        self.data = data

    def __repr__(self):
        return f"Event( type:{self.type} ,data: {self.data}) "


class AsyncEngine:
    """ 通过单线程的异步效果来获得并发效果 ~~"""

    def __init__(self, work_core=10):
        # 用于主循环
        self.loop = asyncio.new_event_loop()
        self._func = defaultdict(list)
        self.work_core = work_core
        # self.queue = ContextVar('queue')
        self.init_flag = True
        self._active = False

    @property
    def status(self):
        """ 状态 """
        return self._active

    async def worker(self, queue):
        await asyncio.sleep(0.1)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            await self.future_finish(event)
            queue.task_done()

    async def _put(self, event):
        await self._queue.put(event)

    def put(self, event):
        self.loop.create_task(self._put(event))

    async def future_finish(self, event: Event):
        for func in self._func.get(event.type):
            await func(event)

    def register(self, type, func):
        # if not iscoroutinefunction(func):
        #     raise TypeError("处理函数错误， 不是一个协程对象")
        handler_list = self._func[type]
        if func not in handler_list:
            handler_list.append(func)

    def unregister(self, type, func):
        handler_list = self._func[type]
        if func in handler_list:
            handler_list.remove(func)

    async def main(self):
        self._active = True
        asyncio.set_event_loop(self.loop)
        self._queue = asyncio.Queue()
        tasks = []
        for i in range(self.work_core):
            task = asyncio.create_task(self.worker(self._queue))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=False)

    def start(self):
        p = Thread(target=self.loop.run_until_complete, args=(self.main(),))
        p.start()
