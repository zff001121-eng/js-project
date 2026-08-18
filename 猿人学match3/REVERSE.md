# 猿人学 Match2023 第3题逆向心得

> 题目：守心 - 简单的指令  
> URL：https://match2023.yuanrenxue.cn/topic/3  
> 最终方案：纯 Node.js，无 jsdom，无浏览器依赖

---

## 1. 题目分析

页面加载后会 POST 请求 `/api/question/21`，请求体包含 `token` 参数（64位 hex），目标就是逆向这个 token 的生成逻辑。

### 页面结构

两个关键脚本：
- **match3.js**（87万字符）：JSVMP 保护的核心逻辑，包含魔改 SM3 算法
- **内联 page_script**：约 120 行，负责 XHR 拦截和流程编排

---

## 2. 逆向过程

### 2.1 确定 token 来源

通过浏览器 `search_in_sources` 在 match3.js 中搜索 `token`，发现在 VM 字节码中出现了 `sm3Digest`、`token`、`_time`、`page` 等字符串，初步判断 token 与 SM3 哈希、时间戳、页码有关。

### 2.2 JSVMP 分析困难

match3.js 使用控制流平坦化（control-flow flattening）保护，代码结构类似：

```javascript
(function(e) {
  var i = e || 2;
  for (;;)
    if (i < 2) { ... }
    else if (i < 128) {
      if (i < 64) { ... }
      // 数千行 switch-case 式跳转
    }
})();
```

直接阅读几乎不可能。观察 VM 暴露的全局函数：

```javascript
// 浏览器 console 中输出
SM3       // → function (构造函数)
sm3Digest // → function (哈希函数)
call      // → function (入口函数)
```

### 2.3 尝试 jsdom 补环境

最初尝试用 jsdom 在 Node.js 中运行 match3.js：

```
Error: Cannot read properties of undefined (reading 'prototype')
→ Cannot read properties of undefined (reading 'createElement')
→ Cannot read properties of undefined (reading 'appendChild')
```

每补一个缺失的 API，就出现新错误，陷入无尽循环。**结论：JSVMP 不适合用 jsdom 补环境**，因为 VM 初始化阶段会访问大量浏览器 API。

### 2.4 放弃 jsdom，转向纯算法还原

关键转折点：在浏览器中 hook `sm3Digest`，捕获其输入输出：

```javascript
// 浏览器 console
sm3Digest(Date.now() + "1")
// 输入: "17799770929151"
// 输出: "0e8ca556aa867f237d31a3b40fbf94df930a84eecad5fe4921fb7392ec87dc1a"
```

确认 token 公式为：`sm3Digest(serverTimestamp + pageNumber)`

### 2.5 分析魔改 SM3 参数

通过浏览器调用 VM 的 prototype 方法，逐步对比标准 SM3：

#### strToBytes（字节编码魔改）

| 字符 | charCode | strToBytes | 规律 |
|------|----------|------------|------|
| '0' | 48 | 48 | LSB=0 → 不变 |
| '1' | 49 | 48 | LSB=1 → 清零 |
| 'a' | 97 | 96 | LSB=1 → 清零 |
| 'b' | 98 | 98 | LSB=0 → 不变 |

**结论：`byte = charCode & 0xFE`（清除最低位）**

#### T 常量魔改

```javascript
sm3._t(0)  // → 0x79DD4519（标准 SM3: 0x79CC4519）
sm3._t(16) // → 0x7C179D8A（标准 SM3: 0x7A879D8A）
```

#### IV 初始向量魔改

通过搜索已有方案和反复测试确认 IV 值：

```
标准 SM3: 0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600...
魔改 SM3: 0x7380067c, 0x7634d2c9, 0x170042d6, 0xda887534...
```

#### 额外的比特掩码

魔改版在压缩函数的每轮计算中增加了三处掩码：

```
SS1: & 0xFCFFFFFF  （清除 bit24, bit25）
TT1: & 0xFFFFFFFA  （清除 bit0, bit2）
TT2: & 0xFFAFFFFF  （清除 bit20, bit22）
```

---

## 3. 最终方案

纯 Node.js 实现魔改 SM3 算法（`match3_solve.js`），零外部依赖：

1. `https.get` 获取服务器时间戳
2. `sm3Digest(timestamp + page)` 生成 token  
3. `https.request` POST 到 API 获取数据

运行结果：

```
Page 1 numbers: 669355, 488782, 586179, 940330, 159643, 832370, 970259, 603537, 407100, 997065
```

---

## 4. 经验总结

### 4.1 JSVMP 不要硬刚补环境

match3.js 是典型的 JSVMP（JS 虚拟机保护），整个 SM3 算法和 token 生成流程全部在 VM 字节码中实现。这种保护方式的特点是：

- VM 初始化时会触碰大量浏览器 API（document.createElement、appendChild 等）
- 这些 API 访问是 VM 初始化流程的一部分，无法跳过
- 用 jsdom 补环境会陷入"补一个漏十个"的死循环

**正确做法：分析清算法后，用原生代码重新实现。**

### 4.2 浏览器是逆向的最佳工具

利用 chrome-devtools-mcp 和 js-reverse-mcp 可以高效地：

1. 搜索混淆脚本中的关键字符串
2. 设置断点定位关键逻辑
3. 在 console 中调用 VM 函数，捕获输入输出
4. 对比标准算法，找出魔改点

### 4.3 魔改密码算法的分析思路

1. 确认算法类型（SM3 / SHA256 / MD5 等）
2. 找到输入编码方式（strToBytes 的魔改）
3. 定位 IV 初始向量（与标准对比）
4. 定位常量表（与标准对比）
5. 逐轮对比压缩函数（发现额外的掩码操作）

### 4.4 补环境 vs 纯算法还原的选择

| 场景 | 推荐方案 |
|------|---------|
| 轻度混淆 + 少量环境检测 | 补环境 |
| JSVMP / 重度混淆 | 纯算法还原 |
| 标准算法无魔改 | 直接调原生库 |
| 魔改算法 | 还原算法参数，手动实现 |
