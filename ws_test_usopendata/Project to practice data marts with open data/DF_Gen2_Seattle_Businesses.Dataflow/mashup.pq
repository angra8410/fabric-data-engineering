[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared Bronze_raw_ingestion = let
    // 1. Direct High-Speed Bulk Stream of ALL Seattle Businesses
    SourceUrl = "https://data.seattle.gov/api/views/wnbq-64tb/rows.csv?accessType=DOWNLOAD",
    
    // 2. Stream all 84,390 rows with UTF-8 encoding
    Source = Csv.Document(
        Web.Contents(SourceUrl),
        [
            Delimiter = ",",
            Columns = 13,
            Encoding = 65001,
            QuoteStyle = QuoteStyle.Csv
        ]
    ),
    
    // 3. Promote headers
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    
    // 4. Standardize column names (lowercase snake_case for Fabric)
    #"Renamed Columns" = Table.RenameColumns(#"Promoted Headers", {
        {"Business Legal Name", "business_legal_name"},
        {"Trade Name", "trade_name"},
        {"Ownership Type", "ownership_type"},
        {"NAICS Code", "naics_code"},
        {"NAICS Description", "naics_description"},
        {"License Start Date", "license_start_date"},
        {"Street Address", "street_address"},
        {"City", "city"},
        {"State", "state"},
        {"Zip", "zip"},
        {"Business Phone", "business_phone"},
        {"City Account Number", "city_account_number"},
        {"UBI", "ubi"}
    })
in
    #"Renamed Columns";
shared Silver_transformations = let
  Source = Bronze_raw_ingestion,
  #"Changed column type with locale" = Table.TransformColumnTypes(Source, {{"license_start_date", type date}}, "en-US"),
  #"Trimmed text" = Table.TransformColumns(#"Changed column type with locale", {{"license_start_date", each Text.Trim(Text.From(_)), type nullable text}, {"business_legal_name", each Text.Trim(Text.From(_)), type nullable text}, {"trade_name", each Text.Trim(Text.From(_)), type nullable text}, {"ownership_type", each Text.Trim(Text.From(_)), type nullable text}, {"naics_code", each Text.Trim(Text.From(_)), type nullable text}, {"naics_description", each Text.Trim(Text.From(_)), type nullable text}, {"city", each Text.Trim(Text.From(_)), type nullable text}, {"street_address", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Cleaned text" = Table.TransformColumns(#"Trimmed text", {{"license_start_date", each Text.Clean(_), type nullable text}, {"business_legal_name", each Text.Clean(_), type nullable text}, {"trade_name", each Text.Clean(_), type nullable text}, {"ownership_type", each Text.Clean(_), type nullable text}, {"naics_code", each Text.Clean(_), type nullable text}, {"naics_description", each Text.Clean(_), type nullable text}, {"city", each Text.Clean(_), type nullable text}, {"street_address", each Text.Clean(_), type nullable text}}),
  #"Added custom" = Table.AddColumn(#"Cleaned text", "age_in_years", each let
    StartDate = try Date.From([license_start_date]) otherwise null,
    Today = DateTime.Date(DateTime.LocalNow())
in
    if StartDate = null then null
    else if StartDate > Today then 0
    else Number.Round((Number.From(Today) - Number.From(StartDate)) / 365, 1)),
  #"Changed column type" = Table.TransformColumnTypes(#"Added custom", {{"age_in_years", type number}}),
  #"Added custom 1" = Table.AddColumn(#"Changed column type", "business_age_formatted", each let
    TotalYears = [age_in_years],
    WholeYears = Number.RoundDown(TotalYears),
    RemainingMonths = Number.Round((TotalYears - WholeYears) * 12)
in
    if TotalYears = null then null
    else if TotalYears = 0 then "Less than 1 month / Pending"
    else Text.From(WholeYears) & " years and " & Text.From(RemainingMonths) & " months"),
    #"Cleaned blanks" = Table.TransformColumns(
    #"Added custom 1", 
    {
      {"ubi", each if _ = null or Text.Trim(Text.From(_)) = "" then "Not Defined" else _, type text},
      {"state", each if _ = null or Text.Trim(Text.From(_)) = "" then "Unknown" else Text.Upper(Text.Trim(_)), type text},
      {"city", each if _ = null or Text.Trim(Text.From(_)) = "" then "Unknown" else Text.Proper(Text.Trim(_)), type text},
      {"naics_code", each if _ = null or Text.Trim(Text.From(_)) = "" then "999999" else Text.Trim(_), type text},
      {"naics_description", each if _ = null or Text.Trim(Text.From(_)) = "" then "Unclassified / General" else Text.Trim(_), type text}
    }
  )
