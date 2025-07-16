#!/usr/bin/env python3
"""
Comprehensive Test Pyramid Execution Script
Runs all tests according to the testing pyramid principle (70% unit, 20% integration, 10% e2e)
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime


class TestPyramidRunner:
    """Runs comprehensive test pyramid for advanced filtering functionality."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "pyramid_distribution": {
                "unit_tests": {"target_percentage": 70, "actual_count": 0, "passed": 0, "failed": 0},
                "integration_tests": {"target_percentage": 20, "actual_count": 0, "passed": 0, "failed": 0},
                "e2e_tests": {"target_percentage": 10, "actual_count": 0, "passed": 0, "failed": 0}
            },
            "detailed_results": [],
            "summary": {},
            "coverage": {},
            "performance": {}
        }
    
    def run_unit_tests(self):
        """Run unit tests (70% of pyramid)."""
        print("🔧 Running Unit Tests (70% of pyramid)...")
        
        unit_test_files = [
            "tests/unit/test_web_server_endpoints.py",
            "tests/unit/test_advanced_filtering.py"
        ]
        
        unit_results = []
        for test_file in unit_test_files:
            if Path(test_file).exists():
                print(f"  Running {test_file}...")
                result = self._run_pytest(test_file, "unit")
                unit_results.append(result)
                
                # Update pyramid stats
                self.results["pyramid_distribution"]["unit_tests"]["actual_count"] += result["test_count"]
                self.results["pyramid_distribution"]["unit_tests"]["passed"] += result["passed"]
                self.results["pyramid_distribution"]["unit_tests"]["failed"] += result["failed"]
        
        self.results["detailed_results"].extend(unit_results)
        print(f"✅ Unit tests completed: {self.results['pyramid_distribution']['unit_tests']}")
    
    def run_integration_tests(self):
        """Run integration tests (20% of pyramid)."""
        print("🔗 Running Integration Tests (20% of pyramid)...")
        
        integration_test_files = [
            "tests/integration/test_filtering_integration.py"
        ]
        
        integration_results = []
        for test_file in integration_test_files:
            if Path(test_file).exists():
                print(f"  Running {test_file}...")
                result = self._run_pytest(test_file, "integration")
                integration_results.append(result)
                
                # Update pyramid stats
                self.results["pyramid_distribution"]["integration_tests"]["actual_count"] += result["test_count"]
                self.results["pyramid_distribution"]["integration_tests"]["passed"] += result["passed"]
                self.results["pyramid_distribution"]["integration_tests"]["failed"] += result["failed"]
        
        self.results["detailed_results"].extend(integration_results)
        print(f"✅ Integration tests completed: {self.results['pyramid_distribution']['integration_tests']}")
    
    def run_e2e_tests(self):
        """Run end-to-end tests (10% of pyramid)."""
        print("🌐 Running E2E Tests (10% of pyramid)...")
        
        e2e_test_files = [
            "tests/e2e/test_filtering_workflow.py"
        ]
        
        e2e_results = []
        for test_file in e2e_test_files:
            if Path(test_file).exists():
                print(f"  Running {test_file}...")
                result = self._run_pytest(test_file, "e2e")
                e2e_results.append(result)
                
                # Update pyramid stats
                self.results["pyramid_distribution"]["e2e_tests"]["actual_count"] += result["test_count"]
                self.results["pyramid_distribution"]["e2e_tests"]["passed"] += result["passed"]
                self.results["pyramid_distribution"]["e2e_tests"]["failed"] += result["failed"]
        
        self.results["detailed_results"].extend(e2e_results)
        print(f"✅ E2E tests completed: {self.results['pyramid_distribution']['e2e_tests']}")
    
    def _run_pytest(self, test_file, test_type):
        """Run pytest on a specific test file."""
        start_time = time.time()
        
        try:
            # Run pytest with verbose output and JSON report
            cmd = [
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v",
                "--tb=short",
                "--disable-warnings"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse pytest output
            output_lines = result.stdout.split('\n')
            
            # Count tests
            test_count = 0
            passed = 0
            failed = 0
            skipped = 0
            
            for line in output_lines:
                if " PASSED" in line:
                    passed += 1
                    test_count += 1
                elif " FAILED" in line:
                    failed += 1
                    test_count += 1
                elif " SKIPPED" in line:
                    skipped += 1
                    test_count += 1
            
            # Extract summary line
            summary_line = ""
            for line in output_lines:
                if "passed" in line and "failed" in line or "passed" in line and "error" in line:
                    summary_line = line
                    break
                elif line.startswith("=") and ("passed" in line or "failed" in line):
                    summary_line = line
                    break
            
            return {
                "file": test_file,
                "type": test_type,
                "test_count": test_count,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration": duration,
                "return_code": result.returncode,
                "summary": summary_line,
                "stdout": result.stdout[:1000] if result.stdout else "",  # Truncate for storage
                "stderr": result.stderr[:500] if result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "file": test_file,
                "type": test_type,
                "test_count": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "duration": 300,
                "return_code": -1,
                "summary": "Test timed out after 5 minutes",
                "stdout": "",
                "stderr": "Timeout"
            }
        except Exception as e:
            return {
                "file": test_file,
                "type": test_type,
                "test_count": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "duration": 0,
                "return_code": -1,
                "summary": f"Error running test: {str(e)}",
                "stdout": "",
                "stderr": str(e)
            }
    
    def calculate_pyramid_compliance(self):
        """Calculate how well the test distribution follows the pyramid principle."""
        total_tests = (
            self.results["pyramid_distribution"]["unit_tests"]["actual_count"] +
            self.results["pyramid_distribution"]["integration_tests"]["actual_count"] +
            self.results["pyramid_distribution"]["e2e_tests"]["actual_count"]
        )
        
        if total_tests == 0:
            return {
                "compliance": 0, 
                "message": "No tests found",
                "actual_distribution": {"unit": 0, "integration": 0, "e2e": 0},
                "target_distribution": {"unit": 70, "integration": 20, "e2e": 10},
                "total_tests": 0
            }
        
        unit_percentage = (self.results["pyramid_distribution"]["unit_tests"]["actual_count"] / total_tests) * 100
        integration_percentage = (self.results["pyramid_distribution"]["integration_tests"]["actual_count"] / total_tests) * 100
        e2e_percentage = (self.results["pyramid_distribution"]["e2e_tests"]["actual_count"] / total_tests) * 100
        
        # Calculate compliance score
        unit_target = 70
        integration_target = 20
        e2e_target = 10
        
        unit_compliance = max(0, 100 - abs(unit_percentage - unit_target))
        integration_compliance = max(0, 100 - abs(integration_percentage - integration_target))
        e2e_compliance = max(0, 100 - abs(e2e_percentage - e2e_target))
        
        overall_compliance = (unit_compliance + integration_compliance + e2e_compliance) / 3
        
        return {
            "compliance": round(overall_compliance, 2),
            "actual_distribution": {
                "unit": round(unit_percentage, 1),
                "integration": round(integration_percentage, 1),
                "e2e": round(e2e_percentage, 1)
            },
            "target_distribution": {
                "unit": unit_target,
                "integration": integration_target,
                "e2e": e2e_target
            },
            "total_tests": total_tests
        }
    
    def generate_summary(self):
        """Generate comprehensive test summary."""
        total_passed = sum(r["passed"] for r in self.results["detailed_results"])
        total_failed = sum(r["failed"] for r in self.results["detailed_results"])
        total_skipped = sum(r["skipped"] for r in self.results["detailed_results"])
        total_tests = total_passed + total_failed + total_skipped
        total_duration = sum(r["duration"] for r in self.results["detailed_results"])
        
        pyramid_compliance = self.calculate_pyramid_compliance()
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "success_rate": round((total_passed / total_tests) * 100, 2) if total_tests > 0 else 0,
            "total_duration": round(total_duration, 2),
            "pyramid_compliance": pyramid_compliance,
            "status": "PASSED" if total_failed == 0 else "FAILED"
        }
    
    def print_summary(self):
        """Print test summary to console."""
        summary = self.results["summary"]
        pyramid = summary["pyramid_compliance"]
        
        print("\n" + "="*80)
        print("🏗️  TEST PYRAMID EXECUTION SUMMARY")
        print("="*80)
        
        print(f"📊 Overall Results:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Skipped: {summary['skipped']} ⏭️")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Duration: {summary['total_duration']} seconds")
        print(f"   Status: {summary['status']}")
        
        print(f"\n🏗️  Test Pyramid Compliance: {pyramid['compliance']}%")
        print(f"   Target Distribution - Unit: 70%, Integration: 20%, E2E: 10%")
        print(f"   Actual Distribution - Unit: {pyramid['actual_distribution']['unit']}%, Integration: {pyramid['actual_distribution']['integration']}%, E2E: {pyramid['actual_distribution']['e2e']}%")
        
        print(f"\n📈 Per Test Type:")
        for test_type in ["unit_tests", "integration_tests", "e2e_tests"]:
            data = self.results["pyramid_distribution"][test_type]
            print(f"   {test_type.replace('_', ' ').title()}: {data['actual_count']} tests ({data['passed']} passed, {data['failed']} failed)")
        
        if summary["failed"] > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results["detailed_results"]:
                if result["failed"] > 0:
                    print(f"   {result['file']}: {result['summary']}")
        
        print("="*80)
    
    def save_results(self, output_file="test_pyramid_results.json"):
        """Save detailed results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"💾 Detailed results saved to {output_file}")
    
    def run_all_tests(self):
        """Run the complete test pyramid."""
        print("🚀 Starting Comprehensive Test Pyramid Execution")
        print("📋 Following Testing Pyramid Principle: 70% Unit, 20% Integration, 10% E2E")
        print("-" * 80)
        
        start_time = time.time()
        
        # Run all test levels
        self.run_unit_tests()
        print()
        self.run_integration_tests()
        print()
        self.run_e2e_tests()
        print()
        
        # Generate summary
        self.generate_summary()
        self.results["summary"]["total_execution_time"] = round(time.time() - start_time, 2)
        
        # Print and save results
        self.print_summary()
        self.save_results()
        
        # Return success status
        return self.results["summary"]["status"] == "PASSED"


if __name__ == "__main__":
    runner = TestPyramidRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)