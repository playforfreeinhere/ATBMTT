'use strict';
const $ = id => document.getElementById(id);
const api = window.A51Demo;
let mode = 'binary', steps = [], position = 0, timer = null, lastCipher = '', lastKey = '', fileURL = null, busy = false;
const tinyKey = '10010101001110100110000';
const saved = {binary: {plain: '111', cipher: '011'}, text: {plain: 'Xin chào Việt Nam! — Nhóm 9', cipher: ''}};
const algorithm = () => $('algorithm').value;
function notice(message = '') { $('notice').textContent = message; }
function stop() { if (timer) clearInterval(timer); timer = null; $('play').textContent = '▶ Phát'; }
function clearVisual() {
  stop(); steps = []; position = 0;
  $('registers').replaceChildren();
  ['clocks', 'majority', 'rotated', 'streamBit', 'xor', 'stream'].forEach(id => $(id).textContent = '—');
  $('stepCount').textContent = 'Chưa có dữ liệu';
  $('phaseName').textContent = 'Bấm Mã hóa hoặc Giải mã để bắt đầu.';
  ['previous', 'play', 'next'].forEach(id => $(id).disabled = true);
}
function invalidate() {
  clearVisual(); notice(); lastCipher = ''; lastKey = '';
  ['encResult', 'decResult', 'transfer'].forEach(id => $(id).hidden = true);
  clearDownload();
}
function clearDownload() {
  if (fileURL) URL.revokeObjectURL(fileURL);
  fileURL = null; $('download').hidden = true; $('fileStatus').textContent = '';
}
function validKeys() {
  for (const id of ['encKey', 'decKey', 'fileKey']) {
    let okay = true;
    try { new api.Cipher(algorithm(), $(id).value.trim(), $('frame').value.trim()); }
    catch (_) { okay = false; }
    $(id).classList.toggle('valid', okay); $(id).classList.toggle('invalid', !okay);
    $(id).setAttribute('aria-invalid', String(!okay));
  }
}
function spec() {
  const tiny = algorithm() === 'tiny';
  $('frameLabel').hidden = tiny;
  document.querySelectorAll('.keyLabel').forEach(el => el.textContent = tiny ? 'Khóa (23 bit)' : 'Khóa A5/1 (64 bit)');
  document.querySelectorAll('.keyHint').forEach(el => el.textContent = tiny ? 'Phải chính xác 23 bit (0 và 1). Khóa chia X: 6, Y: 8, Z: 9 bit.' : 'Số thập phân hoặc hex, ví dụ 0x1223456789ABCDEF.');
  $('spec').textContent = tiny ? 'Theo Chương 4 của PDF: clock X[1], Y[3], Z[3]; tap X[2,4,5], Y[6,7], Z[2,7,8]; lấy S sau khi quay. Khóa là trạng thái ban đầu.' : 'A5/1 GSM: khóa 64 bit, số khung 22 bit, nạp khóa + frame, quay khởi động 100 lần; bảng hiển thị bắt đầu khi sinh dòng khóa.';
  validKeys();
}
function example() {
  invalidate();
  const tiny = algorithm() === 'tiny';
  const key = tiny ? tinyKey : '0x1223456789ABCDEF';
  ['encKey', 'decKey', 'fileKey'].forEach(id => $(id).value = key);
  $('frame').value = '0x134';
  saved.binary = {plain: tiny ? '111' : '0'.repeat(114), cipher: tiny ? '011' : ''};
  saved.text = {plain: 'Xin chào Việt Nam! — Nhóm 9', cipher: ''};
  if (mode !== 'file') { $('plain').value = saved[mode].plain; $('cipher').value = saved[mode].cipher; }
  spec();
}
function changeMode(next) {
  if (mode !== 'file') saved[mode] = {plain: $('plain').value, cipher: $('cipher').value};
  mode = next; invalidate();
  $('forms').hidden = mode === 'file'; $('filePanel').hidden = mode !== 'file'; $('visual').hidden = mode !== 'binary';
  document.querySelectorAll('[data-mode]').forEach(button => {
    button.classList.toggle('selected', button.dataset.mode === mode);
    button.setAttribute('aria-pressed', String(button.dataset.mode === mode));
  });
  if (mode !== 'file') {
    $('plain').value = saved[mode].plain; $('cipher').value = saved[mode].cipher;
    $('encLabel').textContent = mode === 'binary' ? 'Plaintext (nhị phân)' : 'Plaintext (văn bản UTF-8)';
    $('decLabel').textContent = mode === 'binary' ? 'Ciphertext (nhị phân)' : 'Ciphertext (hex)';
    $('plainHint').textContent = mode === 'binary' ? 'Nhập chuỗi nhị phân, ví dụ: 111.' : 'Nhập văn bản có dấu. Kết quả mã hóa được hiển thị dưới dạng hex.';
    $('cipherHint').textContent = mode === 'binary' ? 'Nhập bản mã nhị phân, ví dụ: 011.' : 'Dán bản mã hex có đủ cặp ký tự; không dán văn bản vào ô này.';
  }
}
function result(id, title, lines) {
  const box = $(id); box.replaceChildren();
  const heading = document.createElement('strong'); heading.textContent = title;
  box.append(heading, document.createTextNode('\n' + lines.join('\n'))); box.hidden = false;
}
function execute(decrypt) {
  notice(); clearVisual();
  const key = $(decrypt ? 'decKey' : 'encKey').value.trim();
  const input = $(decrypt ? 'cipher' : 'plain').value;
  const id = decrypt ? 'decResult' : 'encResult';
  $(id).hidden = true;
  if (!decrypt) { $('transfer').hidden = true; lastCipher = ''; }
  try {
    let output;
    if (mode === 'binary') {
      const answer = api.bits(algorithm(), key, $('frame').value.trim(), input);
      output = answer.output; steps = answer.steps; position = 0; render();
    } else {
      const cipher = new api.Cipher(algorithm(), key, $('frame').value.trim());
      const data = decrypt ? api.unhex(input) : new TextEncoder().encode(input);
      if (data.length > 65536) throw new Error('Văn bản tối đa 64 KB cho demo. Dùng File cho dữ liệu lớn.');
      const bytes = cipher.bytes(data);
      if (decrypt) {
        try { output = new TextDecoder('utf-8', {fatal: true}).decode(bytes); }
        catch (_) { throw new Error('Không đọc được UTF-8. Kiểm tra khóa, thuật toán, frame và bản mã. Dùng File cho dữ liệu nhị phân.'); }
      } else output = api.hex(bytes);
    }
    result(id, decrypt ? 'Kết Quả Giải Mã:' : 'Kết Quả Mã Hóa:', [
      `${decrypt ? 'Ciphertext' : 'Plaintext'}: ${input}`,
      `${decrypt ? 'Plaintext' : 'Ciphertext'} (${mode === 'binary' ? 'nhị phân' : decrypt ? 'UTF-8' : 'hex'}): ${output}`,
      `Khóa: ${key}`, ...(algorithm() === 'a51' ? [`Frame: ${$('frame').value}`] : [])]);
    if (!decrypt) { lastCipher = output; lastKey = key; $('transfer').hidden = false; }
  } catch (error) { notice(error.message); }
  validKeys();
}
function render() {
  if (!steps.length) return;
  const index = Math.floor(position / 3), phase = position % 3, step = steps[index];
  const names = ['X', 'Y', 'Z'], clockIndices = algorithm() === 'tiny' ? [1, 3, 3] : [8, 10, 10];
  $('stepCount').textContent = `Bước ${index + 1}/${steps.length}`;
  $('phaseName').textContent = ['Trước khi quay · đọc bit clock', 'Quyết định quay theo majority', 'Sau khi quay · sinh bit S'][phase];
  $('registers').replaceChildren();
  const registers = phase === 2 ? step.after : step.before;
  registers.forEach((register, n) => {
    const card = document.createElement('article'); card.className = 'register' + (phase > 0 && step.clocked[n] ? ' moving' : '');
    const heading = document.createElement('h3'); heading.textContent = `Thanh Ghi ${names[n]} (${register.length} bit)`;
    const row = document.createElement('div'); row.className = 'bitrow';
    register.forEach((value, i) => {
      const wrap = document.createElement('div'); wrap.className = 'bitwrap';
      const cell = document.createElement('span'); cell.className = 'bit' + (i === clockIndices[n] ? ' clock' : '') + (i === register.length - 1 ? ' out' : ''); cell.textContent = value;
      const label = document.createElement('small'); label.textContent = i; wrap.append(cell, label); row.append(wrap);
    });
    const state = document.createElement('div'); state.className = 'state'; state.textContent = phase === 0 ? 'Trạng thái trước khi quay' : step.clocked[n] ? phase === 1 ? 'Sẽ quay' : 'Đã quay' : 'Giữ nguyên';
    card.append(heading, row, state); $('registers').append(card);
  });
  $('clocks').textContent = step.clocks.map((v, i) => `${names[i]}[${clockIndices[i]}] = ${v}`).join(' · ');
  $('majority').textContent = `maj(${step.clocks.join(', ')}) = ${step.majority}`;
  $('rotated').textContent = phase === 0 ? 'Chuyển pha để xem quyết định.' : step.clocked.map((yes, i) => `${names[i]}: ${yes ? 'quay' : 'giữ'}`).join(' · ');
  $('streamBit').textContent = phase < 2 ? 'Chưa sinh bit S ở pha này.' : step.after.map(r => r[r.length - 1]).join(' ⊕ ') + ` = ${step.s}`;
  $('xor').textContent = phase < 2 ? 'Chờ sinh bit S.' : `${step.input} ⊕ ${step.s} = ${step.output}`;
  $('stream').textContent = steps.slice(0, index + (phase === 2 ? 1 : 0)).map(s => s.s).join('') || '—';
  $('previous').disabled = position === 0; $('next').disabled = position === steps.length * 3 - 1; $('play').disabled = false;
}
function advance() {
  if (position < steps.length * 3 - 1) { position++; render(); }
  else stop();
  if (position === steps.length * 3 - 1) stop();
}
async function fileOperation(decrypt) {
  if (busy) return;
  notice(); clearDownload();
  const file = $('fileInput').files[0];
  try {
    if (!file) throw new Error('Hãy chọn file đầu vào.');
    if (file.size > 2 * 1024 * 1024) throw new Error('Chọn file tối đa 2 MB cho demo trực tiếp.');
    const cipher = new api.Cipher(algorithm(), $('fileKey').value.trim(), $('frame').value.trim());
    busy = true;
    const controls = [...document.querySelectorAll('button,input,textarea,select')];
    const oldDisabled = controls.map(control => control.disabled);
    controls.forEach(control => control.disabled = true);
    try {
      const source = new Uint8Array(await file.arrayBuffer()), output = new Uint8Array(source.length);
      for (let offset = 0; offset < source.length; offset += 4096) {
        output.set(cipher.bytes(source.subarray(offset, offset + 4096)), offset);
        $('fileStatus').textContent = `Đang xử lý ${Math.min(offset + 4096, source.length)} / ${source.length} byte…`;
        await new Promise(resolve => setTimeout(resolve, 0));
      }
      fileURL = URL.createObjectURL(new Blob([output], {type: 'application/octet-stream'}));
      const name = decrypt ? (file.name.endsWith('.a51') ? file.name.slice(0, -4) : file.name + '.restored') : file.name + '.a51';
      $('download').href = fileURL; $('download').download = name || 'ket-qua.bin';
      $('download').textContent = 'Tải file kết quả: ' + name; $('download').hidden = false;
      $('fileStatus').textContent = `Đã ${decrypt ? 'giải mã' : 'mã hóa'} ${source.length} byte. Bấm nút bên dưới để lưu.`;
    } finally { controls.forEach((control, i) => control.disabled = oldDisabled[i]); busy = false; }
  } catch (error) { busy = false; notice(error.message); }
}
$('algorithm').addEventListener('change', example);
$('example').addEventListener('click', example);
$('encrypt').addEventListener('click', () => execute(false));
$('decrypt').addEventListener('click', () => execute(true));
$('transfer').addEventListener('click', () => {
  $('cipher').value = lastCipher; $('decKey').value = lastKey; $('decResult').hidden = true; validKeys();
});
$('previous').addEventListener('click', () => { stop(); if (position > 0) position--; render(); });
$('next').addEventListener('click', () => { stop(); advance(); });
$('play').addEventListener('click', () => {
  if (timer) { stop(); return; }
  if (position === steps.length * 3 - 1) position = 0;
  render(); $('play').textContent = 'Ⅱ Tạm dừng'; timer = setInterval(advance, 700);
});
document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => changeMode(button.dataset.mode)));
['encKey', 'decKey', 'fileKey', 'frame', 'plain', 'cipher'].forEach(id => $(id).addEventListener('input', () => { invalidate(); validKeys(); }));
$('fileInput').addEventListener('change', clearDownload);
$('encFile').addEventListener('click', () => fileOperation(false));
$('decFile').addEventListener('click', () => fileOperation(true));
$('check').addEventListener('click', () => {
  const rows = api.checks(); $('checks').hidden = false; $('checkRows').replaceChildren();
  rows.forEach(row => {
    const div = document.createElement('div'); div.className = 'checkrow ' + (row.passed ? 'pass' : 'fail');
    div.textContent = `${row.passed ? 'PASS' : 'FAIL'} · ${row.name}\nKỳ vọng: ${row.expected}\nThực tế: ${row.actual}`;
    div.style.whiteSpace = 'pre-wrap'; $('checkRows').append(div);
  });
  $('checks').scrollIntoView({behavior: 'smooth'});
});
window.addEventListener('pagehide', () => { stop(); clearDownload(); });
example();
