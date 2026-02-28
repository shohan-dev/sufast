"""
Sufast Background Tasks - Run tasks after response is sent.
"""

import asyncio
import threading
import traceback
from typing import Any, Callable, List, Optional
from concurrent.futures import ThreadPoolExecutor


class BackgroundTask:
    """A single background task to run after the response is sent.
    
    Usage:
        task = BackgroundTask(send_email, to="user@example.com", subject="Welcome")
    """
    
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    async def run(self):
        """Execute the background task."""
        if asyncio.iscoroutinefunction(self.func):
            await self.func(*self.args, **self.kwargs)
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.func(*self.args, **self.kwargs))


class BackgroundTasks:
    """Collection of background tasks - FastAPI compatible.
    
    Usage:
        @app.post("/send-notification")
        async def send_notification(background_tasks: BackgroundTasks):
            background_tasks.add_task(write_log, message="notification sent")
            background_tasks.add_task(send_email, email="user@example.com")
            return {"message": "Notification scheduled"}
    """
    
    def __init__(self):
        self.tasks: List[BackgroundTask] = []
    
    def add_task(self, func: Callable, *args, **kwargs):
        """Add a background task to be run after the response."""
        self.tasks.append(BackgroundTask(func, *args, **kwargs))
    
    async def run_all(self):
        """Execute all background tasks."""
        for task in self.tasks:
            try:
                await task.run()
            except Exception as e:
                print(f"Background task error ({task.func.__name__}): {e}")
                traceback.print_exc()
    
    def __len__(self):
        return len(self.tasks)


class TaskScheduler:
    """Simple task scheduler for periodic background tasks.
    
    Usage:
        scheduler = TaskScheduler()
        
        @scheduler.periodic(interval=60)
        async def cleanup():
            # runs every 60 seconds
            pass
        
        @scheduler.once(delay=5)
        async def startup_task():
            # runs once after 5 seconds
            pass
    """
    
    def __init__(self):
        self._periodic_tasks: List[dict] = []
        self._once_tasks: List[dict] = []
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def periodic(self, interval: float, name: Optional[str] = None):
        """Decorator for periodic tasks."""
        def decorator(func):
            self._periodic_tasks.append({
                'func': func,
                'interval': interval,
                'name': name or func.__name__,
                'task': None
            })
            return func
        return decorator
    
    def once(self, delay: float = 0, name: Optional[str] = None):
        """Decorator for one-time delayed tasks."""
        def decorator(func):
            self._once_tasks.append({
                'func': func,
                'delay': delay,
                'name': name or func.__name__,
                'task': None
            })
            return func
        return decorator
    
    async def start(self):
        """Start all scheduled tasks."""
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        # Start periodic tasks
        for task_info in self._periodic_tasks:
            task_info['task'] = asyncio.create_task(
                self._run_periodic(task_info)
            )
        
        # Start one-time tasks
        for task_info in self._once_tasks:
            task_info['task'] = asyncio.create_task(
                self._run_once(task_info)
            )
    
    async def stop(self):
        """Stop all scheduled tasks."""
        self._running = False
        for task_info in self._periodic_tasks + self._once_tasks:
            if task_info.get('task'):
                task_info['task'].cancel()
                try:
                    await task_info['task']
                except asyncio.CancelledError:
                    pass
    
    async def _run_periodic(self, task_info: dict):
        """Run a periodic task."""
        while self._running:
            try:
                await asyncio.sleep(task_info['interval'])
                if asyncio.iscoroutinefunction(task_info['func']):
                    await task_info['func']()
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor, task_info['func']
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Periodic task error ({task_info['name']}): {e}")
    
    async def _run_once(self, task_info: dict):
        """Run a one-time task after delay."""
        try:
            await asyncio.sleep(task_info['delay'])
            if asyncio.iscoroutinefunction(task_info['func']):
                await task_info['func']()
            else:
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, task_info['func']
                )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"One-time task error ({task_info['name']}): {e}")


class RepeatTimer:
    """Thread-based repeat timer for sync code.
    
    Usage:
        timer = RepeatTimer(60, cleanup_function)
        timer.start()
        # ... later ...
        timer.stop()
    """
    
    def __init__(self, interval: float, func: Callable, *args, **kwargs):
        self.interval = interval
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._timer: Optional[threading.Timer] = None
        self._running = False
    
    def start(self):
        """Start the repeating timer."""
        self._running = True
        self._schedule()
    
    def stop(self):
        """Stop the repeating timer."""
        self._running = False
        if self._timer:
            self._timer.cancel()
    
    def _schedule(self):
        """Schedule the next execution."""
        if self._running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
    
    def _run(self):
        """Execute the function and reschedule."""
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            print(f"Timer task error: {e}")
        finally:
            self._schedule()
