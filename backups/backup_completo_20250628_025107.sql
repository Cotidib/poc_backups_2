-- Backup de la base de datos test_db
-- Generado: 2025-06-28 02:51:07

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';
SET AUTOCOMMIT = 0;
START TRANSACTION;

--
-- Estructura de la tabla `employees`
--

DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees` (\n  `id` int NOT NULL AUTO_INCREMENT,\n  `name` varchar(100) NOT NULL,\n  `position` varchar(100) NOT NULL,\n  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,\n  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
;

--
-- Datos de la tabla `employees`
--

INSERT INTO `employees` VALUES ('1','Juan PÃ©rez','Developer','2025-06-28 02:50:48','2025-06-28 02:50:48');
INSERT INTO `employees` VALUES ('2','MarÃ­a GarcÃ­a','Project Manager','2025-06-28 02:50:48','2025-06-28 02:50:48');
INSERT INTO `employees` VALUES ('3','Carlos RodrÃ­guez','QA Engineer','2025-06-28 02:50:48','2025-06-28 02:50:48');

COMMIT;
SET FOREIGN_KEY_CHECKS=1;
