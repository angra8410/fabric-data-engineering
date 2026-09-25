[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared Customers = let
  Source = Fabric.Warehouse(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[warehouseId = "380874ef-e945-469b-8fab-47d6f207cf7e"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Schema = "dbo", Item = "Customers"]}[Data]
in
  #"Navigation 2";
shared Orders = let
  Source = Fabric.Warehouse(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[warehouseId = "380874ef-e945-469b-8fab-47d6f207cf7e"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Schema = "dbo", Item = "Orders"]}[Data]
in
  #"Navigation 2";
shared Merge_Inner_Join = let
  Source = Table.NestedJoin(Customers, {"CustomerID"}, Orders, {"CustomerID"}, "Orders", JoinKind.Inner),
  #"Expanded Orders" = Table.ExpandTableColumn(Source, "Orders", {"OrderID", "OrderTotal", "OrderDate"}, {"OrderID", "OrderTotal", "OrderDate"})
in
  #"Expanded Orders";
shared Merge_Left_Join = let
  Source = Table.NestedJoin(Customers, {"CustomerID"}, Orders, {"CustomerID"}, "Orders", JoinKind.LeftOuter),
  #"Expanded Orders" = Table.ExpandTableColumn(Source, "Orders", {"OrderID", "OrderTotal", "OrderDate"}, {"OrderID", "OrderTotal", "OrderDate"})
in
  #"Expanded Orders";
