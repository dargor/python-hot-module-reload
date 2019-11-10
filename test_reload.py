#! /usr/bin/env python3

import uvloop
import asyncio

import pyinotify
import importlib
import sys

import _test_reload


async def setup_watch(fname, loop, event):

    def handler(notifier):
        event.set()
        # when watching individual files,
        # we must re-add watch after a notification
        wm.add_watch(fname, pyinotify.IN_MODIFY)

    wm = pyinotify.WatchManager()
    pyinotify.AsyncioNotifier(wm, loop, callback=handler,
                              default_proc_fun=pyinotify.ProcessEvent)
    wm.add_watch(fname, pyinotify.IN_MODIFY)


async def do_reload(event):
    global _test_reload
    while True:
        await event.wait()
        try:
            # ensure the module is able to reload properly
            importlib.reload(_test_reload)
            # purge the module from the cache
            del sys.modules['_test_reload']
            del _test_reload
            importlib.invalidate_caches()
            # reload the module from scratch
            _test_reload = importlib.import_module('_test_reload')
        except Exception as e:
            print(f'Reload error: {e}')
        event.clear()


async def main():
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    await setup_watch('_test_reload.py', loop, event)
    loop.create_task(do_reload(event))
    while True:
        await asyncio.sleep(1)
        try:
            _test_reload.tick()
        except Exception as e:
            print(f'Tick error: {e}')


if __name__ == '__main__':
    uvloop.install()
    asyncio.run(main())
