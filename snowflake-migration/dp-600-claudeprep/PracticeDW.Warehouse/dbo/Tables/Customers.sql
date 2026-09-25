CREATE TABLE [dbo].[Customers] (
    [CustomerID] INT MASKED WITH (FUNCTION = 'default()')         NULL,
    [Name]       VARCHAR (50)                                     NULL,
    [Region]     VARCHAR (50)                                     NULL,
    [Email]      VARCHAR (100) MASKED WITH (FUNCTION = 'email()') NULL
);


GO