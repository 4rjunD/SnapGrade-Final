#!/usr/bin/env python3
"""
Test script to verify cross-platform Poppler detection and PDF processing.
"""

import sys
import os
import platform

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_poppler_detection():
    """Test the cross-platform Poppler detection."""
    print("=== Cross-Platform Poppler Detection Test ===\n")
    
    try:
        from file_processor.document_processor import _get_poppler_path, _get_platform_install_instructions
        
        print(f"Operating System: {platform.system()}")
        print(f"Platform: {platform.platform()}")
        print()
        
        # Test Poppler detection
        poppler_path = _get_poppler_path()
        
        if poppler_path:
            print(f"✓ Poppler found at: {poppler_path}")
        else:
            print("✓ Poppler found in system PATH (or will use system PATH)")
        
        # Test pdf2image import
        try:
            from pdf2image import convert_from_bytes
            print("✓ pdf2image library imported successfully")
        except ImportError as e:
            print(f"✗ pdf2image import failed: {e}")
            return False
        
        # Test with a minimal PDF conversion (this will fail without a real PDF, but shows Poppler status)
        try:
            if poppler_path:
                # This will fail but should give us Poppler-specific error info
                convert_from_bytes(b"dummy", dpi=150, poppler_path=poppler_path)
            else:
                convert_from_bytes(b"dummy", dpi=150)
        except Exception as e:
            error_msg = str(e).lower()
            if "poppler" in error_msg or "unable to get page count" in error_msg:
                print(f"✗ Poppler error detected: {e}")
                print("\nInstallation instructions:")
                print(_get_platform_install_instructions())
                return False
            else:
                print("✓ No Poppler-related errors (expected error for dummy data)")
        
        print("\n🎉 Cross-platform setup successful!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

def main():
    """Main test function."""
    success = test_poppler_detection()
    
    if success:
        print("\n✅ Your system should now work on both Windows and macOS!")
    else:
        print("\n❌ There are still issues that need to be resolved.")
        print("Please follow the installation instructions above.")

if __name__ == "__main__":
    main()
