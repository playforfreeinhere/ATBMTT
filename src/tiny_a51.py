"""
Minimal reference implementation of TinyA5/1 for demo purposes.
This is a simplified pedagogical implementation — NOT optimized for performance.
"""

from typing import List


class TinyA51:
    """TinyA5/1: small LFSR-based keystream generator for teaching.

    This tiny variant uses 3 small LFSRs (lengths 5, 7, 9) with simple majority clocking.
    The goal is to provide a working example for tests and demos.
    """

    def __init__(self, key: int):
        # key: integer seed
        self.r1 = key & 0x1F  # 5 bits
        self.r2 = (key >> 5) & 0x7F  # 7 bits
        self.r3 = (key >> 12) & 0x1FF  # 9 bits

    def _bit(self, x: int, pos: int) -> int:
        return (x >> pos) & 1

    def _clock_once(self):
        # simple XOR-feedback taps for demo
        new1 = ((self._bit(self.r1, 2) ^ self._bit(self.r1, 4)) << 4) | (self.r1 >> 1)
        new2 = ((self._bit(self.r2, 3) ^ self._bit(self.r2, 6)) << 6) | (self.r2 >> 1)
        new3 = ((self._bit(self.r3, 4) ^ self._bit(self.r3, 8)) << 8) | (self.r3 >> 1)
        self.r1 = new1 & 0x1F
        self.r2 = new2 & 0x7F
        self.r3 = new3 & 0x1FF

    def keystream_bit(self) -> int:
        # majority clocking simplified: clock all three for tiny variant
        self._clock_once()
        return (self._bit(self.r1, 0) ^ self._bit(self.r2, 0) ^ self._bit(self.r3, 0)) & 1

    def keystream_bytes(self, n: int) -> bytes:
        out = bytearray()
        for _ in range(n):
            b = 0
            for i in range(8):
                b = (b << 1) | self.keystream_bit()
            out.append(b)
        return bytes(out)

    def encrypt(self, data: bytes) -> bytes:
        ks = self.keystream_bytes(len(data))
        return bytes(a ^ b for a, b in zip(data, ks))

    def decrypt(self, data: bytes) -> bytes:
        return self.encrypt(data)  # symmetric
