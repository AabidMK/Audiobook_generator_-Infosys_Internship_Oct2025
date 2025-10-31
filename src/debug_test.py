print("🚀 DEBUG TEST - STEP 1")
print("If you see this, basic Python works!")

try:
    import os
    print("✓ os module imported successfully")
    
    import fitz
    print("✓ PyMuPDF (fitz) imported successfully")
    
    from audiobook_generator import AudiobookGenerator
    print("✓ AudiobookGenerator imported successfully")
    
    print(f"📁 Current directory: {os.getcwd()}")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

input("Press Enter to exit...")