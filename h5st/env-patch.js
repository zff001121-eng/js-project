/**
 * JD H5ST 补环境模块
 *
 * 基于 web-reverse-env skill 方法论:
 * - 诊断驱动: 先定位崩溃点 Object.keys(window.document) → document 未定义
 * - 按层补: 先补中断对象 → 再补检测对象 → 最后保护 native toString
 * - 模块化: 每个对象按 "构造器 → prototype → 实例" 三层结构补全
 *
 * 当前任务: 第1类问题 (undefined 中断) + 第2类 (原型链/描述符检测)
 */

// ============================================================
// 第 1 层: native toString 保护 (优先级最高，先装)
// ============================================================
(function installNativeProtector() {
  const rawToString = Function.prototype.toString;
  const nativeSymbol = Symbol("native_toString");

  function defineHidden(target, key, value) {
    Object.defineProperty(target, key, {
      configurable: true,
      enumerable: false,
      writable: true,
      value,
    });
  }

  function markNative(fn, displayName) {
    if (typeof fn !== "function") return fn;
    const name = displayName || fn.name || "";
    defineHidden(fn, nativeSymbol, "function " + name + "() { [native code] }");
    return fn;
  }

  function protectedToString() {
    if (typeof this === "function" && this[nativeSymbol]) {
      return this[nativeSymbol];
    }
    return rawToString.call(this);
  }

  // 接管 Function.prototype.toString
  defineHidden(Function.prototype, "toString", protectedToString);
  defineHidden(Function, "toString", protectedToString);
  markNative(Function.prototype.toString, "toString");

  // 导出保护工具到全局
  global.__nativeProtector = {
    nativeSymbol,
    markNative,
    protectDescriptor(target, key) {
      const desc = Object.getOwnPropertyDescriptor(target, key);
      if (!desc) return false;
      if (typeof desc.get === "function") markNative(desc.get, "get " + key);
      if (typeof desc.set === "function") markNative(desc.set, "set " + key);
      if (typeof desc.value === "function") markNative(desc.value, desc.value.name || key);
      return true;
    },
    repairFunctionMeta(fn, meta) {
      if (typeof fn !== "function") return fn;
      if (meta && Object.prototype.hasOwnProperty.call(meta, "name")) {
        Object.defineProperty(fn, "name", { configurable: true, enumerable: false, writable: false, value: meta.name });
      }
      if (meta && Object.prototype.hasOwnProperty.call(meta, "length")) {
        Object.defineProperty(fn, "length", { configurable: true, enumerable: false, writable: false, value: meta.length });
      }
      return fn;
    },
  };
})();

const { markNative, protectDescriptor, repairFunctionMeta } = global.__nativeProtector;

// ============================================================
// 第 2 层: 构造器 + 原型链 骨架
// ============================================================

// --- EventTarget (最底层) ---
function EventTarget() {}
EventTarget.prototype.addEventListener = markNative(function addEventListener() {}, "addEventListener");
EventTarget.prototype.removeEventListener = markNative(function removeEventListener() {}, "removeEventListener");
EventTarget.prototype.dispatchEvent = markNative(function dispatchEvent() {}, "dispatchEvent");

// --- Node (继承 EventTarget) ---
function Node() {}
Node.prototype = Object.create(EventTarget.prototype);
Node.prototype.constructor = Node;

// --- Element (继承 Node) ---
function Element() {}
Element.prototype = Object.create(Node.prototype);
Element.prototype.constructor = Element;
Element.prototype.scrollIntoViewIfNeeded = markNative(function scrollIntoViewIfNeeded() {}, "scrollIntoViewIfNeeded");
Element.prototype.querySelector = markNative(function querySelector() { return null; }, "querySelector");
Element.prototype.querySelectorAll = markNative(function querySelectorAll() { return []; }, "querySelectorAll");
Element.prototype.getAttribute = markNative(function getAttribute() { return null; }, "getAttribute");
Element.prototype.setAttribute = markNative(function setAttribute() {}, "setAttribute");
Element.prototype.removeAttribute = markNative(function removeAttribute() {}, "removeAttribute");

