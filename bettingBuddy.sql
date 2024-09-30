CREATE DATABASE bettingBuddy;

USE bettingBuddy;

CREATE TABLE Users (
	userID INT AUTO_INCREMENT PRIMARY KEY, 
	fName TEXT, 
	lName TEXT, 
	tokenAmnt INT, 
	username VARCHAR(14) UNIQUE,
	password VARCHAR(256)
);

CREATE TABLE Admins (
	adminID INT AUTO_INCREMENT PRIMARY KEY, 
	fName TEXT, 
	lName TEXT, 
	username VARCHAR(14) UNIQUE, 
	password VARCHAR(256)
);

CREATE TABLE Bets (
	betID INT AUTO_INCREMENT,
	userID  INT,
 	status INT,
	FOREIGN KEY (userID) REFERENCES Users(userID)	
);
