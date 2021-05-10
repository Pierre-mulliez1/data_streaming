DROP DATABASE IF EXISTS bikes;
CREATE DATABASE bikes;
USE bikes;
DROP TABLE IF EXISTS Bikepoint;
CREATE TABLE Bikepoint (
  id VARCHAR(50),
  commonName VARCHAR(50),
  NbBikes INT,
  NbEmptyDocks INT,
  NbDocks INT,
  lat  DOUBLE(8, 6),
  lon  DOUBLE(6, 5),
  proc_timestamp TIMESTAMP,
  PRIMARY KEY(proc_timestamp, id)
);

