"""
HIGH TECH MOBILE - Production ZIP Packager
Creates a clean, production-ready deployable zip archive.
"""
import os
import zipfile

def create_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_filename = os.path.join(base_dir, "high_tech_mobile_production.zip")
    
    # Exclude unwanted cache and test files
    exclude_dirs = {'__pycache__', '.pytest_cache', '.git', '.vscode', '.gemini', 'tests'}
    exclude_extensions = {'.pyc', '.pyo', '.log'}
    exclude_files = {'test_app.py', 'make_production_zip.py'}
    
    print(f"[*] Packaging HIGH TECH MOBILE into: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.endswith(tuple(exclude_extensions)):
                    continue
                if file == "high_tech_mobile_production.zip":
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                zipf.write(full_path, rel_path)
                
    file_size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    print(f"[SUCCESS] Production package created successfully!")
    print(f" - Path: {zip_filename}")
    print(f" - Size: {file_size_mb:.2f} MB")

if __name__ == '__main__':
    create_zip()
