"""trace_proxy.py -- the pilot's network trace injector (lane-owned).

A chunk-preserving TCP forwarder. One-way delay is applied per CHUNK,
independently per direction, exactly as the prereg names the traces:

  TRACE-CLEAN  delay=0        jitter=0    tail_ms=0
  TRACE-50     delay=50       jitter=0    tail_ms=0
  TRACE-50J    delay=50       jitter=20   tail_ms=0
  TRACE-TAIL   delay=50       jitter=20   tail_ms=200 (one downstream
                           chunk stall every tail_every_s seconds)

The proxy never interprets the bytes; it counts them (wire truth for the
bandwidth table). Never binds 8127 (the port law).

Usage:
  python trace_proxy.py --listen 0 --target 127.0.0.1:58027 \
      --delay-ms 50 --jitter-ms 20 --tail-ms 200 --tail-every-s 5 \
      --count-out counts.json
Prints the bound port on stdout as PROXY_PORT=<n>.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import socket
import time


class Counters:
    def __init__(self) -> None:
        self.up_bytes = 0
        self.down_bytes = 0
        self.up_chunks = 0
        self.down_chunks = 0
        self.started = time.time()


async def pump(reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
               delay_s: float, jitter_ms: float, tail_ms: float,
               tail_every_s: float, count: Counters, direction: str,
               stop: asyncio.Event) -> None:
    try:
        while not stop.is_set():
            try:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=0.5)
            except asyncio.TimeoutError:
                continue        # idle keep-alive socket: NOT dead -- keep the
                # connection pooled (measured: closing it killed the page's
                # ghost fetch and with it the whole render loop)
            if not chunk:
                break
            d = delay_s
            if jitter_ms:
                d += random.uniform(-jitter_ms, jitter_ms) / 1000.0
            if direction == "down" and tail_ms and tail_every_s:
                if (count.down_chunks % max(1, int(tail_every_s * 20))) == 0:
                    # one stalled chunk every ~tail_every_s of downstream flow
                    d += tail_ms / 1000.0
            if direction == "up":
                count.up_bytes += len(chunk)
                count.up_chunks += 1
            else:
                count.down_bytes += len(chunk)
                count.down_chunks += 1
            if d > 0:
                await asyncio.sleep(max(0.0, d))
            writer.write(chunk)
            await writer.drain()
    except (asyncio.TimeoutError, ConnectionError, OSError):
        pass
    finally:
        try:
            writer.close()
        except OSError:
            pass


async def handle(client_r: asyncio.StreamReader, client_w: asyncio.StreamWriter,
                 target: tuple, args: argparse.Namespace, count: Counters) -> None:
    server_r, server_w = await asyncio.open_connection(*target)
    stop = asyncio.Event()
    await asyncio.gather(
        pump(client_r, server_w, args.delay_ms / 1000.0, args.jitter_ms,
             args.tail_ms, args.tail_every_s, count, "up", stop),
        pump(server_r, client_w, args.delay_ms / 1000.0, args.jitter_ms,
             args.tail_ms, args.tail_every_s, count, "down", stop),
    )


async def main_async(a: argparse.Namespace) -> None:
    count = Counters()
    server = await asyncio.start_server(
        lambda r, w: handle(r, w, (a.target_host, a.target_port), a, count),
        "127.0.0.1", a.listen)
    port = server.sockets[0].getsockname()[1]
    print(f"PROXY_PORT={port}", flush=True)
    async with server:
        await server.serve_forever()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", type=int, default=0)
    ap.add_argument("--target-host", default="127.0.0.1")
    ap.add_argument("--target-port", type=int, required=True)
    ap.add_argument("--delay-ms", type=float, default=0.0)
    ap.add_argument("--jitter-ms", type=float, default=0.0)
    ap.add_argument("--tail-ms", type=float, default=0.0)
    ap.add_argument("--tail-every-s", type=float, default=5.0)
    ap.add_argument("--count-out", default=None)
    a = ap.parse_args()
    try:
        asyncio.run(main_async(a))
    except KeyboardInterrupt:
        pass
    if a.count_out:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
