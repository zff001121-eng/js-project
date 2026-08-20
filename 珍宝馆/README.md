# 生成 g2.ltfc.net 的 `cag.tid` Cookie（Python 实现）

## 结论（先说重点）

`cag.tid` 的值 **不是前端本地加密/签名生成的**，而是 Next.js 服务端的
**React Server Action** 动态下发的游客令牌（tourist token）。每次调用都会返回一个
**全新的随机值**，客户端只是把它缓存到 Cookie 里。

用户找到的那段 `async function l() { ... }` 并非"加密函数入口"，而是
**取缓存 → 调服务端 → 写 Cookie** 的封装：

```js
async function l() {
  let e = b();                       // b() 读 cookie「cag.tid」
  return e.token ? e                 // 已有 token 直接返回
    : r || (r = (async () => {
        let e = await (0, o.hP)();   // o.hP() = 调服务端 Server Action
        return (null == e ? void 0 : e.token)
               && await m(e.token, +e.expireAfter),  // m() 写 cookie
        b();
      })().finally(() => { r = void 0; }));
}
```

真正的入口 `o.hP()`：

```js
// 模块 77457
var i = (0, r.$)("510d40750b93bbb35d0a2910b3268b2803a94354");  // hP = i
// 模块 12119 里，$ 是 React 的 createServerReference
function o(t) {
  let { createServerReference: e } = n(6671);
  return e(t, r.callServer);   // t = "510d...94" 即 Server Action ID
}
```

## 请求协议（核心）

生成 `cag.tid` 只需要复刻这一个 POST 请求：

```
POST https://g2.ltfc.net/search?searchType=SUFA&curTab=SUFA
Accept:       text/x-component
Content-Type: text/plain;charset=UTF-8
Next-Action:  510d40750b93bbb35d0a2910b3268b2803a94354   # Server Action ID
Origin:       https://g2.ltfc.net
Referer:      https://g2.ltfc.net/search?searchType=SUFA&curTab=SUFA

Body: []    # 无参数，空 JSON 数组
```

响应为 React Flight(RSC) 文本格式：

```
0:["$@1",["SGU7h02KQj2wghW9aneZN",null]]
1:{"token":"aocJ...==.t","expireAfter":"2592000"}
```

- `token` 就是要写入 `cag.tid` 的值
- `expireAfter` 是过期时长（秒），通常固定为 `2592000`（30 天）

## Cookie 写入规则（对应前端 `m()` 函数）

```
cag.tid        = token
cag.tid.expire = Date.now() + expireAfter * 1000     # 毫秒时间戳
```

## 运行

```bash
pip install -r requirements.txt
python main.py
```

输出示例：

```json
{
  "cag.tid": "aocKWnxszQakzkFKaAfgG/8.9eEaoye4yX3x3v01XQDgNQ==.t",
  "cag.tid.expire": "1789826906094"
}
```

## 验证

已用生成的 token 走通后端完整设备注册链路：

1. `registerDevice`（`POST https://api.quanku.art/cag2.TouristDeviceService/registerDevice`）
   → 200，返回 `tdid`
2. `getDevice`（`POST .../getDevice`）→ 200，返回设备信息

说明该 token 被服务端正常接受，可直接用于后续业务接口（`context.tourToken`）。

## token 结构（仅供参考，无需本地生成）

token 形如 `A.B.t`，共 3 段：

| 段 | 示例 | 长度 | 解码 |
|---|---|---|---|
| A | `aocJCHxszQakzcYxaAfe0kP` | 23 字符 | base64url → 17 字节 |
| B | `F4QJnVYl3fVTvQ35gWAJlA==` | 24 字符 | base64 → 16 字节 |
| C | `t` | 1 字符 | 游客标识 |

该结构由服务端生成、服务端校验，本地无需（也无法）复现内部算法。

## 技术要点

- Next.js App Router + React Server Actions（`createServerReference` / `Next-Action` 头）
- React Flight(RSC) 响应格式解析
- 无客户端加密/签名、无环境指纹检测、无 TLS 指纹强校验（普通 `requests` 即可）
