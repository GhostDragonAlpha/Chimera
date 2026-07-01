"""
MCP Integration Test Runner — Comprehensive MCP automation test suite.

Connects to the Native MCP server at http://localhost:3000/mcp and runs
sequential tests for each major tool category (inspect, control_actor,
manage_level, etc.). Validates responses and logs pass/fail with detailed
error messages. Supports parallel test execution using asyncio.Semaphore.

Generates a JSON report at E:\\PythonChimera\\test_results.json.

Usage:
    python mcp_integration_test_runner.py                    # Run all tests
    python mcp_integration_test_runner.py inspection         # Run only inspection tests
    python mcp_integration_test_runner.py actor_control      # Run only actor control tests
    python mcp_integration_test_runner.py level_management   # Run only level management tests
    python mcp_integration_test_runner.py --help             # Show usage info
"""

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


# ---------------------------------------------------------------------------
# Test Runner Configuration
# ---------------------------------------------------------------------------

REPORT_PATH = r"E:\PythonChimera\test_results.json"

TEST_CATEGORIES = {
    "inspection": {
        "description": "Inspect tool tests (actor inspection, properties, components)",
        "module": "mcp_test_cases.test_inspection",
        "function": "run_inspection_tests"
    },
    "actor_control": {
        "description": "Control actor tests (spawn, transform, component attach/detach)",
        "module": "mcp_test_cases.test_actor_control",
        "function": "run_actor_control_tests"
    },
    "level_management": {
        "description": "Level management tests (list, streaming dry run, metadata)",
        "module": "mcp_test_cases.test_level_management",
        "function": "run_level_management_tests"
    }
}


# ---------------------------------------------------------------------------
# Test Runner Class
# ---------------------------------------------------------------------------

