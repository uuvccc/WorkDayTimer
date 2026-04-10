import os
import shutil

# Paths
dist_exe = os.path.join('dist', 'WorkDayTimer.exe')
target_exe = 'WorkDayTimer.exe'

print(f"Copying {dist_exe} to {target_exe}")

# Check if the source file exists
if os.path.exists(dist_exe):
    print(f"Source file exists: {dist_exe}")
    
    # Check if the target file exists and try to delete it
    if os.path.exists(target_exe):
        print(f"Target file exists, trying to delete: {target_exe}")
        try:
            os.remove(target_exe)
            print(f"Target file deleted successfully")
        except Exception as e:
            print(f"Error deleting target file: {e}")
    
    # Try to copy the file
    try:
        shutil.copy2(dist_exe, target_exe)
        print(f"File copied successfully: {target_exe}")
        print(f"File size: {os.path.getsize(target_exe)} bytes")
    except Exception as e:
        print(f"Error copying file: {e}")
else:
    print(f"Source file not found: {dist_exe}")
    # List directory contents
    print("Dist directory contents:")
    if os.path.exists('dist'):
        for item in os.listdir('dist'):
            print(f"  - {item}")
    else:
        print("  Dist directory does not exist")
