import struct
from pathlib import Path

def read_gguf_kv(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        version, = struct.unpack("<I", f.read(4))
        n_tensors, = struct.unpack("<Q", f.read(8))
        n_kv, = struct.unpack("<Q", f.read(8))
        
        kv_data = {}
        for _ in range(n_kv):
            # Read key
            key_len, = struct.unpack("<Q", f.read(8))
            key = f.read(key_len).decode("utf-8", errors="ignore")
            val_type, = struct.unpack("<I", f.read(4))
            
            # GGUF types: 0: UINT8, 1: INT8, 2: UINT16, 3: INT16, 4: UINT32, 5: INT32, 6: FLOAT32, 7: BOOL, 8: STRING, 9: ARRAY, 10: UINT64, 11: INT64, 12: FLOAT64
            if val_type == 8: # string
                slen, = struct.unpack("<Q", f.read(8))
                val = f.read(slen).decode("utf-8", errors="ignore")
            elif val_type in (0, 1, 7):
                val = ord(f.read(1))
            elif val_type in (2, 3):
                val, = struct.unpack("<h", f.read(2))
            elif val_type in (4, 5):
                val, = struct.unpack("<i", f.read(4))
            elif val_type == 6:
                val, = struct.unpack("<f", f.read(4))
            elif val_type in (10, 11):
                val, = struct.unpack("<q", f.read(8))
            elif val_type == 12:
                val, = struct.unpack("<d", f.read(8))
            else:
                val = f"<type {val_type}>"
                break
            kv_data[key] = val
        return kv_data

print("ADAPTER KV:")
for k, v in read_gguf_kv("models/adapter.gguf").items():
    print(f"  {k} = {v}")
