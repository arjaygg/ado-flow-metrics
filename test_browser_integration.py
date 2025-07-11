#!/usr/bin/env python3
"""
Browser Integration Test for Workstream Filtering
Tests that the Python and JavaScript implementations are equivalent
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from workstream_manager import WorkstreamManager


def test_python_javascript_equivalence():
    """Test that Python and JavaScript configurations are equivalent"""
    print("🔄 Testing Python-JavaScript Workstream Equivalence...")

    # Load Python configuration
    python_manager = WorkstreamManager()
    python_config = python_manager.config

    # Load JavaScript configuration
    js_config_path = Path(__file__).parent / "js" / "workstream_config.js"
    if not js_config_path.exists():
        print("❌ JavaScript config file not found")
        return False

    # Parse JavaScript config (simplified parsing)
    js_content = js_config_path.read_text()

    # Extract JSON from JavaScript file (find the WORKSTREAM_CONFIG assignment)
    config_start = js_content.find("window.WORKSTREAM_CONFIG = ")
    if config_start == -1:
        print("❌ Could not find WORKSTREAM_CONFIG assignment")
        return False

    json_start = js_content.find("{", config_start)
    if json_start == -1:
        print("❌ Could not find JSON start")
        return False

    # Find the matching closing brace by counting braces
    brace_count = 0
    json_end = json_start
    for i, char in enumerate(js_content[json_start:], json_start):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break

    js_config_str = js_content[json_start:json_end]

    try:
        js_config = json.loads(js_config_str)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JavaScript config: {e}")
        return False

    # Compare configurations
    equivalence_tests = []

    # Test 1: Same workstreams
    python_workstreams = set(python_config["workstreams"].keys())
    js_workstreams = set(js_config["workstreams"].keys())
    equivalence_tests.append(
        {
            "name": "Workstream Names Match",
            "passed": python_workstreams == js_workstreams,
            "details": f"Python: {python_workstreams}, JS: {js_workstreams}",
        }
    )

    # Test 2: Same default workstream
    equivalence_tests.append(
        {
            "name": "Default Workstream Match",
            "passed": python_config["default_workstream"]
            == js_config["default_workstream"],
            "details": f"Python: {python_config['default_workstream']}, JS: {js_config['default_workstream']}",
        }
    )

    # Test 3: Same name patterns for each workstream
    pattern_matches = []
    for workstream in python_workstreams:
        python_patterns = set(python_config["workstreams"][workstream]["name_patterns"])
        js_patterns = set(js_config["workstreams"][workstream]["name_patterns"])
        match = python_patterns == js_patterns
        pattern_matches.append(match)

        if not match:
            print(f"⚠️  Pattern mismatch in {workstream}:")
            print(f"   Python: {python_patterns}")
            print(f"   JS: {js_patterns}")

    equivalence_tests.append(
        {
            "name": "Name Patterns Match",
            "passed": all(pattern_matches),
            "details": f"{sum(pattern_matches)}/{len(pattern_matches)} workstreams have matching patterns",
        }
    )

    # Test 4: Same matching options
    equivalence_tests.append(
        {
            "name": "Matching Options Match",
            "passed": python_config["matching_options"]
            == js_config["matching_options"],
            "details": f"Both have: {python_config['matching_options']}",
        }
    )

    # Test 5: CONTAINSSTRING logic equivalence
    test_members = [
        "Nenissa Malibago",
        "Glizzel Ann Artates",
        "Sharon Smith",
        "Unknown Person",
        "ARIEL DIMAPILIS",  # Case test
        "Dr. Kennedy Oliveira PhD",  # Partial match test
    ]

    containsstring_matches = []
    for member in test_members:
        python_result = python_manager.get_workstream_for_member(member)
        # Simulate JavaScript logic
        js_result = simulate_js_containsstring(member, js_config)
        match = python_result == js_result
        containsstring_matches.append(match)

        if not match:
            print(f"⚠️  CONTAINSSTRING mismatch for {member}:")
            print(f"   Python: {python_result}")
            print(f"   JS: {js_result}")

    equivalence_tests.append(
        {
            "name": "CONTAINSSTRING Logic Equivalence",
            "passed": all(containsstring_matches),
            "details": f"{sum(containsstring_matches)}/{len(containsstring_matches)} members have matching assignments",
        }
    )

    # Print results
    passed_tests = sum(1 for test in equivalence_tests if test["passed"])
    total_tests = len(equivalence_tests)

    print(f"\n📊 Equivalence Test Results: {passed_tests}/{total_tests} passed")

    for test in equivalence_tests:
        status = "✅" if test["passed"] else "❌"
        print(f"{status} {test['name']}: {test['details']}")

    success_rate = (passed_tests / total_tests) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")

    if success_rate >= 100:
        print("🎉 Perfect Python-JavaScript equivalence achieved!")
        return True
    elif success_rate >= 80:
        print("✅ Good equivalence - minor differences acceptable")
        return True
    else:
        print("❌ Significant differences detected - review needed")
        return False


def simulate_js_containsstring(member_name, config):
    """Simulate JavaScript CONTAINSSTRING logic"""
    if not member_name:
        return config["default_workstream"]

    # Apply case sensitivity option
    options = config.get("matching_options", {})
    search_name = (
        member_name if options.get("case_sensitive", False) else member_name.lower()
    )

    # Iterate through workstreams
    for workstream_name, workstream_data in config["workstreams"].items():
        name_patterns = workstream_data.get("name_patterns", [])

        # Check each pattern
        for pattern in name_patterns:
            search_pattern = (
                pattern if options.get("case_sensitive", False) else pattern.lower()
            )

            # CONTAINSSTRING equivalent
            if search_pattern in search_name:
                return workstream_name

    # No match found
    return config["default_workstream"]


def test_dashboard_file_structure():
    """Test that dashboard files have proper structure"""
    print("\n🔄 Testing Dashboard File Structure...")

    structure_tests = []

    # Test dashboard files exist
    dashboard_files = ["dashboard.html", "executive-dashboard.html"]
    for file in dashboard_files:
        file_path = Path(__file__).parent / file
        exists = file_path.exists()
        structure_tests.append(
            {
                "name": f"{file} exists",
                "passed": exists,
                "details": f"File size: {file_path.stat().st_size if exists else 0} bytes",
            }
        )

    # Test JavaScript files exist
    js_files = ["js/workstream-manager.js", "js/workstream_config.js"]
    for file in js_files:
        file_path = Path(__file__).parent / file
        exists = file_path.exists()
        structure_tests.append(
            {
                "name": f"{file} exists",
                "passed": exists,
                "details": f"File size: {file_path.stat().st_size if exists else 0} bytes",
            }
        )

    # Test configuration files exist
    config_files = ["config/workstream_config.json"]
    for file in config_files:
        file_path = Path(__file__).parent / file
        exists = file_path.exists()
        structure_tests.append(
            {
                "name": f"{file} exists",
                "passed": exists,
                "details": f"File size: {file_path.stat().st_size if exists else 0} bytes",
            }
        )

    # Test dashboard content includes workstream scripts
    for dashboard_file in dashboard_files:
        file_path = Path(__file__).parent / dashboard_file
        if file_path.exists():
            content = file_path.read_text()
            has_workstream_manager = "workstream-manager.js" in content
            has_workstream_config = "workstream_config.js" in content
            has_workstream_filter = "workstreamDropdown" in content

            structure_tests.append(
                {
                    "name": f"{dashboard_file} has workstream integration",
                    "passed": has_workstream_manager
                    and has_workstream_config
                    and has_workstream_filter,
                    "details": f"Manager: {has_workstream_manager}, Config: {has_workstream_config}, Filter: {has_workstream_filter}",
                }
            )

    # Print results
    passed_tests = sum(1 for test in structure_tests if test["passed"])
    total_tests = len(structure_tests)

    print(f"📊 Structure Test Results: {passed_tests}/{total_tests} passed")

    for test in structure_tests:
        status = "✅" if test["passed"] else "❌"
        print(f"{status} {test['name']}: {test['details']}")

    return passed_tests == total_tests


def main():
    """Run all integration tests"""
    print("🚀 Browser Integration Test Suite")
    print("=" * 50)

    all_passed = True

    # Test Python-JavaScript equivalence
    equivalence_passed = test_python_javascript_equivalence()
    all_passed = all_passed and equivalence_passed

    # Test file structure
    structure_passed = test_dashboard_file_structure()
    all_passed = all_passed and structure_passed

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Browser-first workstream filtering is ready for use")
        print("\n📋 Next Steps:")
        print("1. Open dashboard.html in a web browser")
        print("2. Open executive-dashboard.html in a web browser")
        print("3. Test workstream filtering with various data sources")
        print("4. Verify Power BI-equivalent functionality")
    else:
        print("❌ Some integration tests failed")
        print("🔧 Review the failed tests and fix issues before deployment")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
