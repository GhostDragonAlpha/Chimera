"""Linux lifecycle ownership checks; real stop/restart covered by bootstrap suite."""
import os
import socket
import sys
import unittest
from unittest import mock
import linux_process


@unittest.skipUnless(sys.platform.startswith('linux') and hasattr(os, 'pidfd_open'),
                     'requires Linux procfs and pidfd support')
class LinuxProcessTests(unittest.TestCase):
    def test_current_identity_stable_and_boot_bound(self):
        first = linux_process.identity(os.getpid())
        self.assertEqual(first, linux_process.identity(os.getpid()))
        self.assertGreater(first['start_ticks'], 0)
        self.assertTrue(first['boot_id'])

    def test_socket_ownership_tracks_actual_listening_fd(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); listener.listen()
            port = listener.getsockname()[1]
            self.assertTrue(linux_process.owns_listener(os.getpid(), port))
        self.assertFalse(linux_process.owns_listener(os.getpid(), port))

    def test_mismatched_identity_never_signals(self):
        expected = linux_process.identity(os.getpid())
        expected['start_ticks'] += 1
        with mock.patch.object(linux_process.signal, 'pidfd_send_signal') as send:
            with self.assertRaisesRegex(RuntimeError, 'process_identity_mismatch'):
                linux_process.stop_owned(os.getpid(), expected, 1)
            send.assert_not_called()

    def test_missing_listener_never_signals(self):
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))  # Bound but deliberately not listening.
            port = reserved.getsockname()[1]
            with mock.patch.object(linux_process.signal, 'pidfd_send_signal') as send:
                with self.assertRaisesRegex(RuntimeError, 'listener_identity_mismatch'):
                    linux_process.stop_owned(os.getpid(), linux_process.identity(os.getpid()), port)
                send.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
