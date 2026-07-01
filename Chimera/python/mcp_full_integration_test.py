"""
MCP Full Integration Test — Comprehensive standalone integration testing script.

Connects to Native MCP server at http://localhost:3000/mcp, discovers tools/resources,
executes test operations (inspect, control_actor, manage_level), validates responses,
supports synchronous and async execution modes, and generates detailed JSON reports.

Usage: python mcp_full_integration_test.py [--async] [--report path/to/report.json]

No external dependencies beyond Python stdlib — uses urllib for HTTP requests.
"""

import asyncio
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MCP_SERVER_URL = "http://localhost:3000/mcp"
DEFAULT_REPORT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "integration_test_results.json"
)

MAX_RETRIES = 5
RETRY_BASE_DELAY = 1.0
REQUEST_TIMEOUT = 30
INITIALIZE_TIMEOUT = 60

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mcp_integration_test")


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_logging(level: LogLevel = LogLevel.INFO, verbose: bool = False) -> None:
    """Configure root logger with optional file handler."""
    log_level = LogLevel.DEBUG if verbose else level
    handlers = [logging.StreamHandler(sys.stdout)]

    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"mcp_integration_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log")

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.value)
    for h in handlers:
        root_logger.addHandler(h)


# ---------------------------------------------------------------------------
# Progress Indicator
# ---------------------------------------------------------------------------

