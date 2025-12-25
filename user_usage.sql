-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Dec 25, 2025 at 12:05 PM
-- Server version: 9.1.0
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `browser_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `user_usage`
--

DROP TABLE IF EXISTS `user_usage`;
CREATE TABLE IF NOT EXISTS `user_usage` (
  `ul_id` int NOT NULL,
  `url` varchar(100) NOT NULL,
  `daily_limit` datetime NOT NULL,
  `current_usage` datetime NOT NULL,
  `last_reset` datetime NOT NULL,
  PRIMARY KEY (`ul_id`,`url`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `user_usage`
--

INSERT INTO `user_usage` (`ul_id`, `url`, `daily_limit`, `current_usage`, `last_reset`) VALUES
(1, 'https://www.google.com', '2025-12-26 04:26:46', '2025-12-25 04:29:42', '2025-12-25 04:45:12'),
(1, 'https://youtube.com', '0000-00-00 00:00:00', '1970-01-01 00:01:46', '2025-12-25 04:59:56'),
(1, 'https://instagram.com', '0000-00-00 00:00:00', '2000-01-01 00:01:56', '2025-12-25 04:45:24'),
(1, 'https://facebook.com', '0000-00-00 00:00:00', '2000-01-01 00:00:04', '2025-12-25 04:45:12'),
(1, 'https://www.youtube.com/', '2000-01-01 00:01:00', '2000-01-01 00:01:38', '2025-12-25 05:01:31');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
