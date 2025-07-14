"""
Coverage analysis and gap identification for ADO Flow Hive.

This module provides tools and tests to:
- Analyze current test coverage
- Identify untested code paths
- Generate coverage reports
- Suggest improvements for test coverage
"""

import pytest
import ast
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
from unittest.mock import patch

# Coverage analysis utilities
class CoverageAnalyzer:
    """Analyze test coverage and identify gaps."""
    
    def __init__(self, source_dir: str = "src"):
        self.source_dir = Path(source_dir)
        self.test_dir = Path("tests")
    
    def analyze_function_coverage(self) -> Dict[str, List[str]]:
        """Analyze function coverage across source files."""
        coverage_report = {}
        
        for py_file in self.source_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            functions = self._extract_functions(py_file)
            tested_functions = self._find_tested_functions(py_file.stem)
            
            untested = [func for func in functions if func not in tested_functions]
            coverage_report[py_file.name] = {
                "total_functions": len(functions),
                "tested_functions": len(tested_functions),
                "untested_functions": untested,
                "coverage_percentage": (len(tested_functions) / len(functions) * 100) if functions else 100
            }
        
        return coverage_report
    
    def _extract_functions(self, file_path: Path) -> List[str]:
        """Extract function names from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except (SyntaxError, UnicodeDecodeError):
            return []
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Skip private functions
                    functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if not item.name.startswith('_'):
                            functions.append(f"{node.name}.{item.name}")
        
        return functions
    
    def _find_tested_functions(self, module_name: str) -> Set[str]:
        """Find functions that have tests."""
        tested_functions = set()
        
        test_files = list(self.test_dir.glob(f"*{module_name}*.py"))
        if not test_files:
            test_files = list(self.test_dir.glob("test_*.py"))
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for function calls and imports
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if hasattr(node.func, 'attr'):
                            tested_functions.add(node.func.attr)
                        elif hasattr(node.func, 'id'):
                            tested_functions.add(node.func.id)
                    elif isinstance(node, ast.Name):
                        tested_functions.add(node.id)
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        return tested_functions
    
    def generate_coverage_gaps_report(self) -> str:
        """Generate a comprehensive coverage gaps report."""
        coverage_data = self.analyze_function_coverage()
        
        report = []
        report.append("# Test Coverage Analysis Report")
        report.append("=" * 50)
        report.append("")
        
        total_functions = sum(data["total_functions"] for data in coverage_data.values())
        total_tested = sum(data["tested_functions"] for data in coverage_data.values())
        overall_coverage = (total_tested / total_functions * 100) if total_functions > 0 else 100
        
        report.append(f"## Overall Coverage: {overall_coverage:.1f}%")
        report.append(f"Total Functions: {total_functions}")
        report.append(f"Tested Functions: {total_tested}")
        report.append(f"Untested Functions: {total_functions - total_tested}")
        report.append("")
        
        # Per-file analysis
        report.append("## Coverage by File")
        report.append("")
        
        for filename, data in sorted(coverage_data.items()):
            report.append(f"### {filename}")
            report.append(f"- Coverage: {data['coverage_percentage']:.1f}%")
            report.append(f"- Functions: {data['tested_functions']}/{data['total_functions']}")
            
            if data["untested_functions"]:
                report.append("- **Untested functions:**")
                for func in data["untested_functions"]:
                    report.append(f"  - {func}")
            
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        priority_files = [
            (filename, data) for filename, data in coverage_data.items()
            if data["coverage_percentage"] < 80 and data["total_functions"] > 0
        ]
        
        if priority_files:
            report.append("### High Priority (< 80% coverage):")
            for filename, data in sorted(priority_files, key=lambda x: x[1]["coverage_percentage"]):
                report.append(f"- **{filename}**: {data['coverage_percentage']:.1f}% coverage")
                if data["untested_functions"]:
                    top_functions = data["untested_functions"][:3]
                    report.append(f"  - Focus on: {', '.join(top_functions)}")
        
        # Test suggestions
        report.append("")
        report.append("### Suggested Test Cases")
        report.append("")
        
        for filename, data in coverage_data.items():
            if data["untested_functions"] and data["coverage_percentage"] < 90:
                module_name = filename.replace('.py', '')
                report.append(f"**{module_name}:**")
                for func in data["untested_functions"][:5]:  # Top 5 untested functions
                    report.append(f"- `test_{func.lower().replace('.', '_')}_functionality()`")
                    report.append(f"- `test_{func.lower().replace('.', '_')}_edge_cases()`")
                report.append("")
        
        return "\n".join(report)


@pytest.mark.unit
class TestCoverageAnalysis:
    """Tests for coverage analysis functionality."""
    
    def test_coverage_analyzer_initialization(self):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer()
        assert analyzer.source_dir == Path("src")
        assert analyzer.test_dir == Path("tests")
        
        # Test with custom directories
        analyzer_custom = CoverageAnalyzer("custom_src")
        assert analyzer_custom.source_dir == Path("custom_src")

    def test_function_extraction(self):
        """Test function extraction from Python files."""
        analyzer = CoverageAnalyzer()
        
        # Create temporary Python file with functions
        test_code = '''
def public_function():
    pass

def _private_function():
    pass

class TestClass:
    def public_method(self):
        pass
    
    def _private_method(self):
        pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = Path(f.name)
        
        try:
            functions = analyzer._extract_functions(temp_file)
            assert "public_function" in functions
            assert "_private_function" not in functions  # Private functions excluded
            assert "TestClass.public_method" in functions
            assert "TestClass._private_method" not in functions  # Private methods excluded
        finally:
            temp_file.unlink()

    def test_coverage_gaps_identification(self):
        """Test identification of coverage gaps."""
        analyzer = CoverageAnalyzer()
        
        # This test will work with the actual project structure
        if analyzer.source_dir.exists():
            coverage_report = analyzer.analyze_function_coverage()
            
            # Verify report structure
            assert isinstance(coverage_report, dict)
            
            for filename, data in coverage_report.items():
                assert "total_functions" in data
                assert "tested_functions" in data
                assert "untested_functions" in data
                assert "coverage_percentage" in data
                assert isinstance(data["untested_functions"], list)
                assert 0 <= data["coverage_percentage"] <= 100

    def test_coverage_report_generation(self):
        """Test coverage report generation."""
        analyzer = CoverageAnalyzer()
        
        if analyzer.source_dir.exists():
            report = analyzer.generate_coverage_gaps_report()
            
            # Verify report content
            assert "Test Coverage Analysis Report" in report
            assert "Overall Coverage:" in report
            assert "Coverage by File" in report
            assert "Recommendations" in report
            
            # Report should be non-empty
            assert len(report.split('\n')) > 10


@pytest.mark.unit 
class TestQualityGates:
    """Tests for quality gates and standards."""
    
    def test_minimum_coverage_threshold(self):
        """Test that coverage meets minimum threshold."""
        analyzer = CoverageAnalyzer()
        
        if analyzer.source_dir.exists():
            coverage_data = analyzer.analyze_function_coverage()
            
            total_functions = sum(data["total_functions"] for data in coverage_data.values())
            total_tested = sum(data["tested_functions"] for data in coverage_data.values())
            overall_coverage = (total_tested / total_functions * 100) if total_functions > 0 else 100
            
            # Quality gate: Overall coverage should be > 60%
            # Adjust threshold based on project requirements
            MIN_COVERAGE_THRESHOLD = 60.0
            
            if overall_coverage < MIN_COVERAGE_THRESHOLD:
                pytest.fail(
                    f"Coverage {overall_coverage:.1f}% is below minimum threshold {MIN_COVERAGE_THRESHOLD}%. "
                    f"Need to test {total_functions - total_tested} more functions."
                )

    def test_critical_modules_coverage(self):
        """Test that critical modules have high coverage."""
        analyzer = CoverageAnalyzer()
        
        # Define critical modules that must have high coverage
        CRITICAL_MODULES = {
            "azure_devops_client.py": 80.0,
            "calculator.py": 85.0,
            "data_storage.py": 75.0,
            "config_manager.py": 70.0
        }
        
        if analyzer.source_dir.exists():
            coverage_data = analyzer.analyze_function_coverage()
            
            failures = []
            for module, min_coverage in CRITICAL_MODULES.items():
                if module in coverage_data:
                    actual_coverage = coverage_data[module]["coverage_percentage"]
                    if actual_coverage < min_coverage:
                        failures.append(
                            f"{module}: {actual_coverage:.1f}% < {min_coverage}%"
                        )
            
            if failures:
                pytest.fail(
                    f"Critical modules below coverage threshold:\n" + 
                    "\n".join(f"- {failure}" for failure in failures)
                )

    def test_no_uncovered_error_paths(self):
        """Test that error handling paths are covered."""
        # This is a placeholder for more sophisticated analysis
        # In a real implementation, you would analyze the AST to find
        # try/except blocks, error conditions, etc.
        
        analyzer = CoverageAnalyzer()
        
        if analyzer.source_dir.exists():
            # For now, just ensure we have some error handling tests
            test_files = list(analyzer.test_dir.glob("test_*.py"))
            
            error_test_patterns = [
                "error", "exception", "fail", "invalid", "missing", "timeout", "malformed"
            ]
            
            error_tests_found = 0
            for test_file in test_files:
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        for pattern in error_test_patterns:
                            if pattern in content:
                                error_tests_found += 1
                                break
                except (UnicodeDecodeError, OSError):
                    continue
            
            # Quality gate: Should have error handling tests in most test files
            min_error_test_files = max(1, len(test_files) // 2)
            
            if error_tests_found < min_error_test_files:
                pytest.fail(
                    f"Insufficient error handling tests. Found {error_tests_found}, "
                    f"expected at least {min_error_test_files} test files with error scenarios."
                )


@pytest.mark.integration
class TestCoverageToolsIntegration:
    """Integration tests for coverage tools."""
    
    @pytest.mark.skipif(not Path("requirements.txt").exists(), reason="No requirements.txt found")
    def test_coverage_tool_availability(self):
        """Test that coverage tools are available."""
        try:
            import coverage
            assert hasattr(coverage, 'Coverage')
        except ImportError:
            pytest.skip("Coverage tool not installed")

    def test_generate_full_coverage_report(self):
        """Generate a full coverage report using available tools."""
        analyzer = CoverageAnalyzer()
        
        if analyzer.source_dir.exists():
            # Generate detailed analysis
            report = analyzer.generate_coverage_gaps_report()
            
            # Save report to file for review
            report_file = Path("test_coverage_analysis_report.md")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"Coverage analysis report saved to: {report_file}")
            print(f"Report length: {len(report)} characters")
            
            # Verify report was created
            assert report_file.exists()
            assert report_file.stat().st_size > 0


# Fixtures for coverage testing
@pytest.fixture
def coverage_analyzer():
    """Provide CoverageAnalyzer instance."""
    return CoverageAnalyzer()


@pytest.fixture
def mock_source_files():
    """Create mock source files for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create mock source files
    files = {
        "module1.py": '''
def function1():
    pass

def function2():
    pass

class Class1:
    def method1(self):
        pass
''',
        "module2.py": '''
def function3():
    pass

def _private_function():
    pass
'''
    }
    
    for filename, content in files.items():
        file_path = temp_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
    
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


def run_coverage_analysis():
    """Utility function to run coverage analysis and print results."""
    analyzer = CoverageAnalyzer()
    
    if not analyzer.source_dir.exists():
        print("Source directory 'src' not found. Please run from project root.")
        return
    
    print("Running coverage analysis...")
    report = analyzer.generate_coverage_gaps_report()
    
    print(report)
    
    # Save to file
    with open("coverage_analysis_report.md", 'w') as f:
        f.write(report)
    
    print("\nReport saved to: coverage_analysis_report.md")


if __name__ == "__main__":
    run_coverage_analysis()