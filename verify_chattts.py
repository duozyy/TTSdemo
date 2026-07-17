import hashlib, os
from pathlib import Path

BASE = Path(r"E:/workbuddy/2026-07-15-21-40-09/tts_demo/asset")

files = {
    "Decoder.safetensors": "77aa55e0a977949c4733df3c6f876fa85860d3298cba63295a7bc6901729d4e0",
    "DVAE.safetensors": "1d0b044a8368c0513100a2eca98456b289e6be6a18b7a63be1bcaa315ea874d9",
    "Embed.safetensors": "2ff0be7134934155741b643b74e32fb6bf3eec41257984459b2ed60cdb4c48b0",
    "Vocos.safetensors": "07e5561491cce41f7f90cfdb94b2ff263ff5742c3d89339db99b17ad82cc3f44",
    "gpt/config.json": "0aaa1ecd96c49ad4f473459eb1982fa7ad79fa5de08cde2781bf6ad1f9a0c236",
    "gpt/model.safetensors": "cd0806fd971f52f6a22c923ec64982b305e817bcc41ca83417fcf9141b984a0f",
    "tokenizer/special_tokens_map.json": "bd0ac9d9bb1657996b5c5fbcaa7d80f8de530d01a283da97f89deae5b1b8d011",
    "tokenizer/tokenizer_config.json": "43e9d658b554fa5ee8d8e1d763349323bfef1ed7a89c0794220ab8861387d421",
    "tokenizer/tokenizer.json": "843838a64e121e23e774cc75874c6fe862198d9f7dd43747914633a8fd89c20e",
}

import mmap
def sha256(fileno):
    data = mmap.mmap(fileno, 0, access=mmap.ACCESS_READ)
    h = hashlib.sha256(data).hexdigest()
    del data
    return h

for rel, expected in files.items():
    fp = BASE / rel
    if not fp.exists():
        print(f"[MISSING] {rel}")
        continue
    with open(fp, "rb") as f:
        real = sha256(f.fileno())
    ok = "OK" if real == expected else "MISMATCH"
    print(f"[{ok}] {rel} ({fp.stat().st_size:,} bytes)")
    if real != expected:
        print(f"       expected: {expected}")
        print(f"       real:     {real}")
