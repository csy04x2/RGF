-- RGF v0.1 / MySQL 8.0 schema, based on README section 5
CREATE DATABASE IF NOT EXISTS rgf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rgf;

CREATE TABLE IF NOT EXISTS source_documents (
 id BIGINT PRIMARY KEY AUTO_INCREMENT,
 title VARCHAR(500) NOT NULL,
 source_type ENUM('PDF','TEXT') NOT NULL,
 organization VARCHAR(255),
 published_at DATETIME,
 source_url TEXT,
 file_path TEXT,
 raw_text LONGTEXT,
 metadata_json JSON,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS source_evidence (
 id BIGINT PRIMARY KEY AUTO_INCREMENT,
 source_document_id BIGINT NOT NULL,
 evidence_type ENUM('PAGE_TEXT','PARAGRAPH','TABLE') NOT NULL,
 location_label VARCHAR(255),
 content LONGTEXT NOT NULL,
 structured_data JSON,
 content_hash CHAR(64),
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_evidence_document (source_document_id),
 CONSTRAINT fk_evidence_document FOREIGN KEY (source_document_id) REFERENCES source_documents(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS analysis_runs (
 id BIGINT PRIMARY KEY AUTO_INCREMENT,
 source_document_id BIGINT NOT NULL,
 model_name VARCHAR(100) NOT NULL,
 prompt_version VARCHAR(50) NOT NULL,
 status ENUM('PENDING','RUNNING','COMPLETED','FAILED') NOT NULL DEFAULT 'PENDING',
 structured_source_json JSON,
 analysis_json JSON,
 error_message TEXT,
 started_at DATETIME,
 completed_at DATETIME,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_run_document (source_document_id),
 CONSTRAINT fk_run_document FOREIGN KEY (source_document_id) REFERENCES source_documents(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS article_ideas (
 id BIGINT PRIMARY KEY AUTO_INCREMENT,
 analysis_run_id BIGINT NOT NULL,
 title VARCHAR(500) NOT NULL,
 angle TEXT NOT NULL,
 why_it_matters TEXT NOT NULL,
 reporting_questions JSON NOT NULL,
 evidence_needed JSON NOT NULL,
 reporting_targets JSON,
 priority ENUM('HIGH','MEDIUM','LOW') NOT NULL,
 review_status ENUM('검토대기','승인','보류') NOT NULL DEFAULT '검토대기',
 review_note TEXT,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_idea_run (analysis_run_id),
 CONSTRAINT fk_idea_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS article_evidence (
 article_idea_id BIGINT NOT NULL,
 source_evidence_id BIGINT NOT NULL,
 relation_type ENUM('SUPPORTS','CONTEXT','GAP_TRIGGER') NOT NULL,
 explanation TEXT NOT NULL,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (article_idea_id,source_evidence_id),
 CONSTRAINT fk_article_evidence_idea FOREIGN KEY (article_idea_id) REFERENCES article_ideas(id) ON DELETE CASCADE,
 CONSTRAINT fk_article_evidence_source FOREIGN KEY (source_evidence_id) REFERENCES source_evidence(id) ON DELETE CASCADE
) ENGINE=InnoDB;
