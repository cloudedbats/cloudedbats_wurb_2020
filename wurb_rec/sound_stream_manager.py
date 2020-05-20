#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2020-present Arnold Andreasson
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import asyncio


class SoundStreamManager(object):
    """ Manager base class for sound processing. 
        The module contains worker methods for sources, 
        processing algorithms and targets. 
        Based on asynchio for concurrency.
        Dataflow:
            Source ---> Queue ---> Process ---> Queue ---> Target
    """

    def __init__(self, queue_max_size=120):
        """ """
        try:
            self.queue_max_size = queue_max_size
            self.clear()
        except Exception as e:
            print("Exception: ", e)

    def clear(self):
        """ """
        try:
            self.from_source_queue = asyncio.Queue(maxsize=self.queue_max_size)
            self.to_target_queue = asyncio.Queue(maxsize=self.queue_max_size)
            self.source_task = None
            self.process_task = None
            self.target_task = None
        except Exception as e:
            print("Exception: ", e)

    async def start_streaming(self):
        """ """
        try:
            self.clear()
            self.source_task = asyncio.create_task(self.sound_source_worker())
            self.process_task = asyncio.create_task(self.sound_process_worker())
            self.target_task = asyncio.create_task(self.sound_target_worker())
        except Exception as e:
            print("Exception: ", e)

    async def stop_streaming(self, stop_immediate=True):
        """ """
        try:
            if stop_immediate:
                # Stop all now.
                if self.source_task:
                    self.source_task.cancel()
                if self.process_task:
                    self.process_task.cancel()
                if self.target_task:
                    self.target_task.cancel()
            else:
                # Stop source only and let process and target
                # finish their work.
                if self.source_task:
                    self.source_task.cancel()
                await self.from_source_queue.put(None)  # Terminate.
        except Exception as e:
            print("Exception: ", e)

    async def wait_for_shutdown(self):
        """ To be called after stop_streaming. """
        try:
            if self.source_task and (not self.source_task.done()):
                await self.source_task
            if self.process_task and (not self.process_task.done()):
                await self.process_task
            if self.target_task and (not self.target_task.done()):
                await self.target_task
        except Exception as e:
            print("Exception: ", e)

    async def sound_source_worker(self):
        """ Abstract worker method for sound sources. Mainly files or streams.
            Test implementation to be used as template.
        """
        try:
            counter = 0
            while True:
                try:
                    await asyncio.sleep(0.01)
                    counter += 1
                    print("DEBUG-1: Item: ", "A-" + str(counter))
                    try:
                        self.from_source_queue.put_nowait(" A-" + str(counter))
                    except asyncio.QueueFull:
                        await self.remove_items_from_queue(self.from_source_queue)
                        await self.from_source_queue.put(False)  # Flush.
                except asyncio.CancelledError:
                    print("DEBUG: ", "sound_source_worker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: sound_source_worker exception: ", e)
        except Exception as e:
            print("Exception: ", e)
        finally:
            print("DEBUG: ", "sound_source_worker terminated.")

    async def sound_process_worker(self):
        """ Abstract worker for sound processing algorithms.
            Test implementation to be used as template.
        """
        try:
            while True:
                try:
                    item = await self.from_source_queue.get()
                    if item == None:
                        await self.to_target_queue.put(None)  # Terminate.
                        print("DEBUG-2: Terminated by source.")
                        break
                    if item == False:
                        print("DEBUG-2: Flush.")
                        await self.remove_items_from_queue(self.to_target_queue)
                        await self.to_target_queue.put(False)  # Flush.
                    print("DEBUG-2: Item: ", item)
                    self.from_source_queue.task_done()
                    await asyncio.sleep(0.1)
                    try:
                        self.to_target_queue.put_nowait(item)
                    except asyncio.QueueFull:
                        await self.remove_items_from_queue(self.to_target_queue)
                        await self.to_target_queue.put(False)  # Flush.
                except asyncio.CancelledError:
                    print("DEBUG: ", "soundProcessWorker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: soundProcessWorker exception: ", e)
        except Exception as e:
            print("Exception: ", e)
        finally:
            print("DEBUG: ", "soundProcessWorker terminated.")

    async def sound_target_worker(self):
        """ Abstract worker for sound targets. Mainly files or streams.
            Test implementation to be used as template.
        """
        try:
            while True:
                try:
                    item = await self.to_target_queue.get()
                    if item == None:
                        print("DEBUG-3: Terminated by process.")
                        break
                    if item == False:
                        print("DEBUG-3: Flush.")
                        pass  # TODO.
                    print("DEBUG-3: Item: ", item)
                    self.to_target_queue.task_done()
                    await asyncio.sleep(0.2)
                except asyncio.CancelledError:
                    print("DEBUG: ", "soundTargetWorker cancelled.")
                    break
                except Exception as e:
                    print("DEBUG: soundTargetWorker exception: ", e)
        except Exception as e:
            print("Exception: ", e)
        finally:
            print("DEBUG: soundTargetWorker terminated.")

    async def remove_items_from_queue(self, queue):
        """ Helper method. """
        try:
            while True:
                try:
                    queue.get_nowait()
                    queue.task_done()
                except asyncio.QueueEmpty:
                    return
        except Exception as e:
            print("Exception: ", e)


# === MAIN - for test ===
async def main():
    """ """
    try:
        print("Test started.")
        stream_manager = SoundStreamManager(queue_max_size=20)
        print("Test 1.")
        await stream_manager.start_streaming()
        await asyncio.sleep(2.0)
        print("Test 2.")
        await stream_manager.stop_streaming(stop_immediate=False)
        await asyncio.sleep(2.0)
        print("Test 3.")
        await stream_manager.stop_streaming(stop_immediate=True)
        print("Test 4.")
        await stream_manager.wait_for_shutdown()
        print("Test finished.")
    except Exception as e:
        print("Exception: ", e)


if __name__ == "__main__":
    """ """
    asyncio.run(main(), debug=True)