// --- HTMLElement (继承 Element) ---
function HTMLElement() {}
HTMLElement.prototype = Object.create(Element.prototype);
HTMLElement.prototype.constructor = HTMLElement;

// --- HTMLCanvasElement ---
function HTMLCanvasElement() {}
HTMLCanvasElement.prototype = Object.create(HTMLElement.prototype);
HTMLCanvasElement.prototype.constructor = HTMLCanvasElement;
HTMLCanvasElement.prototype.getContext = markNative(function getContext() { return null; }, "getContext");
HTMLCanvasElement.prototype.toDataURL = markNative(function toDataURL() { return ""; }, "toDataURL");

// --- HTMLDocument ---
function HTMLDocument() {}
HTMLDocument.prototype = Object.create(HTMLElement.prototype);
HTMLDocument.prototype.constructor = HTMLDocument;

// 导出构造器到全局 (env.js 会通过 Object.keys(Element.prototype) 访问)
global.EventTarget = EventTarget;
global.Node = Node;
global.Element = Element;
global.HTMLElement = HTMLElement;
global.HTMLCanvasElement = HTMLCanvasElement;
global.HTMLDocument = HTMLDocument;
global.Document = HTMLDocument; // Document 别名

// ============================================================
// 第 3 层: document 对象 (P0 - 解决崩溃)
// ============================================================
const _document = Object.create(HTMLDocument.prototype);

// document 基础属性 (用访问器保护)
Object.defineProperty(_document, "URL", {
  configurable: true, enumerable: true,
  get: markNative(function URL() { return "https://www.jd.com/"; }, "get URL"),
  set: markNative(function URL() {}, "set URL"),
});
Object.defineProperty(_document, "domain", {
  configurable: true, enumerable: true,
  get: markNative(function domain() { return "jd.com"; }, "get domain"),
});
Object.defineProperty(_document, "referrer", {
  configurable: true, enumerable: true,
  get: markNative(function referrer() { return ""; }, "get referrer"),
});
Object.defineProperty(_document, "readyState", {
  configurable: true, enumerable: true,
  get: markNative(function readyState() { return "complete"; }, "get readyState"),
});
Object.defineProperty(_document, "title", {
  configurable: true, enumerable: true,
  get: markNative(function title() { return "京东"; }, "get title"),
  set: markNative(function title() {}, "set title"),
});

// document.cookie (访问器 - 高频检测点)
let _cookieStore = "3AB9D23F7A4B3C9B=WHHQLOLUJHLHMSPQCJMTO5YU3M5SXM; shshshfpa=34fe889b-4423-9411-df03-e9efb1ca5969-1756717173; shshshfpx=34fe889b-4423-9411-df03-e9efb1ca5969-1756717173; __jda=122270672.17567171712081118022147.1756717171.1756717171.1756717171.1; __jdb=122270672.1.17567171712081118022147|1.1756717171; __jdc=122270672; __jdv=122270672|direct|-|none|-|1758345643037";
Object.defineProperty(_document, "cookie", {
  configurable: true, enumerable: true,
  get: markNative(function cookie() { return _cookieStore; }, "get cookie"),
  set: markNative(function cookie(v) { _cookieStore = v; }, "set cookie"),
});

// document 方法
_document.createElement = markNative(function createElement(tagName) {
  if (typeof tagName === "string" && tagName.toLowerCase() === "canvas") {
    return Object.create(HTMLCanvasElement.prototype);
  }
  return Object.create(HTMLElement.prototype);
}, "createElement");
_document.querySelector = markNative(function querySelector() { return Object.create(HTMLElement.prototype); }, "querySelector");
_document.querySelectorAll = markNative(function querySelectorAll() { return []; }, "querySelectorAll");
_document.getElementById = markNative(function getElementById() { return Object.create(HTMLElement.prototype); }, "getElementById");
_document.getElementsByTagName = markNative(function getElementsByTagName() {
  return [Object.create(HTMLElement.prototype)];
}, "getElementsByTagName");
_document.getElementsByClassName = markNative(function getElementsByClassName() { return []; }, "getElementsByClassName");
_document.head = Object.create(HTMLElement.prototype);
_document.body = Object.create(HTMLElement.prototype);
_document.documentElement = Object.create(HTMLElement.prototype);

