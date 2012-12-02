# -*- coding: utf-8 -*-
import os
import signal

__all__ = ['kill_proc']

try:
    from os import kill
    from signal import SIGTERM
    def kill_proc(pid): return kill(pid, SIGTERM)
except ImportError:
    # http://www.python.org/doc/faq/windows/#how-do-i-emulate-os-kill-in-windows
    def kill_proc(pid):
        """kill function for Win32"""
        import win32api
        handle = win32api.OpenProcess(1, 0, pid)
        return (0 != win32api.TerminateProcess(handle, 0))
