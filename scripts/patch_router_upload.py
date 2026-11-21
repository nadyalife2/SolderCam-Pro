#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch omni_fast_router_v4_9.py to add streaming binary file upload handler
for /api/cartridge/upload.
"""

from pathlib import Path

def apply_patch():
    file_path = Path("scripts/omni_fast_router_v4_9.py")
    content = file_path.read_text(encoding="utf-8")

    # 1. Add handle_cartridge_upload method to RequestHandler
    handler_fn = '''
    def handle_cartridge_upload(self):
        """
        Принимает бинарный поток .omni.zip архива из веб-интерфейса,
        сохраняет в папку cartridges/ проекта, распаковывает и валидирует.
        """
        length = int(self.headers.get("Content-Length", 0))
        filename = self.headers.get("X-Filename", "")
        if not filename:
            parsed = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed.query)
            filename = query_params.get("filename", ["uploaded_cartridge.omni.zip"])[0]
            
        filename = urllib.parse.unquote(filename)
        filename = os.path.basename(filename)
        if not filename.endswith(".zip") and not filename.endswith(".omni.zip"):
            filename += ".omni.zip"
            
        cart_dir = BASE_DIR / "cartridges"
        cart_dir.mkdir(parents=True, exist_ok=True)
        dest_path = cart_dir / filename
        
        remaining = length
        chunk_size = 64 * 1024
        with open(dest_path, "wb") as f:
            while remaining > 0:
                read_len = min(remaining, chunk_size)
                chunk = self.rfile.read(read_len)
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
                
        import zipfile
        unpack_dir = cart_dir / "unpacked" / dest_path.stem
        unpack_dir.mkdir(parents=True, exist_ok=True)
        
        card_data = {}
        has_adapter = False
        try:
            with zipfile.ZipFile(dest_path, "r") as z:
                z.extractall(unpack_dir)
            if (unpack_dir / "adapter.gguf").exists():
                has_adapter = True
            if (unpack_dir / "card.json").exists():
                card_data = json.loads((unpack_dir / "card.json").read_text(encoding="utf-8"))
        except Exception:
            pass
            
        web_cart_dir = BASE_DIR / "web_ui" / "cartridges"
        web_cart_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(dest_path, web_cart_dir / dest_path.name)
        except Exception:
            pass
            
        size_mb = round(dest_path.stat().st_size / (1024 * 1024), 1)
        
        self.send_json({
            "ok": True,
            "filename": filename,
            "path": str(dest_path),
            "size_mb": size_mb,
            "has_adapter": has_adapter,
            "card": card_data,
            "message": f"Картридж {filename} ({size_mb} МБ) успешно сохранен веб-интерфейсом в папку cartridges/!"
        })
'''

    # Insert handle_cartridge_upload before def do_POST(self):
    post_marker = "    def do_POST(self):"
    if post_marker in content and "def handle_cartridge_upload" not in content:
        content = content.replace(post_marker, handler_fn + "\n" + post_marker, 1)
        print("✅ Added handle_cartridge_upload method")

    # In do_POST, intercept /api/cartridge/upload before JSON reading
    intercept_marker = '    def do_POST(self):\n        length = int(self.headers.get("Content-Length", 0))'
    intercept_replace = '''    def do_POST(self):
        if self.path.startswith("/api/cartridge/upload"):
            self.handle_cartridge_upload()
            return
        length = int(self.headers.get("Content-Length", 0))'''
        
    if intercept_marker in content:
        content = content.replace(intercept_marker, intercept_replace, 1)
        print("✅ Intercepted /api/cartridge/upload in do_POST")

    file_path.write_text(content, encoding="utf-8")
    print(f"🎉 Successfully patched {file_path}")

if __name__ == "__main__":
    apply_patch()
