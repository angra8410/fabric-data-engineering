[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared Bronze_Ingestion_Seattle_Permits = let
    // 1. Bulk stream of Seattle Building Permits (192k+ records)
    SourceUrl = "https://data.seattle.gov/api/views/76t5-zqzr/rows.csv?accessType=DOWNLOAD",
    
    // 2. Stream directly into Fabric with CSV quote & delimiter handling
    Source = Csv.Document(
        Web.Contents(SourceUrl),
        [
            Delimiter = ",",
            Columns = 40,
            Encoding = 65001,
            QuoteStyle = QuoteStyle.Csv
        ]
    ),
    
    // 3. Promote headers
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    
    // 4. Select the actual CSV columns corresponding to your required fields
    #"Selected Columns" = Table.SelectColumns(#"Promoted Headers", {
        "PermitNum",
        "PermitTypeDesc",
        "PermitClass",
        "Description",
        "PermitClassMapped",
        "StatusCurrent",
        "AppliedDate",
        "IssuedDate",
        "EstProjectCost",
        "HousingUnitsAdded",
        "HousingUnitsRemoved",
        "ContractorCompanyName",
        "OriginalAddress1",
        "OriginalZip",
        "Latitude",
        "Longitude"
    }),

    // 5. Standardize column names to lowercase snake_case
    #"Renamed Columns" = Table.RenameColumns(#"Selected Columns", {
        {"PermitNum", "permit_num"},
        {"PermitTypeDesc", "permit_type"},
        {"PermitClass", "permit_class"},
        {"Description", "description"},
        {"PermitClassMapped", "category"},
        {"StatusCurrent", "status"},
        {"AppliedDate", "applied_date"},
        {"IssuedDate", "issued_date"},
        {"EstProjectCost", "est_project_cost"},
        {"HousingUnitsAdded", "housing_units_added"},
        {"HousingUnitsRemoved", "housing_units_removed"},
        {"ContractorCompanyName", "contractor_name"},
        {"OriginalAddress1", "address"},
        {"OriginalZip", "zip"},
        {"Latitude", "latitude"},
        {"Longitude", "longitude"}
    })
in
    #"Renamed Columns";
shared #"Silver_Transformation_Seattle_Permits (2)" = let
  Source = Bronze_Ingestion_Seattle_Permits,
  #"Replaced value" = Table.ReplaceValue(Source, "", "NONE", Replacer.ReplaceValue, {"permit_type"}),
  #"Replaced value 1" = Table.ReplaceValue(#"Replaced value", "", "No Description", Replacer.ReplaceValue, {"description"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Replaced value 1", {{"permit_num", type text}, {"permit_type", type text}, {"permit_class", type text}, {"description", type text}, {"category", type text}, {"status", type text}, {"applied_date", type date}, {"issued_date", type date}, {"est_project_cost", Int64.Type}, {"housing_units_added", Int64.Type}, {"housing_units_removed", Int64.Type}, {"contractor_name", type text}, {"address", type text}, {"zip", Int64.Type}, {"latitude", type number}, {"longitude", type number}}),
  #"Uppercased text" = Table.TransformColumns(#"Changed column type", {{"description", each Text.Upper(_), type nullable text}}),
  #"Added custom" = Table.AddColumn(#"Uppercased text", "status_category", each if List.Contains({"Completed", "Approved to Occupy"}, [status]) then "Completed"
else if List.Contains({"Issued", "Active", "Phase Issued", "Inspections Completed"}, [status]) then "Issued / Active"
else if List.Contains({"Canceled", "Closed", "Expired", "Withdrawn", "Denied"}, [status]) then "Closed / Cancelled"
else "Under Review"),
  #"Added custom 1" = Table.AddColumn(#"Added custom", "days_to_issue", each if [issued_date] <> null and [applied_date] <> null 
