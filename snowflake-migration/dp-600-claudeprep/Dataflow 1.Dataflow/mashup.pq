[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared Orders = let
  Source = Fabric.Warehouse(null),
  Navigation = Source{[workspaceId = "cfeefa92-730d-43b2-b2b1-9c46826d5807"]}[Data],
  #"Navigation 1" = Navigation{[warehouseId = "380874ef-e945-469b-8fab-47d6f207cf7e"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Schema = "dbo", Item = "Orders"]}[Data]
in
  #"Navigation 2";
