[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared #"Dataflow 1" = let
  Source = PowerPlatform.Dataflows([]),
  #"Navigation 1" = Source{[Id = "Workspaces"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 3" = #"Navigation 2"{[dataflowId = "a3941c25-f208-4b45-8d8b-0e1ff01aa167"]}[Data],
  #"Expanded Data" = Table.ExpandTableColumn(#"Navigation 3", "Data", {"OrderID", "CustomerID", "OrderTotal", "OrderDate"}, {"OrderID", "CustomerID", "OrderTotal", "OrderDate"}),
  #"Uppercased text" = Table.TransformColumns(#"Expanded Data", {{"entityName", each Text.Upper(Text.From(_)), type nullable text}})
in
  #"Uppercased text";
