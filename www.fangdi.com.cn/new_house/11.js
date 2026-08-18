

function get_enviroment(proxy_array) {
    for(var i=0; i<proxy_array.length; i++){
        handler = '{\n' +
            '    get: function(target, property, receiver) {\n' +
            '        console.log("方法:", "get  ", "对象:", ' +
            '"' + proxy_array[i] + '" ,' +
            '"  属性:", property, ' +
            '"  属性类型:", ' + 'typeof property, ' +
            // '"  属性值:", ' + 'target[property], ' +
            '"  属性值类型:", typeof target[property]);\n' +
            '        return target[property];\n' +
            '    },\n' +
            '    set: function(target, property, value, receiver) {\n' +
            '        console.log("方法:", "set  ", "对象:", ' +
            '"' + proxy_array[i] + '" ,' +
            '"  属性:", property, ' +
            '"  属性类型:", ' + 'typeof property, ' +
            // '"  属性值:", ' + 'target[property], ' +
            '"  属性值类型:", typeof target[property]);\n' +
            '        return Reflect.set(...arguments);\n' +
            '    }\n' +
            '}'
        eval('try{\n' + proxy_array[i] + ';\n'
        + proxy_array[i] + '=new Proxy(' + proxy_array[i] + ', ' + handler + ')}catch (e) {\n' + proxy_array[i] + '={};\n'
        + proxy_array[i] + '=new Proxy(' + proxy_array[i] + ', ' + handler + ')}')
    }
}
proxy_array = ['window', 'document', 'location', 'navigator', 'history','screen','meta_tag','div_tag',]

// 这里写你要补的环境



// 这里写你要补的环境
location = {
    "ancestorOrigins": {},
    "href": "https://www.fangdi.com.cn/new_house/new_house.html",
    "origin": "https://www.fangdi.com.cn",
    "protocol": "https:",
    "host": "www.fangdi.com.cn",
    "hostname": "www.fangdi.com.cn",
    "port": "",
    "pathname": "/new_house/new_house.html",
    "search": "",
    "hash": ""
}
window = global
window.top = window
window.addEventListener = function (){}
window.setTimeout = function (){}
window.setInterval = function (){}
window.location = location
localStorage = {
    length: 0,
    removeItem: function () {
    },
    setItem: function () {
        this[arguments[0]] = arguments[1];
    },
    getItem: function (args) {
        return this[args];
    },
}
sessionStorage = {
    length: 0,
    removeItem: function () {
    },
    setItem: function () {
        this[arguments[0]] = arguments[1];
    },
    getItem: function (args) {
        return this[args];
    },
}
window.self = window;
window.localStorage = localStorage;
window.sessionStorage = sessionStorage;
window.name ='$_YWTU=YBarpxH2Jbtjmhl.UY7DgmO6iZFW5uO8kLQQXp4Z2wg&$_YVTX=WOE&vdFm='
window.Request = function (args)
{
    return {};
}

window.fetch  = function (args)
{
    return {};
}

window.navigator = {}

window.history = {
    length: 1,
    state: null,
    scrollRestoration: "auto",
    replaceState:function (){}
}
div_tag = {
    getElementsByTagName: function (val){
        console.log('divt_tag----------->getElementsByTagName', val)
        if (val ==="i"){
            return []
        }
    }
}
meta_tag = {
    id:"2vmka0flZgDo",
    content:"28j5Sb.goNm.J1y6XGBRr..RvWs4DVAs8yoawvA58zhcpQbLvXPjd9kkdL8JyTuaRlANKyAFhkdaN6X8NqxC5nX9lbQVYPZvt2qRpeU6._Z",
    getAttribute:function (val){
        console.log('meta_tag----------->getAttribute', val)
        if (val === 'r'){
            return'm'
        }
    },
    parentNode:{
        removeChild:function (){
            console.log("meta.parentNode----->removeChild",arguments)
            return {}
        }
    }
}
scripts = [
                {
                    parentElement: {
                        // getAttribute: function(args) {
                        //     if (args == 'r')
                        //     {
                        //         return 'm';
                        //     }
                        // },
                        // getElementsByTagName: function(args) {
                        // },
                         removeChild: function (args) {
                        },
                    },
                    getAttribute: function(args) {
                        if (args == 'r')
                        {
                            return 'm';
                        }
                    }
                },
                {

                    parentElement: {
                        //  getAttribute: function(args) {
                        // },
                        // getElementsByTagName: function(args) {
                        // },
                         removeChild: function (args) {
                        },
                    },
                    getAttribute: function(args) {
                        if (args == 'r')
                        {
                            return 'm';
                        }
                    },
                }
            ]
// frist_get_script = 1;
document = {
    createElement:function (val){
        console.log('document----------->createElement', val)
        if (val ==="div"){
            return div_tag
        }
    },
    getElementById:function (){
        return meta_tag
    },
    getElementsByTagName:function (val){
        console.log('document----------->getElementsByTagName', val)
        if (val==='base'){
            return []
        }
        if (val == 'script')
        {
            console.log('document----------->getElementsByTagName', val)
            // if (frist_get_script == 1)

            return scripts;
        }
    },
    addEventListener:function (){},
    attachEvent:function (){},
    documentElement:{},
    appendChild:function (){},
    removeChild:function (){}

}
Object.defineProperty(document, 'visibilityState', {
    get: function() {
         // 程序执行到这里会自动暂停（需要打开调试器）
        return 'visible';  // 返回你需要的值
    },
    configurable: true,
    enumerable: true
})


const v8 =require('v8');
const vm= require('vm');
v8.setFlagsFromString('--allow-natives-syntax');
let undetectable = vm.runInThisContext("%GetUndetectable()");
v8.setFlagsFromString('--no-allow-natives-syntax');

Object.defineProperty(document,'all',{
    configurable: true,
    enumerable: true,
    value: undetectable,
    writable: true,
})
Object.defineProperty(document.all,'length',{
    get : function (){
        return Object.keys(document.all).length
    }
})
document.all[0] = null;

get_enviroment(proxy_array)
const originalEval = window.eval;
// 重写 eval
window.eval = function(code) {
    // 判断如果是字符串，且包含 debugger
    if (typeof code === 'string' && code.includes('debugger')) {
        // 核心操作：将字符串中的 'debugger' 替换为空字符串或注释掉
        // 注意：使用正则 /\bdebugger\b/g 可以精准匹配单词，避免误伤变量名
        let newCode = code.replace(/\bdebugger\b/g, '');

        // 执行处理后的代码，并返回结果
        return originalEval.call(this, newCode);
    }
    // 如果没有 debugger，直接原样执行
    return originalEval.call(this, code);
};

var content = "28j5Sb.goNm.J1y6XGBRr..RvWs4DVAs8yoawvA58zhcpQbLvXPjd9kkdL8JyTuaRlANKyAFhkdaN6X8NqxC5nX9lbQVYPZvt2qRpeU6._Z"

require('./ts')
require('./link')


function get_cookie()
{
    return document.cookie;
}

console.log(get_cookie())
