CREATE TABLE IF NOT EXISTS `ops`.`google_extra_store` (
  `GoogleExtraStoreID` INT NOT NULL AUTO_INCREMENT,
  `CurrentDeviceInstalls` INT NOT NULL,
  `DailyDeviceInstalls` INT NOT NULL,
  `DailyDeviceUninstalls` INT NOT NULL,
  `DailyDeviceUpgrades` INT NOT NULL,
  `CurrentUserInstalls` INT NOT NULL,
  `TotalUserInstalls` INT NOT NULL,
  `DailyUserInstalls` INT NOT NULL,
  `DailyUserUninstalls` INT NOT NULL,
  `DailyCrashes` INT NOT NULL,
  `DailyANRs` INT NOT NULL,
  `DailyAverageRating` FLOAT,
  `TotalAverageRating` FLOAT,
  `ReportDate` DATE NOT NULL,
  PRIMARY KEY (`GoogleExtraStoreID`))
ENGINE = InnoDB;