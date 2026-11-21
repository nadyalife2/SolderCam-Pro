import struct
import os

orig_dtbo_path = r"d:\для one plus nord n10\dtbo.img"
mod_entry_path = r"d:\для one plus nord n10\dtbo_extracted\entry_01_mod_v2.dtb"
out_img_path = r"d:\для one plus nord n10\dtbo_mod_v2_32m.img"

with open(orig_dtbo_path, "rb") as f:
    orig_data = f.read()

magic, total_size, hdr_size, entry_size, entry_count, entries_offset, page_size, version = struct.unpack(">8I", orig_data[:32])

with open(mod_entry_path, "rb") as f:
    mod_entry_data = f.read()

entries = []
# collect all entries
for i in range(entry_count):
    entry_header = orig_data[entries_offset + i * entry_size : entries_offset + (i + 1) * entry_size]
    dt_size, dt_offset, dt_id, dt_rev = struct.unpack(">4I", entry_header[:16])
    custom = struct.unpack(">4I", entry_header[16:32])
    
    if i == 1: # entry 01
        payload = mod_entry_data
    else:
        payload = orig_data[dt_offset : dt_offset + dt_size]
    
    entries.append({
        "id": dt_id,
        "rev": dt_rev,
        "custom": custom,
        "data": payload
    })

# Compute new offsets
header_table_size = entries_offset + entry_count * entry_size # 32 + 12*32 = 416
cur_offset = header_table_size

packed_entries_headers = bytearray()
packed_payloads = bytearray()

for i, e in enumerate(entries):
    size = len(e["data"])
    offset = cur_offset
    cur_offset += size
    
    entry_bin = struct.pack(">4I", size, offset, e["id"], e["rev"])
    entry_bin += struct.pack(">4I", *e["custom"])
    packed_entries_headers += entry_bin
    packed_payloads += e["data"]

new_total_size = cur_offset
new_header = struct.pack(">8I", magic, new_total_size, hdr_size, entry_size, entry_count, entries_offset, page_size, version)

full_image = new_header + packed_entries_headers + packed_payloads
print(f"Packed DTBO size: {len(full_image)} bytes (header total_size={new_total_size})")

# Pad to 32MB (33554432 bytes)
target_size = 32 * 1024 * 1024
if len(full_image) < target_size:
    full_image += b"\x00" * (target_size - len(full_image))

with open(out_img_path, "wb") as f:
    f.write(full_image)

print(f"Saved {out_img_path}, size={len(full_image)} bytes")