class MCPIntegrationTestRunner:
    """Full MCP automation test suite with parallel execution support."""

    def __init__(self, mcp_url="http://localhost:3000/mcp", max_concurrent=5, report_path=r"E:\PythonChimera\test_results.json"):
        self.mcp_url = mcp_url
        self.max_concurrent = max_concurrent
        self.report_path = report_path
        self.client: MCPTestClient = None
        self.session_initialized = False
        self.all_results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0

    def initialize_client(self) -> bool:
        """Connect to MCP server and initialize session.

        Returns:
            True on success, False on failure
        """
        print("\n" + "=" * 60)
        print("MCP INTEGRATION TEST RUNNER")
        print("=" * 60)
        print(f"\n[MCP] Connecting to server at {self.mcp_url}")

        self.client = MCPTestClient(self.mcp_url)

        if not self.client.initialize_session():
            print("[ERROR] Failed to initialize MCP session — cannot run tests")
            return False

        self.session_initialized = True
        return True

    async def _run_category_test_async(self, category: str, test_func):
        """Run a single test category with semaphore-based concurrency control.

        Args:
            category: Test category name for logging
            test_func: Callable that runs the tests and returns results

        Returns:
            Dict with category results
        """
        print(f"\n{'=' * 60}")
        print(f"RUNNING CATEGORY: {category}")
        print("=" * 60)

        try:
            results = test_func(self.client)
            
            if isinstance(results, list):
                for result in results:
                    self.test_count += 1
                    status = result.get("status", "UNKNOWN")
                    
                    if status == "PASS":
                        self.pass_count += 1
                    elif status == "FAIL":
                        self.fail_count += 1
                    else:
                        self.skip_count += 1

            return {
                "category": category,
                "results": results if isinstance(results, list) else [],
                "status": "completed"
            }

        except Exception as e:
            print(f"[ERROR] Category '{category}' failed with exception: {e}")
            return {
                "category": category,
                "results": [{"test": f"{category}_error", "status": "FAIL", 
                           "detail": str(e), "timestamp": time.time()}],
                "status": "error"
            }

    async def run_categories_parallel(self, categories: List[str]) -> List[Dict[str, Any]]:
        """Run multiple test categories with parallel execution.

        Uses asyncio.Semaphore to limit concurrent operations.

        Args:
            categories: List of category names to run

        Returns:
            List of category result dicts
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def _limited_run(category_name):
            cat_config = TEST_CATEGORIES.get(category_name)
            if not cat_config:
                return {"category": category_name, "status": "skipped", 
                        "reason": f"Unknown category '{category_name}'"}

            module_path = cat_config["module"]
            func_name = cat_config["function"]

            try:
                __import__(module_path)
                import importlib
                module = importlib.import_module(module_path)
                test_func = getattr(module, func_name)
            except (ImportError, AttributeError) as e:
                return {"category": category_name, "status": "skipped", 
                        "reason": f"Failed to load test module: {e}"}

            async with semaphore:
                result = await self._run_category_test_async(category_name, test_func)
                return result

        tasks = [_limited_run(cat) for cat in categories]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, task_result in enumerate(results):
            category = categories[i]
            
            if isinstance(task_result, Exception):
                final_results.append({
                    "category": category,
                    "status": "error",
                    "reason": str(task_result)
                })
            else:
                final_results.append(task_result)

        return final_results

    def run_categories_sequential(self, categories: List[str]) -> List[Dict[str, Any]]:
        """Run test categories sequentially (fallback for non-async environments).

        Args:
            categories: List of category names to run

        Returns:
            List of category result dicts
        """
        results = []

        async def _run():
            return await self.run_categories_parallel(categories)

        cat_results = asyncio.get_event_loop().run_until_complete(_run())

        for cat_result in cat_results:
            self.all_results.extend(cat_result.get("results", []))
            results.append(cat_result)

        return results

    def run_all_tests(self, categories: List[str] = None) -> Dict[str, Any]:
        """Run all tests or selected categories.

        Args:
            categories: List of category names to run. If None, runs all categories.

        Returns:
            Complete test report dict
        """
        if not self.initialize_client():
            return {
                "status": "failed",
                "error": "MCP session initialization failed",
                "report": {}
            }

        if categories is None:
            categories = list(TEST_CATEGORIES.keys())

        print(f"\n[TESTS] Running {len(categories)} category(ies): {', '.join(categories)}")

        start_time = time.time()

        results = self.run_categories_sequential(categories)

        elapsed = time.time() - start_time

        # Build report
        report = {
            "report_version": "1.0.0",
            "generated_at": int(time.time()),
            "mcp_server_url": self.mcp_url,
            "session_initialized": self.session_initialized,
            "execution_time_seconds": round(elapsed, 2),
            "summary": {
                "total_tests": self.test_count,
                "passed": self.pass_count,
                "failed": self.fail_count,
                "skipped": self.skip_count,
                "pass_rate_percent": (self.pass_count / self.test_count * 100) if self.test_count > 0 else 0.0
            },
            "categories": results,
            "all_results": self.all_results
        }

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        for cat_result in results:
            category = cat_result.get("category", "unknown")
            status = cat_result.get("status", "unknown")
            cat_results = cat_result.get("results", [])

            passed = sum(1 for r in cat_results if r.get("status") == "PASS")
            failed = sum(1 for r in cat_results if r.get("status") == "FAIL")

            icon = "[OK]" if status == "completed" else ("[ERR]" if status == "error" else "[SKIP]")
            print(f"\n{icon} {category}: {passed} passed, {failed} failed ({len(cat_results)} total)")

        print("\n" + "=" * 60)
        icon = "[OK]" if self.fail_count == 0 and self.test_count > 0 else ("[FAIL]" if self.fail_count > 0 else "[PENDING]")
        print(f"{icon} OVERALL: {self.pass_count}/{self.test_count} tests passed "
              f"({report['summary']['pass_rate_percent']:.1f}%)")
        print(f"[TIME] Total execution: {elapsed:.2f}s")
        print("=" * 60)

        # Save report to JSON file
        self._save_report(report)

        return report

    def _save_report(self, report: Dict[str, Any]):
        """Save the test report to a JSON file.

        Args:
            report: Complete test report dict
        """
        try:
            os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
            
            with open(self.report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n[REPORT] Test results saved to {self.report_path}")
        except Exception as e:
            print(f"[WARN] Failed to save report: {e}")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the MCP integration test runner."""
    parser = argparse.ArgumentParser(
        description="MCP Integration Test Runner — Comprehensive MCP automation testing"
    )
    parser.add_argument(
        "categories",
        nargs="*",
        default=None,
        help="Test categories to run (inspection, actor_control, level_management). Runs all if omitted."
    )
    parser.add_argument(
        "--mcp-url",
        default="http://localhost:3000/mcp",
        help="MCP server URL (default: http://localhost:3000/mcp)"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent test operations (default: 5)"
    )
    parser.add_argument(
        "--report-path",
        default=REPORT_PATH,
        help=f"Report output path (default: {REPORT_PATH})"
    )

    args = parser.parse_args()

    runner = MCPIntegrationTestRunner(
        mcp_url=args.mcp_url,
        max_concurrent=args.max_concurrent,
        report_path=args.report_path
    )

    report = runner.run_all_tests(categories=args.categories)

    # Exit with appropriate code
    if report.get("summary", {}).get("failed", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
