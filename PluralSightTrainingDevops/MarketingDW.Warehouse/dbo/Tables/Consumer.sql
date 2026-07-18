CREATE TABLE [dbo].[Consumer] (

	[ConsumerID] int NOT NULL, 
	[FirstName] varchar(50) NOT NULL, 
	[LastName] varchar(50) NOT NULL, 
	[Email] varchar(100) NOT NULL, 
	[Phone] varchar(20) NULL, 
	[DateOfBirth] date NULL, 
	[CreatedAt] date NULL
);