// ★ document.all — 特殊对象 (skill 明确标记为高风险)
// 使用 fallback 路线: 创建一个类 HTMLAllCollection 对象
const _documentAll = Object.create(HTMLElement.prototype);
// 模拟 document.all 的特殊行为: typeof === "undefined" 但又能被访问
// 在纯 JS 中难以完美模拟，这里使用 Proxy 降级方案
_document.all = _documentAll;
// 注意: 代码 L800: fF(0x1fd) == typeof document && document.all
// "undefined" == typeof document → 检查是否在全局 undefined 类型的 document
// 实际浏览器中 typeof document === "object"，所以这个分支不会走 document.all 检查

// document 其他属性
_document.characterSet = "UTF-8";
_document.charset = "UTF-8";
_document.compatMode = "CSS1Compat";
_document.contentType = "text/html";
_document.doctype = null;
_document.documentURI = "https://www.jd.com/";
_document.forms = [];
_document.hidden = false;
_document.images = [];
_document.implementation = {};
_document.lastModified = "06/17/2026 22:00:00";
_document.links = [];
_document.scripts = [];
_document.scrollingElement = Object.create(HTMLElement.prototype);
_document.visibilityState = "visible";

// 挂在 window 上
global.document = _document;

// ============================================================
// 第 4 层: Navigator 模块 (P1 - 指纹关键)
// ============================================================
function Navigator() {}
Navigator.prototype.constructor = Navigator;

const _navigator = Object.create(Navigator.prototype);

// 关键字段 (用访问器)
const navUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36";
Object.defineProperty(_navigator, "userAgent", {
  configurable: true, enumerable: true,
  get: markNative(function userAgent() { return navUA; }, "get userAgent"),
});
Object.defineProperty(_navigator, "appVersion", {
  configurable: true, enumerable: true,
  get: markNative(function appVersion() { return "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"; }, "get appVersion"),
});
Object.defineProperty(_navigator, "platform", {
  configurable: true, enumerable: true,
  get: markNative(function platform() { return "Win32"; }, "get platform"),
});
Object.defineProperty(_navigator, "language", {
  configurable: true, enumerable: true,
  get: markNative(function language() { return "zh-CN"; }, "get language"),
});
Object.defineProperty(_navigator, "languages", {
  configurable: true, enumerable: true,
  get: markNative(function languages() { return ["zh-CN", "zh"]; }, "get languages"),
});
Object.defineProperty(_navigator, "webdriver", {
  configurable: true, enumerable: true,
  get: markNative(function webdriver() { return false; }, "get webdriver"),
});
Object.defineProperty(_navigator, "cookieEnabled", {
  configurable: true, enumerable: true,
  get: markNative(function cookieEnabled() { return true; }, "get cookieEnabled"),
});
Object.defineProperty(_navigator, "hardwareConcurrency", {
  configurable: true, enumerable: true,
  get: markNative(function hardwareConcurrency() { return 8; }, "get hardwareConcurrency"),
});
Object.defineProperty(_navigator, "deviceMemory", {
  configurable: true, enumerable: true,
  get: markNative(function deviceMemory() { return 8; }, "get deviceMemory"),
});
Object.defineProperty(_navigator, "maxTouchPoints", {
  configurable: true, enumerable: true,
  get: markNative(function maxTouchPoints() { return 0; }, "get maxTouchPoints"),
});
Object.defineProperty(_navigator, "vendor", {
  configurable: true, enumerable: true,
  get: markNative(function vendor() { return "Google Inc."; }, "get vendor"),
});
Object.defineProperty(_navigator, "vendorSub", {
  configurable: true, enumerable: true,
  get: markNative(function vendorSub() { return ""; }, "get vendorSub"),
});
Object.defineProperty(_navigator, "appCodeName", {
  configurable: true, enumerable: true,
  get: markNative(function appCodeName() { return "Mozilla"; }, "get appCodeName"),
});
Object.defineProperty(_navigator, "appName", {
  configurable: true, enumerable: true,
  get: markNative(function appName() { return "Netscape"; }, "get appName"),
});
Object.defineProperty(_navigator, "onLine", {
  configurable: true, enumerable: true,
  get: markNative(function onLine() { return true; }, "get onLine"),
});
Object.defineProperty(_navigator, "pdfViewerEnabled", {
  configurable: true, enumerable: true,
  get: markNative(function pdfViewerEnabled() { return true; }, "get pdfViewerEnabled"),
});
Object.defineProperty(_navigator, "productSub", {
  configurable: true, enumerable: true,
  get: markNative(function productSub() { return "20030107"; }, "get productSub"),
});

