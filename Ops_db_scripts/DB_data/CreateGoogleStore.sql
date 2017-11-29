CREATE TABLE IF NOT EXISTS `ops`.`google_store` (
  `GoogleStoreID` INT NOT NULL AUTO_INCREMENT,
  `Downloads` INT NOT NULL,
  `Updates` INT NOT NULL,
  `DailyAverageRating` FLOAT,
  `TotalAverageRating` FLOAT,
  `TotalFiveStarCount` INT,
  `TotalFourStarCount` INT,
  `TotalThreeStarCount` INT,
  `TotalTwoStarCount` INT,
  `TotalOneStarCount` INT,
  `ReportDate` DATE NOT NULL,
  PRIMARY KEY (`GoogleStoreID`))
ENGINE = InnoDB;