then Duration.Days([issued_date] - [applied_date]) 
else null),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Added custom 1", {{"days_to_issue", Int64.Type}}),
  #"Added custom 2" = Table.AddColumn(#"Changed column type 1", "is_issued", each if [issued_date] <> null then true else false),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Added custom 2", {{"is_issued", type logical}}),
  #"Replaced value 2" = Table.ReplaceValue(#"Changed column type 2", null, 0, Replacer.ReplaceValue, {"housing_units_added", "housing_units_removed"}),
  #"Replaced value 3" = Table.ReplaceValue(#"Replaced value 2", "", "Direct Owner / Unassigned", Replacer.ReplaceValue, {"contractor_name"}),
  #"Replaced value 4" = Table.ReplaceValue(#"Replaced value 3", null, 0, Replacer.ReplaceValue, {"est_project_cost"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Replaced value 4", {{"zip", type text}}),
  #"Replaced value 5" = Table.ReplaceValue(#"Changed column type 3", null, "Unknown", Replacer.ReplaceValue, {"zip"}),
  #"Uppercased text 1" = Table.TransformColumns(#"Replaced value 5", {{"permit_type", each Text.Upper(_), type nullable text}}),
  #"Uppercased text 2" = Table.TransformColumns(#"Uppercased text 1", {{"permit_class", each Text.Upper(_), type nullable text}}),
  #"Removed duplicates" = Table.Distinct(#"Uppercased text 2", {"permit_num"})
in
  #"Removed duplicates";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_Contractor_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Dim_Contractor = let
  Source = #"Silver_Transformation_Seattle_Permits (2)",
  #"Choose columns" = Table.SelectColumns(Source, {"contractor_name"}),
  #"Removed duplicates" = Table.Distinct(#"Choose columns", {"contractor_name"}),
  #"Added index" = Table.AddIndexColumn(#"Removed duplicates", "Index", 1, 1, Int64.Type),
  #"Renamed columns" = Table.RenameColumns(#"Added index", {{"Index", "contractor_key"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns", {"contractor_key", "contractor_name"})
in
  #"Reordered columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_PermitType_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Dim_PermitType = let
  Source = #"Silver_Transformation_Seattle_Permits (2)",
  #"Choose columns" = Table.SelectColumns(Source, {"permit_type", "permit_class", "category"}),
  #"Removed duplicates" = Table.Distinct(#"Choose columns", {"permit_type", "permit_class", "category"}),
  #"Added index" = Table.AddIndexColumn(#"Removed duplicates", "Index", 1, 1, Int64.Type),
  #"Renamed columns" = Table.RenameColumns(#"Added index", {{"Index", "permit_key"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns", {"permit_key", "permit_type", "permit_class", "category"})
in
  #"Reordered columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_Location_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Dim_Location = let
  Source = #"Silver_Transformation_Seattle_Permits (2)",
  #"Choose columns" = Table.SelectColumns(Source, {"address", "zip", "latitude", "longitude"}),
  #"Removed duplicates" = Table.Distinct(#"Choose columns", {"address", "zip", "latitude", "longitude"}),
  #"Added index" = Table.AddIndexColumn(#"Removed duplicates", "Index", 1, 1, Int64.Type),
  #"Renamed columns" = Table.RenameColumns(#"Added index", {{"Index", "Location_key"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns", {"Location_key", "address", "zip", "latitude", "longitude"})
in
  #"Reordered columns";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Dim_Date_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared Dim_Date = let
    // 1. Define calendar boundaries (covering all historical and active permit years)
    StartDate = #date(2000, 1, 1),
    EndDate = #date(2030, 12, 31),
    DayCount = Duration.Days(EndDate - StartDate) + 1,

    // 2. Generate continuous daily list and convert to table
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    #"Converted to Table" = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    #"Typed Date" = Table.TransformColumnTypes(#"Converted to Table", {{"Date", type date}}),

    // 3. Add Standard Calendar Attributes
    #"Added Year" = Table.AddColumn(#"Typed Date", "Year", each Date.Year([Date]), Int64.Type),
    #"Added MonthNumber" = Table.AddColumn(#"Added Year", "MonthNumber", each Date.Month([Date]), Int64.Type),
    #"Added MonthName" = Table.AddColumn(#"Added MonthNumber", "MonthName", each Date.MonthName([Date], "en-US"), type text),
    #"Added MonthShort" = Table.AddColumn(#"Added MonthName", "MonthShort", each Text.Start([MonthName], 3), type text),
    #"Added YearMonth" = Table.AddColumn(#"Added MonthShort", "YearMonth", each Date.ToText([Date], "yyyy-MM"), type text),
    #"Added YearMonthNumber" = Table.AddColumn(#"Added YearMonth", "YearMonthNumber", each [Year] * 100 + [MonthNumber], Int64.Type),
    #"Added Quarter" = Table.AddColumn(#"Added YearMonthNumber", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    #"Added YearQuarter" = Table.AddColumn(#"Added Quarter", "YearQuarter", each Text.From([Year]) & "-Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    #"Added DayOfMonth" = Table.AddColumn(#"Added YearQuarter", "DayOfMonth", each Date.Day([Date]), Int64.Type),
    #"Added DayOfWeekNumber" = Table.AddColumn(#"Added DayOfMonth", "DayOfWeekNumber", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    #"Added DayOfWeek" = Table.AddColumn(#"Added DayOfWeekNumber", "DayOfWeek", each Date.DayOfWeekName([Date], "en-US"), type text)
