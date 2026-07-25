#!/usr/bin/env python
"""
Test runner for Anomaly Detection System
"""

import subprocess
import sys
import os
import argparse

def run_tests_with_coverage():
    """Run all tests with coverage"""
    print("🚀 Running tests with coverage...\n")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=app",
        "--cov-report=html:coverage_html_report",
        "--cov-report=term",
        "--tb=short",
        "--maxfail=1"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("📊 Coverage report: coverage_html_report/index.html")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
        print("=" * 60)
        return False

def run_quick_tests():
    """Run quick tests only (no coverage)"""
    print("🚀 Running quick tests...\n")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "not slow",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode == 0

def run_specific_test(test_path):
    """Run a specific test file or test"""
    print(f"🚀 Running test: {test_path}\n")
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=long"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode == 0

def run_performance_tests():
    """Run performance tests"""
    print("🚀 Running performance tests...\n")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_performance.py",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Run tests for Anomaly Detection System')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--test', type=str, help='Run specific test file or test path')
    parser.add_argument('--no-coverage', action='store_true', help='Run without coverage')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_specific_test(args.test)
    elif args.quick:
        success = run_quick_tests()
    elif args.performance:
        success = run_performance_tests()
    else:
        success = run_tests_with_coverage()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()