in
  #"Cleaned blanks";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_Industry_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Dim_Industry = let
  Source = Silver_transformations,
  #"Removed other columns" = Table.SelectColumns(Source, {"naics_code", "naics_description"}),
  #"Removed duplicates" = Table.Distinct(#"Removed other columns", {"naics_code", "naics_description"}),
  #"Added index" = Table.AddIndexColumn(#"Removed duplicates", "Index", 1, 1, Int64.Type),
  #"Renamed columns" = Table.RenameColumns(#"Added index", {{"Index", "industry_key"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns", {"industry_key", "naics_code", "naics_description"})
in
  #"Reordered columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_Ownership_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Dim_Ownership = let
  Source = Silver_transformations,
  #"Choose columns" = Table.SelectColumns(Source, {"ownership_type"}),
  #"Removed duplicates" = Table.Distinct(#"Choose columns", {"ownership_type"}),
  #"Added index" = Table.AddIndexColumn(#"Removed duplicates", "Index", 1, 1, Int64.Type),
  #"Renamed columns" = Table.RenameColumns(#"Added index", {{"Index", "ownership_key"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns", {"ownership_key", "ownership_type"})
in
  #"Reordered columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_Location_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "location_key", DestinationColumnName = "location_key"], [SourceColumnName = "street_address", DestinationColumnName = "street_address"], [SourceColumnName = "city", DestinationColumnName = "city"], [SourceColumnName = "state", DestinationColumnName = "state"], [SourceColumnName = "zip", DestinationColumnName = "zip"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared Dim_Location = let
  Source = Silver_transformations,
  #"Removed other columns" = Table.SelectColumns(Source, {"street_address", "city", "state", "zip"}),
  #"Removed duplicates" = Table.Distinct(#"Removed other columns", {"street_address", "city", "state", "zip"}),
  #"Added index" = Table.AddIndexColumn(#"Removed duplicates", "Index", 1, 1, Int64.Type),
  #"Renamed columns" = Table.RenameColumns(#"Added index", {{"Index", "location_key"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns", {"location_key", "street_address", "city", "state", "zip"})
in
  #"Reordered columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Fact_Seattle_Businesses_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "business_legal_name", DestinationColumnName = "business_legal_name"], [SourceColumnName = "trade_name", DestinationColumnName = "trade_name"], [SourceColumnName = "license_start_date", DestinationColumnName = "license_start_date"], [SourceColumnName = "city_account_number", DestinationColumnName = "city_account_number"], [SourceColumnName = "ubi", DestinationColumnName = "ubi"], [SourceColumnName = "age_in_years", DestinationColumnName = "age_in_years"], [SourceColumnName = "business_age_formatted", DestinationColumnName = "business_age_formatted"], [SourceColumnName = "industry_key", DestinationColumnName = "industry_key"], [SourceColumnName = "ownership_key", DestinationColumnName = "ownership_key"], [SourceColumnName = "location_key", DestinationColumnName = "location_key"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared Fact_Seattle_Businesses = let
  Source = Silver_transformations,
  #"Merged queries" = Table.NestedJoin(Source, {"naics_code", "naics_description"}, Dim_Industry, {"naics_code", "naics_description"}, "Dim_Industry", JoinKind.LeftOuter),
  #"Changed column type" = Table.TransformColumnTypes(#"Merged queries", {{"zip", type text}, {"business_phone", Int64.Type}, {"city_account_number", Int64.Type}}),
  #"Expanded Dim_Industry" = Table.ExpandTableColumn(#"Changed column type", "Dim_Industry", {"industry_key"}, {"industry_key"}),
  #"Merged queries 1" = Table.NestedJoin(#"Expanded Dim_Industry", {"ownership_type"}, Dim_Ownership, {"ownership_type"}, "Dim_Ownership", JoinKind.LeftOuter),
  #"Expanded Dim_Ownership" = Table.ExpandTableColumn(#"Merged queries 1", "Dim_Ownership", {"ownership_key"}, {"ownership_key"}),
  #"Merged queries 2" = Table.NestedJoin(#"Expanded Dim_Ownership", {"street_address", "city", "state", "zip"}, Dim_Location, {"street_address", "city", "state", "zip"}, "Dim_Location", JoinKind.LeftOuter),
  #"Expanded Dim_Location" = Table.ExpandTableColumn(#"Merged queries 2", "Dim_Location", {"location_key"}, {"location_key"}),
  #"Removed columns" = Table.RemoveColumns(#"Expanded Dim_Location", {"naics_code", "naics_description", "ownership_type", "street_address", "city", "state", "zip"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns", {{"license_start_date", type date}, {"business_phone", type text}, {"city_account_number", type text}, {"business_age_formatted", type text}})
in
  #"Changed column type 1";
shared Dim_Industry_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "5c1df261-f430-4826-a433-7d3fe6e14f44"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_Industry", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Dim_Ownership_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "5c1df261-f430-4826-a433-7d3fe6e14f44"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_Ownership", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Dim_Location_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "5c1df261-f430-4826-a433-7d3fe6e14f44"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_Location", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Fact_Seattle_Businesses_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "5c1df261-f430-4826-a433-7d3fe6e14f44"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Fact_Businesses", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