in
    #"Added DayOfWeek";
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "Fact_Permits_DataDestination", IsNewTarget = true], Settings = [Kind = "Manual", AllowCreation = true, ColumnSettings = [Mappings = {[SourceColumnName = "permit_num", DestinationColumnName = "permit_num"], [SourceColumnName = "description", DestinationColumnName = "description"], [SourceColumnName = "status", DestinationColumnName = "status"], [SourceColumnName = "applied_date", DestinationColumnName = "applied_date"], [SourceColumnName = "issued_date", DestinationColumnName = "issued_date"], [SourceColumnName = "est_project_cost", DestinationColumnName = "est_project_cost"], [SourceColumnName = "housing_units_added", DestinationColumnName = "housing_units_added"], [SourceColumnName = "housing_units_removed", DestinationColumnName = "housing_units_removed"], [SourceColumnName = "status_category", DestinationColumnName = "status_category"], [SourceColumnName = "days_to_issue", DestinationColumnName = "days_to_issue"], [SourceColumnName = "is_issued", DestinationColumnName = "is_issued"], [SourceColumnName = "contractor_key", DestinationColumnName = "contractor_key"], [SourceColumnName = "permit_key", DestinationColumnName = "permit_key"], [SourceColumnName = "Location_key", DestinationColumnName = "Location_key"]}], DynamicSchema = true, UpdateMethod = [Kind = "Replace"], TypeSettings = [Kind = "Table"]]]}]
shared Fact_Permits = let
  Source = #"Silver_Transformation_Seattle_Permits (2)",
  #"Merged queries" = Table.NestedJoin(Source, {"contractor_name"}, Dim_Contractor, {"contractor_name"}, "Dim_Contractor", JoinKind.LeftOuter),
  #"Expanded Dim_Contractor" = Table.ExpandTableColumn(#"Merged queries", "Dim_Contractor", {"contractor_key"}, {"contractor_key"}),
  #"Removed columns" = Table.RemoveColumns(#"Expanded Dim_Contractor", {"contractor_name"}),
  #"Merged queries 1" = Table.NestedJoin(#"Removed columns", {"permit_type", "permit_class", "category"}, Dim_PermitType, {"permit_type", "permit_class", "category"}, "Dim_PermitType", JoinKind.LeftOuter),
  #"Expanded Dim_PermitType" = Table.ExpandTableColumn(#"Merged queries 1", "Dim_PermitType", {"permit_key"}, {"permit_key"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Expanded Dim_PermitType", {"permit_type", "permit_class", "category"}),
  #"Merged queries 2" = Table.NestedJoin(#"Removed columns 1", {"address", "zip", "latitude", "longitude"}, Dim_Location, {"address", "zip", "latitude", "longitude"}, "Dim_Location", JoinKind.LeftOuter),
  #"Expanded Dim_Location" = Table.ExpandTableColumn(#"Merged queries 2", "Dim_Location", {"Location_key"}, {"Location_key"}),
  #"Removed columns 2" = Table.RemoveColumns(#"Expanded Dim_Location", {"address", "zip", "latitude", "longitude"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns 2", {{"status_category", type text}})
in
  #"Changed column type";
shared Dim_Contractor_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "1dd7223d-967c-4a14-a61d-3da892ad1ad6"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_Contractor", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Dim_PermitType_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "1dd7223d-967c-4a14-a61d-3da892ad1ad6"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_PermitType", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Dim_Location_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "1dd7223d-967c-4a14-a61d-3da892ad1ad6"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_Location", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Dim_Date_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "1dd7223d-967c-4a14-a61d-3da892ad1ad6"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Dim_Date", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared Fact_Permits_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = "4e77d624-be0f-4c9b-8df4-8d8061d10f1e"]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = "1dd7223d-967c-4a14-a61d-3da892ad1ad6"]}[Data],
  Navigation_3 = Navigation_2{[Id = "dbo", ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "Fact_Permits", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
