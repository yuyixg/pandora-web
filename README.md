<br />

<p align="center">
  <h3 align="center">潘多拉Web · PandoraWeb</h3>
  <p align="center">
    复活吧 我的Pandora
  </p>
</p>

## 一睹为快

![login_new](https://github.com/GavinGoo/pandora-web/blob/dev/doc/images/login_new.jpg)

![chat_new](https://github.com/GavinGoo/pandora-web/blob/dev/doc/images/chat_new.jpg)

![login_old](https://github.com/GavinGoo/pandora-web/blob/dev/doc/images/login_old.png)

![PandoraNeverDie](https://github.com/GavinGoo/pandora-web/blob/dev/doc/images/PandoraNeverDie.png)



## 相关特性

- 两套UI任君选择，随意搭配
- 设置站点密码
- 支持老Pandora式的无密码直接访问(见后文配置说明)
- API对话自动保存
- 重定向3.5/4模型
- 携带历史对话(可设置当历史消息数量大于设定数量时，自动携带第一组历史对话)
- 模型`Auth`轮询
- 单独指定模型的网络代理
- 设定内置Prompt
- 隐藏式(假删除)对话(默认,可更改)
- 仅OAI(仅支持3.5模型)/API或二者共存运行
- 文生图模型可调用其他文本模型以生成/优化你的绘图Prompt
- 对于某些以二进制文件(Blob对象)作为响应的文生图模型(比如Cloudflare AI)，自动保存并转为url输出(若使用了CDN服务，请注意**流量消耗**)



**API模型支持：**

- ChatGLM 4
- Cloudflare AI文本模型
- Cloudflare AI文生图模型(`stable-diffusion-xl-base-1.0`,`dreamshaper-8-lcm`,`stable-diffusion-xl-lightning`)
- Gemini-Pro
- 某个连夜改成每月仅免费50条消息的模型
- 其他OpenAI标准输出模型



## 配置说明


程序参数：

```
--email: 您的 OpenAI 邮箱。
--password: 您的 OpenAI 密码(不建议直接设置密码，可仅配置Email然后在终端输入密码)。
--mfa: 您的 OpenAI mfa认证码。
--proxy_api: OpenAI 前端的代理地址。
--login_url: 获取Access Token的地址。
--site_password: 网站密码。如果以server模式启动，必须设置此项。
-p/--proxy: 使用代理。格式为 protocol://user:pass@ip:port。
--gpt4: 从 "api.json" 文件中选择 GPT-4 的请求模型。
--gpt35: 从 "api.json" 文件中选择 GPT-3.5 的请求模型。
--history_count: 为 API 携带的历史消息数量。默认为4。
--best_history: 当历史消息数量大于设定数量时，自动携带第一组历史对话。
--true_del: 真正地从数据库中，而非将其设为隐藏(is_visible=0)。
-l/--local: 仅在本地运行，不使用 OAI 服务。
--timeout: 请求超时，默认60s，单位(秒)。
--oai_only: 仅使用 OAI 服务。
-t/--token_file: 指定Access Token字符串。
--tokens_file: 指定一个存放多Access Token的文件路径。
--config_dir: 指定配置目录存放Access Token文件、API配置文件api.json、本地对话数据库文件local_conversation.db、以二进制文件(Blob对象)作为响应的文生图模型图片保存目录text2img、登录会话目录sessions(默认跟随系统,docker则位于/data)
-s/--server: 作为一个代理服务器启动。格式为 ip:port，默认为 0.0.0.0:8008。
--threads: server模式的线程数，默认为8。
-a/--api: 使用gpt-3.5-turbo 聊天 API。注意：OpenAI 将会向您收费。
--login_local: 使用本地环境登录，你可能需要一个合适的代理IP以避免账号被风控！
-v/--verbose: 显示调试信息，且出错时打印异常堆栈信息，供查错使用。
--old_login: 使用老Pandora登陆页面。
--old_chat: 使用老Pandora聊天页面。
```



环境变量：

1. `OPENAI_EMAIL`, `OPENAI_PASSWORD`,`OPENAI_MFA_CODE`: OAI账密相关(**不建议**直接设置密码，可仅配置Email然后在终端输入密码)。
2. `OPENAI_API_PREFIX`: OpenAI 前端的代理地址。
3. `OPENAI_LOGIN_URL`: 获取Access Token的地址。
4. `PANDORA_ACCESS_TOKEN`:  指定`Access Token`字符串。
5. `PANDORA_TOKENS_FILE`: 指定一个存放多`Access Token`的文件路径。
6. `USER_CONFIG_DIR`: 指定配置目录存放`Access Token`文件、API配置文件`api.json`、本地对话数据库文件`local_conversation.db`、以二进制文件(Blob对象)作为响应的文生图模型图片保存目录`text2img`、登录会话目录`sessions`(默认跟随系统，docker则位于/data)
7. `PANDORA_SERVER`: 以`http`服务方式启动，格式：`ip:port`，默认：`0.0.0.0:8008`。
8. `PANDORA_SITE_PASSWORD`: 站点密码，如果以server模式启动该值为必填。
9. `OPENAI_MFA_CODE`: OpenAI 的多因素认证码，可以通过命令行参数 `--mfa` 设置。
10. `PANDORA_PROXY`: 代理地址，可以通过命令行参数 `--proxy` 设置。
11. `PANDORA_GPT4_MODEL`: 从 "api.json" 文件中选择 GPT-4 模型。
12. `PANDORA_GPT35_MODEL`: 从 "api.json" 文件中选择 GPT-3.5 模型。
13. `PANDORA_HISTORY_COUNT`: 设置历史消息的数量。
14. `PANDORA_BEST_HISTORY`: 当历史消息数量大于设定数量时，自动携带第一组历史对话。
15. `PANDORA_TRUE_DELETE`: **真正地从数据库中**删除对话，而非将其设为隐藏(is_visible=0)。
16. `PANDORA_LOCAL_OPTION`: 仅API模式，不使用 OAI 服务。
17. `PANDORA_TIMEOUT`: 请求超时，默认60s，单位(秒)。
18. `PANDORA_OAI_ONLY`: 仅使用 OAI 服务。
19. `PANDORA_OLD_LOGIN`: 使用老Pandora登陆页面。
20. `PANDORA_OLD_CHAT`: 使用老Pandora聊天页面。
21. `PANDORA_API`: 使用`gpt-3.5-turbo`API请求，**你可能需要向`OpenAI`支付费用**。
22. `PANDORA_LOGIN_LOCAL`: 使用本地环境登录，**你可能需要一个合适的代理IP以避免账号被风控！**
23. `PANDORA_VERBOSE`: 显示调试信息，且出错时打印异常堆栈信息，供查错使用。
24. `PANDORA_THREADS`: server模式的线程数，默认为8。
25. `PANDORA_CLOUD`: Pandora Cloud模式(原参数，不知还可用否?)。

> 使用Docker仅配置环境变量即可，无视上述`程序参数`。
>
> 如果想实现老Pandora无登录功能点开即用，将`--site_password`/`PANDORA_SITE_PASSWORD`设置为`I_KNOW_THE_RISKS_AND_STILL_NO_SITE_PASSWORD`即可(这可能是个危险设置，请注意)。



API配置：

使用`api.json`文件配置，默认位于用户配置目录，可通过环境变量`USER_CONFIG_DIR`或程序参数`config_dir`设置

> 默认用户配置目录：
>
> Mac OS X: same as user_data_dir (Python appdirs模块的说明)
> Unix: ~/.config/Pandora-ChatGPT # or in $XDG_CONFIG_HOME, if defined
> Win : C:\Users\\`<User Name>`\AppData\Local\Pandora-ChatGPT\Pandora-ChatGPT
>
> 无论是否设置，启动时都会把路径打印出来

以下是参考模板：

```json
{
    "coze": {
        "slug": "coze",
        "url": "<Coze-Discord-Proxy Url>",
        "auth": "<Coze-Discord-Proxy AUTH>",
        "title": "Coze(可联网)",
        "description": "https://coze.com",
        "max_tokens": 8191 
    },
    "glm-4": {
        "slug": "glm-4",
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "auth": "<智谱AI Token>",
        "title": "ChatGLM-4",
        "description": "ChatGLM-4",
        "max_tokens": 8191 
    },
    "cogview-3": {
        "slug": "cogview-3",
        "url": "https://open.bigmodel.cn/api/paas/v4/images/generations",
        "auth": "<智谱AI Token>",
        "title": "CogView(文生图|收费)",
        "description": "刚开始没留意这玩意不是消耗token额度，现在倒欠3块大洋还没还",
        "max_tokens": 8191 
    },
    "gemini-pro": {
        "slug": "gemini-pro",
        "url": "https://generativelanguage.googleapis.com/v1/models/gemini-pro:streamGenerateContent?key=<Your Google AI Key>",
        "title": "Gemini-Pro",
        "description": "Gemini-Pro",
        "max_tokens": 8191 
    },
    "llama-2-7b-chat-fp16": {
        "slug": "llama-2-7b-chat-fp16",
        "url": "https://api.cloudflare.com/client/v4/accounts/<Your Cloudflare Account ID>/ai/run/@cf/meta/llama-2-7b-chat-fp16",
        "auth": "<Your Cloudflare AI Key>",
        "title": "llama-2-7b-chat-fp16",
        "description": "llama-2-7b-chat-fp16",
        "max_tokens": 8191 
    },
    "stable-diffusion-xl-base-1.0": {
        "slug": "stable-diffusion-xl-base-1.0",
        "url": "https://api.cloudflare.com/client/v4/accounts/<Your Cloudflare Account ID>/ai/run",
        "image_model": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
        "prompt_model": "glm-4",
        "auth": "<Your Cloudflare AI Key>",
        "title": "cfai(文生图)",
        "description": "cfai(文生图)",
        "max_tokens": 8191 
    },
    "gpt-4": {
        "slug": "gpt-4",
        "url": "<Your API Url>",
        "auth": ["鸡", "你", "太", "美"],
        "prompt": "You use the GPT-4 version of OpenAI’s GPT models.Respond in the following locale: zh-cn.",
        "title": "GPT-4",
        "description": "GPT-4",
        "max_tokens": 8191 
    }
}
```

> 参数说明：
>
> `slug`: 请求时的模型名(请与键值保持一致)
>
> `url`: 模型请求的url
>
> `auth`: 模型请求的验证头(智谱家的与某模型会自动处理(`slug`需包含关键词比如`glm`)，直接填入你的Key即可)无则不写`auth`这个键，比如Gemini
>
> `proxy`: 指定该模型使用的网络代理(优先级最高)
>
> `prompt`: 你的内置Prompt
>
> `title`: 前端页面上的模型显示名称
>
> `description`: 老Pandora页面上的模型描述
>
> `max_tokens`: (不知道啥玩意，官方有我也就顺便带上了)
>
> 特殊参数：
>
> `prompt_model`: 指定**文本模型**生成/优化绘图Prompt(使用**非流式**请求)，此时`prompt`支持使用"`<Prompt>`"作为原Prompt的占位符，当占位符不存在时则自动将原Prompt追加到文末(如果文生图模型非Cloudflare AI 即url非`"https://api.cloudflare.com/client/v4/accounts/<Your Cloudflare Account ID>/ai/run"`，则不支持Cloudflare AI的文本模型)
>
> `image_model`: 仅由用于Cloudflare AI文生图模型，填入`Model ID`。格式：`"@cf/***/<model>"`，参见：`"https://developers.cloudflare.com/workers-ai/models/<model>"`



## 如何运行

- 本地运行

  Python版本最好在`3.8`及以上(我的版本为3.10.0)

  进入项目根目录，运行：

  ```
  # 安装依赖
  pip install --no-cache-dir -r requirements.txt

  # 启用OAI服务：
  python -m src.pandora.launcher -s --email <Your OAI Email> --proxy_api <Your OAI Service Proxy Endpoint> --login_url <Your OAI Login Url> -p <> --site_password <Your Site Password> --history_count 10
  
  # 仅API模式：
  python -m src.pandora.launcher -s -l --site_password <Your Site Password>
  ```
  
  > 后台运行：`nohup python -m src.pandora.launcher -s -l --site_password <Your Site Password> &`





## 其他说明

* 本二改项目是站在zhile与其他巨人的肩膀上，感谢！！

* 本人代码水平太糟糕了，在此表示抱歉

* 最近这段时间除非重要Bug外可能实在没空维护
