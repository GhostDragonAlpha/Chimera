"""
Playtest Runner — Executes automated behavioral tests using Unreal Engine's automation framework.

Uses UE's built-in Automation Test framework to execute generated test modules
in a headless, deterministic manner via -NullRHI, -Unattended, -NoPause flags.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional


class TestResult:
    """Represents the result of a single test execution."""
    
    def __init__(self, test_name: str, status: str, duration_ms: int = 0):
        self.test_name = test_name
        self.status = status  # PASSED, FAILED, SKIPPED
        self.duration_ms = duration_ms
        self.assertions = []
        self.statistics = None
        self.suggestion = None


class PlaytestReport:
    """Represents the complete playtest report."""
    
    def __init__(self):
        self.timestamp = ""
        self.project = ""
        self.summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "pass_rate": 0.0
        }
        self.tests = []


class PlaytestRunner:
    """Executes automated behavioral tests using UE's automation framework."""

    def __init__(self, project_path: str, test_spec: dict):
        """Initialize with path to compiled .uproject and parsed test DSL."""
        self.project_path = Path(project_path)
        self.test_spec = test_spec
        self.ue_root = self._find_ue_root()

    def _find_ue_root(self) -> Optional[str]:
        """Find Unreal Engine installation root using detection order: UE_ROOT env var → common paths scan."""
        # Check UE_ROOT environment variable first
        ue_root = os.environ.get('UE_ROOT')
        if ue_root and Path(ue_root).exists():
            engine_binaries = Path(ue_root) / "Engine" / "Binaries" / "Win64"
            if (engine_binaries / "UnrealEditor-Cmd.exe").exists():
                return str(Path(ue_root).resolve())
            
            # Also check DotNET/UnrealBuildTool path for UBT compatibility
            ubt_path = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
            if ubt_path.exists():
                return str(Path(ue_root).resolve())
            
            ubt_legacy_path = Path(ue_root) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool.exe"
            if ubt_legacy_path.exists():
                return str(Path(ue_root).resolve())

        # Try common Windows UE installation paths in order of likelihood
        common_paths = [
            r"C:\Program Files\Epic Games\UE_5.8",
            r"C:\Program Files\Epic Games\UE_5.7",
            r"C:\Program Files\Epic Games\UE_5.6",
            r"C:\Program Files\Epic Games\UE_5.5",
            r"C:\Program Files\Epic Games\UE_5.4"
        ]
        
        for path in common_paths:
            engine_binaries = Path(path) / "Engine" / "Binaries" / "Win64"
            if (engine_binaries / "UnrealEditor-Cmd.exe").exists():
                return str(Path(path).resolve())
                
        # Fallback: check DotNET paths for UE 5.8+
        for path in common_paths:
            ubt_path = Path(path) / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealEditor-Cmd.exe"
            if ubt_path.exists():
                return str(Path(path).resolve())
            
            ubt_legacy_path = Path(path) / "Engine" / "Binaries" / "DotNET" / "UnrealEditor-Cmd.exe"
            if ubt_legacy_path.exists():
                return str(Path(path).resolve())
                
        return None

    def run_all_tests(self) -> PlaytestReport:
        """Execute all tests and return structured results."""
        report = PlaytestReport()
        report.timestamp = "playtest_execution_timestamp"
        
        if not self.ue_root:
            # UE not available - mark all tests as skipped
            test_defs = self.test_spec.get("tests", {}).get("test_definitions", [])
            for td in test_defs:
                test_result = TestResult(td.get("name", "Unknown"), "SKIPPED")
                test_result.suggestion = "UE editor executable not found at expected path. Install Unreal Engine 5.x or set UE_ROOT to enable automated playtesting."
                report.tests.append(test_result)
                
            report.summary["skipped"] = len(test_defs)
            report.summary["total_tests"] = len(test_defs)
            report.summary["pass_rate"] = 0.0 if test_defs else 1.0
            return report

        # Extract test names to run
        test_defs = self.test_spec.get("tests", {}).get("test_definitions", [])
        test_names = [td.get("name", "Unknown") for td in test_defs]
        
        # Execute tests via UE automation
        results = self._execute_ue_automation(test_names)

        if not results and test_defs:
            # Final fallback: simulated/empty results with all tests marked as failed or skipped based on context
            print("[PlaytestRunner] No test execution results obtained, applying fallback.")
            for test_name in test_names:
                results[test_name] = {
                    "status": "FAILED",
                    "duration_ms": 0,
                    "suggestion": "Test execution could not be performed. Check build and UE automation logs."
                }

        # Build report from results
        for test_name, result_data in results.items():
            test_result = TestResult(
                test_name,
                result_data.get("status", "FAILED"),
                result_data.get("duration_ms", 0)
            )
            test_result.assertions = result_data.get("assertions", [])
            if "statistics" in result_data:
                test_result.statistics = result_data["statistics"]
            if "suggestion" in result_data:
                test_result.suggestion = result_data["suggestion"]
                
            report.tests.append(test_result)
            
        # Calculate summary
        total = len(report.tests)
        passed = sum(1 for t in report.tests if t.status == "PASSED")
        failed = sum(1 for t in report.tests if t.status == "FAILED")
        skipped = sum(1 for t in report.tests if t.status == "SKIPPED")
        
        report.summary["total_tests"] = total
        report.summary["passed"] = passed
        report.summary["failed"] = failed
        report.summary["skipped"] = skipped
        report.summary["pass_rate"] = passed / total if total > 0 else 0.0
        
        return report

    def run_test(self, test_name: str) -> TestResult:
        """Execute a single test by name."""
        # Filter to just this test
        filtered_spec = {"tests": {"test_definitions": [td for td in self.test_spec.get("tests", {}).get("test_definitions", []) if td.get("name") == test_name]}}
        
        report = self.run_all_tests()
        for t in report.tests:
            if t.test_name == test_name:
                return t
                
        return TestResult(test_name, "SKIPPED")

    def run_tests_by_type(self, test_type: str) -> PlaytestReport:
        """Run only unit/integration/balance tests."""
        filtered_spec = {
            "tests": {
                "test_definitions": [
                    td for td in self.test_spec.get("tests", {}).get("test_definitions", [])
                    if td.get("type") == test_type
                ]
            }
        }
        
        # Create a temporary runner with filtered spec
        temp_runner = PlaytestRunner(self.project_path, filtered_spec)
        return temp_runner.run_all_tests()


    def _execute_ue_automation(self, test_names: List[str]) -> Dict[str, Any]:
        """Execute UE automation tests and parse results with RHI fallback chain."""
        if not self.ue_root:
            return {}
            
        editor_cmd = Path(self.ue_root) / "Engine" / "Binaries" / "Win64" / "UnrealEditor-Cmd.exe"
        
        if not editor_cmd.exists():
            return {}
            
        # Build automation command - using standard UE automation framework output to stdout/stderr
        project_name = self.project_path.stem
        exec_cmds = f'Automation RunTests {project_name}Tests; Quit'
        
        # RHI flags to try in fallback order for headless/CI testing:
        # 1. --dx11 (UE's standard DX11 flag) + -ForceD3D11RHI
        # 2. --d3d12 + -ForceD3D12RHI  
        # 3. --vulkan + -ForceVulkanRHI
        # 4. Render off-screen with Null RHI but proper module loading
        rhi_attempts = [
            ["--dx11", "-ForceD3D11RHI"],
            ["--d3d12", "-ForceD3D12RHI"],
            ["--vulkan", "-ForceVulkanRHI"],
            [],  # Fallback to default (which may use Null RHI but without -NullRHI flag)
        ]
        
        for rhi_flags in rhi_attempts:
            cmd_args = [
                str(editor_cmd),
                str(self.project_path),
                "-ExecCmds=" + exec_cmds,
                "-Log",
                "-NoSound",
                "-NoSplash",
                "-Unattended",
                "-NoPause",
                "-TestExit=Automation Test Queue Empty"
            ]
            
            # Add RHI flags if present
            for rhi_flag in rhi_flags:
                cmd_args.append(rhi_flag)
            
            results = {}
            
            try:
                # Execute UE automation command
                process = subprocess.run(
                    cmd_args,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                # Parse output for test results
                output = process.stdout + process.stderr
                
                # Check if module initialization succeeded (look for success indicators or absence of init errors)
                if "could not be successfully initialized after it was loaded" in output or "Engine exit requested" in output:
                    # Module init failed with this RHI flag, try the next one
                    continue
                    
                # Extract test results from UE automation output
                # UE 5.8 automation outputs lines like:
                # "LogAutomation: Test '<ModuleName>.TestName' Passed." or "... Failed."
                # Also supports: "LogAutomation: Test '<ModuleName>.<TestName>' passed/failed"
                has_valid_results = False
                for test_name in test_names:
                    # Pattern matches: LogAutomation: Test 'TddtestsuitegameTests.DashCooldownCorrect' Passed.
                    test_pattern = rf"LogAutomation:\s*Test\s+'[^']*\.{re.escape(test_name)}'\s+(Passed|Failed|passed|failed)"
                    match = re.search(test_pattern, output, re.IGNORECASE)
                    
                    if match:
                        status = "PASSED" if match.group(1).lower() == 'passed' else "FAILED"
                        results[test_name] = {
                            "status": status,
                            "duration_ms": 0
                        }
                        has_valid_results = True
                    else:
                        # Check for UE's alternative format: "Test '<ModuleName>.<TestName>' Passed/Failed"
                        alt_pattern = rf"Test\s+'[^']*\.{re.escape(test_name)}'\s+(Passed|Failed)"
                        alt_match = re.search(alt_pattern, output, re.IGNORECASE)
                        
                        if alt_match:
                            status = "PASSED" if alt_match.group(1).lower() == 'passed' else "FAILED"
                            results[test_name] = {
                                "status": status,
                                "duration_ms": 0
                            }
                            has_valid_results = True
                        else:
                            # Check for skipped or not found
                            skipped_pattern = rf"Test\s+'[^']*\.{re.escape(test_name)}'\s+Skipped|skipped.*{re.escape(test_name)}"
                            if re.search(skipped_pattern, output, re.IGNORECASE):
                                results[test_name] = {
                                    "status": "SKIPPED",
                                    "duration_ms": 0
                                }
                                has_valid_results = True
                            else:
                                # Default to failed if not explicitly passed or skipped
                                results[test_name] = {
                                    "status": "FAILED",
                                    "duration_ms": 0,
                                    "suggestion": f"Test execution did not produce explicit result for {test_name}. Check UE automation logs in Saved/Logs directory."
                                }

                # If we got valid results or no module init errors, return these results
                if has_valid_results or len(results) == len(test_names):
                    return results
                    
            except subprocess.TimeoutExpired:
                # Timeout - this RHI flag failed, try the next one
                continue
            except Exception as e:
                # Execution error with this RHI flag, try the next one
                continue
                
        # All RHI flags failed - fall back to simulated/empty results with clear warning
        print(f"[PlaytestRunner] All RHI initialization attempts (--dx11/-ForceD3D11RHI, --d3d12/-ForceD3D12RHI, --vulkan/-ForceVulkanRHI, default) failed. Falling back to simulated test results.")
        
        results = {}
        for test_name in test_names:
            results[test_name] = {
                "status": "FAILED",
                "duration_ms": 0,
                "suggestion": f"UE automation tests could not initialize game modules with any RHI configuration. Check GPU drivers or UE logs in Saved/Logs/{project_name}.log."
            }
            
        return results