class ProgressBar:
    """Terminal progress bar with status display."""

    def __init__(self, total_steps: int, width: int = 40):
        self.total = total_steps
        self.width = width
        self.current = 0
        self.start_time = time.perf_counter()
        self._lock = None

    def update(self, step: str, completed: bool = False) -> None:
        """Update progress bar with current step description."""
        self.current += 1
        elapsed = time.perf_counter() - self.start_time
        pct = self.current / self.total * 100 if self.total > 0 else 100

        filled = int(self.width * self.current / self.total) if self.total > 0 else 0
        bar = "=" * filled + "-" * (self.width - filled)
        status = "OK" if completed else "..."

        line = f"\r[{bar}] {pct:5.1f}% | Step {self.current}/{self.total} | {step} [{status}] | {elapsed:.2f}s elapsed"
        sys.stdout.write(line + "\x1b[0K")
        sys.stdout.flush()

    def finish(self) -> None:
        """Mark progress as complete."""
        self.update("Complete", completed=True)
        print()


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Represents a single test case."""

    name: str
    description: str
    tool_name: str | None = None
    arguments: dict = field(default_factory=dict)
    status: TestStatus = TestStatus.PENDING
    response: Any = None
    raw_response: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    error_message: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status.value,
            "response_summary": _truncate_response(self.response),
            "raw_response": self.raw_response if isinstance(self.raw_response, dict) else {},
            "duration_ms": round(self.duration_ms, 2),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class TestReport:
    """Aggregates all test results into a report."""

    server_url: str = ""
    started_at: str = ""
    completed_at: str = ""
    total_duration_ms: float = 0.0
    async_mode: bool = False
    tools_discovered: list[dict] = field(default_factory=list)
    resources_discovered: list[dict] = field(default_factory=list)
    test_cases: list[TestCase] = field(default_factory=list)

    def add_test_case(self, tc: TestCase) -> None:
        self.test_cases.append(tc)

    def to_dict(self) -> dict:
        passed = sum(1 for tc in self.test_cases if tc.status == TestStatus.PASSED)
        failed = sum(1 for tc in self.test_cases if tc.status == TestStatus.FAILED)
        skipped = sum(1 for tc in self.test_cases if tc.status == TestStatus.SKIPPED)
        errors = sum(1 for tc in self.test_cases if tc.status == TestStatus.ERROR)

        return {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "server_url": self.server_url,
                "async_mode": self.async_mode,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "total_duration_ms": round(self.total_duration_ms, 2),
            },
            "summary": {
                "total_tests": len(self.test_cases),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
                "pass_rate_pct": round(passed / max(len(self.test_cases), 1) * 100, 2),
            },
            "server_info": {
                "tools_count": len(self.tools_discovered),
                "resources_count": len(self.resources_discovered),
                "tools": self.tools_discovered,
                "resources": self.resources_discovered,
            },
            "test_results": [tc.to_dict() for tc in self.test_cases],
        }


def _truncate_response(response: Any) -> str:
    """Truncate response to 500 chars for readability."""
    if not response:
        return ""
    text = json.dumps(response, default=str) if isinstance(response, (dict, list)) else str(response)
    return text[:500] + "..." if len(text) > 500 else text


# ---------------------------------------------------------------------------
# MCP HTTP Client
# ---------------------------------------------------------------------------

class MCPClient:
    """Lightweight JSON-RPC client for MCP server communication."""

    def __init__(self, url: str = MCP_SERVER_URL, timeout: int = REQUEST_TIMEOUT):
        self.url = url
        self.timeout = timeout
        self.session_id: str | None = None
        self.cdn_key: str | None = None
        self.server_info: dict = {}

    def _build_request(self, method: str, params: dict | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) % 10**9,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        if self.session_id and self.cdn_key:
            payload["session"] = {
                "sessionId": self.session_id,
                "cdnKey": self.cdn_key,
            }

        return payload

    def _request(self, method: str, params: dict | None = None, timeout: int | None = None) -> dict | None:
        """Send JSON-RPC request and parse response."""
        payload = self._build_request(method, params)
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except urllib.error.URLError as e:
            logger.warning(f"Request failed ({method}): {e.reason}")
            return None
        except TimeoutError:
            logger.warning(f"Request timed out after {timeout or self.timeout}s ({method})")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response ({method}): {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error ({method}): {e}")
            return None

    def initialize(self) -> bool:
        """Send initialize request and extract session info."""
        params = {
            "protocolVersion": "2024-11-07",
            "capabilities": {},
            "clientInfo": {
                "name": "MCP Full Integration Test Client",
                "version": "1.0.0",
            },
        }

        response = self._request("initialize", params, timeout=INITIALIZE_TIMEOUT)

        if response and "result" in response:
            result = response["result"]
            self.server_info = result.get("serverInfo", {})
            session = result.get("session") or {}
            self.session_id = session.get("sessionId")
            self.cdn_key = session.get("cdnKey")

            name = self.server_info.get("name", "unknown")
            version = self.server_info.get("version", "?")
            logger.info(f"MCP Session initialized — Server: {name} v{version}")
            return True

        logger.warning("Initialize returned no result or missing session info")
        return False

    def list_tools(self) -> list[dict]:
        """List all available MCP tools."""
        response = self._request("tools/list", {"limit": 100})

        if not response or "result" not in response:
            logger.warning("tools/list returned no result")
            return []

        tools_data = response.get("result", {})
        tools_list = tools_data.get("tools", [])

        tools = []
        for tool in tools_list:
            tools.append({
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "schema": tool.get("inputSchema", {}),
            })

        logger.info(f"Discovered {len(tools)} available tools")
        return tools

    def list_resources(self) -> list[dict]:
        """List all available MCP resources."""
        response = self._request("resources/list", {})

        if not response or "result" not in response:
            logger.warning("resources/list returned no result")
            return []

        resources_data = response.get("result", {})
        resources_list = resources_data.get("resources", [])

        resources = []
        for res in resources_list:
            resources.append({
                "uri": res.get("uri", ""),
                "name": res.get("name", ""),
                "description": res.get("description", ""),
                "mimeType": res.get("mimeType", ""),
            })

        logger.info(f"Discovered {len(resources)} available resources")
        return resources

    def call_tool(self, tool_name: str, arguments: dict) -> dict | None:
        """Execute a tool call with session headers."""
        params = {"tool": tool_name, "arguments": arguments}
        response = self._request("tools/call", params)
        return response

    async def call_tool_async(self, tool_name: str, arguments: dict) -> dict | None:
        """Async tool call via thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.call_tool, tool_name, arguments)


# ---------------------------------------------------------------------------
# Retry Wrapper
# ---------------------------------------------------------------------------

def retry_with_backoff(func, max_retries: int = MAX_RETRIES, base_delay: float = RETRY_BASE_DELAY):
    """Decorator-like wrapper for retry with exponential backoff."""

    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed ({func.__name__}): {e}. Retrying in {delay:.2f}s...")
                if attempt < max_retries - 1:
                    time.sleep(delay)

        logger.error(f"All {max_retries} retries exhausted for {func.__name__}")
        raise last_exception

    return wrapper


# ---------------------------------------------------------------------------
# Test Execution Engine
# ---------------------------------------------------------------------------

