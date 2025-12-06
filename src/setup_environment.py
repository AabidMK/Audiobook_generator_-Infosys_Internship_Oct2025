import subprocess
import sys
import os

def install_packages():
    """Install required packages"""
    packages = [
        "langchain-community",
        "chromadb", 
        "pypdf",
        "sentence-transformers",
        "numpy",
        "reportlab"
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
    
    print("\n✅ All packages installed!")

def create_directories():
    """Create necessary directories"""
    directories = ["./documents", "./chroma_db", "./output"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

if __name__ == "__main__":
    install_packages()
    create_directories()
    print("\n🎉 Environment setup completed!")
    print("\nNext steps:")
    print("1. Download Ollama from https://ollama.ai/")
    print("2. Run: ollama serve")
    print("3. Run: ollama pull nomic-embed-text")
    print("4. Add your PDF files to the 'documents' folder")
    print("5. Run: python final_reg_system.py")