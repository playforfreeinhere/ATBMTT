import pytest

from src.tiny_a51 import TinyA51


def test_keystream_repeatability():
    key = 0x1A2B3C
    t1 = TinyA51(key)
    t2 = TinyA51(key)
    a = t1.keystream_bytes(16)
    b = t2.keystream_bytes(16)
    assert a == b


def test_encrypt_decrypt_roundtrip():
    key = 0xDEADBEEF
    t = TinyA51(key)
    data = b"Test data for encryption".ljust(32, b"\x00")
    c = t.encrypt(data)
    # reset generator
    t2 = TinyA51(key)
    p = t2.decrypt(c)
    assert p == data


from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher
from attacks.keystream_reuse import demo_reuse


def test_a51_published_vector():
    # Marc Briceno / Ian Goldberg / David Wagner A5/1 reference test:
    # key bytes 12 23 45 67 89 AB CD EF, frame 0x134;
    # bytes loaded in order, least significant bit first within each byte.
    key = bytes.fromhex('1223456789abcdef')
    cipher = A51Cipher([(byte >> i) & 1 for byte in key for i in range(8)], 0x134)
    for expected in ('534eaa582fe8151ab6e1855a728c00',
                     '24fd35a35d5fb6526d32f906df1ac0'):
        bits = [cipher.get_keystream_bit() for _ in range(114)] + [0] * 6
        packed = bytes(sum(bits[j + k] << (7 - k) for k in range(8))
                       for j in range(0, 120, 8))
        assert packed.hex() == expected


def test_tiny_hand_vector():
    cipher = TinyA51Cipher([1, 0, 1, 1, 0, 0], [0, 1, 0, 1, 0, 1, 1, 0],
                           [1, 1, 0, 0, 1, 0, 1, 0, 1])
    stream, logs = cipher.generate_keystream(4)
    assert stream == [1, 0, 0, 1]
    assert logs[0]['clock_bits'] == (1, 1, 0)
    assert logs[0]['clocked'] == (True, True, False)
    assert logs[0]['r1'] == [1, 1, 0, 1, 1, 0]


def test_reuse_attack():
    p1, p2 = b'Hello world!', b'Attack at dawn!'
    c1, c2, result = demo_reuse(p1, p2, 0x12345)
    assert c1 != p1 and c2 != p2
    assert result == bytes(a ^ b for a, b in zip(p1, p2))


@pytest.mark.parametrize('key', [-1, 1 << 32, 'invalid'])
def test_invalid_tiny_key(key):
    with pytest.raises(ValueError):
        TinyA51(key)


@pytest.mark.parametrize('key,frame', [([0] * 63, 0), ([2] * 64, 0),
                                       ([0] * 64, -1), ([0] * 64, 1 << 22),
                                       (None, 0), ([0] * 64, None)])
def test_invalid_a51_input(key, frame):
    with pytest.raises(ValueError):
        A51Cipher(key, frame)


def test_invalid_tiny_registers():
    with pytest.raises(ValueError):
        TinyA51Cipher([0] * 6, [0] * 7, [0] * 9)


@pytest.mark.parametrize('data', [b'', bytes(range(256)), 'Xin chào Việt Nam'.encode()])
def test_cli_roundtrip(tmp_path, data):
    import subprocess
    import sys
    source, encrypted, decrypted = (tmp_path / name for name in ('plain', 'cipher', 'back'))
    source.write_bytes(data)
    for command, first, second in [('encrypt', source, encrypted),
                                   ('decrypt', encrypted, decrypted)]:
        result = subprocess.run([sys.executable, '-m', 'ui.cli', command,
                                 str(first), str(second), '0x1A2B3C4D'],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    assert decrypted.read_bytes() == data


@pytest.mark.parametrize('case', ['bad-key', 'missing-input', 'existing-output', 'same-file'])
def test_cli_errors_preserve_files(tmp_path, case):
    import subprocess
    import sys
    source, output = tmp_path / 'input', tmp_path / 'output'
    source.write_bytes(b'original input')
    output.write_bytes(b'original output')
    first = tmp_path / 'missing' if case == 'missing-input' else source
    second = source if case == 'same-file' else output
    key = 'invalid' if case == 'bad-key' else '123'
    result = subprocess.run([sys.executable, '-m', 'ui.cli', 'encrypt',
                             str(first), str(second), key], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Traceback' not in result.stderr
    assert source.read_bytes() == b'original input'
    assert output.read_bytes() == b'original output'


def test_tiny_chunked_processing():
    data = bytes(range(128))
    cipher = TinyA51(0xDEADBEEF)
    assert cipher.encrypt(data[:7]) + cipher.encrypt(data[7:]) == TinyA51(0xDEADBEEF).encrypt(data)
