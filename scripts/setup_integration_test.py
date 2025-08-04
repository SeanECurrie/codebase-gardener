#!/usr/bin/env python3
"""
Setup script for integration testing.

This script sets up a real environment for testing the codebase gardener
with actual models, real file systems, and proper configuration.
"""

import os
import sys
from pathlib import Path
import subprocess
import shutil
from typing import Optional

def check_python_version():
    """Ensure we're running Python 3.11+"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

def check_dependencies():
    """Check that required packages are installed."""
    required_packages = [
        "sentence-transformers",
        "torch",
        "tree-sitter",
        "numpy",
        "pytest",
        "psutil"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n📦 Installing missing packages: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)

def setup_environment():
    """Set up environment variables and directories."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env from .env.example")
        shutil.copy(env_example, env_file)
    
    # Set up data directory
    data_dir = Path.home() / ".codebase-gardener"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "embeddings").mkdir(exist_ok=True)
    (data_dir / "models").mkdir(exist_ok=True)
    (data_dir / "projects").mkdir(exist_ok=True)
    
    print(f"✅ Data directory: {data_dir}")

def download_test_model():
    """Download the embedding model for testing."""
    print("🔮 Testing model download...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # This will download the model if not already cached
        model = SentenceTransformer("microsoft/codebert-base")
        
        # Test that it works
        test_embedding = model.encode(["def hello(): return 'world'"])
        print(f"✅ Model loaded, embedding dimension: {len(test_embedding[0])}")
        
    except Exception as e:
        print(f"❌ Model download failed: {e}")
        return False
    
    return True

def run_integration_test():
    """Run the integration test to validate everything works."""
    print("\n🧪 Running integration test...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/test_end_to_end_pipeline.py",
            "-v", "-s"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Integration test passed!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Integration test failed!")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    """Main setup function."""
    print("🌱 Codebase Gardener Integration Test Setup\n")
    
    # Check prerequisites
    check_python_version()
    check_dependencies()
    setup_environment()
    
    # Download and test model
    if not download_test_model():
        print("\n❌ Setup failed at model download")
        sys.exit(1)
    
    # Run integration test
    if not run_integration_test():
        print("\n❌ Setup failed at integration test")
        sys.exit(1)
    
    print("\n🎉 Integration test setup complete!")
    print("\nYou can now run integration tests with:")
    print("  python -m pytest tests/integration/ -v")

if __name__ == "__main__":
    main()