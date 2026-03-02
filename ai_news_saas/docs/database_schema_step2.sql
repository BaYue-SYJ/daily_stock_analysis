-- Step 2: Multi-tenant SaaS schema focused on users/accounts/articles/tasks/billing

CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(128) NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'admin',
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_tenant_email (tenant_id, email),
  KEY idx_users_tenant_id (tenant_id)
);

CREATE TABLE wechat_accounts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  account_name VARCHAR(128) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  app_secret VARCHAR(128) NOT NULL,
  access_token VARCHAR(512) NULL,
  refresh_token VARCHAR(512) NULL,
  token_expires_at DATETIME NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_wechat_tenant_id (tenant_id),
  KEY idx_wechat_user_id (user_id),
  UNIQUE KEY uk_tenant_app_id (tenant_id, app_id),
  CONSTRAINT fk_wechat_accounts_user_id FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE articles (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  wechat_account_id BIGINT NULL,
  source_name VARCHAR(128) NOT NULL,
  source_url VARCHAR(512) NOT NULL,
  title VARCHAR(255) NOT NULL,
  original_url VARCHAR(512) NOT NULL,
  content LONGTEXT NOT NULL,
  summary LONGTEXT NULL,
  ai_model VARCHAR(64) NULL,
  published_to_wechat TINYINT(1) NOT NULL DEFAULT 0,
  published_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_tenant_original_url (tenant_id, original_url),
  KEY idx_articles_tenant_id (tenant_id),
  KEY idx_articles_wechat_account_id (wechat_account_id),
  CONSTRAINT fk_articles_wechat_account_id FOREIGN KEY (wechat_account_id) REFERENCES wechat_accounts(id)
);

CREATE TABLE tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  task_type VARCHAR(64) NOT NULL DEFAULT 'rss_fetch_and_summarize',
  cron_expr VARCHAR(64) NULL,
  interval_seconds INT NULL,
  source_url VARCHAR(512) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'enabled',
  last_run_at DATETIME NULL,
  next_run_at DATETIME NULL,
  last_result TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_tasks_tenant_id (tenant_id),
  KEY idx_tasks_user_id (user_id),
  CONSTRAINT fk_tasks_user_id FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE subscriptions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  plan_code VARCHAR(64) NOT NULL,
  plan_name VARCHAR(128) NOT NULL,
  price_monthly DECIMAL(10,2) NOT NULL,
  article_quota INT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  start_at DATETIME NOT NULL,
  end_at DATETIME NOT NULL,
  auto_renew TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_subscriptions_tenant_id (tenant_id),
  KEY idx_subscriptions_status (status)
);

CREATE TABLE billing_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  subscription_id BIGINT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
  pay_channel VARCHAR(32) NOT NULL DEFAULT 'wechat_pay',
  external_trade_no VARCHAR(128) NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  paid_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_billing_tenant_id (tenant_id),
  KEY idx_billing_subscription_id (subscription_id),
  CONSTRAINT fk_billing_subscription_id FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);
