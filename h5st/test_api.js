/**
 * 验证脚本: 为 JD 搜索 API 生成 h5st 并用 curl 测试
 */
window = global
require('./env-patch')
require('./env')

// ============================================================
// 目标 API: pc_search_searchWare
// 从用户 curl 中提取的参数
// ============================================================
const functionId = "pc_search_searchWare"
const t = Date.now()
const body = {
    "enc": "utf-8",
    "pvid": "16e2663426ac4107a7e055cab9e28480",
    "from": "home",
    "area": "19_1607_4773_62123",
    "page": 1,
    "mode": "",
    "concise": false,
    "hoverPictures": false,
    "newAdvRepeat": false,
    "mixerParam": false,
    "new_interval": true,
    "s": 1,
    "searchbarKeyword": "白酒"
}

const f = {
    appid: "search-pc-java",
    functionId: functionId,
    client: "pc",
    clientVersion: "1.0.0",
    t: t,
    body: require('crypto').createHash('sha256').update(JSON.stringify(body)).digest('hex')
}

// 创建签名实例
window.PSign = new window.ParamsSign({
    appId: 'f06cc',
    preRequest: false,
    onSign: (res) => {
        if (res.code != 0) console.log('[onSign] 签名异常, code:', res.code)
    },
    onRequestTokenRemotely: (res) => {
        if (res.code != 200) console.log('[onRequestTokenRemotely] 异常, code:', res.code)
    },
})

// 生成 h5st
const result = window.PSign._$sdnmd(f)
console.log('_ste:', result._ste)
console.log('_stk:', result._stk)
console.log('t:', t)
console.log('h5st_len:', result.h5st.length)

// 输出 JSON 供 Python 读取
console.log('\n---JSON_OUTPUT---')
console.log(JSON.stringify({
    t: t,
    h5st: result.h5st,
    functionId: functionId,
    appid: "search-pc-java",
    client: "pc",
    clientVersion: "1.0.0",
    body: JSON.stringify(body),
}))
