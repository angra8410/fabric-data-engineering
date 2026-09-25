CREATE SECURITY POLICY [Security].[FilterCustomers]
    ADD FILTER PREDICATE [Security].[fn_securitypredicate]([Region]) ON [dbo].[Customers]
    WITH (STATE = ON);


GO