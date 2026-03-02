# GitHub 发布指南

## 1. 代码准备

- 确认 `README.md`、`.env.example`、`docker-compose.yml` 最新。
- 确认不包含敏感信息（`.env`、真实密钥）。

## 2. 本地检查

```bash
python -m compileall app
docker compose config
```

## 3. Git 发布

```bash
git add .
git commit -m "chore: prepare release v0.1.0"
git tag v0.1.0
git push origin <branch>
git push origin v0.1.0
```

## 4. GitHub Release 内容建议

- 新增能力（抓取、总结、发布、小程序 API）
- 启动步骤（`.env` + `docker compose up --build -d`）
- 已知限制（需配置 OpenAI Key，微信发布需公众号资质）
