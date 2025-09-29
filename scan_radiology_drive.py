#!/usr/bin/env python3
"""
Scan and preview radiology materials on X drive
"""

import os
from pathlib import Path
import collections

def scan_radiology_drive():
    """Scan the X drive for radiology materials"""
    
    source_dir = Path(r"X:\Subfolders\Rads HDD")
    
    print("=== RADIOLOGY DRIVE SCANNER ===")
    print(f"Scanning: {source_dir}")
    
    if not source_dir.exists():
        print(f"ERROR: Directory does not exist: {source_dir}")
        print("\nPossible solutions:")
        print("1. Check if the X: drive is mounted")
        print("2. Verify the path is correct")
        print("3. Ensure you have read access to the directory")
        return False
    
    print("SUCCESS: Directory exists, scanning files...")
    
    # Track file statistics
    file_stats = collections.defaultdict(int)
    total_size = 0
    sample_files = []
    
    supported_extensions = {'.pdf', '.ppt', '.pptx'}
    
    try:
        # Scan all files
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_stats[ext] += 1
                
                if ext in supported_extensions:
                    try:
                        size = file_path.stat().st_size
                        total_size += size
                        
                        # Collect sample files
                        if len(sample_files) < 20:
                            sample_files.append({
                                'name': file_path.name,
                                'path': str(file_path.relative_to(source_dir)),
                                'size_mb': size / (1024 * 1024),
                                'type': ext
                            })
                    except (PermissionError, OSError):
                        print(f"WARNING: Cannot access: {file_path}")
        
        # Display results
        print(f"\nFILE STATISTICS:")
        print(f"Total supported files found: {sum(file_stats[ext] for ext in supported_extensions)}")
        
        for ext in sorted(supported_extensions):
            count = file_stats[ext]
            print(f"  {ext.upper()} files: {count}")
        
        print(f"\nTotal size: {total_size / (1024**3):.2f} GB")
        
        print(f"\nSAMPLE FILES (first 20):")
        for i, file_info in enumerate(sample_files, 1):
            print(f"{i:2d}. {file_info['name']:<50} {file_info['size_mb']:>8.1f} MB {file_info['type']}")
        
        if file_stats['.pdf'] + file_stats['.ppt'] + file_stats['.pptx'] > 20:
            remaining = sum(file_stats[ext] for ext in supported_extensions) - len(sample_files)
            print(f"     ... and {remaining} more files")
        
        print(f"\nDIRECTORY STRUCTURE (top-level):")
        subdirs = []
        for item in source_dir.iterdir():
            if item.is_dir():
                # Count files in this subdirectory
                subdir_files = sum(1 for f in item.rglob('*') if f.is_file() and f.suffix.lower() in supported_extensions)
                if subdir_files > 0:
                    subdirs.append((item.name, subdir_files))
        
        for dirname, file_count in sorted(subdirs, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  DIR: {dirname:<40} ({file_count} files)")
        
        print(f"\nReady to process {sum(file_stats[ext] for ext in supported_extensions)} radiology files!")
        return True
        
    except Exception as e:
        print(f"ERROR: Error scanning directory: {e}")
        return False

def main():
    success = scan_radiology_drive()
    
    if success:
        print(f"\nNEXT STEPS:")
        print("1. Run the bulk ingestion script:")
        print("   python bulk_ingest_materials.py")
        print("\n2. Or process files through the Streamlit app:")
        print("   - Use the Document Management section")
        print("   - Upload files manually for more control")
        
        print(f"\nNOTE: Processing large numbers of files will take time")
        print("   Estimated time: 1-2 minutes per file depending on size")
    else:
        print(f"\nERROR: Cannot access the radiology drive.")
        print("Please check the drive connection and path.")

if __name__ == "__main__":
    main()