/* Handwritten A5/1 and TinyA5/1-PDF cores. No cryptographic libraries. */
(function (root) {
  'use strict';
  function binary(value, size, label = 'Dữ liệu') {
    if (!/^[01]+$/.test(value) || (size && value.length !== size))
      throw new Error(`${label} phải ${size ? 'có đúng ' + size + ' bit' : 'là chuỗi bit không rỗng'} (chỉ 0 và 1).`);
    return [...value].map(Number);
  }
  function integer(value, width, label) {
    if (!/^(0x[0-9a-f]+|[0-9]+)$/i.test(value)) throw new Error(`${label}: nhập số thập phân hoặc hex 0x...`);
    const n = BigInt(value);
    if (n >= (1n << BigInt(width))) throw new Error(`${label} vượt quá ${width} bit.`);
    return n;
  }
  class Cipher {
    constructor(algorithm, key, frame = '0x134') {
      this.tiny = algorithm === 'tiny';
      if (!this.tiny && algorithm !== 'a51') throw new Error('Thuật toán không hợp lệ.');
      if (this.tiny) {
        const bits = binary(key, 23, 'Khóa TinyA5/1');
        this.r = [bits.slice(0, 6), bits.slice(6, 14), bits.slice(14)];
        // PDF chapter 4: clock x1,y3,z3; output after clocking.
        this.taps = [[2, 4, 5], [6, 7], [2, 7, 8]];
        this.clocks = [1, 3, 3];
      } else {
        this.r = [Array(19).fill(0), Array(22).fill(0), Array(23).fill(0)];
        this.taps = [[13, 16, 17, 18], [20, 21], [7, 20, 21, 22]];
        this.clocks = [8, 10, 10];
        const n = integer(key, 64, 'Khóa A5/1');
        for (let byte = 7; byte >= 0; byte--)
          for (let bit = 0; bit < 8; bit++) this.load(Number((n >> BigInt(byte * 8 + bit)) & 1n));
        const f = integer(frame, 22, 'Số khung');
        for (let i = 0; i < 22; i++) this.load(Number((f >> BigInt(i)) & 1n));
        for (let i = 0; i < 100; i++) this.step();
      }
    }
    rotate(index, input = 0) {
      const feedback = this.taps[index].reduce((v, bit) => v ^ this.r[index][bit], input);
      this.r[index] = [feedback, ...this.r[index].slice(0, -1)];
    }
    load(bit) { for (let i = 0; i < 3; i++) this.rotate(i, bit); }
    step(input = 0, trace = false) {
      const before = trace ? this.r.map(r => [...r]) : null;
      const clocks = this.clocks.map((position, i) => this.r[i][position]);
      const majority = Number(clocks.reduce((a, b) => a + b, 0) >= 2);
      const clocked = clocks.map(v => v === majority);
      clocked.forEach((yes, index) => { if (yes) this.rotate(index); });
      const s = this.r.reduce((value, r) => value ^ r[r.length - 1], 0);
      return trace ? {before, after: this.r.map(r => [...r]), clocks, majority, clocked, s,
        input, output: input ^ s} : s;
    }
    bytes(data) {
      const output = new Uint8Array(data.length);
      for (let i = 0; i < data.length; i++) {
        let stream = 0;
        for (let j = 0; j < 8; j++) stream = (stream << 1) | this.step();
        output[i] = data[i] ^ stream;
      }
      return output;
    }
  }
  function bits(algorithm, key, frame, input) {
    const source = binary(input);
    if (source.length > 4096) throw new Error('Tối đa 4096 bit ở chế độ từng bước. Dùng File cho dữ liệu lớn.');
    const cipher = new Cipher(algorithm, key, frame);
    const steps = source.map(bit => cipher.step(bit, true));
    return {output: steps.map(s => s.output).join(''), stream: steps.map(s => s.s).join(''), steps};
  }
  function hex(bytes) { return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''); }
  function unhex(value) {
    if (!/^(?:[0-9a-f]{2})*$/i.test(value)) throw new Error('Bản mã hex phải có đủ cặp ký tự 0–9, a–f.');
    return Uint8Array.from(value.match(/../g) || [], b => parseInt(b, 16));
  }
  function checks() {
    const key = '10010101001110100110000';
    const a = bits('tiny', key, '', '111');
    const cipher = new Cipher('a51', '0x1223456789abcdef', '0x134');
    function burst() {
      const source = Array.from({length: 114}, () => cipher.step()).concat(Array(6).fill(0));
      return hex(Uint8Array.from({length: 15}, (_, i) => source.slice(i * 8, i * 8 + 8).reduce((v, b) => v * 2 + b, 0)));
    }
    const first = burst(), second = burst();
    return [
      {name: 'Ví dụ PDF — TinyA5/1', expected: '011', actual: a.output},
      {name: 'Giải mã ví dụ PDF', expected: '111', actual: bits('tiny', key, '', a.output).output},
      {name: 'Vector A5/1 — 114 bit đầu', expected: '534eaa582fe8151ab6e1855a728c00', actual: first},
      {name: 'Vector A5/1 — 114 bit tiếp', expected: '24fd35a35d5fb6526d32f906df1ac0', actual: second},
    ].map(row => ({...row, passed: row.expected === row.actual}));
  }
  const api = {Cipher, bits, binary, hex, unhex, checks};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.A51Demo = api;
})(typeof window !== 'undefined' ? window : globalThis);