// plugins / mimeTypes — 类数组结构 (高频检测点)
const _plugins = Object.create(Object.prototype);
Object.defineProperty(_plugins, "length", { configurable: true, enumerable: true, get: markNative(function() { return 5; }, "get length") });
_plugins[0] = { name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format", length: 1 };
_plugins[1] = { name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: "", length: 1 };
_plugins[2] = { name: "Native Client", filename: "internal-nacl-plugin", description: "", length: 2 };
_plugins[3] = { name: " Widevine Content Decryption Module", filename: "widevinecdmadapter.dll", description: "Enables Widevine licenses for playback of HTML audio/video content.", length: 1 };
_plugins[4] = { name: " Microsoft Edge®", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: "", length: 0 };
Object.defineProperty(_navigator, "plugins", {
  configurable: true, enumerable: true,
  get: markNative(function plugins() { return _plugins; }, "get plugins"),
});

const _mimeTypes = Object.create(Object.prototype);
Object.defineProperty(_mimeTypes, "length", { configurable: true, enumerable: true, get: markNative(function() { return 4; }, "get length") });
_mimeTypes[0] = { type: "application/pdf", suffixes: "pdf", description: "Portable Document Format" };
_mimeTypes[1] = { type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format" };
_mimeTypes[2] = { type: "application/x-nacl", suffixes: "", description: "Native Client Executable" };
_mimeTypes[3] = { type: "application/vnd.google.picasa", suffixes: "", description: "" };
Object.defineProperty(_navigator, "mimeTypes", {
  configurable: true, enumerable: true,
  get: markNative(function mimeTypes() { return _mimeTypes; }, "get mimeTypes"),
});

global.navigator = _navigator;

// ============================================================
// 第 5 层: window 对象补全 (P1)
// ============================================================

// window 引用关系
global.window = global;
global.self = global;
global.top = global;
global.parent = global;
global.frames = global;
global.globalThis = global;

// crypto (P1 - getRandomValues 调用)
global.crypto = {
  getRandomValues: markNative(function getRandomValues(buf) {
    // 简单的随机填充
    if (buf instanceof Uint8Array || buf instanceof Uint8ClampedArray) {
      for (let i = 0; i < buf.length; i++) buf[i] = Math.floor(Math.random() * 256);
    } else if (buf instanceof Uint16Array) {
      for (let i = 0; i < buf.length; i++) buf[i] = Math.floor(Math.random() * 65536);
    } else if (buf instanceof Uint32Array) {
      for (let i = 0; i < buf.length; i++) buf[i] = Math.floor(Math.random() * 4294967296);
    }
    return buf;
  }, "getRandomValues"),
  subtle: {},
  randomUUID: markNative(function randomUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }, "randomUUID"),
};
global.msCrypto = global.crypto;

// localStorage (P1 - 存储态读取)
const _localStorageStore = {};
global.localStorage = {
  getItem: markNative(function getItem(key) { return _localStorageStore[key] || null; }, "getItem"),
  setItem: markNative(function setItem(key, value) { _localStorageStore[key] = String(value); }, "setItem"),
  removeItem: markNative(function removeItem(key) { delete _localStorageStore[key]; }, "removeItem"),
  clear: markNative(function clear() { for (const k in _localStorageStore) delete _localStorageStore[k]; }, "clear"),
  key: markNative(function key(index) { return Object.keys(_localStorageStore)[index] || null; }, "key"),
};
Object.defineProperty(global.localStorage, "length", {
  configurable: true, enumerable: true,
  get: markNative(function length() { return Object.keys(_localStorageStore).length; }, "get length"),
});

// sessionStorage
const _sessionStorageStore = {};
global.sessionStorage = {
  getItem: markNative(function getItem(key) { return _sessionStorageStore[key] || null; }, "getItem"),
  setItem: markNative(function setItem(key, value) { _sessionStorageStore[key] = String(value); }, "setItem"),
  removeItem: markNative(function removeItem(key) { delete _sessionStorageStore[key]; }, "removeItem"),
  clear: markNative(function clear() { for (const k in _sessionStorageStore) delete _sessionStorageStore[k]; }, "clear"),
  key: markNative(function key(index) { return Object.keys(_sessionStorageStore)[index] || null; }, "key"),
};
Object.defineProperty(global.sessionStorage, "length", {
  configurable: true, enumerable: true,
  get: markNative(function length() { return Object.keys(_sessionStorageStore).length; }, "get length"),
});

// XMLHttpRequest (P1 - 网络请求) ★ 真实 HTTP 实现
const _http = require('http');
const _https = require('https');
const _url = require('url');

function XMLHttpRequest() {
  this.readyState = 0;
  this.status = 0;
  this.statusText = "";
  this.responseText = "";
  this.response = null;
  this.responseType = "";
  this.responseURL = "";
  this.responseXML = null;
  this.onreadystatechange = null;
  this.onload = null;
  this.onerror = null;
  this.ontimeout = null;
  this.timeout = 0;
  this.withCredentials = false;
  this._method = "GET";
  this._url = "";
  this._async = true;
  this._headers = {};
  this._body = null;
}
XMLHttpRequest.UNSENT = 0;
XMLHttpRequest.OPENED = 1;
XMLHttpRequest.HEADERS_RECEIVED = 2;
XMLHttpRequest.LOADING = 3;
XMLHttpRequest.DONE = 4;

XMLHttpRequest.prototype.open = markNative(function open(method, url, async) {
  this._method = method.toUpperCase();
  this._url = url;
  this._async = async !== false;
  this._headers = {};
  this.readyState = XMLHttpRequest.OPENED;
}, "open");

XMLHttpRequest.prototype.setRequestHeader = markNative(function setRequestHeader(name, value) {
  this._headers[name] = value;
}, "setRequestHeader");

XMLHttpRequest.prototype.send = markNative(function send(body) {
  this._body = body || null;
  const self = this;
  const parsed = _url.parse(this._url);
  const isHttps = parsed.protocol === 'https:';
  const transport = isHttps ? _https : _http;

  const options = {
    hostname: parsed.hostname,
    port: parsed.port || (isHttps ? 443 : 80),
    path: parsed.path,
    method: this._method,
    headers: Object.assign({}, this._headers),
    rejectUnauthorized: false,
  };

  if (this._body && !options.headers['Content-Length']) {
    options.headers['Content-Length'] = Buffer.byteLength(this._body);
  }

  const req = transport.request(options, function(res) {
    self.status = res.statusCode;
    self.statusText = res.statusMessage;
    self.readyState = XMLHttpRequest.HEADERS_RECEIVED;
    if (self.onreadystatechange) self.onreadystatechange();

    let data = '';
    res.on('data', function(chunk) { data += chunk; });
    res.on('end', function() {
      self.responseText = data;
      self.response = data;
      self.readyState = XMLHttpRequest.DONE;
      if (self.onreadystatechange) self.onreadystatechange();
      if (self.onload) self.onload();
    });
  });

  req.on('error', function(err) {
    self.readyState = XMLHttpRequest.DONE;
    self.status = 0;
    self.responseText = '';
    if (self.onerror) self.onerror(err);
    if (self.onreadystatechange) self.onreadystatechange();
  });

  if (this._body) req.write(this._body);
  req.end();
}, "send");

XMLHttpRequest.prototype.getResponseHeader = markNative(function getResponseHeader(name) {
  return null;
}, "getResponseHeader");

XMLHttpRequest.prototype.getAllResponseHeaders = markNative(function getAllResponseHeaders() {
  return "";
}, "getAllResponseHeaders");

XMLHttpRequest.prototype.abort = markNative(function abort() {}, "abort");

global.XMLHttpRequest = XMLHttpRequest;

// getComputedStyle (P2)
global.getComputedStyle = markNative(function getComputedStyle() {
  return {
    getPropertyValue: markNative(function getPropertyValue() { return ""; }, "getPropertyValue"),
  };
}, "getComputedStyle");

// chrome 对象 (P2 - 检测点 L8714)
global.chrome = {
  runtime: {},
  loadTimes: markNative(function loadTimes() {}, "loadTimes"),
  csi: markNative(function csi() {}, "csi"),
  app: {},
};

// ============================================================
// 第 6 层: Location / History / Screen (P1)
// ============================================================
global.location = {
  href: "https://www.jd.com/",
  host: "www.jd.com",
  hostname: "www.jd.com",
  origin: "https://www.jd.com",
  pathname: "/",
  protocol: "https:",
  port: "",
  search: "",
  hash: "",
  assign: markNative(function assign() {}, "assign"),
  replace: markNative(function replace() {}, "replace"),
  reload: markNative(function reload() {}, "reload"),
  toString: markNative(function toString() { return this.href; }, "toString"),
};

global.history = {
  length: 1,
  state: null,
  back: markNative(function back() {}, "back"),
  forward: markNative(function forward() {}, "forward"),
  go: markNative(function go() {}, "go"),
  pushState: markNative(function pushState() {}, "pushState"),
  replaceState: markNative(function replaceState() {}, "replaceState"),
};

global.screen = {
  width: 1920,
  height: 1080,
  availWidth: 1920,
  availHeight: 1040,
  colorDepth: 24,
  pixelDepth: 24,
  availLeft: 0,
  availTop: 0,
};

// ============================================================
// 第 7 层: 微应用环境标志 (P2 - L5614 检测)
// 这些必须为 undefined/false，代码才会继续执行
// ============================================================
// window.__MICRO_APP_ENVIRONMENT_TEMPORARY__ → undefined (不设置)
// window.__MICRO_APP_ENVIRONMENT__ → undefined
// window.rawWindow → undefined
// window.__MICRO_APP_PROXY_WINDOW__ → undefined
// window.__MICRO_APP_BASE_APPLICATION__ → undefined
// 这些都不设置，保持 undefined

// ============================================================
// 第 8 层: Error.stack 保护
// ============================================================
// 重写 Error 构造函数的 stack getter，隐藏 Node 路径
const _origErrorCapture = Error.captureStackTrace;
const _origPrepareStackTrace = Error.prepareStackTrace;
Error.prepareStackTrace = function(error, structuredStackTrace) {
  return structuredStackTrace
    .filter(function(frame) {
      const fn = frame.getFileName() || "";
      return !fn.includes("env-patch.js") && !fn.includes("node:");
    })
    .map(function(frame) {
      return "    at " + (frame.getFunctionName() || "<anonymous>") + " (" + (frame.getFileName() || "https://www.jd.com/a.js") + ":" + frame.getLineNumber() + ":" + frame.getColumnNumber() + ")";
    })
    .join("\n");
};

// ============================================================
// 第 9 层: 辅助工具 (对应 skill 的 Proxy 吐环境)
// 可选: 取消注释以下代码开启 Proxy 诊断
// ============================================================
/*
global.__enableObserver = function() {
  const observer = require("./web-reverse-env/scripts/observe-runtime.js");
  const obs = observer.createRuntimeObserver({ maxDepth: 3, logOpen: true });
  global.window = obs.wrap(global.window, "window");
  global.navigator = obs.wrap(global.navigator, "navigator");
  global.document = obs.wrap(global.document, "document");
  console.log("[env-patch] Proxy observer enabled");
};
*/

// ============================================================
// 完成标记
// ============================================================
console.log("[env-patch] Browser environment initialized for JD H5ST");
