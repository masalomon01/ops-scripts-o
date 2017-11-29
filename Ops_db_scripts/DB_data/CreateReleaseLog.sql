CREATE TABLE IF NOT EXISTS `ops`.`release_log` (
  `ReleaseLogID` INT NOT NULL,
  `Module` VARCHAR(128),
  `Server/App/Network` VARCHAR(128),
  `City` VARCHAR(128),
  `Description` VARCHAR(128) NOT NULL,
  `Completed` BOOLEAN NOT NULL,
  `AddDate` DATE NOT NULL,
  `ModDate` DATE NOT NULL,
  PRIMARY KEY (`ReleaseLogID`))
ENGINE = InnoDB;