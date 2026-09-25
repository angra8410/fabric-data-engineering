[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "dim_customer_DataDestination", IsNewTarget = false], Settings = [Kind = "Manual", AllowCreation = false, ColumnSettings = [Mappings = {[SourceColumnName = "customer_key", DestinationColumnName = "customer_key"], [SourceColumnName = "customer_name", DestinationColumnName = "customer_name"], [SourceColumnName = "address", DestinationColumnName = "address"], [SourceColumnName = "nation_key", DestinationColumnName = "nation_key"], [SourceColumnName = "phone", DestinationColumnName = "phone"], [SourceColumnName = "account_balance", DestinationColumnName = "account_balance"], [SourceColumnName = "market_segment", DestinationColumnName = "market_segment"], [SourceColumnName = "nation_name", DestinationColumnName = "nation_name"], [SourceColumnName = "region_name", DestinationColumnName = "region_name"]}], DynamicSchema = false, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared dim_customer = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "CUSTOMER", ItemKind = "Table"]}[Data],
  #"Merged queries" = Table.NestedJoin(#"Navigation 2", {"C_NATIONKEY"}, dim_geography, {"nation_key"}, "dim_geography", JoinKind.LeftOuter),
  #"Expanded dim_geography" = Table.ExpandTableColumn(#"Merged queries", "dim_geography", {"nation_name", "region_name"}, {"nation_name", "region_name"}),
  #"Renamed columns" = Table.RenameColumns(#"Expanded dim_geography", {{"C_CUSTKEY", "customer_key"}, {"C_NAME", "customer_name"}, {"C_ADDRESS", "address"}, {"C_NATIONKEY", "nation_key"}, {"C_PHONE", "phone"}, {"C_ACCTBAL", "account_balance"}, {"C_MKTSEGMENT", "market_segment"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"C_COMMENT"})
in
  #"Removed columns";
shared dim_geography = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "dim_geography", ItemKind = "Table"]}[Data]
in
  #"Navigation 2";
shared dim_customer_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true]),
  Navigation_1 = Pattern{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "dim_customer", ItemKind = "Table"]}[Data]
in
  TableNavigation;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "dim_supplier_DataDestination", IsNewTarget = false], Settings = [Kind = "Manual", AllowCreation = false, ColumnSettings = [Mappings = {[SourceColumnName = "supplier_key", DestinationColumnName = "supplier_key"], [SourceColumnName = "supplier_name", DestinationColumnName = "supplier_name"], [SourceColumnName = "address", DestinationColumnName = "address"], [SourceColumnName = "nation_key", DestinationColumnName = "nation_key"], [SourceColumnName = "phone", DestinationColumnName = "phone"], [SourceColumnName = "account_balance", DestinationColumnName = "account_balance"], [SourceColumnName = "nation_name", DestinationColumnName = "nation_name"], [SourceColumnName = "region_name", DestinationColumnName = "region_name"]}], DynamicSchema = false, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared dim_supplier = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "SUPPLIER", ItemKind = "Table"]}[Data],
  #"Merged queries" = Table.NestedJoin(#"Navigation 2", {"S_NATIONKEY"}, dim_geography, {"nation_key"}, "dim_geography", JoinKind.LeftOuter),
  #"Expanded dim_geography" = Table.ExpandTableColumn(#"Merged queries", "dim_geography", {"nation_name", "region_name"}, {"nation_name", "region_name"}),
  #"Renamed columns" = Table.RenameColumns(#"Expanded dim_geography", {{"S_SUPPKEY", "supplier_key"}, {"S_NAME", "supplier_name"}, {"S_ADDRESS", "address"}, {"S_NATIONKEY", "nation_key"}, {"S_PHONE", "phone"}, {"S_ACCTBAL", "account_balance"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"S_COMMENT"})
in
  #"Removed columns";
shared dim_supplier_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true]),
  Navigation_1 = Pattern{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "dim_supplier", ItemKind = "Table"]}[Data]
