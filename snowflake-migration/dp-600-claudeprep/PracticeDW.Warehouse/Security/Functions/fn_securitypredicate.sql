-- 2. Crear la función de predicado (iTVF) con SCHEMABINDING (obligatorio para RLS)
CREATE FUNCTION Security.fn_securitypredicate(@Region AS VARCHAR(50))
    RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN SELECT 1 AS fn_securitypredicate_result
WHERE 
    -- El administrador (o cualquier usuario que no sea de prueba) ve todo
    SUSER_SNAME() NOT IN ('viewer-test@velykapet.com', 'developer-test@velykapet.com')
    -- El usuario viewer-test solo ve Antioquia
    OR (SUSER_SNAME() = 'viewer-test@velykapet.com' AND @Region = 'Antioquia')
    -- El usuario developer-test solo ve Valle
    OR (SUSER_SNAME() = 'developer-test@velykapet.com' AND @Region = 'Valle');

GO