// ============================================================
// JD H5ST work.js — 补环境入口
// 基于 web-reverse-env skill 诊断补全
// ============================================================

window = global

// 第 0 步: 先加载浏览器环境补丁 (env-patch.js)
// 按 skill 方法论: prototype-builder → descriptor-guard → native-protector → BOM/DOM 对象
require('./env-patch')

// 第 1 步: 加载 JD H5ST 算法本体 (env.js)
require('./env')

// ============================================================
// 第 2 步: 调用签名
// ============================================================

// 填充实际参数 (用户按需修改)
const e = "search"          // functionId: 接口标识
const i = Date.now()        // t: 时间戳
const t = null              // body: 请求体 (无 body 时传 null)

const f = {
    appid: "search-pc-java",
    functionId: e,
    client: "pc",
    clientVersion: "1.0.0",
    t: i
}

// 如果有请求体，计算 SHA256
if (t) {
    // SHA256 由 env.js 内部提供，通过 crypto-js 模块访问
    // 若 window.SHA256 未直接暴露，使用 Node 内置 crypto:
    const crypto = require('crypto')
    f.body = crypto.createHash('sha256').update(JSON.stringify(t)).digest('hex')
}

// 创建签名实例
window.PSign = new window.ParamsSign({
    appId: 'f06cc',
    preRequest: false,
    onSign: (res) => {
        if (res.code != 0) {
            console.log('[onSign] 签名失败, code:', res.code)
        }
    },
    onRequestTokenRemotely: (res) => {
        if (res.code != 200) {
            console.log('[onRequestTokenRemotely] Token请求失败, code:', res.code)
        }
    },
})

// 调用 _$sdnmd 生成 h5st 签名
const data = window.PSign._$sdnmd(f)

console.log('=== H5ST 签名结果 ===')
console.log(data.h5st.length)
console.log(JSON.stringify(data, null, 2))