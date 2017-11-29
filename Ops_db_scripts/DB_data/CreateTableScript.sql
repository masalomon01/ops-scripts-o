-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema OperationDatabase
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema OperationDatabase
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `OperationDatabase` ;
USE `OperationDatabase` ;

-- -----------------------------------------------------
-- Table `OperationDatabase`.`GooglePlayStats`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `OperationDatabase`.`GooglePlayStats` (
  `GooglePlayStatsID` INT NOT NULL AUTO_INCREMENT,
  `CurrentDeviceInstalls` INT NOT NULL,
  `DailyDeviceUpgrades` INT NOT NULL,
  `CurrentUserInstalls` INT NOT NULL,
  `TotalUserInstalls` INT NOT NULL,
  `DailyUserInstalls` INT NOT NULL,
  `DailyUserUninstalls` INT NOT NULL,
  `DailyAverageRating` INT NOT NULL,
  `TotalAverageRating` INT NOT NULL,
  `DailyCrashes` INT NOT NULL,
  `DailyANRs` INT NOT NULL,
  `ReportDate` DATE NOT NULL,
  PRIMARY KEY (`GooglePlayStatsID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `OperationDatabase`.`AppStoreStats`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `OperationDatabase`.`AppStoreStats` (
  `AppStoreStatsID` INT NOT NULL AUTO_INCREMENT,
  `DailyDeviceInstalls` INT NOT NULL,
  `DailyCrashes` INT NOT NULL,
  `DailySessions` INT NOT NULL,
  `DailyActiveDevices` INT NOT NULL,
  `ReportDate` DATE NOT NULL,
  PRIMARY KEY (`AppStoreStatsID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `OperationDatabase`.`AndroidBitbucket`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `OperationDatabase`.`AndroidBitbucket` (
  `AndroidBitbucketID` INT NOT NULL AUTO_INCREMENT,
  `TicketNumber` INT NOT NULL,
  `Title` VARCHAR(45) NOT NULL,
  `Priority` VARCHAR(45) NOT NULL,
  `Status` VARCHAR(45) NOT NULL,
  `Kind` VARCHAR(45) NOT NULL,
  `ModDate` DATETIME NOT NULL,
  `AddDate` DATETIME NOT NULL,
  PRIMARY KEY (`AndroidBitbucketID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `OperationDatabase`.`iOSBitbucket`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `OperationDatabase`.`iOSBitbucket` (
  `iOSBitbucketID` INT NOT NULL AUTO_INCREMENT,
  `TicketNumber` INT NOT NULL,
  `Title` VARCHAR(45) NOT NULL,
  `Priority` VARCHAR(45) NOT NULL,
  `Status` VARCHAR(45) NOT NULL,
  `Kind` VARCHAR(45) NOT NULL,
  `ModDate` DATETIME NOT NULL,
  `AddDate` DATETIME NOT NULL,
  PRIMARY KEY (`iOSBitbucketID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `OperationDatabase`.`RouteDebuggingBitbucket`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `OperationDatabase`.`RouteDebuggingBitbucket` (
  `RouteDebuggingBitbucketID` INT NOT NULL AUTO_INCREMENT,
  `TicketNumber` INT NULL,
  `Title` VARCHAR(45) NULL,
  `Server` VARCHAR(45) NULL,
  `Module` VARCHAR(45) NULL,
  `City` VARCHAR(45) NULL,
  `Description` VARCHAR(45) NULL,
  `Priority` VARCHAR(45) NULL,
  `Status` VARCHAR(45) NULL,
  `Kind` VARCHAR(45) NULL,
  `ModDate` DATETIME NULL,
  `AddDate` DATETIME NULL,
  PRIMARY KEY (`RouteDebuggingBitbucketID`))
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
