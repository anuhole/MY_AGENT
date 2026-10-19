"""
AutoTestAI - Quick Verification Script
Runs diagnostics on the environment, dependencies, and backend services.
"""
import sys
import os

def check_mark(success):
    return "✅ PASS" if success else "❌ FAIL"

def main():
    print("=" * 60)
    print("🤖 AutoTestAI Environment & Setup Verification")
    print("=" * 60)

    # 1. Python Check
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 9)
    print(f"\n1. Python Version: {py_ver} -> {check_mark(py_ok)}")
    if not py_ok:
        print("   ⚠️ Python 3.9+ is recommended.")

    # 2. File Structure Check
    base_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        os.path.join(base_dir, "backend", "app", "main.py"),
        os.path.join(base_dir, "backend", "requirements.txt"),
        os.path.join(base_dir, "frontend", "index.html"),
        os.path.join(base_dir, "frontend", "styles.css"),
        os.path.join(base_dir, "frontend", "app.js"),
    ]

    print("\n2. Project Files:")
    for f in required_files:
        rel = os.path.relpath(f, base_dir)
        exists = os.path.exists(f)
        print(f"   - {rel}: {check_mark(exists)}")

    # 3. Dependency Check
    print("\n3. Core Python Dependencies:")
    deps = ["fastapi", "uvicorn", "pydantic", "openpyxl", "docx", "bs4", "jinja2"]
    for dep in deps:
        try:
            __import__(dep)
            print(f"   - {dep}: {check_mark(True)}")
        except ImportError:
            print(f"   - {dep}: {check_mark(False)} (install via: pip install -r backend/requirements.txt)")

    # 4. Instructions
    print("\n" + "=" * 60)
    print("🚀 How to Launch:")
    print("=" * 60)
    print("Option A (Frontend Only - Immediate Test):")
    print(f"   Open: file:///{os.path.join(base_dir, 'frontend', 'index.html').replace(os.sep, '/')}")
    print("\nOption B (Full Stack with Backend):")
    print("   Terminal 1: cd backend && uvicorn app.main:app --reload --port 8000")
    print("   Terminal 2: cd frontend && python -m http.server 3000")
    print("   Visit:      http://localhost:3000")
    print("=" * 60)

if __name__ == "__main__":
    main()
