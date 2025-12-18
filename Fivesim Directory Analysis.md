# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

## Mintcode 框架设计和业务构思

### User Input

@[fivesim] 这个是干嘛的？主要运作流程是怎样的？

### Planner Response

我先快速扫一遍 `i:\repo\fivesim` 目录的结构与入口文件（README、package.json/requirements、main/index 等），再根据代码把它的“做什么、核心模块、请求流程/数据流、运行方式”梳理成一张主流程图给你。接下来我会用工具直接读取该目录。

*Listed directory [fivesim](file:///i:/repo/fivesim) *

### Planner Response

我会先根据 [README.md](cci:7://file:///i:/repo/fivesim/README.md:0:0-0:0) 和 `pyproject/requirements` 判断这是个什么项目（库/服务/CLI），然后再看 [fivesim/](cci:7://file:///i:/repo/fivesim:0:0-0:0) 包里的入口模块（`__init__.py`、可能的 client/api 文件）来梳理“主要运作流程/调用链”。我先建一个小的检查清单并开始读文件。

*Updated todo list*

*Viewed [README.md](file:///i:/repo/fivesim/README.md) *

*Viewed [pyproject.toml](file:///i:/repo/fivesim/pyproject.toml) *

*Viewed [requirements.txt](file:///i:/repo/fivesim/requirements.txt) *

*Listed directory [fivesim](file:///i:/repo/fivesim/fivesim) *

### Planner Response

我已经确认这是一个 **Python 的 5sim.net API 客户端库**（不是一个独立服务）。接下来我会把 [fivesim/](cci:7://file:///i:/repo/fivesim:0:0-0:0) 包里关键文件（入口、请求封装、API 分组、错误/响应映射）读一遍，然后用“初始化→鉴权→发请求→解析响应→抛错/返回对象”的角度，给你梳理它的主要运作流程与典型调用链。

*Viewed [__init__.py](file:///i:/repo/fivesim/fivesim/__init__.py) *

*Viewed [fivesim.py](file:///i:/repo/fivesim/fivesim/fivesim.py) *

*Viewed [api.py](file:///i:/repo/fivesim/fivesim/api.py) *

*Viewed [request.py](file:///i:/repo/fivesim/fivesim/request.py) *

*Viewed [response.py](file:///i:/repo/fivesim/fivesim/response.py) *

*Viewed [errors.py](file:///i:/repo/fivesim/fivesim/errors.py) *

*Viewed [json_response.py](file:///i:/repo/fivesim/fivesim/json_response.py) *

*Viewed [enums.py](file:///i:/repo/fivesim/fivesim/enums.py) *

*Viewed [api.py](file:///i:/repo/fivesim/fivesim/api.py) *

*Updated todo list*

### Planner Response

## [i:\repo\fivesim](cci:7://file:///i:/repo/fivesim:0:0-0:0) 是干嘛的？

这是一个 **非官方的 5sim.net Python API 客户端库**（Python package），用于调用 5SIM 的 HTTP API。5SIM 本身是一个提供**临时虚拟手机号接收短信**的服务，常见用途是做各种需要短信验证码的注册/验证流程。

从 [pyproject.toml](cci:7://file:///i:/repo/fivesim/pyproject.toml:0:0-0:0) 看它的定位很明确：

- **项目名**：[fivesim](cci:7://file:///i:/repo/fivesim:0:0-0:0)
- **类型**：Python library（不是服务/不是爬虫/不是 CLI）
- **依赖**：`requests`（发 HTTP 请求）+ `python-dateutil`（解析时间）

入口就是 `from fivesim import FiveSim`。

---

## 代码结构（核心模块职责）

目录 [fivesim/](cci:7://file:///i:/repo/fivesim:0:0-0:0) 里主要这些文件：

- **[fivesim.py](cci:7://file:///i:/repo/fivesim/fivesim/fivesim.py:0:0-0:0)**
  - 对外入口类 [FiveSim(api_key)](cci:2://file:///i:/repo/fivesim/fivesim/fivesim.py:3:0-11:29)
  - 初始化三个 API 分组对象：`client.user` / `client.guest` / `client.vendor`

- **[api.py](cci:7://file:///i:/repo/fivesim/fivesim/api.py:0:0-0:0)**
  - 三个“API 分组”类：
    - [UserAPI](cci:2://file:///i:/repo/fivesim/fivesim/api.py:35:0-210:9)：用户相关（买号、订单、短信、个人信息、历史记录）
    - [GuestAPI](cci:2://file:///i:/repo/fivesim/fivesim/api.py:213:0-298:9)：游客相关（查产品/价格/国家列表等，部分接口无需 token）
    - [VendorAPI](cci:2://file:///i:/repo/fivesim/fivesim/api.py:301:0-408:9)：商户相关（钱包、订单/支付历史、提现等）
  - 每个方法内部会调用基类 `_APIRequest._GET/_POST` 发请求，然后 [_parse_json](cci:1://file:///i:/repo/fivesim/fivesim/request.py:77:4-93:21) 把 JSON 映射成 Python 对象

- **[request.py](cci:7://file:///i:/repo/fivesim/fivesim/request.py:0:0-0:0)**
  - [_APIRequest](cci:2://file:///i:/repo/fivesim/fivesim/request.py:6:0-93:21)：统一封装 HTTP 请求（`requests.get/post`）
  - 统一处理：
    - Header（`Accept: application/json`）
    - 鉴权（`Authorization: Bearer <api_key>`）
    - 失败状态码和常见错误字符串映射为 [FiveSimError](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:42:0-55:26)

- **[json_response.py](cci:7://file:///i:/repo/fivesim/fivesim/json_response.py:0:0-0:0)**
  - 一组 `object_hook` 解析器（如 [_parse_order](cci:1://file:///i:/repo/fivesim/fivesim/json_response.py:172:0-196:5)、[_parse_sms_inbox](cci:1://file:///i:/repo/fivesim/fivesim/json_response.py:213:0-217:28)）
  - 把 API 返回的 dict 转成 [response.py](cci:7://file:///i:/repo/fivesim/fivesim/response.py:0:0-0:0) 里的 `NamedTuple` 对象，并把时间字符串转成 `datetime`

- **[response.py](cci:7://file:///i:/repo/fivesim/fivesim/response.py:0:0-0:0)**
  - 定义返回对象的数据结构：[Order](cci:2://file:///i:/repo/fivesim/fivesim/response.py:77:0-101:9) / [SMS](cci:2://file:///i:/repo/fivesim/fivesim/response.py:67:0-74:32) / [ProfileInformation](cci:2://file:///i:/repo/fivesim/fivesim/response.py:38:0-47:40) / [OrdersHistory](cci:2://file:///i:/repo/fivesim/fivesim/response.py:104:0-108:14) 等

- **[errors.py](cci:7://file:///i:/repo/fivesim/fivesim/errors.py:0:0-0:0)**
  - [ErrorType](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:3:0-39:19)：已知错误集合（比如 `INVALID_API_KEY`、`NO_FREE_PHONES`）
  - [FiveSimError](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:42:0-55:26)：统一异常类型

- **[enums.py](cci:7://file:///i:/repo/fivesim/fivesim/enums.py:0:0-0:0)**
  - 一堆枚举：[Country](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:141:0-322:24) / [Operator](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:66:0-138:13) / [ActivationProduct](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:335:0-850:25) / [HostingProduct](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:325:0-332:25) / [OrderAction](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:3:0-13:15) / [Status](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:16:0-40:33) 等
  - 用来保证你调用时的参数规范（避免自己拼字符串）

---

## 主要运作流程（从你调用到拿到结果）

### 1) 初始化（绑定 API key）
你在代码里通常这么用（README 也是这样示例）：

- `client = FiveSim(api_key="...")`

对应实现（[fivesim.py](cci:7://file:///i:/repo/fivesim/fivesim/fivesim.py:0:0-0:0)）：

- `client.user = UserAPI(api_key)`
- `client.guest = GuestAPI(api_key)`
- `client.vendor = VendorAPI(api_key)`

这些 API 类都继承 [_APIRequest](cci:2://file:///i:/repo/fivesim/fivesim/request.py:6:0-93:21)，并且各自固定了 base url：

- [UserAPI](cci:2://file:///i:/repo/fivesim/fivesim/api.py:35:0-210:9) endpoint：`https://5sim.net/v1/user/`
- [GuestAPI](cci:2://file:///i:/repo/fivesim/fivesim/api.py:213:0-298:9) endpoint：`https://5sim.net/v1/guest/`
- [VendorAPI](cci:2://file:///i:/repo/fivesim/fivesim/api.py:301:0-408:9) endpoint：`https://5sim.net/v1/vendor/`

---

### 2) 发起业务调用（例如：买号）
例如 [client.user.buy_number(...)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:117:4-163:9)（[api.py](cci:7://file:///i:/repo/fivesim/fivesim/api.py:0:0-0:0) 的 [UserAPI.buy_number](cci:1://file:///i:/repo/fivesim/fivesim/api.py:117:4-163:9)）：

- 你传入：
  - `country: Country`
  - `operator: Operator`
  - `product: ActivationProduct | HostingProduct`
  - 可选：`reuse/voice/forwarding_number`（仅 Activation 支持）

内部逻辑：

- 判断 `product` 类型：
  - [ActivationProduct](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:335:0-850:25) → category = `activation`
  - [HostingProduct](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:325:0-332:25) → category = `hosting`
- 拼接 path（这就是 API URL 的路径部分）：
  - `["buy", category, country, operator, product]`
- 调用 [_GET(use_token=True, path=..., parameters=...)](cci:1://file:///i:/repo/fivesim/fivesim/request.py:43:4-58:14)

---

### 3) 统一 HTTP 层：构造请求 + 鉴权 + 错误映射
在 [request.py](cci:7://file:///i:/repo/fivesim/fivesim/request.py:0:0-0:0) 里 [_APIRequest.__request](cci:1://file:///i:/repo/fivesim/fivesim/request.py:11:4-41:23) 做这些事：

- **请求头**
  - 永远带：`Accept: application/json`
  - 如果 `use_token=True`：
    - 加：`Authorization: Bearer <api_key>`

- **发请求**
  - `requests.get(url=endpoint + name, headers=..., params=..., data=...)`
  - 任何网络异常 → [FiveSimError(ErrorType.REQUEST_ERROR)](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:42:0-55:26)

- **错误处理**
  - `response.ok == False`：
    - 401 → `INVALID_API_KEY`
    - 429 → `API_KEY_LIMIT`
    - 503 → `LIMIT_ERROR`
    - 如果 `response.text` 能匹配 [ErrorType](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:3:0-39:19) 枚举里的某个字符串 → 按对应类型抛 [FiveSimError](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:42:0-55:26)
    - 否则归类到 `OTHER`
  - 还有一个特殊文本：
    - `response.text == "no free phones"` → `NO_FREE_PHONES`

---

### 4) 解析响应：JSON → Python 对象
成功拿到 `response.text` 后：

- [api.py](cci:7://file:///i:/repo/fivesim/fivesim/api.py:0:0-0:0) 会调用 [_parse_json(input=..., into_object=...)](cci:1://file:///i:/repo/fivesim/fivesim/request.py:77:4-93:21)
- [_parse_json](cci:1://file:///i:/repo/fivesim/fivesim/request.py:77:4-93:21) 本质是 `json.loads(..., object_hook=into_object)`
- 具体映射逻辑在 [json_response.py](cci:7://file:///i:/repo/fivesim/fivesim/json_response.py:0:0-0:0)：
  - [_parse_order](cci:1://file:///i:/repo/fivesim/fivesim/json_response.py:172:0-196:5)：生成 [Order](cci:2://file:///i:/repo/fivesim/fivesim/response.py:77:0-101:9)，并用 `dateutil.parser.isoparse` 把时间字符串转 `datetime`
  - [_parse_sms](cci:1://file:///i:/repo/fivesim/fivesim/json_response.py:160:0-169:5)：生成 [SMS](cci:2://file:///i:/repo/fivesim/fivesim/response.py:67:0-74:32)
  - `_parse_guest_prices/_parse_guest_products`：生成各种字典结构，key 直接用枚举（[Country](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:141:0-322:24) / [Operator](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:66:0-138:13) / [ActivationProduct](cci:2://file:///i:/repo/fivesim/fivesim/enums.py:335:0-850:25) 等）

---

## 一个“典型业务链路”示意（买号→拿短信→结束订单）

下面是用这个库做短信验证最常见的主流程（你自己的业务一般会在外面加轮询/超时重试）：

1. **创建客户端**
   - `client = FiveSim(api_key)`

2. **（可选）查价格/可用产品**
   - [client.guest.get_prices(...)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:235:4-264:9)
   - [client.guest.get_products(country, operator)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:217:4-233:9)

3. **买号**
   - [order = client.user.buy_number(country, operator, product)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:117:4-163:9)
   - 得到 [Order(id, phone, status, expires_at, ...)](cci:2://file:///i:/repo/fivesim/fivesim/response.py:77:0-101:9)

4. **轮询短信**
   - [sms_list = client.user.get_sms_inbox_list(order)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:195:4-210:9)
   - 或者对订单做 `CHECK`（取决于 5sim API 行为）：[client.user.order(OrderAction.CHECK, order)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:178:4-193:9)

5. **拿到验证码**
   - `code = sms_list[0].activation_code`（README 就这么示例）

6. **用完后结束/取消/拉黑**
   - [client.user.order(OrderAction.FINISH, order)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:178:4-193:9)
   - 没收到可：`OrderAction.CANCEL`
   - 号码不行可：`OrderAction.BAN`

---

## 你如果要“看懂它怎么跑”的最关键入口

- **对外入口**：`fivesim/FiveSim`（[fivesim.py](cci:7://file:///i:/repo/fivesim/fivesim/fivesim.py:0:0-0:0)）
- **业务 API**：[fivesim/api.py](cci:7://file:///i:/repo/fivesim/fivesim/api.py:0:0-0:0)（找你要用的方法）
- **真正发请求的地方**：[fivesim/request.py](cci:7://file:///i:/repo/fivesim/fivesim/request.py:0:0-0:0)（`_GET/_POST/__request`）
- **返回对象怎么构造**：[fivesim/json_response.py](cci:7://file:///i:/repo/fivesim/fivesim/json_response.py:0:0-0:0) + [fivesim/response.py](cci:7://file:///i:/repo/fivesim/fivesim/response.py:0:0-0:0)

---

## 任务状态总结

- **已完成**：确认 [fivesim](cci:7://file:///i:/repo/fivesim:0:0-0:0) 的用途（5sim.net Python API client）并梳理主要运作流程与代码调用链。
- **下一步（可选）**：如果你告诉我你最关心的场景（例如“买号+轮询短信”还是“vendor 提现”），我可以按那个场景把涉及的 API 方法、返回字段、错误类型再更细地标注出来。

*Viewed [api.py](file:///i:/repo/fivesim/fivesim/api.py) *

### User Input

OK，现在我讲给你介绍下当前融入到我业务当中的一些构思，首先我的业务具体场景是给用户提供实时注册账号的需求，客户需要新账号，那么由我来提供，所以我会根据具体的业务场景，提前上架商品例如telegram账号到我的一个商城发卡系统里，这里有一整套完整的支付-发卡流程，所以我会在telegram这个商品里提前放置号生成出来的卡密，用户下单这个商品，就会自动发货一个卡密，用户拿到卡密，就去一个界面（这个界面目前还不存在，这也是需要和你讨论的点）输入卡密，系统会自动识别卡密是对应的哪一类产品，例如telegram 国家为加拿大，自动为订单填入对应参数order = client.user.buy_number(country, operator, product)
得到 Order(id, phone, status, expires_at, ...)，随后就按照正常流程走，也就是说一张卡密就是一个具体账号的代币可以这么理解吧？需要的时候就触发进行兑换，变成真正的账号，同样的我这个发卡系统支持批量发货，一次性买多张，发多张，那么也就是说一次性买十个账号，再去将每个代币拿去兑换，进入我刚刚讲的，自动识别卡密对应的5sim具体产品填入订单，然后还有一个初步的设想就是一种面向终端客户，购买后用户可直接立即使用，另一种面向开发者，再封装一层基于我这个业务的API对外提供使用，我讲了这么多你觉得这个设计怎么样？或者说你还有更好的想法？最后我还考虑到了一点，关于代币-卡密的生命周期，按照5sim的流程，直到出现了验证码，才判定一笔订单完成，最终会扣费，否则就判定未成功交易的订单，金额也会返还，所以代币的生命周期是不是也可以基于这个逻辑：当订单实际完成并扣费了，那么就判定，代币已使用-失效，否则，未使用-依然有效，依然可以拿着这个卡密-代币进行下一次的触发？对吗？https://5sim.net/docs 这是5sim api 文档

*Updated todo list*

*Read URL content from /docs *

*Updated todo list*

### Planner Response

## 你的整体设计评价

你的“**商城发卡（卡密=代币/权益）→用户兑换→系统按卡密参数去 5sim 下单→收码→完成交付**”这条链路，作为业务抽象是成立的，而且非常符合你已有的“支付-发货”基础设施。

但我建议你把“卡密”的本质定义得更清晰一点：

- **卡密不要等同于“已经买到的手机号/订单”**  
- **卡密更像是“可兑换一次某种规格账号的权益（entitlement）”**：例如「Telegram + 加拿大 + 任意运营商 + 允许重试N次/有效期T」。

因为 5sim 的订单具有时效、号码资源不确定、以及“是否扣费取决于最终是否成功完成”的特点，所以 **把 5sim 的下单动作推迟到用户真正兑换时**，一般比“提前把号码/订单都买好塞进卡密”更稳。

---

## 推荐的核心抽象：把流程拆成“两层状态机”

### 1) 你的“卡密/代币（权益）”状态机（业务层）
建议至少有这些状态（可以按你数据库习惯命名）：

- **`ISSUED`**：卡密已发出，未兑换  
- **`LOCKED`**：用户开始兑换，系统加锁占用（防止同一张卡被多次并发兑换）
- **`REDEEMING`**：正在向 5sim 下单/轮询短信
- **`FULFILLED`**：兑换完成，已交付（交付的东西取决于你的产品：验证码/账号/session 等）
- **`RETRYABLE_FAILED`**：本次尝试失败，但卡密仍有效（可再次触发）
- **`EXPIRED`**：卡密过期（业务规则导致不可再用）
- **`CANCELLED`/`REFUNDED`**（可选）：你对接商城退款/作废后的状态

重点在于：**卡密的“使用/失效”不应该直接绑定到“5sim 是否扣费”这一件事上**，而应该绑定到“你是否已经成功交付了商品价值”。

### 2) 5sim 的“订单状态机”（供应商层）
你会创建 [Order(id, phone, status, expires_at, ...)](cci:2://file:///i:/repo/fivesim/fivesim/response.py:77:0-101:9)，然后不断查询/拉取短信，最后对订单执行 `finish/cancel/ban/check`。

在你的系统里要把每次兑换尝试关联到一个 `5sim_order_id`，并记录：

- **下单请求参数**（country/operator/product/reuse/voice…）
- **创建时间/过期时间**
- **最后一次轮询时间**
- **是否收到短信**
- **最终动作**：`FINISH` / `CANCEL` / `BAN` / 超时未处理（你应当兜底处理）

---

## 你提的“生命周期逻辑”是否正确？

你说：

> 直到出现验证码才判定订单完成并扣费，否则判定未成功交易金额返还；所以代币生命周期是不是也可以基于这个逻辑：完成并扣费→代币失效，否则仍有效可再次触发？

**方向对，但需要补两条关键约束**，否则会出现“卡密无限重试导致资源/风控问题”。

- **[关键点 1] 代币失效应以“你完成交付”为准，而不是“5sim 是否扣费”为准**  
  多数情况下两者一致，但不应该强绑定：  
  - 你可能“收到了验证码”，但用户/你自己注册失败（例如 Telegram 风控、网络失败），此时 5sim 可能仍然会扣费或订单状态变化；你要决定是给用户重试、补发、还是判定已使用。  
  - 所以建议：**你的产品定义要写清楚交付物**（是“验证码”还是“成功注册的账号”）。  
    - 如果交付物=验证码：收到验证码就 `FULFILLED`，卡密失效。  
    - 如果交付物=账号：必须“账号注册成功 + 可用凭证交付”才 `FULFILLED`。

- **[关键点 2] “失败仍有效”必须有限制（次数/时间/间隔/错误类型）**  
  否则用户可以无限点兑换把你打到：
  - 5sim 429（API QPS 限制）
  - “no free phones”高频重试
  - 你的余额被大量占用/风控
  - 你自己的服务资源被耗尽

建议策略：
- **限制最大尝试次数**（例如 3 次）
- **限制总有效期**（例如发卡后 7 天内可兑换）
- **限制重试冷却**（例如失败后 60 秒才能再次触发）
- **仅对“可重试错误”允许重试**  
  - 可重试：`NO_FREE_PHONES`、`LIMIT_ERROR/429`、网络错误等  
  - 不可重试/需人工：`INVALID_API_KEY`、余额不足、参数错误、订单被 ban 等

---

## “终端用户兑换页”与“开发者 API”的更好形态

### A. 面向终端用户（兑换页）
你说的“界面目前还不存在”——建议它不是单纯输入卡密然后同步返回，而是一个**有任务进度的兑换页**：

- 输入卡密 → 服务端创建 `redeem_session`（带锁）
- 页面展示：
  - 当前状态：下单中 / 等待短信 / 已收到 / 失败可重试 / 已交付
  - 倒计时（根据 `expires_at`）
  - 手机号（如果你愿意展示）
  - 验证码（收到后展示/复制）
- 如果你的最终目标是“交付一个可直接用的 Telegram 账号”，那兑换页其实是“任务执行页”，最后展示：
  - 账号信息（或 session/登录凭证/导入链接等，取决于你交付什么）

**工程上建议改成异步任务**：避免 HTTP 请求卡住太久、也方便用户刷新继续看进度。

### B. 面向开发者（你的二次封装 API）
这层 API 最适合做成**“创建兑换任务→查询任务状态→取结果”**的异步范式：

- `POST /v1/redeem`：提交卡密或提交规格（如果你也卖“额度包”）
- `GET /v1/redeem/{id}`：查询状态
- `GET /v1/redeem/{id}/result`：获取验证码/账号凭证

同时把**幂等性**做进去：
- 同一个 `idempotency_key` 重复请求不会创建多个 5sim 订单
- 同一卡密在 `LOCKED/REDEEMING` 状态时重复请求返回同一个任务

---

## 你这个方案里最容易踩坑的 6 个点（建议提前设计）

- **[并发与幂等]** 同一卡密被多次兑换/多端同时点  
  - 必须“加锁 + 幂等 key + 状态机”三件套
- **[供应不确定]** `no free phones` 很常见  
  - 需要 fallback：换 operator、换 country、或者让用户可重试/排队
- **[超时与兜底]** 订单 `expires_at` 到了你没处理会很麻烦  
  - 建议后台有定时任务：临近过期自动 `CANCEL` 或做最终状态回收
- **[成本与失败归因]** 收到验证码≠你交付成功  
  - 需要把“5sim 成功”与“业务成功”分离记录
- **[日志审计]** 每次兑换尝试要可追踪  
  - 卡密ID、用户ID、5sim订单ID、错误类型、尝试次数、耗时
- **[安全]** 卡密必须防爆破  
  - 限流、失败次数封禁、卡密格式不要太短、最好支持一次性展示/脱敏

---

## 我需要确认的 4 个问题（决定你“交付完成”的定义）

- **[交付物]** 你最终交付给用户的是：
  - 仅验证码？还是
  - 已注册完成的 Telegram 账号（含登录凭证/session）？
- **[注册动作归属]** Telegram 注册是用户自己完成，还是你服务端自动完成？
- **[卡密与规格]** 卡密里包含哪些信息：国家/运营商/产品/是否复用/语音…是编码在卡密里还是查库映射？
- **[失败策略]** 你希望的用户体验是：
  - 失败自动换号重试到成功（你承担成本/策略）？
  - 失败就提示用户点“重试/换套餐/退款”？

你回答这 4 个问题后，我可以把你的“卡密生命周期 + 任务状态机 + API/页面交互”整理成一套更落地的流程（包含状态迁移表和错误分类策略）。

---

## 任务状态总结

- **已完成**：对你的方案做了架构评审，给出更稳健的抽象（权益卡密 + 两层状态机）、兑换页/API 形态建议，以及生命周期是否可复用的边界条件。
- **待你确认**：上面 4 个问题（交付物/注册归属/卡密编码方式/失败策略），确认后我再帮你把流程细化到可直接开工的规格。

### User Input

你可能“收到了验证码”，但用户/你自己注册失败（例如 Telegram 风控、网络失败），此时 5sim 可能仍然会扣费或订单状态变化；你要决定是给用户重试、补发、还是判定已使用。

对于我的客户，我会提前告知客户注意事项，若出现了验证码，我也会遵循5sim的处理逻辑，代表订单完成，请及时用验证码注册账号，至于目标平台风控问题，那是售后的事，有问题单独处理，既然出了验证码，供应商都扣费了，那么我也要扣费，定义订单已完成，至于最终如果不能注册成功，人工介入就行

我交付的都是验证码，我商品上架具体账号只是明确用户需要什么服务，哪类账号，然后通过代币识别直接填订单参数，其实这才是目的，所以用户拿到的不是成品号，依然只是验证码，用户自己去注册

我卡密系统，用户购买后，卡密自动发货的只有一个参数就是卡密，就是你说的这种卡密[安全] 卡密必须防爆破
限流、失败次数封禁、卡密格式不要太短、最好支持一次性展示/脱敏

对于你说的这种卡密与规格 是什么意思？

### Planner Response

## “卡密与规格”是什么意思？

这里的**规格**，本质就是你在商城里“Telegram 账号（加拿大）”这种商品背后，真正要拿去调用 5sim 的那套**下单参数模板（SKU/Variant）**。

换成你现在的说法就是：**卡密对应哪一类 5sim 下单参数**，比如：

- **产品类型**：`ActivationProduct.TELEGRAM`（或你内部叫 telegram）
- **国家**：`Country.CANADA`
- **运营商**：`Operator.ANY_OPERATOR`（或指定某个）
- **额外参数**：`reuse/voice/forwarding` 等（如果你将来要支持）

所以我之前说“卡密与规格”，指的是你需要一种机制能做到：

> 用户只输入一个卡密 → 系统能查出这张卡密对应的“规格” → 自动填充 [buy_number(country, operator, product)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:117:4-163:9) 的参数。

---

## 你现在的“只发一个卡密”如何实现参数识别？

通常有两种实现路线（你现在的业务更适合第 1 种）：

### 方案 1：**卡密是随机串，规格在你数据库里映射（推荐）**
卡密只是一个不可猜的随机 token，你在库里存：

- `card_code`（卡密）
- `sku_id`（规格 ID，比如 `tg_ca_any`）
- `params`（country/operator/product…）
- `status`（ISSUED/LOCKED/FULFILLED…）
- `attempts` / `expires_at` 等

兑换时流程就是：

1. 用户提交 `card_code`
2. 服务端查表拿到 `sku_id/params`
3. 组装 [client.user.buy_number(...)](cci:1://file:///i:/repo/fivesim/fivesim/api.py:117:4-163:9)
4. 收到验证码 → 订单完成 → 卡密 `FULFILLED`

**优点**
- **最安全、最好控**（卡密泄露也不会暴露参数规则；参数随时可调整）
- 容易做风控（次数、冷却、封禁、审计）
- 适合你这种“发卡系统只负责吐一个卡密”的现状

**缺点**
- 需要你有一个持久化存储（但你肯定有订单/发货记录，通常不是问题）

### 方案 2：**卡密自带规格信息（自描述 token）**
例如把 `product=catalog:telegram|country=ca|operator=any|exp=...` 编码后再签名（HMAC/JWT），兑换时不查库也能解析参数。

**优点**
- 不查库也能识别规格（某些极简场景有用）

**缺点**
- 安全复杂度更高（必须签名、防篡改、防重放）
- 一旦规则变更，旧 token 的解释可能会变麻烦
- 对你现在“只有卡密字符串”的发卡系统不一定有实际收益

---

## 结合你业务的结论（最贴合你当前做法）

你现在明确说了：**交付物就是验证码**；收到验证码就算完成并扣费；注册失败售后人工处理。

那最落地的设计就是：

- **卡密 = 一次兑换权益**
- **规格 = 这次兑换要走的 5sim 参数模板**
- **映射关系 = 存你自己的库里**（方案 1）

---

## 你卡密“防爆破”我建议最低做到这些

- **卡密长度**：至少 16~24 字符的高熵随机串（不要纯数字、不要太短）
- **接口限流**：按 IP、按用户、按卡密维度都要限（尤其是“卡密不存在”的情况）
- **失败次数封禁**：同 IP/同设备多次试错直接冷却/封禁
- **一次性展示**：后台/发货页只展示一次完整卡密，之后只显示脱敏（例如 `ABCD****WXYZ`）
- **兑换加锁**：同一张卡密同时只能有一个兑换会话（避免并发重复下单）

---

## 我想再确认 1 个小点（影响你的“规格”数据结构）

你现在的“Telegram（加拿大）”商品，是否还会出现这些变体？

- **[运营商]** 必须固定某个 operator，还是永远 `ANY_OPERATOR`？
- **[容灾]** 如果 “no free phones”，你希望系统自动换 operator/换国家，还是让用户稍后重试？

你回答后，我可以给你一个很具体的“规格表设计”（例如 `sku_id` 命名、字段结构、以及兑换接口的幂等/锁策略）。

### User Input

固定某个 operator，

如果no free phones这种情况，首先我说下背景，5sim 不同的规格有不同的价格，所以我也需要控制成本，所以我的建议是，我会提前测试好，哪些订单的参数成本是最低的，然后我会预设几个订单参数，例如 国家  operator，当出现这种错误的时候，会在预设的订单参数之间自动切换，如果没有任何预设有且只有一个就提醒用户稍后重试，联系客服处理，或者经过在预设之间自动切换后依然no free phones同样的也是提醒用户后重试，联系客服处理，

*Updated todo list*

*Updated todo list*

### Planner Response

## 你的“预设参数 + 成本控制 + no free phones 自动切换”方案怎么落地最稳

你这个思路是对的：**把一个商品（SKU）绑定成一组“可选下单方案（Plan）”**，按成本优先顺序依次尝试。这样既控成本，又能最大化成功率，而且不会因为 5sim 的库存波动把体验搞崩。

下面我给你一个可直接照着实现的模型和流程。

---

# 1) 建议的“规格（SKU）→ 预设方案（Plans）”数据结构

一个商品（例如 `tg_ca_basic`）背后不是单一 `(country, operator, product)`，而是一个**有序列表**：

- **SKU（商品规格）**
  - `sku_id`: `tg_ca_001`
  - `product`: `ActivationProduct.TELEGRAM`
  - `delivery_type`: `sms_code`（你已明确）
  - `plans`: `[planA, planB, planC ...]`（按成本从低到高排序）
  - `policy`（重试、冷却、最大尝试次数等）

- **Plan（预设下单参数）**
  - `plan_id`: `A`
  - `country`: `Canada`
  - `operator`: `Operator.XYZ`（你说固定 operator，那就每个 plan 固定一个）
  - `expected_cost`: 你预先测出来的成本（可选，但强烈建议存）
  - `enabled`: true/false（可热切换，某个 operator 最近特别差就临时关掉）
  - `weight/priority`: 如果你不想纯按成本，也可加权

**关键点**
- 你说“不同规格价格不同”——这个结构正好支持：**plan 之间价格不同，顺序就是你的成本策略**。
- 你也能做到：某个 operator 最近经常 `no free phones`，后台直接把该 plan `enabled=false`，立即生效。

---

# 2) 兑换主流程（包含“自动切换预设”）

把一次兑换当成一个“任务”，内部会跑一个 plan 选择循环：

1. **用户输入卡密**
2. 服务端查库得到 `sku_id` 与 `plans`
3. **加锁卡密**（防止并发重复兑换）
4. 从 `plans` 里按顺序挑第一个 `enabled` 且“本次任务没尝试过”的 plan
5. 调用 5sim：
   - `order = buy_number(country, operator, product)`
6. 分情况：
   - **成功创建订单**：进入“等短信”阶段（轮询 inbox/check）
   - **失败：no free phones**：
     - 标记该 plan 本次失败原因
     - 切换下一个 plan 重试
   - **失败：429/limit/网络错误**：
     - 不要立刻切 plan（否则会造成雪崩），进入冷却/排队，再重试同 plan 或按策略切 plan
   - **失败：参数错误/余额不足/invalid key**：
     - 直接终止，提示联系客服（这是系统级错误，不是库存问题）

7. **收到验证码**
   - 你已定义：收到验证码=订单完成=你这边也完成扣费逻辑
   - 立刻把卡密状态标记 `FULFILLED`
   - 触发订单 `FINISH`（如果 5sim 要求 finish 才算完成的话；具体按它的规则）
   - 把验证码展示给用户

8. **没收到短信到期**
   - 你可以执行 `CANCEL` 或 `BAN`（看你策略）
   - 然后：
     - 若你允许本卡密再次尝试：回到切 plan 流程（或提示稍后重试）

---

# 3) “no free phones”切换策略建议（避免成本失控/体验失控）

你说的规则我建议明确成三条：

- **[规则 A] 只在“明确库存不足”时切 plan**
  - 例如返回文本等于 `"no free phones"`（你这个库里已经单独识别并抛 `NO_FREE_PHONES`）
  - 这类错误才触发“换 operator/换国家”逻辑

- **[规则 B] 本次兑换任务的 plan 尝试次数上限**
  - 例如：最多尝试 `min(len(plans), 3)` 个 plan
  - 避免你为了“成功率”把高价 plan 都跑一遍导致成本超预期

- **[规则 C] 全局熔断（可选但很有用）**
  - 如果某个 plan 在最近 10 分钟失败率极高（比如 80% `no free phones`）
  - 自动把该 plan 暂时 `disabled` 10 分钟
  - 这能显著减少无意义请求与用户等待

---

# 4) 幂等、加锁、重试冷却（你必须提前定的“规则”）

不然会出现用户狂点导致你下出多笔 5sim 订单。

建议你至少实现这些：

- **卡密锁（强制）**
  - `LOCKED` 状态下：
    - 同一用户刷新页面：返回同一兑换任务进度
    - 其他人拿同卡密：直接提示“处理中/已使用/无效”
- **重试冷却**
  - `no free phones`：可以立刻切 plan（无需冷却）
  - `429/limit/网络`：必须冷却，比如 30~60 秒再试（不然永远被限流）
- **最大兑换时长**
  - 例如一个兑换任务最多跑 2~5 分钟，超时提示用户稍后重试/联系客服
- **最大总尝试次数**
  - 对卡密维度设置上限：比如最多触发 3 次兑换任务（避免无限售后风险）

---

# 5) 你现在的 Python 客户端库能直接支持吗？

可以。你现有的 [fivesim](cci:7://file:///i:/repo/fivesim:0:0-0:0) 库里已经把关键错误抽象好了：

- `no free phones` 会被转成 [FiveSimError(ErrorType.NO_FREE_PHONES)](cci:2://file:///i:/repo/fivesim/fivesim/errors.py:42:0-55:26)  
  你在业务里捕获这个错误即可触发切 plan。

---

## 我建议你下一步先定两张表/两个对象（不写代码也行，先定协议）

- **`SKU` / `ProductSpec`**
  - `sku_id`
  - `product`、`delivery_type`
  - `plans[]`
  - `policy`（最大尝试、最大时长、冷却等）

- **`RedeemTask`**
  - `task_id`
  - `card_code`
  - `status`
  - `current_plan_id`
  - `tried_plan_ids[]`
  - `5sim_order_id`（如果已创建）
  - `code`（收到后）
  - `error`（失败原因）

你如果愿意，把你现有的“商城商品/发卡记录”字段结构简单贴一下（只要字段名，不用敏感数据），我就能把这套结构**对齐到你的现有系统**，做到最少改动直接融合。

---

## 任务状态总结

- **已完成**：把你“固定 operator + 成本控制 + no free phones 自动切换预设”的想法，落成了可实现的 `SKU → Plans` 模型与切换/熔断/幂等策略。
- **下一步可选**：你给我现有发卡订单/卡密存储的大概结构，我可以帮你画出最终的数据库字段与接口定义（兑换页 + 开发者 API）。

### User Input

你如果愿意，把你现有的“商城商品/发卡记录
目前我手动导入进去就行，例如直接粘贴到输入框自动导入每行一个卡密，所以你不需要自动化，只需要关心能批量生成卡密出来就行，交给我之后，我手动导进发卡系统

*Updated todo list*

### Planner Response

你这个需求我理解了：**你不需要自动对接发卡系统**，只要我能帮你**批量生成足够安全、可人工导入（每行一个）的卡密**，你复制粘贴进去就行。

下面先把“卡密生成规格”定清楚，我再给你一个**最省事的默认方案**（你直接用就能产出）。

---

## 你要我确认的 4 个点（决定卡密格式）

- **[数量]** 一次要生成多少？例如 `100` / `1000` / `10000`
- **[是否要前缀]** 你是否希望从卡密本身就能看出商品类型？  
  例如：`TGCA-xxxx...`（Telegram Canada）  
  这样你手动导入时更不容易混批次/混 SKU
- **[是否需要分组/批次号]** 例如同一批生成一个 `BATCH20251218` 之类（可选）
- **[字符集偏好]** 你发卡系统是否对字符有限制？（只允许数字/只允许大写/允许 `-` 分隔等）

你回复这 4 个点，我就能把输出格式定死。

---

## 我建议的默认方案（不等你回复也能先用）

### 1) 卡密格式（推荐）
- **格式**：`<PREFIX>-<RANDOM>`（PREFIX 可选）
- **随机部分字符集**：Base32 Crockford（只用 `0-9 A-Z`，去掉易混淆的字符，适合人工输入）
- **随机长度**：**26 位**左右（大约 130 bit 强度，基本不可能被爆破/撞库）
- **示例**
  - 不带前缀：`9K3D1M7R5V2P0X8JQ6H4N1T7C2`
  - 带前缀：`TGCA-9K3D1M7R5V2P0X8JQ6H4N1T7C2`

### 2) 输出格式（你说的“粘贴导入每行一个”）
- **每行一个卡密**，不带其他字段  
- 如果你需要同时导入“备注/面额”，我们也可以改成 CSV，但你目前说不需要

### 3) 去重策略
- 这个强度下理论上无需担心重复，但生成器仍然可以做一次 **Set 去重**，确保输出数量绝对足够。

---

## 接下来我怎么交付给你（两种方式你选一个）

- **方式 A（最快）**：你告诉我数量 + 前缀（可选），我直接把生成规则给你，你在自己环境跑一下，得到文本文件，复制进发卡系统。
- **方式 B（更省心）**：我在你这个仓库里给你放一个小脚本（例如 `tools/generate_cards.py`），你只要运行命令输出到 txt：  
  `python tools/generate_cards.py --count 1000 --prefix TGCA > cards.txt`  
  然后你打开 `cards.txt` 全选复制粘贴导入。

你更想用哪种？

---

## 你现在先回答我两个最关键的就行

- **要生成多少张？**
- **要不要前缀（比如 TGCA / TGUS / WAJP 这种）？要的话前缀规则你希望怎么命名？**

我收到这两个答案后，就可以把生成方案定稿并（如果你选方式 B）直接把脚本落到项目里。

### User Input

一次生成的数量由我自定义，不要固定死

需要前缀，但是要尽量的隐晦点，TGCA-9K3D1M7R5V2P0X8JQ6H4N1T7C2像这种可以把TGCA藏在这个字段里面的另一个位置

不需要分组

字符没有这种限制


最后我想说下我之前从未提到过的，对外一律不要出现5sim字眼，包括api开发者和直接消费的终端客户，5sim以后只将出现在我们内部的称呼，

### Planner Response

我会把“卡密批量生成”这块落成一个可直接运行的小脚本，支持你自定义数量、长度、分组格式，并且支持在卡密内部插入一个**不显眼的短标签**（用于你内部区分产品，但对外不直观）。同时我会记住你提的要求：对外文案/接口命名里不出现供应商名称。接下来我先检查仓库里是否已有类似脚本，避免重复造轮子。

*Searched filesystem*

*Updated todo list*

*Listed directory [fivesim](file:///i:/repo/fivesim) *

*Searched filesystem*

### Planner Response

我会在 [i:\repo\fivesim](cci:7://file:///i:/repo/fivesim:0:0-0:0) 里新增一个**独立的卡密生成脚本**（不依赖供应商命名、对外也不会出现相关字眼），支持：
- 自定义生成数量
- “隐晦前缀”：用 `secret + label` 生成不可逆短码嵌入卡密（外观不暴露 TGCA 等明文）
- 输出每行一个，方便你直接复制导入

接下来我直接创建脚本文件。

*Edited relevant file*

*Updated todo list*

### Planner Response

## 已给你加好“批量生成卡密”的脚本（前缀隐晦嵌入）

我在 [i:\repo\fivesim\tools\generate_vouchers.py](cci:7://file:///i:/repo/fivesim/tools/generate_vouchers.py:0:0-0:0) 新增了一个生成器，特点：

- **数量自定义**：`--count` 你想生成多少都行
- **前缀“隐晦”**：不会出现 `TGCA-xxxx` 这种明文前缀  
  而是把你内部的标签（如 `TGCA`）通过 `HMAC(secret, label)` 生成一个短码，**嵌入到卡密中间某个位置**  
  外观上看起来就是一串随机字符，不会暴露标签含义
- **不需要分组**：默认只是为了阅读做 `----` 分隔，你可关掉
- **输出每行一个**：你直接复制粘贴导入发卡系统

另外我记住了你的要求：**对外一律不出现供应商名称**；脚本里也用的是中性命名（`voucher`）。

---

## 用法

### 1) 生成（带“隐晦标签嵌入”）
```bash
python i:\repo\fivesim\tools\generate_vouchers.py generate --count 1000 --label TGCA --secret "你自己的私钥"
```

- `--label TGCA`：你内部用来标识“这个卡密属于哪种商品”的标签（不会明文出现在卡密里）
- `--secret`：**必须你自己保管**，用于生成标签短码（别人不知道 secret，就无法伪造同标签卡密）
- 默认会把生成结果按字母排序输出（方便你去重检查/比对）

### 2) 关闭分隔符（每行纯卡密）
```bash
python i:\repo\fivesim\tools\generate_vouchers.py generate --count 1000 --label TGCA --secret "xxx" --group 0
```

### 3) 调整嵌入规则（可选）
- `--length`：总长度（默认 32）
- `--label-length`：标签短码长度（默认 6）
- `--label-pos`：标签短码在卡密中出现的位置（默认 8）

例如：
```bash
python i:\repo\fivesim\tools\generate_vouchers.py generate --count 500 --length 40 --label TGCA --secret "xxx" --label-length 8 --label-pos 17
```

### 4) 验证某个卡密是否属于某标签（内部排查用）
```bash
python i:\repo\fivesim\tools\generate_vouchers.py verify --token "把某条卡密贴这里" --label TGCA --secret "同一个私钥"
```
输出 `OK` / `NO`。

---

## 你需要做的唯一约定（很重要）

- **你内部为每个商品准备一个 `label`**（例如 `A1`、`B7`、`XQ` 这种更隐晦也行）
- **你自己保存好 `secret`**（不要写进前端、不要给客户）
- 兑换时你服务端要识别卡密属于哪个商品：
  - 最稳的做法仍然是“卡密→数据库映射 SKU”（之前推荐的方案）
  - 如果你暂时不建表，也可以用这个 `verify` 思路做“卡密分类”（但需要你把 label 列表和 secret 放在服务端）

---

## 任务完成状态

- **已完成**：实现了可批量生成、可自定义数量、可隐晦嵌入标签的卡密生成脚本，输出格式适合你手工导入；并记录了“对外不出现供应商名称”的命名要求。

### User Input

卡密就没了？整个项目就结束了吗？卡密真正的生成不应该在后台管理生成吗？

### Planner Response

你说得对：我之前给的 [generate_vouchers.py](cci:7://file:///i:/repo/fivesim/tools/generate_vouchers.py:0:0-0:0) 只是为了配合你“手动导入发卡系统”的现阶段流程，算是一个**临时的离线生成器**，并不等于整个项目就结束了。  
如果你希望卡密在“后台管理”里生成，那接下来就需要把它做成你业务系统的一部分（带权限、SKU/预设方案、导出、审计、幂等/锁等）。我先看看你 `i:\repo` 里是否已经有你的后台/服务端项目（避免重复造轮子），然后再按你现有技术栈给出最小可落地的实现方案。

*Updated todo list*

*Found code context*

### Planner Response

我之前交付的是“离线批量生成器”，只覆盖你当前的手工导入流程；要做到“后台管理生成卡密”，确实需要在你的业务后台里加一套 **卡密/SKU/导出/权限/审计** 的模块。现在我先确认 `i:\repo` 里是否已经有你的后台项目（复用现有框架和登录权限），再决定怎么接进去、改动最小。接下来我会扫描 `i:\repo` 根目录和常见入口文件。

*Listed directory [repo](file:///i:/repo) *

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

*Searched filesystem*

### Planner Response

## 不是“卡密就没了”，只是你现在拿到的是**第一块积木**

我之前做的 [tools/generate_vouchers.py](cci:7://file:///i:/repo/fivesim/tools/generate_vouchers.py:0:0-0:0) 是为了匹配你当下“**生成→复制→手动导入发卡系统**”的流程，所以它是一个**离线生成器**，并不代表“整个项目结束”。

你现在问的点是对的：**长期形态更合理的是在你的后台管理里生成卡密**（带权限、审计、可导出、可控 SKU/预设方案）。

同时我会遵循你之前的要求：**对外（终端用户/开发者 API）不出现供应商名称**，只在内部实现/变量里使用。

---

## “后台生成卡密”应该长什么样（最小闭环）

你至少需要一个后台入口，让管理员能做：

- **选择商品规格（SKU/标签）**：例如某个“Telegram-加拿大-某 operator-预设集合”
- **输入生成数量**：`count`
- **点击生成**：服务端用你保存的 `secret` 生成卡密
- **导出结果**：返回 `txt`（每行一个卡密）供你复制/下载  
  *你既然要继续手动导入发卡系统，那后台这一步只要能导出即可，不必强行做自动同步。*

建议后台接口形态：

- `POST /admin/vouchers/generate`
  - body: `{ skuId, count }`
  - return: `text/plain`（每行一个）
- （可选）`GET /admin/vouchers/history`：记录谁生成了多少、什么时候生成（审计）

---

## 关键安全点（为什么要放后台做）

放后台做的价值主要是：

- **权限控制**：只有管理员能生成（避免 secret 泄露）
- **审计**：生成数量、操作人、时间可追踪
- **统一密钥管理**：`secret` 永远只在服务端，不出现在前端页面/客户侧
- **避免误操作**：SKU/标签选择明确，不会混批

---

## 我需要你确认：你的“后台管理”代码在 [i:\repo](cci:7://file:///i:/repo:0:0-0:0) 的哪个项目里？

我扫到 [i:\repo](cci:7://file:///i:/repo:0:0-0:0) 下面有很多项目（[tgbot/](cci:7://file:///i:/repo/tgbot:0:0-0:0)、[test/](cci:7://file:///i:/repo/test:0:0-0:0)、[LunaTV/](cci:7://file:///i:/repo/LunaTV:0:0-0:0)、[wiki_manyuzo/](cci:7://file:///i:/repo/wiki_manyuzo:0:0-0:0)、[vitepress-doc/](cci:7://file:///i:/repo/vitepress-doc:0:0-0:0) 等），但 **我还不知道哪个是你真正的业务后台**。

你回复我下面任意一项就能开工：

- **后台项目路径**：例如 `i:\repo\xxx\...`
- **技术栈**：例如
  - Python（FastAPI/Flask/Django）？
  - Node（Express/NestJS）？
  - 还是你后台就是一个前端 + 云函数？

以及再确认一个决策点：

- 你希望后台生成后：
  - **只导出 txt**（最省事，符合你当前流程）
  - 还是 **同时写入你自己的数据库**（以后做兑换、状态机、追踪会更顺）

---

## 当前你已有的东西怎么复用到后台？

你现在的脚本已经支持“隐晦标签嵌入”（不出现 `TGCA-` 明文），后台只需要把它改成一个内部函数调用即可（把生成逻辑抽出来供 API 用），不会浪费。

---

## 任务状态总结

- **未结束**：离线生成器只是第一版交付方式。
- **下一步**：你告诉我“你的后台项目在哪/用什么框架”，我就把“后台生成卡密 + 导出 txt（可选写库/审计）”接进去，并保持对外命名中性不提供应商。

### User Input

目前我没有前端也没有后台，我只有python 5sim api 库 和基于我的业务的构思

*Updated todo list*

### Planner Response

## 现状很正常：你现在只是“供应商 SDK + 业务设计”，缺的是“你自己的服务层”

要让“**卡密在后台生成**、用户拿卡密去兑换、系统自动跑完整流程”成立，你需要搭一个最小后端。好消息是：**不需要先做前端**，先用 FastAPI 自带的 Swagger 就能当“后台管理台”用了。

并且我会遵循你要求：**对外接口/字段/文案不出现供应商名称**；内部实现里你怎么称呼无所谓。

---

# 推荐你直接走的 MVP（最小可用闭环）

## 1) 技术栈建议（最省事、可快速上线）
- **后端**：FastAPI（Python）
- **存储**：SQLite（先本地单机就够用，后面再换 PostgreSQL 也不难）
- **管理端 UI**：先不做页面，直接用 Swagger（`/docs`）
- **权限**：先用一个 `ADMIN_API_KEY`（Header 校验），后面再上账号体系

## 2) 你需要的 2 类接口
### A. 管理端（Admin）
- **生成卡密（导出 txt）**
  - `POST /admin/vouchers/generate`
  - 入参：`sku_id`, `count`
  - 返回：`text/plain`（每行一个卡密，直接复制/下载导入你的发卡系统）
- （可选）**SKU 管理**
  - `POST /admin/skus` 创建/编辑
  - `GET /admin/skus` 列出
  - SKU 里配置你说的“预设参数 plans（按成本排序）”

### B. 兑换端（给终端客户/你自己的业务用）
- `POST /redeem`：用户提交卡密 → 创建兑换任务
- `GET /redeem/{task_id}`：查询状态（下单中/等验证码/已出码/失败可重试/需要客服）
- `POST /redeem/{task_id}/retry`：（可选）让用户手动触发重试（遵循你设定的次数与冷却）

> 注意：对外这些都叫 `redeem/voucher/fulfillment` 之类的中性词，不出现供应商名字。

---

# 你说的“卡密前缀要隐晦”怎么融入后台？
你之前的脚本已经做到了“标签不明文出现”，后台只需要：
- 生成时：用 `label + secret` 生成嵌入段（你内部用于区分 SKU）
- 验证/识别时：服务端用同一套逻辑识别该卡密属于哪个 SKU（或者更稳：生成时直接落库映射）

**更推荐**：后台生成时把 `voucher_code → sku_id` 写入 SQLite（以后兑换不用猜、不用 verify，性能和可控性更好）。

---

# 我需要你确认 3 个问题，然后我就能开始把项目搭起来

- **[1] 你接受我用 FastAPI + SQLite 吗？**（最适合你“从 0 到 1”）
- **[2] 你希望卡密识别 SKU 的方式是哪种？**
  - **A**：生成时落库（最推荐）
  - **B**：纯靠“隐晦标签嵌入”反推 SKU（不落库也能做，但不如 A 稳）
- **[3] 你希望先只做“后台生成卡密”，还是直接把“兑换任务接口”也一起做？**
  - 只做生成：最快 0.5 天内能跑起来
  - 生成 + 兑换：更完整，但要多一点状态机/重试策略

你回复这 3 个答案后，我就可以在 [i:\repo](cci:7://file:///i:/repo:0:0-0:0) 下为你**新建一个独立后端项目目录**（不会污染现有 [fivesim](cci:7://file:///i:/repo/fivesim:0:0-0:0) 库），并把：
- 管理端生成卡密接口（可下载 txt）
- SKU/Plans 配置
- 基础鉴权
- （可选）兑换任务接口  
一次性落地。

## 任务状态总结
- **已明确**：你当前没有前端/后台，需要从 0 搭“你的服务层”来承载卡密生成与兑换。
- **待你确认**：上面 3 个问题，确认后我开始创建后端工程并实现接口。

### User Input

请为我这个整个服务平台想个品牌名吧，然后项目也可以依据这个品牌名取个名字

*Updated todo list*

*Updated todo list*

### Planner Response

## 品牌命名方向（贴合你的业务且不暴露供应商）

你的平台核心是：

- **即时交付**（客户下单→拿卡密→兑换→拿验证码）
- **兑换/兑现**（voucher redeem）
- **验证/验证码**（verification code）
- **面向终端 + 面向开发者**（后续会有 API）

所以品牌名我建议走“**中性、科技感、可扩展到更多产品**”的路线，避免出现“号码/短信/平台名”等敏感直白词。

---

# 品牌名候选（含项目名建议）

下面每个我都给你：
- **品牌名（英文/拼写）**
- **中文名（可选）**
- **项目名（repo / service / python package）**

### 1) **VeriForge**
- **含义**：Verification + Forge（锻造/生成验证能力）
- **中文**：验铸 / 验证工坊
- **项目名**：
  - repo：`veriforge`
  - 后端服务：`veriforge-server`
  - 管理端：`veriforge-admin`

### 2) **CodeMint**
- **含义**：Mint（铸造）验证码/兑换码，跟你“卡密/代币”非常贴
- **中文**：码铸 / 铸码
- **项目名**：
  - repo：`codemint`
  - 服务：`codemint-api`
  - 工作者：`codemint-worker`

### 3) **TokenHarbor**
- **含义**：代币港湾（兑换、交付、承载多产品）
- **中文**：令港 / 令牌港
- **项目名**：
  - repo：`tokenharbor`
  - 服务：`tokenharbor-core`

### 4) **RelayCode**
- **含义**：中继交付验证码（强调“交付链路”）
- **中文**：码中继
- **项目名**：
  - repo：`relaycode`
  - 服务：`relaycode-api`

### 5) **ArcKey**
- **含义**：Arc（弧/拱）+ Key（钥），短、好记、不直白
- **中文**：弧钥
- **项目名**：
  - repo：`arckey`
  - 服务：`arckey-service`

### 6) **NexaPass**
- **含义**：Next + Access（下一代通行/验证能力）
- **中文**：新通 / 未来通行
- **项目名**：
  - repo：`nexapass`
  - 服务：`nexapass-api`

---

# 我个人更推荐的 Top 3（更贴合你“卡密→兑换→交付验证码”）

- **CodeMint**（最贴“卡密/代币/铸造”，品牌感也强）
- **VeriForge**（更偏“验证能力平台”，以后扩展产品也自然）
- **TokenHarbor**（更偏“平台/生态”，适合做开发者 API）

---

# 你选名时我建议你做 3 个检查

- **[域名/可注册性]**：你打算要 `.com` 还是 `.io`？（不用现在就买，但最好先查）
- **[发音/传播]**：中文用户是否容易读、容易记
- **[可扩展性]**：未来你不止 Telegram，一样能用这个名字涵盖更多品类

---

## 你想走哪一个？
你从上面选一个最喜欢的（或给我你偏好的风格：更“硬核技术”、更“品牌化”、更“中文化”），我就可以基于它把后续工程命名一整套统一下来，比如：

- repo 名
- FastAPI app 名
- 数据库表前缀
- 管理端路由前缀（`/admin` 还是 `/console`）
- 对外 API 命名（完全避开供应商字眼）  

## 任务状态总结
- **已完成**：给出多组不暴露供应商、贴合你业务的品牌名与项目命名方案。
- **下一步**：你选定一个品牌名（或给风格偏好），我就按这个名字把后端工程结构命名并开始搭建。

### User Input

Mint 我更偏重这个单词的薄荷名词含义怎么办？我觉得这个形象比较好，能不能结合一下？

*Updated todo list*

*Updated todo list*

### Planner Response

## 可以结合，而且我觉得这是个更好的品牌方向

你喜欢 `Mint` 作为“薄荷”意象（清爽、干净、快速、提神），这跟你平台的核心体验其实很契合：

- **清爽**：一键兑换、立即交付验证码
- **干净**：不暴露供应商、流程标准化
- **快速**：即时出码、自动切换预设方案
- **可延展**：以后不止一个产品线也能用“薄荷”统一品牌视觉

下面给你几组“薄荷意象 + 业务含义”更自然的组合。

---

# 推荐品牌名（Top 3）

## 1) **MintPass**
- **感觉**：薄荷通行证（清爽 + 通行/验证）
- **适配你业务**：卡密=pass，兑换=激活通行
- **项目名建议**
  - repo：`mintpass`
  - 服务端：`mintpass-api`
  - 管理端：`mintpass-console`
  - Worker：`mintpass-worker`

## 2) **MintKey**
- **感觉**：薄荷钥匙（Key/卡密/兑换码）
- **适配你业务**：用户拿“钥匙”去“开”验证码交付
- **项目名建议**
  - repo：`mintkey`
  - 服务端：`mintkey-service`
  - 管理端：`mintkey-console`

## 3) **MintFlow**
- **感觉**：薄荷流程（强调“兑换→出码→完成”的流水线）
- **适配你业务**：你后续要做开发者 API，会非常流程化
- **项目名建议**
  - repo：`mintflow`
  - 服务端：`mintflow-api`
  - 管理端：`mintflow-admin`

---

# 如果你更想“薄荷”更明显一点（但依然不直白）
这些偏品牌化：

- **PepperMint** / **Peppermint**（更像纯薄荷品牌，但在技术圈略普通）
- **MintLeaf**
- **MintArc**
- **MintHarbor**

---

# 视觉意象怎么落地（不需要现在就做，但可以统一方向）
- **主色**：薄荷绿 `#2DD4BF` / `#34D399` 一类
- **图标**：叶片 + 钥匙孔 / 叶片 + 勾 / 叶片 + 闪电
- **术语统一**（对外中性）
  - 卡密：`voucher` / `key`
  - 兑换：`redeem`
  - 交付结果：`delivery` / `result`
  - 管理台：`console`

---

## 你现在选一个就能定工程名
你更喜欢哪一个作为最终品牌？

- `MintPass`
- `MintKey`
- `MintFlow`

你定下来后，我后续创建后端项目目录、包名、服务名就全部按这个走（并继续保证对外不出现供应商名称）。

## 任务状态总结
- **已完成**：给出可与“薄荷（Mint）意象”融合的品牌名候选，并提供对应项目命名方案。
- **待你确认**：从 `MintPass / MintKey / MintFlow` 里选一个最终名字。

### User Input

MintPass 我更喜欢这个，但是中文名字我不喜欢 薄荷通行？这好俗气啊，薄荷还行，后面通行、通行证太丑了

*Updated todo list*

*Updated todo list*

### Planner Response

## `MintPass` 的中文名：保留“薄荷”的质感，但不出现“通行/通行证”

你可以把中文名当成**品牌中文别名**（用于宣传/页面标题），而英文品牌仍然统一用 `MintPass`（技术栈、域名、repo 都保持一致）。中文别名可以更“意象化”，不必逐字翻译 `Pass`。

下面是我觉得更高级、不俗气的一组候选（都避开“通行/通行证”）：

### 候选 A（偏品牌感、好记）
- **薄荷云**：强调“交付在云端”、轻盈清爽
- **薄荷引擎**：强调“自动化、可扩展、稳定出码流程”
- **薄荷工坊**：强调“铸造/生成/交付”，比“通行证”高级很多

### 候选 B（偏科技感、偏“兑换/交付”）
- **薄荷兑**：一个字点题“兑换”，短且不土
- **薄荷递**：强调“即时递送/交付”
- **薄荷链**：强调“卡密→兑换→交付”的链路（也适合你做开发者 API 平台）

### 候选 C（偏克制高级风）
- **薄荷**（就叫这两个字）：极简，但需要你后续靠视觉与 Slogan 把含义补足  
  例如：Slogan 用“薄荷一下，秒速交付”

---

# 我给你的最终推荐（Top 3）

- **薄荷引擎**（最贴你“自动切换预设、稳定交付”的系统属性）
- **薄荷云**（最像一个平台品牌，后续扩品也自然）
- **薄荷工坊**（最贴“mint/铸造”的感觉，但不直白）

如果你想再“短一点、狠一点”，就选：**薄荷兑**。

---

## 项目命名怎么统一（建议）
- **对外英文品牌**：`MintPass`（固定）
- **对外中文别名**：从上面选一个，比如“薄荷引擎”
- **repo / 服务名**：
  - `mintpass`
  - `mintpass-api`
  - `mintpass-console`

---

## 我需要你拍板一件事
你更偏好中文名的风格是哪种？

- **[平台感]** 薄荷云  
- **[技术感]** 薄荷引擎  
- **[品牌感]** 薄荷工坊  
- **[极简短促]** 薄荷兑  

你选定后，我后续写项目目录、README 标题、API 名称时就按这个统一（并继续遵守“对外不出现供应商名称”）。

### User Input

薄荷验证工坊怎么样？

### Planner Response

## “薄荷验证工坊”我觉得可行，而且比“薄荷通行证”高级很多

- **[契合业务]** “验证”直接命中你交付的是验证码；“工坊”对应 `Mint` 的“铸造/生成”意象，也保留了薄荷的清爽调性。  
- **[对外表达安全]** 全程不涉及任何供应商名称，符合你“对外不出现供应商字眼”的原则。  
- **[可扩展]** 以后不止一种产品（不止 Telegram），也仍然能叫“验证工坊”，不会限制品类。

---

## 可能的不足与优化（可选）
- **[长度稍长]** “薄荷验证工坊”7 个字，做 Logo/导航栏可能略占空间。  
  我建议你给它配一个**短称呼**，用于 UI/菜单：
  - **短称**：`薄荷工坊`（最自然）
  - **短称**：`薄荷验证`（更直给）
  - **短称**：`薄荷验坊`（更品牌化，但要看你喜不喜欢这个词感）

---

## 品牌与项目命名怎么统一（建议）
- **英文品牌/技术名**：`MintPass`（repo、服务名、包名统一用它）
- **中文品牌名**：`薄荷验证工坊`（官网标题、宣传用）
- **对外产品页/控制台标题**：`薄荷工坊`（短称）

---

## 一句 Slogan（可选）
- `薄荷一下，秒速出码`
- `清爽交付，稳定验证`

如果你确认就用“薄荷验证工坊”，我后面就按这个组合固定下来：**MintPass（英文/项目名） + 薄荷验证工坊（中文品牌）**。

## 任务状态总结
- **已确定方向**：`MintPass` 作为英文品牌；中文名候选“薄荷验证工坊”匹配业务且不俗气。

### User Input

薄荷码工坊这个呢？我是根据这个产生的灵感

*Updated todo list*

*Updated todo list*

### Planner Response

## “薄荷码工坊”我更推荐，你这个灵感很对

相较于“薄荷验证工坊”，“薄荷码工坊”有几个优势：

- **[更品牌化]** “码”更抽象、更轻盈，不会把你锁死在“验证码”一个交付物上（以后你可能扩展到激活码、兑换码、授权码、API key 等都能涵盖）。
- **[不俗气]** 没有“通行/通行证”那种直白感，读起来更像一个产品品牌。
- **[贴合 Mint 意象]** “工坊” + “码”天然就是“铸造/生成/交付”的感觉。

### 唯一需要注意的点
- **“码”有轻微歧义**：用户第一次看到不一定立刻知道你是“验证码交付”。  
  但这反而可以用 **副标题/Slogan** 解决，而且更高级。

---

# 最终命名落地清单（建议你就按这套定了）

## 品牌
- **英文品牌**：`MintPass`
- **中文品牌**：`薄荷码工坊`
- **中文短称**（UI/菜单）：`薄荷工坊` 或 `薄荷码`

## 项目/仓库命名
- **repo**：`mintpass`
- **后端服务**：`mintpass-api`
- **管理端**（未来）：`mintpass-console`
- **任务执行器**（未来）：`mintpass-worker`

## 对外用词规范（继续遵守你的要求）
- **卡密**：`兑换码` / `卡密`（对外可叫“兑换码”更自然）
- **兑换**：`兑换` / `Redeem`
- **交付结果**：`验证码` / `结果`
- **供应商**：对外不出现任何供应商名称（内部随你怎么叫）

## Slogan（可选）
- `薄荷一下，秒速出码`
- `清爽交付，稳定出码`
- `一码即兑，立即交付`

---

## 任务状态总结
- **已完成**：对比并推荐“薄荷码工坊”作为中文品牌名，并给出与 `MintPass` 对应的统一命名方案（repo/service/短称/对外用词）。

### User Input

那这样的话英文品牌也需要变，你有推荐的吗？

*Updated todo list*

### Planner Response

## 英文品牌不一定必须变，但如果要更贴“薄荷码工坊”，我推荐这些

你中文已经从“验证/通行”转向更品牌化的“码工坊”，英文确实可以从 `Pass` 转到更中性的 `Code/Key/Mint` 语义，更一致。

下面是我建议的英文品牌名候选（都不含供应商字眼）：

---

# 最推荐（Top 3）

## 1) **MintCode**
- **匹配度**：几乎就是“薄荷码”的直译但不土
- **优点**：短、好记、产品含义明确（code=验证码/兑换码/授权码都能扩展）
- **项目名建议**：
  - repo：`mintcode`
  - 服务：`mintcode-api`
  - 管理端：`mintcode-console`

## 2) **MintKey**
- **匹配度**：偏“卡密/钥匙”的意象，更接近你核心资产（兑换码）
- **优点**：更品牌化一点，不局限于“code”
- **项目名建议**：
  - repo：`mintkey`
  - 服务：`mintkey-api`

## 3) **MintForge**
- **匹配度**：对应“工坊/铸造”，和“工坊”意象强绑定
- **优点**：更有品牌故事（forge=锻造/铸造）
- **项目名建议**：
  - repo：`mintforge`
  - 服务：`mintforge-api`

---

# 备选（如果你想更“平台化”）
- **MintWorks**（works=工坊/作品集）
- **MintLab**（偏实验室风）
- **MintWorkshop**（直白但略长）

---

## 我给你的最终建议（直接拍板用也行）

- 如果你希望英文像中文一样直给：选 **`MintCode`**
- 如果你更偏“卡密=钥匙”的隐喻：选 **`MintKey`**
- 如果你想突出“工坊”的品牌感：选 **`MintForge`**

你更想要哪种气质：**直给**、**隐喻**、还是**品牌故事**？选一个我就把整套 repo/service 命名也跟着固定下来。

### User Input

我选择这个 MintCode

*Updated todo list*

### Planner Response

## 已定稿：英文 **MintCode** + 中文 **薄荷码工坊**

我会按这个统一后续所有命名（并继续遵守你要求：**对外不出现供应商名称**）。

### 命名落地清单
- **英文品牌**：`MintCode`
- **中文品牌**：`薄荷码工坊`
- **中文短称**：`薄荷工坊`（UI/菜单推荐用这个）
- **仓库/项目名建议**：
  - repo：`mintcode`
  - 后端：`mintcode-api`
  - 管理端：`mintcode-console`（未来）
  - worker：`mintcode-worker`（未来）

---

## 下一步（如果你确认，我就开始搭后端骨架）
你之前已经认可用 **FastAPI + SQLite** 做 MVP，我建议现在就创建一个 `i:\repo\mintcode-api` 的独立后端工程，先实现：

- **管理端接口**
  - 生成卡密并导出 txt（每行一个）
  - SKU/预设方案（Plans）基础配置（先可以写在 SQLite 或配置文件）
- **兑换端接口（可选一起做）**
  - 提交卡密 → 生成兑换任务
  - 查询任务状态 → 返回验证码/错误

### 我需要你再确认 1 个选择
- **A：只先做“后台生成卡密 + 导出 txt”**（最快上线）
- **B：同时做“生成 + 兑换任务接口”**（一步到位）

你回我 `A` 或 `B`，我就开始创建 `mintcode-api` 工程并落地接口。  

## 任务状态总结
- **已完成**：品牌最终确定为 `MintCode` / `薄荷码工坊`，并已记录为后续工程命名规范。

*Viewed [api.py](file:///i:/repo/fivesim/fivesim/api.py) *

### User Input

最后我还想问下部署的问题，或者说更推荐用什么语去实现，包括后面还要兼顾到 给开发者提供的 api 接口

*Updated todo list*

*Updated todo list*

### Planner Response

## 技术选型：用什么语言/框架最推荐？

你现在手上已经有 **Python 的供应商 SDK**，并且核心业务（卡密生成、兑换状态机、轮询短信、自动切换预设方案、对外开发者 API）都非常适合用 Python 快速落地，所以我建议：

### 方案 A（我最推荐，MVP→商用都能走通）
- **后端语言**：Python
- **框架**：**FastAPI**
- **原因**
  - **开发效率高**：你要做的管理端/开发者 API 都是标准 HTTP API
  - **文档自带**：`/docs` 直接就是后台管理（先不做前端也行）
  - **和现有库同语言**：减少跨语言的复杂度
  - 后续拆分 worker、上队列也很自然

### 方案 B（你未来团队偏 Node 时可选）
- Node/NestJS 做对外 API，Python 做 worker（专跑下单/轮询）
- 这是“重型架构”，不适合你现在从 0 起步（除非你已经有 Node 体系）

结论：**先用 FastAPI 做单体**，后面按压力再拆分。

---

## 部署推荐：先 VPS + Docker（比 Serverless 更适合你）

你的业务里存在**长轮询/等待验证码/状态机**，这类任务在 Serverless（函数）上容易踩坑：

- 函数超时、冷启动
- 长连接/轮询成本高
- 并发与限流控制更麻烦

所以我建议部署路线：

### 阶段 1：单机部署（最快上线）
- **一台 VPS**（Linux）
- **Docker Compose**
- 组件：
  - **`mintcode-api`**：FastAPI + Uvicorn/Gunicorn
  - **SQLite**（最初可以用文件，单机足够）
- 反向代理：
  - **Nginx / Caddy**（HTTPS、域名、限流、日志）
- 适合：你刚开始小规模订单、内部使用为主

### 阶段 2：可商用（推荐很快就切）
- 数据库升级：**PostgreSQL**（托管或自建）
- 加一个缓存/限流：**Redis**
- 任务执行拆分：
  - `mintcode-api`：只接请求、创建任务
  - `mintcode-worker`：跑“下单→轮询→切换预设→收码→完成”
- 好处：
  - API 响应稳定（不会被轮询拖慢）
  - 更好扩容（多 worker 并行跑任务）
  - 更好做重试、冷却、熔断

### 阶段 3：高并发/多实例
- API 多副本 + 负载均衡
- worker 多副本
- Redis Queue（RQ/Celery/Arq）或更正式的队列（RabbitMQ/Kafka，通常用不上那么重）

---

## 给开发者提供 API：怎么设计才“像产品”且好维护？

建议你从一开始就把接口分两类（命名全部中性，不出现供应商名称）：

### 1) 终端用户/你自己业务用：`redeem`（兑换）
- `POST /redeem`：提交卡密，创建兑换任务
- `GET /redeem/{id}`：查询状态
- `GET /redeem/{id}/result`：拿验证码（或一次性展示）

### 2) 开发者 API：`v1`（对外）
- `POST /v1/orders`：创建“交付任务”（可选择传卡密或传 SKU）
- `GET /v1/orders/{id}`：状态
- `GET /v1/orders/{id}/code`：验证码

关键能力：
- **API Key 鉴权**（开发者）
- **幂等性**（`Idempotency-Key`）
- **限流**（按开发者 key / IP）
- **审计日志**（谁在何时拿到了什么）

---

## 运维与安全要点（你这种业务必须提前做的）

- **密钥管理**
  - `ADMIN_API_KEY`、开发者 `API_KEYS`、以及你“隐晦标签”的 `VOUCHER_SECRET` 全部放环境变量/密钥管理，不写代码里
- **限流**
  - 兑换接口：防爆破（你之前也提到）
  - 开发者 API：防滥用、保护成本
- **日志**
  - 必须记录：卡密 ID（脱敏）、任务 ID、SKU、预设 plan、错误类型、耗时
- **供应商侧限速**
  - 对供应商请求要做节流（尤其 429/503），并加冷却重试，不然你会自杀式触发封控

---

## 我建议你按这个路线落地（最短路径）

- **第一步（1-2 天）**：`mintcode-api` 单体
  - 管理端：生成卡密（导出 txt）
  - 兑换端：提交卡密→创建任务→轮询→返回验证码
  - 存储：SQLite
- **第二步（上线前）**：Postgres + Redis + worker
  - 把“轮询/切 plan”迁到 worker
- **第三步（对外开发者）**：加 API Key + 限流 + 幂等

---

## 我需要你做一个选择（影响我后续给你搭项目）
你倾向哪种部署起步方式？

- **A：本地跑起来就行**（先验证流程）
- **B：直接按 VPS + Docker Compose 的方式搭**（你准备近期上线）

你回复 `A` 或 `B`，我就按这个给你生成 `mintcode-api` 的工程结构、依赖、配置文件（含 Dockerfile/compose）。  

## 任务状态总结
- **已完成**：给出推荐技术栈（FastAPI/Python）与部署路线（VPS+Docker→Postgres+Redis+Worker），并说明如何兼容未来开发者 API。