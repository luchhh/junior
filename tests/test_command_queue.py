from unittest.mock import MagicMock

from lib.command_queue import CommandQueue


class TestCommandQueue:
    def test_executes_enqueued_function(self):
        q = CommandQueue()
        fn = MagicMock()
        q.enqueue(fn)
        q.wait()
        fn.assert_called_once()

    def test_passes_args_to_function(self):
        q = CommandQueue()
        fn = MagicMock()
        q.enqueue(fn, 1, 2, key="val")
        q.wait()
        fn.assert_called_once_with(1, 2, key="val")

    def test_executes_multiple_commands_in_order(self):
        q = CommandQueue()
        results = []
        q.enqueue(results.append, 1)
        q.enqueue(results.append, 2)
        q.enqueue(results.append, 3)
        q.wait()
        assert results == [1, 2, 3]

    def test_clear_discards_pending_commands(self):
        q = CommandQueue()
        fn = MagicMock()

        # Block the worker with a slow first command, then clear before it runs the rest
        barrier = MagicMock(side_effect=lambda: q.clear())
        q.enqueue(barrier)
        q.enqueue(fn)
        q.enqueue(fn)
        q.wait()

        fn.assert_not_called()

    def test_error_in_command_does_not_stop_queue(self):
        q = CommandQueue()
        fn = MagicMock()
        q.enqueue(MagicMock(side_effect=RuntimeError("boom")))
        q.enqueue(fn)
        q.wait()
        fn.assert_called_once()

    def test_delay_waits_before_executing(self):
        import time
        q = CommandQueue()
        timestamps = []
        q.enqueue(lambda: timestamps.append(time.monotonic()))
        q.enqueue(lambda: timestamps.append(time.monotonic()), delay=0.1)
        q.wait()
        assert timestamps[1] - timestamps[0] >= 0.1
