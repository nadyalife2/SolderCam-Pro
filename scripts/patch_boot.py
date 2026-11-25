import struct
import gzip
import os

def patch_boot(input_boot, output_boot):
    with open(input_boot, 'rb') as f:
        orig_hdr = f.read(2048)
        magic, k_sz, k_addr, r_sz, r_addr, s_sz, s_addr, t_addr, page_sz = struct.unpack('<8sIIIIIIII', orig_hdr[:40])
        assert magic == b'ANDROID!', f"Bad magic: {magic}"
        
        k_pages = (k_sz + page_sz - 1) // page_sz
        f.seek(page_sz)
        kernel_data = f.read(k_sz)
        
        f.seek(page_sz + k_pages * page_sz)
        ramdisk_data = f.read(r_sz)
        
        second_data = b''
        if s_sz > 0:
            r_pages = (r_sz + page_sz - 1) // page_sz
            f.seek(page_sz + (k_pages + r_pages) * page_sz)
            second_data = f.read(s_sz)

    decompressed = gzip.decompress(ramdisk_data)
    
    pos = 0
    records = []
    while pos < len(decompressed) - 110:
        c_magic = decompressed[pos:pos+6]
        if c_magic != b'070701':
            break
        hdr_110 = decompressed[pos:pos+110]
        namesize = int(hdr_110[94:102], 16)
        filesize = int(hdr_110[54:62], 16)
        name = decompressed[pos+110:pos+110+namesize-1].decode('latin-1', errors='ignore')
        
        header_end = pos + 110 + namesize
        file_start = (header_end + 3) & ~3
        file_end = file_start + filesize
        next_pos = (file_end + 3) & ~3
        
        data = decompressed[file_start:file_end]
        records.append({
            'cpio_hdr': hdr_110,
            'name': name,
            'namesize': namesize,
            'data': data
        })
        pos = next_pos
        if name == 'TRAILER!!!':
            break

    new_records = []
    for r in records:
        if r['name'] == 'default.prop':
            text = r['data'].decode('latin-1')
            lines = text.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('ro.secure='):
                    new_lines.append('ro.secure=0')
                elif line.startswith('ro.debuggable='):
                    new_lines.append('ro.debuggable=1')
                elif line.startswith('ro.adb.secure='):
                    new_lines.append('ro.adb.secure=0')
                elif line.startswith('security.perf_harden='):
                    new_lines.append('security.perf_harden=0')
                elif line.startswith('persist.sys.usb.config='):
                    new_lines.append('persist.sys.usb.config=mtp,adb')
                else:
                    new_lines.append(line)
            new_lines.append('service.adb.root=1')
            new_lines.append('ro.force.debuggable=1')
            
            new_data = '\n'.join(new_lines).encode('latin-1')
            new_filesize = len(new_data)
            
            hdr_bytes = bytearray(r['cpio_hdr'])
            hdr_bytes[54:62] = f"{new_filesize:08X}".encode('ascii')
            r['cpio_hdr'] = bytes(hdr_bytes)
            r['data'] = new_data
            print("Patched default.prop successfully!")
            
        elif r['name'] == 'fstab.mt6797':
            text = r['data'].decode('latin-1')
            text = text.replace('/by-name/system /system ext4 ro wait,verify',
                                '/by-name/system /system ext4 rw wait')
            new_data = text.encode('latin-1')
            new_filesize = len(new_data)
            hdr_bytes = bytearray(r['cpio_hdr'])
            hdr_bytes[54:62] = f"{new_filesize:08X}".encode('ascii')
            r['cpio_hdr'] = bytes(hdr_bytes)
            r['data'] = new_data
            print("Patched fstab.mt6797 for RW system!")
            
        elif r['name'] == 'sbin/adbd':
            adbd_bytes = bytearray(r['data'])
            # Patch at 0x18ec: jump directly to 0x1a08
            # 0x1a08 - 0x18ec = 0x11c = 71 instructions = 0x14000047
            adbd_bytes[0x18ec:0x18f0] = b'\x47\x00\x00\x14'
            
            # Also nop setuid/setgid just in case
            nop_ret = b'\x00\x00\x80\xd2\xc0\x03\x5f\xd6'
            adbd_bytes[0x376fc:0x376fc+8] = nop_ret
            adbd_bytes[0x37714:0x37714+8] = nop_ret
            adbd_bytes[0x3775c:0x3775c+8] = nop_ret
            
            r['data'] = bytes(adbd_bytes)
            print("Patched sbin/adbd: permanent root bypass on privilege dropping!")
            
        elif r['name'] == 'init.miui.early_boot.sh':
            text = r['data'].decode('latin-1')
            payload = """
# === ANTI-BOOTLOOP PERMANENT FIX ===
mount -o remount,rw /system 2>/dev/null
rm -rf /data/app/com.google.android.gms*
rm -rf /data/data/com.google.android.gms*
rm -rf /data/user_de/0/com.google.android.gms*
rm -rf /system/priv-app/GmsCore*
rm -rf /data/app/com.android.vending*
rm -rf /data/data/com.android.vending*
rm -rf /data/dalvik-cache/arm64/*gms*
rm -rf /data/dalvik-cache/arm/*gms*
echo "ANTI-BOOTLOOP FIX COMPLETED AT $(date)" > /data/local/tmp/fix_gms.log
"""
            text = text + payload
            new_data = text.encode('latin-1')
            new_filesize = len(new_data)
            hdr_bytes = bytearray(r['cpio_hdr'])
            hdr_bytes[54:62] = f"{new_filesize:08X}".encode('ascii')
            r['cpio_hdr'] = bytes(hdr_bytes)
            r['data'] = new_data
            print("Patched init.miui.early_boot.sh with root GMS cleanup payload!")
            
        new_records.append(r)
        
    out_cpio = bytearray()
    for r in new_records:
        hdr = r['cpio_hdr']
        name_bytes = r['name'].encode('latin-1') + b'\x00'
        out_cpio.extend(hdr)
        out_cpio.extend(name_bytes)
        while len(out_cpio) % 4 != 0:
            out_cpio.append(0)
        out_cpio.extend(r['data'])
        while len(out_cpio) % 4 != 0:
            out_cpio.append(0)
            
    out_gzip = gzip.compress(out_cpio, compresslevel=9, mtime=0)
    print(f"New ramdisk compressed size: {len(out_gzip)}")
    
    new_r_sz = len(out_gzip)
    k_pages = (k_sz + page_sz - 1) // page_sz
    r_pages = (new_r_sz + page_sz - 1) // page_sz
    s_pages = (s_sz + page_sz - 1) // page_sz if s_sz > 0 else 0
    
    boot_hdr = bytearray(orig_hdr)
    struct.pack_into('<I', boot_hdr, 16, new_r_sz)
    
    cmdline_bytes = boot_hdr[64:576].split(b'\x00')[0]
    new_cmdline = cmdline_bytes.decode('ascii') + " androidboot.selinux=permissive"
    boot_hdr[64:576] = b'\x00' * 512
    boot_hdr[64:64+len(new_cmdline)] = new_cmdline.encode('ascii')
    
    with open(output_boot, 'wb') as f_out:
        f_out.write(boot_hdr)
        f_out.write(kernel_data)
        pad_k = (k_pages * page_sz) - k_sz
        if pad_k > 0:
            f_out.write(b'\x00' * pad_k)
            
        f_out.write(out_gzip)
        pad_r = (r_pages * page_sz) - new_r_sz
        if pad_r > 0:
            f_out.write(b'\x00' * pad_r)
            
        if s_sz > 0:
            f_out.write(second_data)
            pad_s = (s_pages * page_sz) - s_sz
            if pad_s > 0:
                f_out.write(b'\x00' * pad_s)
                
    total_sz = os.path.getsize(output_boot)
    print(f"Patched boot image successfully created: {output_boot} ({total_sz} bytes)")

if __name__ == '__main__':
    src = r'DOWNLOADS_ARCHIVE\nikel_firmware\nikel_global_images_V10.2.1.0.MBFMIXM_20190123.0000.00_6.0_global\images\boot.img'
    dst = r'DOWNLOADS_ARCHIVE\nikel_firmware\boot_root_insecure.img'
    patch_boot(src, dst)
