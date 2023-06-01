-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema buff
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema buff
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `legal` DEFAULT CHARACTER SET utf8 ;
USE `legal` ;

-- -----------------------------------------------------
-- Table `buff`.`items`
-- -----------------------------------------------------
CREATE TABLE `doc` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `doc_id` text DEFAULT NULL,
  `org` text DEFAULT NULL,
  `domain` varchar(200) DEFAULT NULL,
  `receiver` text DEFAULT NULL,
  `date` text DEFAULT NULL,
  `signer` text DEFAULT NULL,
  `content` LONGTEXT DEFAULT NULL,
  `appendix` LONGTEXT DEFAULT NULL,

  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `link` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `link` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `doc2` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `doc_id` text DEFAULT NULL,
  `org` text DEFAULT NULL,
  `domain` varchar(200) DEFAULT NULL,
  `receiver` text DEFAULT NULL,
  `date` text DEFAULT NULL,
  `signer` text DEFAULT NULL,
  `content` LONGTEXT DEFAULT NULL,
  `appendix` LONGTEXT DEFAULT NULL,
  `link` varchar(400) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
