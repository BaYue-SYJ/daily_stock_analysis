# AI News SaaS (FastAPI)

一个多租户 SaaS 样板：自动抓取 AI 行业 RSS、调用 GPT 总结、并发布到微信公众号，同时提供小程序内容 API。

## 使用 Docker 启动（支持 .env）

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 按需修改 `.env`（OpenAI Key、MySQL 密码、端口等）。

3. 启动四个服务（web / worker / redis / mysql）：

```bash
docker compose up --build
```

## 服务
- Web(FastAPI): http://localhost:8000/docs
- MySQL: localhost:3306
- Redis: localhost:6379

## 核心模块
- 用户注册登录（JWT + tenant）
- 多公众号账号绑定
- RSS 抓取
- OpenAI 总结
- Celery 异步流水线
- 公众号发布
- 小程序文章 API

详见：
- `docs/database_schema.sql`
- `docs/api_design.md`
