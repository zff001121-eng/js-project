const { performance } = require('perf_hooks')

function random(min, max) {
    return Math.random() * (max - min) + min
}

function buildTrack() {

    const count = Math.floor(Math.random() * 3) + 1

    const track = []

    let x = 300
    let y = 400
    let aaa = 10000 + Math.random() * 20000

    // 用 performance.now 模拟真实时间起点
    let start = performance.now() + aaa

    for (let i = 0; i < count; i++) {

        // 模拟人不是连续动，而是“动一下 + 停顿”
        const moveDelay = random(16, 60)
        start += moveDelay

        // 微抖动
        x += random(-15, 30)
        y += random(-10, 20)

        track.push({
            elementId: "",
            clientX: Math.round(x),
            clientY: Math.round(y),

            // 核心：类似 event.timeStamp
            timestamp: Math.floor(start)
        })

        // 偶尔停顿
        if (Math.random() < 0.3) {
            start += random(80, 300)
        }
    }

    return track
}

window = global
// delete Buffer
document = {
    addEventListener: function(){},
    cookie:""
}
screen  = {
    availWidth: 1920,
    availHeight: 1032
}
localStorage = {
    _nano_fp :"Xpm8n5E8XpdyX0dyno_f8uaWG~bhKpkANqy0eMPf",
}
window.chrome = {}
window.DeviceOrientationEvent = function (){}
window.DeviceMotionEvent = function (){}
window.Buffer = undefined
window.outerHeight = 1032
window.outerWidth = 1920
history = {}
location = {
    "ancestorOrigins": {},
    "href": "https://pinduoduo.com/home/girlclothes/",
    "origin": "https://pinduoduo.com",
    "protocol": "https:",
    "host": "pinduoduo.com",
    "hostname": "pinduoduo.com",
    "port": "",
    "pathname": "/home/girlclothes/",
    "search": "",
    "hash": ""
}
Navigator = {
    webdriver:false,
    plugins:{
        length:5
    },
    languages: ['zh-CN', 'en', 'en-GB', 'en-US'],
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
}

navigator = {}
Object.setPrototypeOf(navigator, Navigator)
