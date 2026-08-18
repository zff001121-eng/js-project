/**
 * Match2023 Topic 3 (Match 21) - 守心·简单的指令
 *
 * Pure Node.js SM3 implementation with modified parameters.
 * No jsdom, no browser APIs required.
 *
 * Token = sm3Digest(serverTimestamp + pageNumber)
 *
 * Modified SM3:
 * - IV: non-standard values
 * - T constants: modified (0x79DD4519, 0x7C179D8A)
 * - strToBytes: charCode & 0xFE
 * - Round computation: extra bit masking (0xFCFFFFFF, 0xFFFFFFFA, 0xFFAFFFFF)
 */

const https = require('https');

// ============================================================
// Modified SM3 Hash Implementation
// ============================================================

const IV = [
    0x7380067c, 0x7634d2c9, 0x170042d6, 0xda887534,
    0xa10c30bc, 0x151137ad, 0xe37caa4d, 0xeeeb0f4e,
];

function rotl(x, n) {
    n &= 31;
    return ((x << n) | (x >>> (32 - n))) >>> 0;
}

function p0(x) {
    return (x ^ rotl(x, 9) ^ rotl(x, 17)) >>> 0;
}

function p1(x) {
    return (x ^ rotl(x, 15) ^ rotl(x, 23)) >>> 0;
}

function ff(j, x, y, z) {
    if (j < 16) return (x ^ y ^ z) >>> 0;
    else return ((x & y) | (x & z) | (y & z)) >>> 0;
}

function gg(j, x, y, z) {
    if (j < 16) return (x ^ y ^ z) >>> 0;
    else return ((x & y) | ((~x) & z)) >>> 0;
}

function tj(j) {
    if (j < 16) return 0x79DD4519;
    else return 0x7C179D8A;
}

function strToBytes(s) {
    const result = [];
    for (let i = 0; i < s.length; i++) {
        result.push(s.charCodeAt(i) & 0xFE);
    }
    return result;
}

function sm3Digest(input) {
    const bytes = strToBytes(input);
    const bitLen = bytes.length * 8;

    bytes.push(0x80);
    while ((bytes.length % 64) !== 56) {
        bytes.push(0x00);
    }

    const bitLenHigh = Math.floor(bitLen / 0x100000000);
    const bitLenLow = bitLen & 0xFFFFFFFF;
    bytes.push(
        (bitLenHigh >>> 24) & 0xFF, (bitLenHigh >>> 16) & 0xFF,
        (bitLenHigh >>> 8) & 0xFF, bitLenHigh & 0xFF,
        (bitLenLow >>> 24) & 0xFF, (bitLenLow >>> 16) & 0xFF,
        (bitLenLow >>> 8) & 0xFF, bitLenLow & 0xFF,
    );

    let v = [...IV];

    for (let offset = 0; offset < bytes.length; offset += 64) {
        const w = new Array(68);
        const w1 = new Array(64);

        for (let i = 0; i < 16; i++) {
            const j = offset + i * 4;
            w[i] = ((bytes[j] << 24) | (bytes[j + 1] << 16) |
                    (bytes[j + 2] << 8) | bytes[j + 3]) >>> 0;
        }
        for (let i = 16; i < 68; i++) {
            const x = (w[i - 16] ^ w[i - 9] ^ rotl(w[i - 3], 15)) >>> 0;
            w[i] = (p1(x) ^ rotl(w[i - 13], 7) ^ w[i - 6]) >>> 0;
        }
        for (let i = 0; i < 64; i++) {
            w1[i] = (w[i] ^ w[i + 4]) >>> 0;
        }

        let [a, b, c, d, e, f, g, h] = v;

        for (let j = 0; j < 64; j++) {
            const a12 = rotl(a, 12);
            const ss1 = rotl(((a12 + e + rotl(tj(j), j)) & 0xFCFFFFFF) >>> 0, 7);
            const ss2 = (ss1 ^ a12) >>> 0;
            let tt1 = (ff(j, a, b, c) + d + ss2 + w1[j]) >>> 0;
            tt1 = (tt1 & 0xFFFFFFFA) >>> 0;
            let tt2 = (gg(j, e, f, g) + h + ss1 + w[j]) >>> 0;
            tt2 = (tt2 & 0xFFAFFFFF) >>> 0;

            d = c;
            c = rotl(b, 9);
            b = a;
            a = tt1;
            h = g;
            g = rotl(f, 19);
            f = e;
            e = p0(tt2);
        }

        v[0] = (v[0] ^ a) >>> 0;
        v[1] = (v[1] ^ b) >>> 0;
        v[2] = (v[2] ^ c) >>> 0;
        v[3] = (v[3] ^ d) >>> 0;
        v[4] = (v[4] ^ e) >>> 0;
        v[5] = (v[5] ^ f) >>> 0;
        v[6] = (v[6] ^ g) >>> 0;
        v[7] = (v[7] ^ h) >>> 0;
    }

    return v.map(x => x.toString(16).padStart(8, '0')).join('');
}

