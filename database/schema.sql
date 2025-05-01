-- 建立資料庫（如果不存在）
CREATE DATABASE IF NOT EXISTS `113_2`;
USE `113_2`;

-- 設定字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- G_BOM (成品配方) 表格
CREATE TABLE `group4_g_bom` (
  `recipe_id` int NOT NULL AUTO_INCREMENT COMMENT '配方唯一識別碼',
  `product_code` varchar(50) NOT NULL COMMENT '產品編號',
  `recipe_name` varchar(100) NOT NULL COMMENT '配方名稱',
  `version` varchar(20) NOT NULL COMMENT '版本別',
  `standard_hours` varchar(50) COMMENT '標準工時',
  `specification` varchar(255) COMMENT '規格',
  `notes` text COMMENT '單據備註',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
  PRIMARY KEY (`recipe_id`),
  INDEX `idx_product_code` (`product_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成品配方主檔';

-- F_BOM (半成品配方) 表格
CREATE TABLE `group4_f_bom` (
  `recipe_id` int NOT NULL AUTO_INCREMENT COMMENT '配方唯一識別碼',
  `product_code` varchar(50) NOT NULL COMMENT '產品編號',
  `recipe_name` varchar(100) NOT NULL COMMENT '配方名稱',
  `version` varchar(20) NOT NULL COMMENT '版本別',
  `standard_hours` varchar(50) COMMENT '標準工時',
  `specification` varchar(255) COMMENT '規格',
  `notes` text COMMENT '單據備註',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
  PRIMARY KEY (`recipe_id`),
  INDEX `idx_product_code` (`product_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='半成品配方主檔';

-- MATERIAL_A (一般原料) 表格
CREATE TABLE `group4_material_a` (
  `material_code` varchar(50) NOT NULL COMMENT '貨品編號',
  `material_name` varchar(100) NOT NULL COMMENT '貨品名稱',
  `specification` varchar(255) COMMENT '規格',
  `unit` varchar(20) COMMENT '單位',
  `unit_price_wo_tax` float COMMENT '單價未稅',
  `characteristic` text COMMENT '特性描述',
  `supplier_id` varchar(50) COMMENT '供應商號',
  `supplier_name` varchar(100) COMMENT '供應商名稱',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
  PRIMARY KEY (`material_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='A類原料主檔';

-- MATERIAL_B (管制原料) 表格
CREATE TABLE `group4_material_b` (
  `material_code` varchar(50) NOT NULL COMMENT '貨品編號',
  `material_name` varchar(100) NOT NULL COMMENT '貨品名稱',
  `specification` varchar(255) COMMENT '規格',
  `unit` varchar(20) COMMENT '單位',
  `unit_price_wo_tax` float COMMENT '單價未稅',
  `characteristic` text COMMENT '特性描述',
  `supplier_id` varchar(50) COMMENT '供應商號',
  `supplier_name` varchar(100) COMMENT '供應商名稱',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
  PRIMARY KEY (`material_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='B類原料主檔';

-- RECIPE_STEP (配方步驟) 表格
CREATE TABLE `group4_recipe_step` (
  `step_id` int NOT NULL AUTO_INCREMENT COMMENT '步驟唯一識別碼',
  `recipe_id` int NOT NULL COMMENT '所屬配方ID',
  `recipe_type` enum('G','F') NOT NULL COMMENT '配方類型(G或F)',
  `step_order` int NOT NULL COMMENT '步驟順序',
  `material_code` varchar(50) COMMENT '原料標號',
  `unit` varchar(20) COMMENT '單位',
  `quantity` float NOT NULL DEFAULT 0 COMMENT '原料用量',
  `product_base` float NOT NULL DEFAULT 1 COMMENT '產品基數',
  `notes` text COMMENT '附註',
  PRIMARY KEY (`step_id`),
  INDEX `idx_recipe` (`recipe_id`, `recipe_type`),
  INDEX `idx_material_code` (`material_code`),
  CONSTRAINT `fk_step_material_a` FOREIGN KEY (`material_code`) REFERENCES `group1_material_a` (`material_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_step_material_b` FOREIGN KEY (`material_code`) REFERENCES `group1_material_b` (`material_code`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方步驟明細';

-- 建立配方關聯的外鍵約束
ALTER TABLE `group4_recipe_step`
  ADD CONSTRAINT `fk_step_gbom` FOREIGN KEY (`recipe_id`) REFERENCES `group1_g_bom` (`recipe_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_step_fbom` FOREIGN KEY (`recipe_id`) REFERENCES `group1_f_bom` (`recipe_id`) ON DELETE CASCADE ON UPDATE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;