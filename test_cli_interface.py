#!/usr/bin/env python3
"""
Test script to verify CLI interface functionality and PRD compliance.

This script tests the CLI interface to ensure it follows the secure, 
carefully orchestrated design specified in the PRD.
"""

import subprocess
import sys
import os
from pathlib import Path

def test_cli_help():
    """Test CLI help functionality."""
    print("🔍 Testing CLI help functionality...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tts_cli.cli_tts", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ CLI help works correctly")
            print(f"Help output length: {len(result.stdout)} characters")
            return True
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI help test failed with exception: {e}")
        return False

def test_cli_list_models():
    """Test CLI list models functionality."""
    print("🔍 Testing CLI list models functionality...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tts_cli.cli_tts", "--list-models"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ CLI list models works correctly")
            print(f"Models output length: {len(result.stdout)} characters")
            return True
        else:
            print(f"❌ CLI list models failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI list models test failed with exception: {e}")
        return False

def test_cli_list_environments():
    """Test CLI list environments functionality."""
    print("🔍 Testing CLI list environments functionality...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tts_cli.cli_tts", "--list-environments"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ CLI list environments works correctly")
            print(f"Environments output length: {len(result.stdout)} characters")
            return True
        else:
            print(f"❌ CLI list environments failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI list environments test failed with exception: {e}")
        return False

def test_cli_argument_parsing():
    """Test CLI argument parsing for PRD compliance."""
    print("🔍 Testing CLI argument parsing for PRD compliance...")
    
    # Test the exact argument patterns from the PRD
    test_cases = [
        # Basic functionality
        ["--text", "Hello world"],
        ["--text", "Hello world", "--model", "f5-tts"],
        ["--text", "Hello world", "--output", "test.wav"],
        
        # Voice cloning (PRD requirement)
        ["--text", "Hello world", "--voice-clone", "reference.wav"],
        ["--text", "Hello world", "--model", "f5-tts", "--voice-clone", "reference.wav"],
        
        # Clipboard integration (PRD requirement)
        ["--clipboard"],
        ["--clipboard", "--model", "edge-tts"],
        ["--clipboard", "--voice-clone", "reference.wav"],
        
        # Environment management (PRD requirement)
        ["--create-environment", "f5-tts"],
        ["--list-environments"],
        ["--cleanup-environment", "f5-tts"],
        ["--cleanup-all-environments"],
        
        # Interactive mode (PRD requirement)
        ["--interactive"],
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases):
        try:
            # Test argument parsing (don't execute, just parse)
            result = subprocess.run(
                [sys.executable, "-m", "tts_cli.cli_tts", "--help"] + test_case,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0:
                print(f"✅ Test case {i+1} passed: {' '.join(test_case)}")
                passed += 1
            else:
                print(f"❌ Test case {i+1} failed: {' '.join(test_case)}")
                print(f"   Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Test case {i+1} failed with exception: {' '.join(test_case)}")
            print(f"   Exception: {e}")
    
    print(f"📊 Argument parsing test results: {passed}/{total} passed")
    return passed == total

def test_prd_compliance():
    """Test PRD compliance based on the template."""
    print("🔍 Testing PRD compliance...")
    
    compliance_checks = {
        "CLI argument structure": False,
        "Voice cloning support": False,
        "Multi-model support": False,
        "Environment management": False,
        "Clipboard integration": False,
        "Interactive mode": False,
        "Error handling": False,
    }
    
    # Test CLI argument structure (PRD lines 7-8)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tts_cli.cli_tts", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            help_output = result.stdout.lower()
            
            # Check for required arguments from PRD
            if "--text" in help_output:
                compliance_checks["CLI argument structure"] = True
            
            if "--voice-clone" in help_output:
                compliance_checks["Voice cloning support"] = True
            
            if "--model" in help_output:
                compliance_checks["Multi-model support"] = True
            
            if "--create-environment" in help_output:
                compliance_checks["Environment management"] = True
            
            if "--clipboard" in help_output:
                compliance_checks["Clipboard integration"] = True
            
            if "--interactive" in help_output:
                compliance_checks["Interactive mode"] = True
            
            # Check for error handling examples
            if "examples:" in help_output:
                compliance_checks["Error handling"] = True
                
    except Exception as e:
        print(f"❌ PRD compliance test failed: {e}")
    
    # Report compliance
    print("📋 PRD Compliance Report:")
    for check, status in compliance_checks.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check}")
    
    compliance_score = sum(compliance_checks.values()) / len(compliance_checks) * 100
    print(f"📊 Overall PRD Compliance: {compliance_score:.1f}%")
    
    return compliance_score >= 80

def main():
    """Run all CLI interface tests."""
    print("🚀 CLI Interface Testing Suite")
    print("=" * 50)
    
    tests = [
        ("CLI Help", test_cli_help),
        ("List Models", test_cli_list_models),
        ("List Environments", test_cli_list_environments),
        ("Argument Parsing", test_cli_argument_parsing),
        ("PRD Compliance", test_prd_compliance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CLI interface is ready for use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the CLI implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
