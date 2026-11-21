import struct
import os

with open(r"d:\для one plus nord n10\dtbo.img", "rb") as f:
    data = f.read()

magic, total_size, hdr_size, entry_size, entry_count, entries_offset, page_size, version = struct.unpack(">8I", data[:32])
print(f"Entry size: {entry_size}, count: {entry_count}")

# Entry struct: dt_size (4), dt_offset (4), id (4), rev (4), custom[4]
os.makedirs(r"d:\для one plus nord n10\dtbo_extracted", exist_ok=True)

for i in range(entry_count):
    entry_data = data[entries_offset + i * entry_size : entries_offset + (i + 1) * entry_size]
    dt_size, dt_offset, dt_id, dt_rev = struct.unpack(">4I", entry_data[:16])
    custom = struct.unpack(">4I", entry_data[16:32])
    print(f"Entry {i:02d}: size={dt_size:<8} offset={dt_offset:<8} id=0x{dt_id:08x} rev=0x{dt_rev:08x} custom={[hex(c) for c in custom]}")
    
    dtb = data[dt_offset : dt_offset + dt_size]
    with open(rf"d:\для one plus nord n10\dtbo_extracted\entry_{i:02d}.dtb", "wb") as out:
        out.write(dtb)
