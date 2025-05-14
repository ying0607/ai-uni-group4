-- 建立資料庫（如果不存在）
CREATE DATABASE IF NOT EXISTS `113_2`;
USE `113_2`;

-- 設定字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

SELECT '正在建立 BOM 表格...' AS progress;

-- BOM表格
CREATE TABLE `group4_bom` (
  `recipe_id` varchar(50) NOT NULL COMMENT '產品編號',
  `recipe_name` varchar(100) NOT NULL COMMENT '產品名稱',
  `recipe_type` enum('G','F') NOT NULL COMMENT '配方類型(G/F)',
  `version` varchar(20) NOT NULL COMMENT '版本別',
  `standard_hours` varchar(50) COMMENT '標準工時',
  `specification` varchar(255) COMMENT '規格',
  `notes` text COMMENT '單據備註',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
  PRIMARY KEY (`recipe_id`),
  INDEX `idx_product_code` (`recipe_id`),
  INDEX `idx_recipe_type` (`recipe_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='BOM主檔(G成品/F半成品)';

SELECT 'BOM 表格建立完成！' AS progress;

SELECT '正在建立材料表格...' AS progress;

-- 原料表格（一般和管制原料）
CREATE TABLE `group4_materials` (
  `material_code` varchar(50) NOT NULL COMMENT '貨品編號',
  `material_name` varchar(100) NOT NULL COMMENT '貨品名稱',
  `material_type` varchar(10) NOT NULL COMMENT '原料類型',
  `specification` varchar(255) NOT NULL COMMENT '規格',
  `unit` varchar(20) NOT NULL COMMENT '單位',
  `unit_price_wo_tax` float COMMENT '單價未稅',
  `characteristic` text COMMENT '特性描述',
  `supplier_id` varchar(50) COMMENT '供應商號',
  `supplier_name` varchar(100) COMMENT '供應商名稱',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新時間',
  PRIMARY KEY (`material_code`),
  INDEX `idx_material_type` (`material_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料主檔(A一般/B管制)';

SELECT '材料表格建立完成！' AS progress;

SELECT '正在建立步驟表格...' AS progress;

-- 配方步驟表格
CREATE TABLE `group4_recipe_step` (
  `step_id` varchar(50) NOT NULL COMMENT '序號(PK)',
  `recipe_id` varchar(50) NOT NULL COMMENT '產品編號',
  `step_order` int NOT NULL COMMENT '步驟順序',
  `material_code` varchar(50) NOT NULL COMMENT '原料編號',
  `unit` varchar(20) COMMENT '單位',
  `quantity` float NOT NULL DEFAULT 0 COMMENT '原料用量',
  `product_base` float NOT NULL DEFAULT 100 COMMENT '產品基數',
  `notes` text COMMENT '附註',
  PRIMARY KEY (`step_id`),
  INDEX `idx_recipe` (`recipe_id`),
  INDEX `idx_material_code` (`material_code`),
  CONSTRAINT `fk_step_recipe` FOREIGN KEY (`recipe_id`) REFERENCES `group4_bom` (`recipe_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_step_material` FOREIGN KEY (`material_code`) REFERENCES `group4_materials` (`material_code`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方步驟明細';

SET FOREIGN_KEY_CHECKS = 1;

SELECT '步驟表格建立完成！' AS progress;