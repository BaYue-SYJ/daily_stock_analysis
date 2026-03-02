# API 设计（v1）

Base URL: `/api/v1`
认证方式：`Authorization: Bearer <JWT>`，JWT 中包含 `tenant_id`。

## 1) 用户注册登录

### POST `/auth/register`
- 描述：创建租户 + 创建首个管理员。
- 请求体：
```json
{
  "tenant_name": "acme-ai",
  "email": "owner@acme.com",
  "password": "StrongPass123"
}
```
- 响应：
```json
{"access_token":"...","token_type":"bearer"}
```

### POST `/auth/login`
- 描述：租户用户登录。
- 请求体同上（含 tenant_name）。
- 响应同注册。

## 2) 多公众号账号绑定

### POST `/accounts/wechat`
- 描述：绑定租户下一个公众号账号。
- 请求体：
```json
{
  "account_name":"品牌号",
  "app_id":"wx123",
  "app_secret":"***"
}
```

## 3) RSS 抓取配置

### POST `/content/rss`
- 描述：新增 AI 资讯 RSS 源。
- 请求体：
```json
{"name":"OpenAI Blog","url":"https://openai.com/blog/rss.xml"}
```

## 4) 同步抓取 + AI 总结（Celery）

### POST `/content/sync?source_id=1`
- 描述：触发异步任务：RSS抓取 -> 正文抽取 -> GPT总结 -> 入库。
- 响应：
```json
{"task_id":"celery-task-id","status":"queued"}
```

## 5) 发布到微信公众号

### POST `/publish/wechat?article_id=1&wechat_account_id=1`
- 描述：发布指定文章到公众号草稿箱，结果落地到 `publish_log`。

## 6) 小程序内容 API

### GET `/content/mini/articles?limit=20`
- 描述：小程序拉取租户文章列表（标题、摘要、链接、发布时间）。

## 错误码建议
- `401` 未认证/Token无效
- `403` 非租户资源
- `404` 资源不存在
- `422` 参数校验失败
- `500` 平台内部异常