in
  TableNavigation;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "dim_part_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "part_key", DestinationColumnName = "part_key"], [SourceColumnName = "part_name", DestinationColumnName = "part_name"], [SourceColumnName = "manufacturer", DestinationColumnName = "manufacturer"], [SourceColumnName = "brand", DestinationColumnName = "brand"], [SourceColumnName = "part_type", DestinationColumnName = "part_type"], [SourceColumnName = "part_size", DestinationColumnName = "part_size"], [SourceColumnName = "container", DestinationColumnName = "container"], [SourceColumnName = "retail_price", DestinationColumnName = "retail_price"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared dim_part = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "PART", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"P_PARTKEY", "part_key"}, {"P_NAME", "part_name"}, {"P_MFGR", "manufacturer"}, {"P_BRAND", "brand"}, {"P_TYPE", "part_type"}, {"P_SIZE", "part_size"}, {"P_CONTAINER", "container"}, {"P_RETAILPRICE", "retail_price"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"P_COMMENT"})
in
  #"Removed columns";
shared dim_part_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "dim_part", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "fact_inventory_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "part_key", DestinationColumnName = "part_key"], [SourceColumnName = "supplier_key", DestinationColumnName = "supplier_key"], [SourceColumnName = "available_quantity", DestinationColumnName = "available_quantity"], [SourceColumnName = "supply_cost", DestinationColumnName = "supply_cost"], [SourceColumnName = "total_stock_value", DestinationColumnName = "total_stock_value"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared fact_inventory = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "PARTSUPP", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"PS_PARTKEY", "part_key"}, {"PS_SUPPKEY", "supplier_key"}, {"PS_AVAILQTY", "available_quantity"}, {"PS_SUPPLYCOST", "supply_cost"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"PS_COMMENT"}),
  #"Added custom" = Table.AddColumn(#"Removed columns", "total_stock_value", each [available_quantity] * [supply_cost]),
  #"Changed column type" = Table.TransformColumnTypes(#"Added custom", {{"total_stock_value", type number}})
in
  #"Changed column type";
shared fact_inventory_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "fact_inventory", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "fact_sales_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared fact_sales = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "LINEITEM", ItemKind = "Table"]}[Data],
  #"Merged queries" = Table.NestedJoin(#"Navigation 2", {"L_ORDERKEY"}, ORDERS, {"O_ORDERKEY"}, "ORDERS", JoinKind.LeftOuter),
  #"Expanded ORDERS" = Table.ExpandTableColumn(#"Merged queries", "ORDERS", {"O_CUSTKEY", "O_ORDERSTATUS", "O_ORDERDATE", "O_ORDERPRIORITY", "O_SHIPPRIORITY"}, {"O_CUSTKEY", "O_ORDERSTATUS", "O_ORDERDATE", "O_ORDERPRIORITY", "O_SHIPPRIORITY"}),
  #"Renamed columns" = Table.RenameColumns(#"Expanded ORDERS", {{"L_ORDERKEY", "order_key"}, {"L_PARTKEY", "part_key"}, {"L_SUPPKEY", "supplier_key"}, {"L_LINENUMBER", "line_number"}, {"L_QUANTITY", "quantity"}, {"L_EXTENDEDPRICE", "extended_price"}, {"L_DISCOUNT", "discount_percentage"}, {"L_TAX", "tax_percentage"}, {"L_RETURNFLAG", "return_flag"}, {"L_LINESTATUS", "line_status"}, {"L_SHIPDATE", "ship_date"}, {"L_COMMITDATE", "commit_date"}, {"L_RECEIPTDATE", "receipt_date"}, {"L_SHIPINSTRUCT", "ship_instructions"}, {"L_SHIPMODE", "ship_mode"}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Renamed columns", {{"O_CUSTKEY", "customer_key"}, {"O_ORDERSTATUS", "order_status"}, {"O_ORDERDATE", "order_date"}, {"O_ORDERPRIORITY", "order_priority"}, {"O_SHIPPRIORITY", "ship_priority"}, {"L_COMMENT", "comment"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns 1", {"comment"})
in
  #"Removed columns";
shared ORDERS = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "ORDERS", ItemKind = "Table"]}[Data]
in
  #"Navigation 2";
shared NavigationQuery = let
  Source = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true])
in
  Source;
shared fact_sales_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "48cce0aa-0bc6-4243-b797-465d8a50ce0a"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "fact_sales", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
