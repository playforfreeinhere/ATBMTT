const assert = require('node:assert/strict');
const {Cipher, bits, checks, hex, unhex} = require('../ui/web/core.js');
for (const row of checks()) { assert.equal(row.actual, row.expected, row.name); console.log('PASS', row.name); }
const k = '10010101001110100110000';
const tiny = bits('tiny', k, '', '111');
assert.equal(tiny.stream, '100');
assert.deepEqual(tiny.steps[0].clocks, [0,0,1]);
assert.equal(tiny.steps[0].majority, 0);
assert.deepEqual(tiny.steps[0].clocked, [true,true,false]);
for (const [algorithm, key] of [['tiny', k], ['a51', '0x1223456789abcdef']]) {
  const original = new TextEncoder().encode('Xin chào Việt Nam 🔑');
  const enc = new Cipher(algorithm, key).bytes(original);
  assert.notDeepEqual(enc, original);
  assert.deepEqual(new Cipher(algorithm, key).bytes(enc), original);
  assert.deepEqual(unhex(hex(enc)), enc);
  const data = Uint8Array.from({length: 9000}, (_,i)=>i % 256);
  const cipher = new Cipher(algorithm, key);
  const chunked = new Uint8Array(9000);
  chunked.set(cipher.bytes(data.subarray(0,4096)));
  chunked.set(cipher.bytes(data.subarray(4096)),4096);
  assert.deepEqual(chunked, new Cipher(algorithm, key).bytes(data));
  console.log('PASS', algorithm, 'UTF-8/binary/chunked roundtrips');
}
for (const bad of ['', '01 1', 'abc']) assert.throws(()=>bits('tiny', k, '', bad));
assert.throws(()=>new Cipher('tiny', k.slice(1)));
assert.throws(()=>new Cipher('a51', '0x10000000000000000'));
assert.throws(()=>new Cipher('a51', '1', '0x400000'));
assert.throws(()=>unhex('123'));
assert.throws(()=>unhex('zz'));
console.log('PASS invalid inputs rejected');
