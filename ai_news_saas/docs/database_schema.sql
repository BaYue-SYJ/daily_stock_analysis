CREATE TABLE tenant (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'admin',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_tenant FOREIGN KEY (tenant_id) REFERENCES tenant(id),
  CONSTRAINT uk_tenant_email UNIQUE (tenant_id, email)
);

CREATE TABLE wechat_account (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  account_name VARCHAR(128) NOT NULL,
  app_id VARCHAR(64) NOT NULL,
  app_secret VARCHAR(128) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_wechat_tenant FOREIGN KEY (tenant_id) REFERENCES tenant(id)
);

CREATE TABLE rss_source (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  url VARCHAR(512) NOT NULL,
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_rss_tenant FOREIGN KEY (tenant_id) REFERENCES tenant(id)
);

CREATE TABLE article (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  source_id BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  link VARCHAR(512) NOT NULL UNIQUE,
  content LONGTEXT NOT NULL,
  summary LONGTEXT NOT NULL,
  published_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_article_tenant FOREIGN KEY (tenant_id) REFERENCES tenant(id),
  CONSTRAINT fk_article_source FOREIGN KEY (source_id) REFERENCES rss_source(id)
);

CREATE TABLE publish_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  article_id BIGINT NOT NULL,
  wechat_account_id BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  response_payload LONGTEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_publish_tenant FOREIGN KEY (tenant_id) REFERENCES tenant(id),
  CONSTRAINT fk_publish_article FOREIGN KEY (article_id) REFERENCES article(id),
  CONSTRAINT fk_publish_wechat FOREIGN KEY (wechat_account_id) REFERENCES wechat_account(id)
);
