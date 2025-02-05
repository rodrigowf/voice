import sys
import os
from pathlib import Path

def patch_pystray():
    """Patch pystray to use PIL.Image.Resampling.LANCZOS instead of ANTIALIAS"""
    try:
        # Find pystray installation
        import pystray
        pystray_dir = Path(pystray.__file__).parent
        
        # Files to patch
        files_to_patch = [
            pystray_dir / '_xorg.py',
            pystray_dir / '_win32.py',
            pystray_dir / '_darwin.py'
        ]
        
        for file_path in files_to_patch:
            if file_path.exists():
                print(f"Patching {file_path}")
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace ANTIALIAS with Resampling.LANCZOS
                content = content.replace('PIL.Image.ANTIALIAS', 'PIL.Image.Resampling.LANCZOS')
                
                with open(file_path, 'w') as f:
                    f.write(content)
                    
        print("Pystray patched successfully")
        return True
    except Exception as e:
        print(f"Failed to patch pystray: {e}")
        return False

if __name__ == '__main__':
    patch_pystray() 