"""Browser integration checks; run with python tests/web_ui.py (Playwright + Chromium)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
with sync_playwright() as p, TemporaryDirectory() as temporary:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
                                 args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 1000}, accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.set_content((root / 'giao_dien.html').read_text())
    page.click('#encrypt')
    assert 'Ciphertext (nhị phân): 011' in page.locator('#encResult').inner_text()
    page.click('#transfer')
    page.click('#decrypt')
    assert 'Plaintext (nhị phân): 111' in page.locator('#decResult').inner_text()
    page.click('#next')
    page.click('#next')
    assert page.locator('#streamBit').inner_text() == '0 ⊕ 1 ⊕ 0 = 1'
    page.click('#play')
    page.wait_for_timeout(800)
    page.click('#play')
    assert page.locator('#play').inner_text() == '▶ Phát'
    page.fill('#encKey', '001')
    page.click('#encrypt')
    assert '23 bit' in page.locator('#notice').inner_text()
    assert page.locator('#encResult').is_hidden()
    page.click('#example')
    page.click('#check')
    assert page.locator('.checkrow.pass').count() == 4
    print('PASS PDF example, validation, phases, playback, standard vector display')
    for algorithm in ['tiny', 'a51']:
        page.select_option('#algorithm', algorithm)
        page.click('[data-mode="text"]')
        original = 'Xin chào Việt Nam! <script>alert(1)</script> 🔑'
        page.fill('#plain', original)
        page.click('#encrypt')
        page.click('#transfer')
        page.click('#decrypt')
        assert f'Plaintext (UTF-8): {original}' in page.locator('#decResult').inner_text()
        assert page.locator('#decResult script').count() == 0
        page.click('[data-mode="file"]')
        source = Path(temporary) / f'{algorithm}.bin'
        data = bytes(range(256)) * 33
        source.write_bytes(data)
        page.set_input_files('#fileInput', str(source))
        page.click('#encFile')
        page.locator('#download').wait_for(state='visible')
        with page.expect_download() as pending:
            page.click('#download')
        encrypted = Path(temporary) / f'{algorithm}.bin.a51'
        pending.value.save_as(str(encrypted))
        assert encrypted.read_bytes() != data
        page.set_input_files('#fileInput', str(encrypted))
        page.click('#decFile')
        page.locator('#download').wait_for(state='visible')
        with page.expect_download() as pending:
            page.click('#download')
        restored = Path(temporary) / f'{algorithm}-restored.bin'
        pending.value.save_as(str(restored))
        assert restored.read_bytes() == data
        page.click('[data-mode="binary"]')
        print('PASS', algorithm, 'UTF-8 + safe rendering + real binary file download roundtrip')
    page.select_option('#algorithm', 'tiny')
    page.click('#encrypt')
    page.click('#next')
    page.click('#next')
    page.screenshot(path=str(root / 'docs/giao_dien_pdf.png'), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    print('PASS responsive layout, no JavaScript runtime errors')
    browser.close()