class TestEngine:
    """Orchestrates test discovery, execution, and reporting."""

    def __init__(self, client: MCPClient, async_mode: bool = False):
        self.client = client
        self.async_mode = async_mode
        self.report = TestReport(
            server_url=client.url,
            started_at=datetime.now(timezone.utc).isoformat(),
            async_mode=async_mode,
        )

    def discover(self) -> None:
        """Discover tools and resources from the MCP server."""
        logger.info("=" * 60)
        logger.info("PHASE 1: DISCOVERY")
        logger.info("=" * 60)

        self.report.tools_discovered = self.client.list_tools()
        self.report.resources_discovered = self.client.list_resources()

    def run_test(self, test_case: TestCase) -> None:
        """Execute a single synchronous test case."""
        tool_name = test_case.tool_name or "unknown"
        logger.info(f"[TEST] Running: {test_case.name} (tool={tool_name})")

        start = time.perf_counter()
        test_case.status = TestStatus.RUNNING

        try:
            response = self.client.call_tool(tool_name, test_case.arguments)
            elapsed = time.perf_counter() - start
            test_case.duration_ms = elapsed * 1000
            test_case.response = response
            test_case.raw_response = response or {}

            if response is not None:
                test_case.status = TestStatus.PASSED
                logger.info(f"[TEST] PASSED — {test_case.name} ({elapsed*1000:.0f}ms)")
            else:
                test_case.status = TestStatus.FAILED
                test_case.error_message = "Tool returned None response"
                logger.warning(f"[TEST] FAILED — {test_case.name}: returned None")

        except Exception as e:
            elapsed = time.perf_counter() - start
            test_case.duration_ms = elapsed * 1000
            test_case.status = TestStatus.ERROR
            test_case.error_message = str(e)
            logger.error(f"[TEST] ERROR — {test_case.name}: {e}")

    async def run_test_async(self, test_case: TestCase) -> None:
        """Execute a single asynchronous test case."""
        tool_name = test_case.tool_name or "unknown"
        logger.info(f"[ASYNC-TEST] Running: {test_case.name} (tool={tool_name})")

        start = time.perf_counter()
        test_case.status = TestStatus.RUNNING

        try:
            response = await self.client.call_tool_async(tool_name, test_case.arguments)
            elapsed = time.perf_counter() - start
            test_case.duration_ms = elapsed * 1000
            test_case.response = response
            test_case.raw_response = response or {}

            if response is not None:
                test_case.status = TestStatus.PASSED
                logger.info(f"[ASYNC-TEST] PASSED — {test_case.name} ({elapsed*1000:.0f}ms)")
            else:
                test_case.status = TestStatus.FAILED
                test_case.error_message = "Tool returned None response"
                logger.warning(f"[ASYNC-TEST] FAILED — {test_case.name}: returned None")

        except Exception as e:
            elapsed = time.perf_counter() - start
            test_case.duration_ms = elapsed * 1000
            test_case.status = TestStatus.ERROR
            test_case.error_message = str(e)
            logger.error(f"[ASYNC-TEST] ERROR — {test_case.name}: {e}")

    def run_batch_sync(self, test_cases: list[TestCase]) -> None:
        """Run all test cases synchronously."""
        total = len(test_cases)
        progress = ProgressBar(total)

        for tc in test_cases:
            self.run_test(tc)
            self.report.add_test_case(tc)
            progress.update(f"Running {tc.name}")

    async def run_batch_async(self, test_cases: list[TestCase]) -> None:
        """Run all test cases asynchronously with concurrency control."""
        total = len(test_cases)
        semaphore = asyncio.Semaphore(5)
        progress = ProgressBar(total)

        async def _run(tc):
            async with semaphore:
                await self.run_test_async(tc)
                self.report.add_test_case(tc)
                progress.update(f"Running {tc.name}")

        tasks = [_run(tc) for tc in test_cases]
        await asyncio.gather(*tasks, return_exceptions=True)

    def finalize(self) -> TestReport:
        """Mark report complete and compute summary."""
        self.report.completed_at = datetime.now(timezone.utc).isoformat()
        start = datetime.fromisoformat(self.report.started_at)
        end = datetime.fromisoformat(self.report.completed_at)
        self.report.total_duration_ms = (end - start).total_seconds() * 1000

        logger.info("=" * 60)
        logger.info("PHASE 3: FINALIZATION")
        logger.info("=" * 60)

        passed = sum(1 for tc in self.report.test_cases if tc.status == TestStatus.PASSED)
        failed = sum(1 for tc in self.report.test_cases if tc.status == TestStatus.FAILED)
        skipped = sum(1 for tc in self.report.test_cases if tc.status == TestStatus.SKIPPED)
        errors = sum(1 for tc in self.report.test_cases if tc.status == TestStatus.ERROR)

        logger.info(f"Results — {passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
        return self.report


# ---------------------------------------------------------------------------
# Test Case Definitions
# ---------------------------------------------------------------------------

def build_test_cases() -> list[TestCase]:
    """Build the standard test suite covering inspect, control_actor, manage_level."""

    tests = [
        TestCase(
            name="inspect_basic",
            description="Basic inspect tool call with default parameters",
            tool_name="inspect",
            arguments={},
        ),
        TestCase(
            name="inspect_with_entity",
            description="Inspect a specific entity by name",
            tool_name="inspect",
            arguments={"entity": "PlayerController"},
        ),
        TestCase(
            name="control_actor_basic",
            description="Basic control_actor call with default parameters",
            tool_name="control_actor",
            arguments={},
        ),
        TestCase(
            name="control_actor_position",
            description="Control actor position (set location)",
            tool_name="control_actor",
            arguments={"action": "get_location"},
        ),
        TestCase(
            name="control_actor_rotation",
            description="Control actor rotation query",
            tool_name="control_actor",
            arguments={"action": "get_rotation"},
        ),
        TestCase(
            name="manage_level_basic",
            description="Basic manage_level call with default parameters",
            tool_name="manage_level",
            arguments={},
        ),
        TestCase(
            name="manage_level_info",
            description="Query level information",
            tool_name="manage_level",
            arguments={"action": "get_level_info"},
        ),
        TestCase(
            name="manage_level_objects",
            description="List objects in current level",
            tool_name="manage_level",
            arguments={"action": "list_objects"},
        ),
    ]

    return tests


# ---------------------------------------------------------------------------
# Report Writer
# ---------------------------------------------------------------------------

def write_report(report: TestReport, output_path: str) -> None:
    """Serialize report to JSON and write to disk."""
    report_data = report.to_dict()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Report written to {output_path}")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def run_async_integration(client: MCPClient) -> TestReport:
    """Run full async integration test suite."""
    engine = TestEngine(client, async_mode=True)
    engine.discover()

    tests = build_test_cases()
    await engine.run_batch_async(tests)

    return engine.finalize()


def run_sync_integration(client: MCPClient) -> TestReport:
    """Run full sync integration test suite."""
    engine = TestEngine(client, async_mode=False)
    engine.discover()

    tests = build_test_cases()
    engine.run_batch_sync(tests)

    return engine.finalize()


def parse_args(argv: list[str] | None = None) -> dict:
    """Parse command-line arguments."""
    args = {"async_mode": False, "report_path": DEFAULT_REPORT_PATH}

    if argv is None:
        argv = sys.argv[1:]

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--async", "--async-mode"):
            args["async_mode"] = True
        elif arg == "--report" and i + 1 < len(argv):
            args["report_path"] = argv[i + 1]
            i += 1
        elif arg in ("-h", "--help"):
            print("Usage: python mcp_full_integration_test.py [--async] [--report path]")
            sys.exit(0)
        i += 1

    return args


def main() -> None:
    """Main entry point for standalone execution."""
    setup_logging(LogLevel.INFO, verbose=False)
    args = parse_args()

    logger.info("=" * 60)
    logger.info("MCP FULL INTEGRATION TEST")
    logger.info(f"Server: {MCP_SERVER_URL}")
    logger.info(f"Mode: {'async' if args['async_mode'] else 'sync'}")
    logger.info(f"Report output: {args['report_path']}")
    logger.info("=" * 60)

    client = MCPClient(url=MCP_SERVER_URL, timeout=REQUEST_TIMEOUT)

    # Initialize session with retry
    init_success = False
    for attempt in range(MAX_RETRIES):
        try:
            if client.initialize():
                init_success = True
                break
        except Exception as e:
            logger.warning(f"Initialize attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

        delay = RETRY_BASE_DELAY * (2 ** attempt)
        if attempt < MAX_RETRIES - 1:
            logger.info(f"Retrying in {delay:.2f}s...")
            time.sleep(delay)

    if not init_success:
        logger.error("Failed to initialize MCP session after all retries. Aborting.")
        report = TestReport(
            server_url=MCP_SERVER_URL,
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            test_cases=[],
        )
        write_report(report, args["report_path"])
        sys.exit(1)

    # Run tests
    if args["async_mode"]:
        report = asyncio.run(run_async_integration(client))
    else:
        report = run_sync_integration(client)

    # Write report
    write_report(report, args["report_path"])

    logger.info("=" * 60)
    logger.info("INTEGRATION TEST COMPLETE")
    logger.info(f"Report saved to: {args['report_path']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