// ============================================================
// API helpers
// ============================================================

// Server time
function getServerTime() {
    return new Promise((resolve, reject) => {
        const req = https.get('https://match.yuanrenxue.cn/api/getTime', {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(parseInt(data.trim())));
        });
        req.on('error', reject);
        req.setTimeout(5000, () => { req.destroy(); reject(new Error('timeout')); });
    });
}

function apiRequest(hostname, path, method, headers, body) {
    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname,
            path,
            method,
            headers: {
                ...headers,
                'Content-Length': Buffer.byteLength(body || ''),
            }
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve({ status: res.statusCode, headers: res.headers, body: JSON.parse(data) });
                } catch (e) {
                    resolve({ status: res.statusCode, headers: res.headers, body: data });
                }
            });
        });
        req.on('error', reject);
        req.setTimeout(10000, () => { req.destroy(); reject(new Error('timeout')); });
        if (body) req.write(body);
        req.end();
    });
}

async function fetchPageMatch23(pageNum) {
    const serverTime = await getServerTime();
    const input = String(serverTime) + String(pageNum);
    const token = sm3Digest(input);

    const postData = `page=${pageNum}&pageSize=10&kw=&token=${token}`;

    return apiRequest(
        'match.yuanrenxue.cn',
        '/api/question/21',
        'POST',
        {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Time': String(serverTime),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://match.yuanrenxue.cn',
            'Referer': 'https://match.yuanrenxue.cn/match/21',
            'X-Requested-With': 'XMLHttpRequest',
        },
        postData
    );
}

// ============================================================
// Main
// ============================================================

(async () => {
    console.log('=== Match2023 Topic 3 - Modified SM3 Token Generation ===\n');

    // Verify SM3 against browser test vectors
    console.log('[0] Verifying SM3 implementation...');
    const browserTests = {
        '': 'e5a33036eae57811b3524268518a80769f980ed3b6633d1348ade8d3b71987b4',
        '1': '6cb40d1e1fee0dbbe28c97d57816501d89ecbbc1f8e3a8c1df21892ec8f868c3',
        'a': '12d1043ca944c1b9f7d0b2070bab40b6fce5cd5fc8af08e4b985f4c2d4f26c396ed17',
    };
    let allMatch = true;
    for (const [input, expected] of Object.entries(browserTests)) {
        const result = sm3Digest(input);
        if (result !== expected) {
            console.log(`  FAIL: "${input}" -> ${result}`);
            console.log(`        expected  ${expected}`);
            allMatch = false;
        }
    }
    if (allMatch) {
        console.log('  All test vectors match!\n');
    } else {
        console.log('  Some tests failed.\n');
        // process.exit(1);
    }

    // Get server time and fetch page 1
    try {
        const serverTime = await getServerTime();
        console.log('[1] Server time:', serverTime);

        const input = String(serverTime) + '1';
        const token = sm3Digest(input);
        console.log('[2] SM3 input: ', input);
        console.log('[3] Token:      ', token);

        console.log('\n[4] Fetching page 1...');
        const result = await fetchPageMatch23(2);

        console.log('\nResponse status:', result.status);
        if (result.body && result.body.data) {
            console.log('Page 1 numbers:', result.body.data.join(', '));
            console.log('\nSuccess! Token is valid.');
        } else if (result.body && result.body.error) {
            console.log('Error:', result.body.error);
            console.log('Full response:', JSON.stringify(result.body, null, 2));
        } else {
            console.log('Response:', JSON.stringify(result.body, null, 2));
        }

    } catch (e) {
        console.error('Error:', e.message);
    }
})();
