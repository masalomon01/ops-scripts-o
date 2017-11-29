CREATE TABLE IF NOT EXISTS `ops`.`review` (
  `ReviewID` INT NOT NULL AUTO_INCREMENT,
  `Author` varchar(128),
  `Version` varchar(128),
  `Title` Text,
  `Description` Text,
  `Rating` Float,
  `Store` varchar(128),
  `AddDate` DATETIME NOT NULL,
  PRIMARY KEY (`ReviewID`))
ENGINE = InnoDB;