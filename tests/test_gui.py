"""Tests for desktop text/file behavior and an optional display smoke check."""
import os
import sys
import tkinter as tk
import time

import pytest

from ui.gui import CipherApp, make_cipher, process_file, process_text


@pytest.mark.parametrize('algorithm,key', [('TinyA5/1', '0x1A2B3C4D'),
                                          ('A5/1', '0x1223456789ABCDEF')])
def test_text_and_binary_files(tmp_path, algorithm, key):
    text = 'Xin chào Việt Nam!\nDòng thứ hai 🔑'
    encrypted = process_text(algorithm, key, '0x134', text, False)
    assert bytes.fromhex(encrypted) != text.encode()
    assert process_text(algorithm, key, '0x134', encrypted, True) == text
    first, second, third = [tmp_path / name for name in ('plain', 'cipher', 'restored')]
    # Cross a chunk boundary to ensure one cipher state is kept for the whole file.
    data = bytes(range(256)) * 257
    first.write_bytes(data)
    assert process_file(algorithm, key, '0x134', str(first), str(second)) == len(data)
    assert process_file(algorithm, key, '0x134', str(second), str(third)) == len(data)
    assert third.read_bytes() == data
    with pytest.raises(FileExistsError):
        process_file(algorithm, key, '0x134', str(first), str(second))
    assert third.read_bytes() == data
    with pytest.raises(ValueError):
        process_file(algorithm, key, '0x134', str(first), str(first))
    assert first.read_bytes() == data


def test_gui_a51_key_byte_order():
    operation = make_cipher('A5/1', '0x1223456789ABCDEF', '0x134')
    assert operation(bytes(14)).hex() == '534eaa582fe8151ab6e1855a728c'


@pytest.mark.parametrize('algorithm,key,frame,text,decrypt', [
    ('TinyA5/1', '-1', '0', 'text', False),
    ('TinyA5/1', '0x100000000', '0', 'text', False),
    ('A5/1', 'abc', '0', 'text', False),
    ('A5/1', '1', '0x400000', 'text', False),
    ('TinyA5/1', '1', '0', 'not hex', True),
])
def test_bad_input(algorithm, key, frame, text, decrypt):
    with pytest.raises(ValueError):
        process_text(algorithm, key, frame, text, decrypt)


@pytest.mark.skipif(sys.platform != 'win32' and not os.environ.get('DISPLAY'),
                    reason='Requires a display; run under Xvfb on Linux')
def test_window_text_roundtrip():
    root = tk.Tk()
    app = CipherApp(root)
    try:
        expected = app.input.get('1.0', 'end-1c')
        for decrypt in (False, True):
            app.run_text(decrypt)
            deadline = time.monotonic() + 10
            while app.future is not None and time.monotonic() < deadline:
                root.update()
                time.sleep(0.01)
            assert app.future is None
            if not decrypt:
                assert app.output.get('1.0', 'end-1c') != expected
                app.reuse_result()
        assert app.output.get('1.0', 'end-1c') == expected
        app.algorithm.set('A5/1')
        app.update_algorithm()
        assert str(app.frame_entry['state']) == 'normal'
        app.algorithm.set('TinyA5/1')
        app.update_algorithm()
        assert str(app.frame_entry['state']) == 'disabled'
    finally:
        app.close()


@pytest.mark.skipif(sys.platform != 'win32' and not os.environ.get('DISPLAY'),
                    reason='Requires a display')
def test_window_binary_roundtrip():
    root = tk.Tk()
    app = CipherApp(root)
    try:
        for algorithm in ('TinyA5/1', 'A5/1'):
            app.binary_algorithm.set(algorithm)
            app.load_binary_example()
            original = app.binary_input.get('1.0', 'end-1c')
            for decrypt in (False, True):
                app.run_binary(decrypt)
                deadline = time.monotonic() + 10
                while app.future is not None and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.01)
                assert app.future is None
                assert 'Bước 1' in app.binary_trace.get('1.0', 'end-1c')
                if not decrypt:
                    app.reuse_binary()
            assert app.binary_result == original
    finally:
        app.close()
