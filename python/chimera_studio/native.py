# SPDX-License-Identifier: AGPL-3.0-or-later
"""Private native scene, no connection to the agents' running engine or models."""
import ctypes
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
class NativeError(RuntimeError): pass
class NativeScene:
    def __init__(self, dll=None):
        dll=Path(dll) if dll else ROOT/'build/native/Release/chimera_studio_bridge.dll'
        self.lib=ctypes.CDLL(str(dll))
        self.lib.cs_create.restype=ctypes.c_void_p
        self.lib.cs_destroy.argtypes=[ctypes.c_void_p]
        self.lib.cs_call.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p]
        self.lib.cs_call.restype=ctypes.c_char_p
        self.lib.cs_step.argtypes=[ctypes.c_void_p,ctypes.c_int]
        self.lib.cs_step.restype=ctypes.c_char_p
        if self.lib.cs_abi_version()!=1: raise NativeError('Native ABI mismatch')
        self.handle=self.lib.cs_create()
        if not self.handle: raise NativeError('Native allocation failed')
    @staticmethod
    def decode(raw):
        value=json.loads(raw)
        if value.get('ok') is False: raise NativeError(value.get('error','Native call failed'))
        return value
    def call(self, operation, payload=None):
        if not self.handle: raise NativeError('Closed scene')
        raw=json.dumps(payload,separators=(',',':'),allow_nan=False) if payload is not None else '{}'
        return self.decode(self.lib.cs_call(self.handle,operation.encode(),raw.encode()))
    def advance(self, steps):
        if type(steps) is not int or steps<1: raise ValueError('Positive integer substep count required')
        while steps:
            n=min(200,steps); self.decode(self.lib.cs_step(self.handle,n)); steps-=n
    def close(self):
        if getattr(self,'handle',None): self.lib.cs_destroy(self.handle); self.handle=None
    def __del__(self): self.close()
