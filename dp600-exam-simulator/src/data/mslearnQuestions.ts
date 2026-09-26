import { Question } from '../types';

export const MS_LEARN_50_QUESTIONS: Question[] = [
  {
    "id": "mslearn-set2-q01",
    "type": "multiple_choice",
    "text": "You are developing a Microsoft Power BI semantic model.\n\nTwo tables in the data model are not connected in a physical relationship.\n\nYou need to establish a virtual relationship between the tables.\n\nWhich DAX function should you use?",
    "options": [
      {
        "id": "A",
        "text": "CROSSFILTER()"
      },
      {
        "id": "B",
        "text": "PATH()"
      },
      {
        "id": "C",
        "text": "TREATAS()"
      },
      {
        "id": "D",
        "text": "USERELATIONSHIP()"
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "DAX Calculations & Measures",
    "difficulty": "Medium",
    "explanation": "TREATAS() applies the result of a table expression as filters to columns from an unrelated table. USERELATIONSHIP() activates different physical relationships between tables during a query execution. CROSSFILTER() defines the cross filtering direction of a physical relationship. PATH() returns a string of all the members in the column hierarchy.\n\nTREATAS function - DAX | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - DAX Calculations & Measures",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q02",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a workspace named Workspace1. Workspace1 is assigned to an F64 capacity and contains a lakehouse. The lakehouse contains one billion historical sales records and receives up to 10,000 new or updated sales records throughout the day at 15-minute intervals.\n\nYou plan to build a custom Microsoft Power BI semantic model and Power BI reports from the data. The solution must provide the best report performance while supporting near-real-time (NRT) data reporting.\n\nWhich Power BI semantic model storage mode should you use?",
    "options": [
      {
        "id": "A",
        "text": "Direct Lake"
      },
      {
        "id": "B",
        "text": "Import and Direct Lake combined"
      },
      {
        "id": "C",
        "text": "DirectQuery"
      },
      {
        "id": "D",
        "text": "Import"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Direct Lake Storage Mode",
    "difficulty": "Medium",
    "explanation": "Direct Lake storage mode provides NRT access to data, while providing performance close to Import storage mode and much better performance than DirectQuery. DirectQuery provides NRT access to data, but queries can run slowly when working with large datasets. Import produces fast performance; however, it requires data to be loaded to the memory of Power BI and will not provide NRT. Direct Lake tables cannot currently be mixed with other table types, such as Import, DirectQuery, or Dual, in the same model. Composite models are not yet supported.\n\nLearn about Direct Lake in Power BI and Microsoft Fabric - Power BI | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Direct Lake Storage Mode",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q03",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace and a Microsoft Power BI semantic model that contains the following tables:\n\nSales (ProductKey,CustomerKey,DateKey,SalesAmont)\nProduct (ProductKey,ProductName,ProductCategory)\nDate (DateKey,Date,Month,Year)\nCustomer (CustomerKey,CustmomerName,CustomerCity)\nThe Product table has a 1-to-many relationship with the Sales table based on ProductKey.\n\nThe Customer table has a 1-to-many relationship with the Sales table based on CustomerKey.\n\nThe Date table has a 1-to-many relationship with the Sales table based on DateKey.\n\nYou need to create a Power BI report so that end users can use a one column chart to analyze SalesAmount by ProductCategory or Year or CustomerCity. The solution must minimize development effort.\n\nWhat should you do?",
    "options": [
      {
        "id": "A",
        "text": "Add three bar chart visuals to the report, one by each ProductCategory, Year, and CustomerCity. Overlay the charts and use buttons and bookmarks to display one at a time."
      },
      {
        "id": "B",
        "text": "Create a custom visual that has custom buttons with ProductCategory, Year, and CustomerCity."
      },
      {
        "id": "C",
        "text": "Set up a Fields parameter with ProductCategory, Year, and CustomerCity. Use the Fields parameter in the visual."
      },
      {
        "id": "D",
        "text": "Set up three identical report pages, each with a bar chart by either ProductCategory, Year, and CustomerCity. Set up buttons and bookmarks to navigate between the pages."
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Field Parameters",
    "difficulty": "Medium",
    "explanation": "While you can use bookmarks to navigate between report pages or change the visibility of visuals, using the Fields parameter is a much easier and more efficient way of allowing an end-user to change the fields on a visual. Developing a custom visual with built-in buttons to switch the items on the axis, involves extra development effort.\n\nUse parameters to visualize variables - Power BI | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Field Parameters",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q04",
    "type": "multiple_choice",
    "text": "You have a Microsoft Power BI report that contains a table visual. The visual contains three DAX measures named Sales, Units, and Customers.\n\nYou need to apply logic-based DAX formatting to the Sales measure. The solution must minimize administrative effort and prevent the modification of the other two measures.\n\nHow should you apply the logic?",
    "options": [
      {
        "id": "A",
        "text": "Use calculation group measure formatting."
      },
      {
        "id": "B",
        "text": "Use conditional formatting."
      },
      {
        "id": "C",
        "text": "Use dynamic measure formatting."
      },
      {
        "id": "D",
        "text": "Use the fields parameter."
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "DAX Calculations & Measures",
    "difficulty": "Medium",
    "explanation": "Dynamic measure formatting is the simplest and most effective way to add logic-based formatting to a single measure. Calculation groups can add logic-based formatting, but these are applied at the visual, page, or report level, and cannot be easily added to single measures.\n\nCreate dynamic format strings for measures in Power BI Desktop - Power BI | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - DAX Calculations & Measures",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q05",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a workspace named Workspace1. Workspace1 is assigned to an F64 Fabric capacity and contains a warehouse.\n\nYou are working on a custom Microsoft Power BI semantic model that sources data from the warehouse tables. You apply optimization best practices to reduce the model size. You estimate that once the model is published to the Power BI service and fully loaded, it will approach 50 GB.\n\nWhich option should you configure to enable the semantic model to refresh in the Power BI service?",
    "options": [
      {
        "id": "A",
        "text": "Large semantic model storage format"
      },
      {
        "id": "B",
        "text": "Parameters"
      },
      {
        "id": "C",
        "text": "Query Scale-out"
      },
      {
        "id": "D",
        "text": "Scheduled refresh"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Semantic Model Optimization",
    "difficulty": "Medium",
    "explanation": "The large semantic model storage format can be enabled from the Power BI service from the semantic model settings. It will allow data to grow beyond the 10-GB limit for Power BI premium capacities or Fabric capacities of F64 or higher. The other options do not change the default limit of 10 GB after compression.\n\nDesign scalable semantic models",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Semantic Model Optimization",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q06",
    "type": "multiple_choice",
    "text": "You are working on a Microsoft Power BI report based on a Power BI semantic model that contains the following tables:\n\nSales (SalesAmount,OrderDateKey,ShipDateKey)\nDate (DateKey, Date, Month, Quarter, Year)\nYou have connected the Date table to the Sales table on DateKey to OrderDateKey with a 1-to-many active relationship. You have connected the Date table to the Sales table on DateKey to ShipDateKey with a 1-to-many inactive relationship.\n\nYou need to create two measures that calculate Sales Amount Ordered and Sales Amount Shipped so that you can place them side-by-side in a table visual and analyze them by Year.\n\nHow should you create the measures?",
    "options": [
      {
        "id": "A",
        "text": "Sales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)\n\nSales Ordered =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[OrderDateKey] )\n)"
      },
      {
        "id": "B",
        "text": "Sales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    USERELATIONSHIP ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)\n\nSales Ordered =\nSUM ( 'Sales'[SalesAmount] )"
      },
      {
        "id": "C",
        "text": "Sales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)\n\nSales Ordered =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    RELATED ( 'Date'[DateKey], 'Sales'[OrderDateKey] )\n)"
      },
      {
        "id": "D",
        "text": "Sales Ordered =\nSUM ( 'Sales'[SalesAmount] )\n\nSales Shipped =\nCALCULATE (\n    SUM ( 'Sales'[SalesAmount] ),\n    USERELATIONSHIP ( 'Date'[DateKey], 'Sales'[ShipDateKey] )\n)"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "DAX Calculations & Measures",
    "difficulty": "Medium",
    "explanation": "In this example, the Date dimension is a role-playing dimension. Sales has an active relationship with Date based on OrderedDate, which means that Sales Amount based on Order Date can be calculated by a simple SUM function. Sales has an inactive relationship with Date based on ShippedDate. To create calculations based on inactive relationships, you can use the USERELATIONSHIP function and specify the two columns that are used in the existing inactive relationship. The RELATED function returns a value from \"one\" side of a relationship.\n\nActive vs inactive relationship guidance - Power BI | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - DAX Calculations & Measures",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q07",
    "type": "multiple_choice",
    "text": "You are designing a dimension table named dimCustomer that will be used to analyze historical sales data by customer zip code. The table will be joined to a table named FactSales on a column named CustomerKey to report historical sales data by customer zip code.\n\nThe sales data must be reported based on the zip codes of customers at the time of the sale, not their most recent zip code.\n\nYou need to design dimCustomer to contain a fixed number of columns.\n\nWhich type of dimension should you choose for dimCustomer?",
    "options": [
      {
        "id": "A",
        "text": "type 0 slowly changing dimension (SCD)"
      },
      {
        "id": "B",
        "text": "type 1 slowly changing dimension (SCD)"
      },
      {
        "id": "C",
        "text": "type 2 slowly changing dimension (SCD)"
      },
      {
        "id": "D",
        "text": "type 3 slowly changing dimension (SCD)"
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dimensional Modeling (SCD)",
    "difficulty": "Medium",
    "explanation": "Type 0 SCD attributes never change and will not fit the requirement. Type 1 SCD overwrites the changes and historical analysis of data based on the zip code at the time of the sales will be impossible. Type 2 SCD will keep track of historical data by adding new records with new keys whenever an attribute changes. Type 3 SCD adds new columns to a table for attribute changes.\n\nExplore data load strategies - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dimensional Modeling (SCD)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q08",
    "type": "multiple_choice",
    "text": "You have a Fabric lakehouse.\n\nYou are building a semantic model for a sales dataset.\n\nReport users require that visuals always reflect the latest data in the lakehouse.\n\nYou need to configure the semantic model.\n\nWhich storage mode should you use?",
    "options": [
      {
        "id": "A",
        "text": "Composite model"
      },
      {
        "id": "B",
        "text": "Direct Lake"
      },
      {
        "id": "C",
        "text": "DirectQuery"
      },
      {
        "id": "D",
        "text": "Import"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Direct Lake Storage Mode",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n3.1 Design and build semantic models\n\nWhat This Item Tests:\n\nChoose a storage mode\n\nAdditional Reading:\n\nChoose the best storage mode\nTable storage mode in Power BI semantic models\nDesign scalable semantic models\nRationale:\n\nDirect Lake enables a semantic model to query Delta tables stored in OneLake directly, without importing data into the model and without relying on scheduled refresh. Queries read the latest data from the lakehouse while maintaining high performance because the engine reads the Delta files directly. Import storage mode loads data into the semantic model and requires a refresh to reflect the changes. DirectQuery sends queries to the underlying data source at runtime but is typically used for relational sources rather than directly scanning Delta tables in OneLake. Composite models combine storage modes but are not required when the goal is to query lakehouse Delta tables directly without importing data.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Direct Lake Storage Mode",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q09",
    "type": "multiple_choice",
    "text": "You have an Azure SQL database.\n\nYou have a Microsoft Power BI report connected to a semantic model that uses a DirectQuery connection to the database.\n\nYou need to reduce the number of queries sent to the database when a user is interacting with the report by using filters and/or slicers.\n\nWhat should you do?",
    "options": [
      {
        "id": "A",
        "text": "Add apply buttons to all the basic filters."
      },
      {
        "id": "B",
        "text": "Add Top N filters to all the visuals."
      },
      {
        "id": "C",
        "text": "Change default visual interaction from cross highlighting to cross filtering."
      },
      {
        "id": "D",
        "text": "Enable automatic page refresh for each report page."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "DirectQuery Performance",
    "difficulty": "Medium",
    "explanation": "Adding apply buttons will pause all requests to the Azure SQL database until you finalize your filter and/or slicer selections. Then a single request can be sent once the apply button is selected. The other options will not change the number of unique query requests sent to the database.\n\nCreate Apply all and Clear all slicers buttons in reports - Power BI | Microsoft Learn\n\nDirectQuery optimization scenarios with the Optimize ribbon in Power BI Desktop - Power BI | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - DirectQuery Performance",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q10",
    "type": "multiple_choice",
    "text": "You have a Microsoft Power BI semantic model assigned to you for ownership and maintenance.\n\nYou need to perform an audit on the model to identify and resolve potential performance or design issues.\n\nWhich Tabular Editor tool should you use?",
    "options": [
      {
        "id": "A",
        "text": "Best Practices Analyzer"
      },
      {
        "id": "B",
        "text": "Perspective Editor"
      },
      {
        "id": "C",
        "text": "TOM Explorer"
      },
      {
        "id": "D",
        "text": "Vertipaq Analyzer"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Tabular Editor & Best Practice Analyzer",
    "difficulty": "Medium",
    "explanation": "Only Best Practices Analyzer lets you specify a ruleset to review the model and multiple options for quick fixes by using C# scripts.\n\nExternal tools in Power BI Desktop - Power BI | Microsoft Learn\n\nBest Practice Analyzer | Tabular Editor Documentation",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Tabular Editor & Best Practice Analyzer",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q11",
    "type": "multiple_choice",
    "text": "You have a Fabric semantic model in Import storage mode. The model contains a table named Sales. Sales contains three years of data and a column named TransactionDate (datetime).\n\nRefreshing the table takes more than three hours.\n\nYou need to ensure that scheduled refresh processes only new and updated rows.\n\nWhat should you do in Microsoft Power BI Desktop?",
    "options": [
      {
        "id": "A",
        "text": "Create monthly partitions for Sales."
      },
      {
        "id": "B",
        "text": "Enable large semantic model storage format."
      },
      {
        "id": "C",
        "text": "Convert the semantic model storage mode to DirectQuery."
      },
      {
        "id": "D",
        "text": "In Power Query, configure incremental refresh for the table."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Semantic Model Optimization",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n3.2 Optimize enterprise-scale semantic models\n\nWhat This Item Tests:\n\nImplement incremental refresh for semantic models\n\nAdditional Reading:\n\nData refresh in Power BI\nRationale:\n\nIncremental refresh requires defining the RangeStart and RangeEnd parameters, applying them as a filter on the date column in Power Query, and configuring an incremental refresh policy for the table. This enables refresh operations to process only new and changed partitions. Enabling large semantic model storage format increases model capacity but does not change the refresh behavior. Creating partitions manually does not enable service-managed incremental refresh. Converting the model to DirectQuery removes the import refresh scenario rather than optimizing it.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Semantic Model Optimization",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q12",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse named Lakehouse1.\n\nA SELECT query from a managed Delta table in Lakehouse1 takes longer than expected to complete. The table receives new records daily and must keep change history for seven days.\n\nYou notice that the table contains 1,000 Parquet files that are each 1 MB.\n\nYou need to improve query performance and reduce storage costs.\n\nWhat should you do from Lakehouse explorer?",
    "options": [
      {
        "id": "A",
        "text": "Manually delete any files that have a creation date that is older than seven days."
      },
      {
        "id": "B",
        "text": "Select Maintenance and run the OPTIMIZE command."
      },
      {
        "id": "C",
        "text": "Select Maintenance and run the OPTIMIZE command as well as the VACUUM command with a retention policy of seven days."
      },
      {
        "id": "D",
        "text": "Select Maintenance and run the VACUUM command with a retention policy of seven days."
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Delta Lake (OPTIMIZE & VACUUM)",
    "difficulty": "Medium",
    "explanation": "The ideal file size for Fabric engines is between 128 MB and 1 GB. This improves query performance since it reduces the need to scan numerous small files. OPTIMIZE compacts and rewrites the files into fewer larger files. VACUUM removes older Parquet files that are no longer in use. While this reduces the storage size, it by itself does not reduce the number of active files that must be scanned.\n\nUse table maintenance feature to manage delta tables in Fabric - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Delta Lake (OPTIMIZE & VACUUM)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q13",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a workspace named Workspace1. Workspace1 contains a lakehouse named Lakehouse1.\n\nYou open a notebook in Lakehouse1 and attach it to a Spark session.\n\nYou plan to start a new notebook in Lakehouse1 and attach it to the same Spark session. However, you notice that the New high concurrency session option is unavailable, and the only available option is Standard session.\n\nYou need to ensure that the high concurrency mode for notebooks is enabled.\n\nWhere can you check the high concurrency mode?",
    "options": [
      {
        "id": "A",
        "text": "Fabric tenant settings"
      },
      {
        "id": "B",
        "text": "Lakehouse settings"
      },
      {
        "id": "C",
        "text": "Notebook properties from the Edit menu"
      },
      {
        "id": "D",
        "text": "Workspace settings"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "PySpark & Notebooks",
    "difficulty": "Medium",
    "explanation": "The high concurrency mode for Fabric notebooks is set at the workspace level. It is on by default; however, it can be turned off in scenarios where notebooks require dedicated compute resources.\n\nConfigure high concurrency mode for notebooks - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - PySpark & Notebooks",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q14",
    "type": "multiple_choice",
    "text": "You have a DAX measure that contains the following code.\n\nVariance KPI =\n\nIF( [Variance] > 0.80, \"Amazing!\", IF( [Variance] > 0.60, \"Good\", \"Bad\" ) )\n\nYou need to optimize the measure so that it will calculate faster.\n\nWhich code should you use?",
    "options": [
      {
        "id": "A",
        "text": "SWITCH( TRUE(),\n    [Variance] > 0.80, \"Amazing!\",\n    [Variance] > 0.60, \"Good\",\n    \"Bad\"\n)"
      },
      {
        "id": "B",
        "text": "VAR Calc = [Variance]\nRETURN\nSWITCH(TRUE(),\n    Calc > 0.80, \"Amazing!\",\n    Calc > 0.60, \"Good\",\n    \"Bad\"\n)"
      },
      {
        "id": "C",
        "text": "VAR Calc = [Variance]\nRETURN\nSWITCH( TRUE(),\n    Calc > 0.80, \"Amazing!\",\n    [Variance] > 0.60, \"Good\",\n    \"Bad\"\n)"
      },
      {
        "id": "D",
        "text": "VAR Calc = [Variance]\nRETURN\nSWITCH( TRUE(),\n    [Variance] > 0.80, \"Amazing!\",\n    [Variance] > 0.60, \"Good\",\n    \"Bad\"\n)"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "DAX Calculations & Measures",
    "difficulty": "Medium",
    "explanation": "Declaring the [Variance] measure as a VAR will cache the measure and only load it once. This reduces the amount of processing and data loading that the measure must do and increases its speed. All other formulas do not leverage the VAR for best performance.\n\nUse variables to improve your DAX formulas - DAX | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - DAX Calculations & Measures",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q15",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace that contains a lakehouse named Lakehouse1.\n\nYou need to create a data pipeline and ingest data into Lakehouse1 by using the Copy data activity.\n\nWhich properties on the General tab are mandatory for the activity?",
    "options": [
      {
        "id": "A",
        "text": "Name and Retry only"
      },
      {
        "id": "B",
        "text": "Name and Timeout only"
      },
      {
        "id": "C",
        "text": "Name only"
      },
      {
        "id": "D",
        "text": "Name, Timeout, and Retry"
      },
      {
        "id": "E",
        "text": "Retry only"
      },
      {
        "id": "F",
        "text": "Timeout only"
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Data Ingestion & Pipelines",
    "difficulty": "Medium",
    "explanation": "For the Copy Data Activity, only the name must be defined on the General tab. All the other properties are optional.\n\nLakehouse tutorial - Ingest data into the lakehouse - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Data Ingestion & Pipelines",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q16",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a workspace named Workspace1. Workspace1 contains two data warehouses named Warehouse1 and Warehouse2. Warehouse1 contains HR data. Warehouse2 contains sales data.\n\nYou are analyzing the sales data in Warehouse2 by using the SQL analytics endpoint.\n\nYou need to recommend a solution that utilizes a query to combine the sales data from Warehouse2 with the HR data from Warehouse1. The solution must minimize development effort and data movement.\n\nWhat should you recommend?",
    "options": [
      {
        "id": "A",
        "text": "Set up a Dataflow Gen2 query to copy the HR data from Warehouse1 to Warehouse2 and reference the copied data in the query."
      },
      {
        "id": "B",
        "text": "Set up a pipeline that uses a Copy data activity to copy the HR data from Warehouse1 to Warehouse2 and reference the copied data in the query."
      },
      {
        "id": "C",
        "text": "Use a Spark notebook to copy the HR data from Warehouse1 to Warehouse2 and reference the copied data in the query."
      },
      {
        "id": "D",
        "text": "Use cross-database querying between Warehouse1 and Warehouse2."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Fabric Warehouse & T-SQL",
    "difficulty": "Medium",
    "explanation": "You can query data across Fabric warehouses by using cross-database querying. While you can copy the data from one warehouse to another, this involves moving data.\n\nUnderstand data warehouses in Fabric - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Fabric Warehouse & T-SQL",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q17",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse named Lakehouse1.\n\nYou have a large 1 TB dataset in an external data source.\n\nYou need to recommend a method to ingest the dataset into Lakehouse1. The solution must provide the highest throughput. The solution must be suitable for developers who prefer the low-code/no-code option.\n\nWhat should you recommend?",
    "options": [
      {
        "id": "A",
        "text": "Use Dataflow Gen2 to import the files and load them to a table."
      },
      {
        "id": "B",
        "text": "Use notebooks and PySpark to load the data to a DataFrame and write the results to a location in Lakehouse1."
      },
      {
        "id": "C",
        "text": "Use Lakehouse explorer to upload the files directly."
      },
      {
        "id": "D",
        "text": "Use the Copy data activity of a pipeline to copy the data."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Data Ingestion & Pipelines",
    "difficulty": "Medium",
    "explanation": "Dataflow Gen2 is a low code / no code option to ingest data but for straight bulk copy of data is not as efficient for large data size as the copy data activity.\nUsing Lakehouse explorer allows for low code no code but is not good for high throughput and also assumes the data is in files in the first part but the external source has not been defined.\nNotebooks are efficient however these are not a low code/no code option.\n\nOptions to get data into the Lakehouse – Microsoft Fabric | Microsoft Learn\n\nIngest data with Microsoft Fabric - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Data Ingestion & Pipelines",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q18",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse named Lakehouse1.\n\nYou need to ingest data into Lakehouse1 from a large Azure SQL Database table that contains more than 500 million records. The data must be ingested without applying any additional transformations. The solution must minimize costs and administrative effort.\n\nWhat should you use to ingest the data?",
    "options": [
      {
        "id": "A",
        "text": "a pipeline with the Copy data activity"
      },
      {
        "id": "B",
        "text": "a SQL stored procedure"
      },
      {
        "id": "C",
        "text": "Dataflow Gen2"
      },
      {
        "id": "D",
        "text": "notebooks"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Data Ingestion & Pipelines",
    "difficulty": "Medium",
    "explanation": "When ingesting a large data source without applying transformations, the recommended method is to use the Copy data activity in pipelines. Notebooks are recommended for complex data transformations, whereas Dataflow Gen2 is suitable for smaller data and/or specific connectors. Stored procedures are not available in lakehouse they are a warehouse feature so no a valid option.\n\nOptions to get data into the Lakehouse - Microsoft Fabric | Microsoft Learn\n\nIngest data with Microsoft Fabric - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Data Ingestion & Pipelines",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q19",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse named Lakehouse1.\n\nA notebook named Notebook1 is used to ingest data from an external data source named Externaldata1 into Lakehouse1. A notebook named Notebook2 is used to transform the data in the lakehouse.\n\nYou create a pipeline named Pipeline1 to first run Notebook1 to ingest data then on success Notebook2 to transform.\n\nYou need to configure a schedule that runs the process daily at 7:00AM.\n\nOn which object should you configure the schedule?",
    "options": [
      {
        "id": "A",
        "text": "Externaldata1"
      },
      {
        "id": "B",
        "text": "Lakehouse1"
      },
      {
        "id": "C",
        "text": "Notebook1"
      },
      {
        "id": "D",
        "text": "Pipeline1"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Data Ingestion & Pipelines",
    "difficulty": "Medium",
    "explanation": "Scheduling on the external datasource does not affect the load. Lakehouse1 doesn't have scheduling.\nNotebook1 has scheduling but it is a per notebook configuration and will not ensure both notebooks run one after the other. Pipeline scheduling allows scheduling and running both.\n\nData pipeline runs - Microsoft Fabric | Microsoft Learn\n\nUse Data Factory pipelines in Microsoft Fabric - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Data Ingestion & Pipelines",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q20",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse named Lakehouse1.\n\nYou have forecast data stored in Azure Data Lake Storage Gen2.\n\nYou plan to ingest the forecast data into Lakehouse1. The data is already formatted, and you do NOT need to apply any further data transformations. The solution must minimize development effort and costs.\n\nWhich method should you recommend to efficiently ingest the data?",
    "options": [
      {
        "id": "A",
        "text": "First, download the data to your computer, and then use Lakehouse explorer to upload it to Lakehouse1."
      },
      {
        "id": "B",
        "text": "Use a Spark notebook."
      },
      {
        "id": "C",
        "text": "Use Dataflow Gen2."
      },
      {
        "id": "D",
        "text": "Use the Copy activity in a pipeline."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Data Ingestion & Pipelines",
    "difficulty": "Medium",
    "explanation": "The Copy data activity should be used when you must copy data directly between a supported source and a destination without applying any transformations. Dataflow Gen2 or Spark notebooks should be used when you must apply data transformations. Downloading data to your local computer and uploading it is inefficient and will incur unnecessary egress charges.\n\nUse the Copy Data activity - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Data Ingestion & Pipelines",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q21",
    "type": "multiple_choice",
    "text": "You have an Azure SQL database that contains fact table named UnpostedSales. UnpostedSales contains unposted payments.\n\nEach day payment records from the previous day are automatically truncated from the UnpostedSales table and replaced with today's payment records.\n\nYou need to use a Dataflow Gen2 query to import the data into either a lakehouse or a warehouse. The solution must ensure that all current and historical records are maintained.\n\nWhat should you do to retain current and historical records during a refresh?",
    "options": [
      {
        "id": "A",
        "text": "Configure the refresh to append data for the query."
      },
      {
        "id": "B",
        "text": "Configure the refresh to replace data for the query."
      },
      {
        "id": "C",
        "text": "Use Optimize to apply V-order for the query."
      },
      {
        "id": "D",
        "text": "Ensure that query folding occurs for the whole query."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "Appending data for the query will add new rows each time a refresh occurs, ensuring that both historical and current records are kept and combined. All other options will not keep the historical records.\n\nLakehouse Load to Delta Lake tables - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q22",
    "type": "multiple_choice",
    "text": "You have a Fabric lakehouse that contains a managed Delta table named Product.\n\nYou plan to analyze the data by using a Fabric notebook and PySpark.\n\nYou load the data to a DataFrame by running the following code.\n\ndf = spark.sql(\"SELECT * FROM Product\")\n\nYou need to display the top 100 rows from the DataFrame.\n\nWhich PySpark command should you run?",
    "options": [
      {
        "id": "A",
        "text": "describe(df.limit(100))"
      },
      {
        "id": "B",
        "text": "df.describe(100)"
      },
      {
        "id": "C",
        "text": "df.printSchema(100)"
      },
      {
        "id": "D",
        "text": "display(df.limit(100))"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "PySpark & Notebooks",
    "difficulty": "Medium",
    "explanation": "The display PySpark method is used to display data in a DataFrame. To limit the data displayed, limit(100) can be specified.\n\nWork with data in a Spark dataframe - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - PySpark & Notebooks",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q23",
    "type": "multiple_choice",
    "text": "You have a Fabric lakehouse that contains a Fabric notebook. The notebook contains a PySpark DataFrame with order data from a source system. The DataFrame contains a column named InvoiceDate.\n\nYou need to add a column named InvoiceYear that will hold only the Year value of the InvoiceDate.\n\nWhich PySpark method should you use?",
    "options": [
      {
        "id": "A",
        "text": "alias"
      },
      {
        "id": "B",
        "text": "union"
      },
      {
        "id": "C",
        "text": "withColumn"
      },
      {
        "id": "D",
        "text": "withMetadata"
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "PySpark & Notebooks",
    "difficulty": "Medium",
    "explanation": "The method to add new columns to a DataFrame is withColumn.\n\nLakehouse tutorial - Prepare and transform data in the lakehouse - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - PySpark & Notebooks",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q24",
    "type": "multiple_choice",
    "text": "You have a Fabric warehouse.\n\nYou have an Azure SQL database that contains a fact table named Sales and a second table named ExceptionRecords. Both tables contain a unique key column named Record ID.\n\nYou plan to ingest the Sales table into the warehouse.\n\nYou need to use Dataflow Gen2 to configure a merge type to ensure that the Sales table excludes any records found in the ExceptionRecords table, and that query folding is maintained.\n\nWhich applied steps should you use?",
    "options": [
      {
        "id": "A",
        "text": "Merge (inner join) applied step, and then the expand columns applied step"
      },
      {
        "id": "B",
        "text": "Merge (left anti join) applied step, and then the expand columns applied step"
      },
      {
        "id": "C",
        "text": "Merge (left anti join) applied step, delete the “expand columns” column"
      },
      {
        "id": "D",
        "text": "Merge (right anti join) applied step, and then the expand columns applied step"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "A left anti join ensures that only rows not found in the ExceptionRecords table are loaded, and the expand columns step ensures that query folding is maintained for performance.\n\nMerge queries overview - Power Query | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q25",
    "type": "multiple_choice",
    "text": "You have a Parquet file named Customers.parquet uploaded to the Files section of a Fabric lakehouse.\n\nYou plan to use Data Wrangler to view basic summary statistics for the data before you load it to a Delta table.\n\nYou open a notebook in the lakehouse.\n\nYou need to load the data to a pandas DataFrame.\n\nWhich PySpark code should you run to complete the task?",
    "options": [
      {
        "id": "A",
        "text": "df = pandas.read_parquet(\"/lakehouse/default/Files/Customers.parquet\")"
      },
      {
        "id": "B",
        "text": "df = pandas.read_parquet(\"/lakehouse/Files/Customers.parquet\")"
      },
      {
        "id": "C",
        "text": "import pandas as pd\ndf = pd.read_parquet(\"/lakehouse/default/Files/Customers.parquet\")"
      },
      {
        "id": "D",
        "text": "import pandas as pd\ndf = pd.read_parquet(\"/lakehouse/Files/Customers.parquet\")"
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "PySpark & Notebooks",
    "difficulty": "Medium",
    "explanation": "To load data to a pandas DataFrame, you must first import the pandas library by running import pandas as pd. Pandas DataFrames use the File API Path vs. the File relative path that Spark uses. The File API Path has the format of lakehouse/default/Files/Customers.parquet.\n\nAccelerate data prep with Data Wrangler - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - PySpark & Notebooks",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q26",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse.\n\nYou are creating a notebook to explore the data in the lakehouse.\n\nYou need to create a query to find the total number of records in the fact table for every individual product. The displayed results must be sorted in descending order.\n\nHow should you structure the query?",
    "options": [
      {
        "id": "A",
        "text": "df.groupBy(\"ProductKey\").count().sort(\"count\", descending=True).show()"
      },
      {
        "id": "B",
        "text": "df.groupBy(\"ProductKey\").count().sort(\"ProductKey\", descending=True).show()"
      },
      {
        "id": "C",
        "text": "df.groupBy(\"ProductKey\").count().sort(\"count\").show()"
      },
      {
        "id": "D",
        "text": "df.groupBy(\"ProductKey\").count().sort(\"ProductKey\").show()"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "PySpark & Notebooks",
    "difficulty": "Medium",
    "explanation": "GroupBy will group the data per ProductKey, and then count will return the total number of records for each ProductKey. Next, we sort the data per total number of records in descending order, and finally display the DataFrame results.\n\nUse Apache Spark in Microsoft Fabric - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - PySpark & Notebooks",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q27",
    "type": "multi_select",
    "text": "You are profiling the data stored in a Fabric lakehouse.\n\nYou run the following statement.\n\ndf.describe().show()\n\nWhich three functions will be included in the results for the numeric data? Each correct answer presents a complete solution.",
    "options": [
      {
        "id": "A",
        "text": "AVG"
      },
      {
        "id": "B",
        "text": "COUNT"
      },
      {
        "id": "C",
        "text": "DISTINCTCOUNT"
      },
      {
        "id": "D",
        "text": "MEAN"
      },
      {
        "id": "E",
        "text": "STDDEV (standard deviation)"
      },
      {
        "id": "F",
        "text": "TOP"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": [
      "B",
      "D",
      "E"
    ],
    "selectCount": 3,
    "domain": "domain2",
    "topic": "PySpark & Notebooks",
    "difficulty": "Medium",
    "explanation": "describe is used to generate descriptive statistics of the DataFrame. For numeric data, results include COUNT*,* MEAN*,* STD*,* MIN*,* and MAX, while for object data it will also include TOP, UNIQUE, and FREQ.\n\nExplore and transform data in a lakehouse - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - PySpark & Notebooks",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q28",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace. The workspace contains a Dataflow Gen2 query that displays dimensional product information. The query table contains a column named Product ID/Name that is a concatenation of Product ID and Product Name values.\n\nYou need to use an applied step in Microsoft Power Query Editor to create a new column for Product ID and Product Name. The solution must use a single command to create two new columns and remove the original combined (Product ID/Name) column.\n\nWhich applied step should you use?",
    "options": [
      {
        "id": "A",
        "text": "Add Column From Example"
      },
      {
        "id": "B",
        "text": "Conditional Column"
      },
      {
        "id": "C",
        "text": "Replace Values"
      },
      {
        "id": "D",
        "text": "Split Column"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "Split Column is the only applied step in Power Query Editor that will both remove the source column and create two new columns by using just a single command/applied step.\n\nSplit columns by delimiter - Power Query | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q29",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace that contains a Microsoft Power BI report.\n\nYou need to modify the column names in the Power BI report without changing the original names in the underlying Delta table.\n\nWhich warehouse object should you create?",
    "options": [
      {
        "id": "A",
        "text": "columnstore index"
      },
      {
        "id": "B",
        "text": "schema"
      },
      {
        "id": "C",
        "text": "table-valued function"
      },
      {
        "id": "D",
        "text": "view"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Fabric Warehouse & T-SQL",
    "difficulty": "Medium",
    "explanation": "A view provides a convenient way to encapsulate additional query logic, such as renaming columns, filtering, aggregating, etc. Views contain only a query definition and do not change the underlying tables.\n\nCREATE VIEW (Transact-SQL) - SQL Server | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Fabric Warehouse & T-SQL",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q30",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace that contains a Microsoft Power BI report named Sales.\n\nYou plan to use Dataflow Gen2 to add an additional column to the report. The new column must be based on the unit price of a product. Any product that has a unit price that is greater than $1,000 must be labeled as High, while any product that has a unit price that is less than $1,000 must be labeled as Regular.\n\nWhat should you select on the Add column tab in Power Query Editor?",
    "options": [
      {
        "id": "A",
        "text": "Duplicate column"
      },
      {
        "id": "B",
        "text": "Conditional column"
      },
      {
        "id": "C",
        "text": "Index column"
      },
      {
        "id": "D",
        "text": "Merge columns"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "The Conditional column option enables adding new columns whose values will be based on one or more conditions applied to the existing table columns.\n\nAdd a conditional column - Power Query | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q31",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a lakehouse named Lakehouse1.\n\nYou plan to use Dataflow Gen2 to ingest and transform data from an Azure SQL Database into Lakehouse1.\n\nWhich language should you use to transform the data in the dataflow?",
    "options": [
      {
        "id": "A",
        "text": "DAX"
      },
      {
        "id": "B",
        "text": "M"
      },
      {
        "id": "C",
        "text": "SQL"
      },
      {
        "id": "D",
        "text": "XML"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "When ingesting data by using Dataflow Gen2, you get the same surface area as in Microsoft Power Query. This assumes that you will use the M language for data manipulation, no matter which data source you are connecting to.\n\nExplore Dataflows (Gen2) in Microsoft Fabric - Training | Microsoft Learn\n\nWhat is Power Query? - Power Query | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q32",
    "type": "multiple_choice",
    "text": "You have a Fabric warehouse that contains the following tables:\n\nSales (DateKey, ProductKey, SalesAmount)\nProduct(ProductKey,ProductName)\nDate (DateKey, Day, Month, Year)\nThere is a 1-to-many relationship between the Date and Sales tables on DateKey. There is a 1-to-many relationship between the Product and Sales tables on ProductKey.\n\nYou begin to write the following SQL query to analyze the Sales data by ProductName and Year, but only for products that have a yearly SalesAmount of more than $10000.\n\nSelect p.ProductName,  d.Year, Sum(s.SalesAmount)\n\nFrom Sales s\n\nLEFT JOIN DimProduct p on s.ProductKey = p.ProductKey\n\nLEFT JOIN DimDate d on s.DateKey = d.DateKey\n\nYou need to complete the query to meet the requirements.\n\nHow should you complete the query?",
    "options": [
      {
        "id": "A",
        "text": "GROUP BY p.ProductKey, d.DateKey\nHAVING SUM(s.SalesAmount) > 10000"
      },
      {
        "id": "B",
        "text": "GROUP BY p.ProductName, d.Year\nHAVING SUM(s.SalesAmount) > 10000"
      },
      {
        "id": "C",
        "text": "WHERE s.SalesAmount > 10000\nGROUP BY p.ProductKey, d.DateKey"
      },
      {
        "id": "D",
        "text": "WHERE s.SalesAmount > 10000\nGROUP BY p.ProductName, d.Year"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Fabric Warehouse & T-SQL",
    "difficulty": "Medium",
    "explanation": "The GroupBY columns must match the columns used in the SELECT statement. Using WHERE will eliminate individual sales records that has a daily SalesAmount that is larger than 10,000. The goal is to remove records for which the total SalesAmount for a year is larger than 10,000. This can be achieved by using HAVING since it works on the result of the GroupBy.\n\nHAVING (Transact-SQL) - SQL Server | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Fabric Warehouse & T-SQL",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q33",
    "type": "multiple_choice",
    "text": "You have a Fabric data warehouse that contains two tables named dbo.FactSales and dbo.DimCustomer. The tables contain the following columns:\n\ndbo.FactSales:\nOrderID\nCustomerKey\nSalesAmount\ndbo.DimCustomer:\nCustomerKey\nRegion\nStakeholders require a reusable dataset that returns one row per region with:\n\nTotalSales = sum of SalesAmount\nOrderCount = count of OrderID\nYou create the query in the visual query editor.\n\nYou need the result to be referenced like a table in future queries by all workspace users, without requiring the users to write SQL.\n\nWhat should you do in the visual query editor?",
    "options": [
      {
        "id": "A",
        "text": "Save the query as a view."
      },
      {
        "id": "B",
        "text": "Save the query as a table."
      },
      {
        "id": "C",
        "text": "Use Data preview mode and pin the results."
      },
      {
        "id": "D",
        "text": "Save the generated SQL in the My queries folder."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Fabric Warehouse & T-SQL",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n2.3 Query and analyze data\n\nWhat This Item Tests:\n\nSelect, filter, and aggregate data by using the Visual Query Editor\n\nAdditional Reading:\n\nQuery and transform data\nExplore data in your mirrored database using Microsoft Fabric\n\nQuery using the SQL query editor\n\nRationale:\n\nSaving the query as a view creates a reusable database object that other users can reference like a table in future queries without needing to write or maintain SQL themselves. Saving the query as a table materializes the result and requires a managing refresh or reprocessing rather than dynamically reflecting the source data. Saving SQL in My queries stores the script for only the current user and does not create a shared dataset object. Data preview only displays results in the editor and cannot be referenced in other queries.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Fabric Warehouse & T-SQL",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q34",
    "type": "multiple_choice",
    "text": "You have a Fabric warehouse.\n\nYou are writing a T-SQL statement to retrieve data from a table named Sales to display the highest sales amount for specific customers.\n\nSELECT CustomerKey\n\n, SalesAmount\n\n, <target1></target1> OVER(ORDER BY SalesAmount DESC) AS Ranking\n\nFROM dbo.Sales\n\nWHERE CustomerKey IN (1, 2, 3)\n\nYou need to ensure that after ties for SalesAmount, the next Sales amount increments the Ranking value by one.\n\nThe following is an example of the expected result.\n\nCustomerKey|SalesAmount|Ranking\n\n1|100|1\n\n2|100|1\n\n1|80|2\n\nWhich function should you use for <target1></target1> in the T-SQL statement?",
    "options": [
      {
        "id": "A",
        "text": "DENSE_RANK()"
      },
      {
        "id": "B",
        "text": "NTILE()"
      },
      {
        "id": "C",
        "text": "RANK()"
      },
      {
        "id": "D",
        "text": "ROW_NUMBER()"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Fabric Warehouse & T-SQL",
    "difficulty": "Medium",
    "explanation": "DENSE_RANK() function returns the rank of each row within the result set partition, with no gaps in the ranking values. The RANK() function includes gaps in the ranking.\n\nRanking Functions (Transact-SQL) - SQL Server | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Fabric Warehouse & T-SQL",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q35",
    "type": "multiple_choice",
    "text": "You have a Fabric warehouse that contains two tables named dbo.FactSales and dbo.DimCustomer. The tables contain the following columns:\n\ndbo.FactSales:\nOrderID\nCustomerKey\nSalesAmount\ndbo.DimCustomer:\nCustomerKey\nRegion\nIn the visual query editor, you drag both tables onto a canvas and create an inner join on CustomerKey by using Merge queries as new.\n\nYou need to generate T-SQL for the query by selecting View query. The T-SQL must include the join and aggregations defined in the visual query editor.\n\nWhat should you do before selecting View query?",
    "options": [
      {
        "id": "A",
        "text": "Add an ORDER BY Region step."
      },
      {
        "id": "B",
        "text": "Enable load for the merged query result."
      },
      {
        "id": "C",
        "text": "Open a new SQL query window and paste the visual query steps."
      },
      {
        "id": "D",
        "text": "Save the query as a view and view the SQL from the saved view."
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n2.3 Query and analyze data\n\nWhat This Item Tests:\n\nSelect, filter, and aggregate data by using the Visual Query Editor\n\nAdditional Reading:\n\nQuery using the visual query editor\nQuery and transform data\nExplore the visual query editor\n\nRationale:\n\nEnabling load for the merged query result ensures that the query is materialized in the visual query pipeline so the View query option can generate the corresponding T-SQL, including the join and aggregation steps defined in the editor. Adding an ORDER BY clause does not affect whether the generated SQL includes the configured joins and aggregations. Opening a separate SQL query window does not convert the visual query steps into T-SQL. Saving the query as a view occurs after query generation and is not required to view the SQL produced by the visual query editor.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q36",
    "type": "multi_select",
    "text": "You use Microsoft Fabric for data warehousing with data in FactSales and DimProduct tables.\n\nYou need to generate a monthly report summarizing sales by product category using the visual query editor.\n\nEach correct answer presents part of the solution. Which two actions should you take?",
    "options": [
      {
        "id": "A",
        "text": "Add FactSales and DimProduct tables."
      },
      {
        "id": "B",
        "text": "Enable load for DimProduct."
      },
      {
        "id": "C",
        "text": "Merge FactSales and DimProduct on ProductKey."
      },
      {
        "id": "D",
        "text": "Select ProductCategory and sum SalesAmount after merging tables."
      },
      {
        "id": "E",
        "text": "Sort products by sales amount."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": [
      "A",
      "C"
    ],
    "selectCount": 2,
    "domain": "domain2",
    "topic": "Dataflows Gen2 & Power Query",
    "difficulty": "Medium",
    "explanation": "To create a report showing total sales for each product category by month, you must first drag and drop the FactSales and DimProduct tables onto the canvas to set up the query environment. Then, use the Merge queries as new operator to join these tables on ProductKey, which is essential for aggregating sales data by product category. Sorting or filtering for specific sales amounts are not necessary steps for this task. Selecting ProductCategory and summing SalesAmount after merging tables seems complete but misses enabling load for DimProduct.\n\nExplore the visual query editor - Training | Microsoft Learn\nExplore Dataflows Gen2 in Microsoft Fabric - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Dataflows Gen2 & Power Query",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q37",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace that contains a KQL database with a table named requests. The table contains the following columns:\n\ntimestamp (datetime)\nsuccess (bool)\nduration (real)\ncloud_RoleName (string)\nYou need to write a KQL query that returns results from the last 24 hours. The query must meet the following requirements.:\n\nInclude one row per hour per cloud role.\nInclude the number of failed requests.\nInclude the average duration of failed requests.\nWhich query should you use?",
    "options": [
      {
        "id": "A",
        "text": "requests\n| where timestamp > ago(24h)\n| summarize failedCount = count(), avgDuration = avg(duration) by timestamp, cloud_RoleName\n| where success == false"
      },
      {
        "id": "B",
        "text": "requests\n| where timestamp > ago(24h)\n| where success == false\n| summarize failedCount = count(), avgDuration = avg(duration) by bin(timestamp, 1h), cloud_RoleName"
      },
      {
        "id": "C",
        "text": "requests\n| where timestamp > ago(24h)\n| where success == false\n| summarize failedCount = count(), avgDuration = avg(duration) by cloud_RoleName"
      },
      {
        "id": "D",
        "text": "requests\n| where timestamp > ago(24h)\n| where success == false\n| project timestamp, cloud_RoleName, failedCount = count(), avgDuration = avg(duration)\n| summarize by bin(timestamp, 1h), cloud_RoleName"
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain3",
    "topic": "Real-Time Intelligence & KQL",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n2.3 Query and analyze data\n\nWhat This Item Tests:\n\nSelect, filter, and aggregate data by using KQL\n\nAdditional Reading:\n\nWrite basic KQL queries\nKusto Query Language\nTutorial: Learn common operators\nIntroduction\nRationale:\n\nThe correct query filters the last 24 hours of data, filters failed requests (success == false), and uses summarize with bin(timestamp, 1h) and cloud_RoleName to return one row per hour per service, including the count of failed requests and the average duration. Filtering after aggregation (option B) is invalid because success is unavailable after summarize. Option C incorrectly attempts to compute aggregates inside the project, which does not support aggregation functions. Option D aggregates only by service and does not produce hourly results.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Real-Time Intelligence & KQL",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q38",
    "type": "multiple_choice",
    "text": "Your company uses Microsoft Fabric for data analytics. You must protect sensitive data from unauthorized access in the data warehouse.\n\nYou need to manage access to specific objects in the warehouse.\n\nWhat action should you take to achieve this?",
    "options": [
      {
        "id": "A",
        "text": "Set item-level permissions to warehouse."
      },
      {
        "id": "B",
        "text": "Configure dynamic data masking on objects."
      },
      {
        "id": "C",
        "text": "Use TSQL to grant granular permissions."
      },
      {
        "id": "D",
        "text": "Implement row-level security for objects."
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Security & Access Control (RLS/DDM)",
    "difficulty": "Medium",
    "explanation": "Using T-SQL to grant permissions on specific objects is the correct method to ensure only authorized users can interact with certain warehouse objects. Row-level security applies per table and is not granular enough. Dynamic data masking obfuscates data, but isn't considered access control. Item-level permissions prevent certain access within the warehouse, but not granular to the objects.\nConfigure SQL granular permissions using T-SQL",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Security & Access Control (RLS/DDM)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q39",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains a workspace named Workspace1. Workspace1 contains a lakehouse, a data pipeline, a notebook, and several Microsoft Power BI reports.\n\nA user named User1 plans to use SQL to access the lakehouse to analyze data. User1 must have the following access:\n\nUser1 must have read-only access to the lakehouse.\nUser1 must NOT be able to access the rest of the items in Workspace1.\nUser1 must NOT be able to use Spark to query the underlying files in the lakehouse.\nYou need to configure access for User1.\n\nWhat should you do?",
    "options": [
      {
        "id": "A",
        "text": "Add User1 to the workspace as a member, share the lakehouse with User1, and select Read all SQL E ndpoint data."
      },
      {
        "id": "B",
        "text": "Add User1 to the workspace as a viewer, share the lakehouse with User1, and select Read all SQL E ndpoint data."
      },
      {
        "id": "C",
        "text": "Share the lakehouse with User1 directly and select Build reports on the default dataset."
      },
      {
        "id": "D",
        "text": "Share the lakehouse with User1 directly and select Read all SQL E ndpoint data."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Security & Access Control (RLS/DDM)",
    "difficulty": "Medium",
    "explanation": "Since the user only needs access to the lakehouse and not the other items in the workspace, you should share the lakehouse directly and select Read all SQL Endpoint data. The user should not be added as a member of the workspace. All members of the workspace, even viewers, will be able to open all Power BI reports in the workspace. The SQL analytics endpoint itself cannot be shared directly; the Share options only show for the lakehouse.\n\nLakehouse sharing and permission management - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Security & Access Control (RLS/DDM)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q40",
    "type": "multiple_choice",
    "text": "You have a Fabric tenant that contains two lakehouses named Lakehouse1 and Lakehouse2. Lakehouse1 contains a table named FactSales that is partitioned by a column named CustomerID.\n\nYou need to create a shortcut to the FactSales table in Lakehouse2. The shortcut must only connect to data for CustomerID 100.\n\nWhat should you do?",
    "options": [
      {
        "id": "A",
        "text": "Add a filter activity after the copy data activity in a data pipeline."
      },
      {
        "id": "B",
        "text": "As you create the shortcut select the CustomerKey=100 folder under the FactSales folder in Files."
      },
      {
        "id": "C",
        "text": "As you create the shortcut, select the CustomerKey=100 folder under the FactSales folder in Tables."
      },
      {
        "id": "D",
        "text": "In the semantic models connected to the lakehouses, add a report-level filter for CustomerKey = 100."
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain2",
    "topic": "OneLake Shortcuts",
    "difficulty": "Medium",
    "explanation": "During the shortcut setup process, you can expand the FactSales folder to see each folder per CustomerID partition and select the folder for CustomerID=100. These folders are unavailable under Files, and all other options will connect to all the customer data in the shortcut.\n\nReferencing data to a Lakehouse using shortcuts - Microsoft Fabric | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - OneLake Shortcuts",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q41",
    "type": "multi_select",
    "text": "Your organization uses Microsoft Fabric for data analytics solutions, including sensitive financial information that must be protected to comply with regulatory standards.\n\nYou need to restrict user access based on their role and protect certain sensitive data within the data warehouse. \n\nEach correct answer presents part of the solution. Which three actions should you take?",
    "options": [
      {
        "id": "A",
        "text": "Apply sensitivity labels."
      },
      {
        "id": "B",
        "text": "Endorse the data warehouse."
      },
      {
        "id": "C",
        "text": "Implement row-level security."
      },
      {
        "id": "D",
        "text": "Grant Viewer role to authorized users."
      },
      {
        "id": "E",
        "text": "Use dynamic data masking."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": [
      "A",
      "C",
      "E"
    ],
    "selectCount": 3,
    "domain": "domain1",
    "topic": "Security & Access Control (RLS/DDM)",
    "difficulty": "Medium",
    "explanation": "Applying sensitivity labels is essential for classifying and protecting sensitive data, ensuring compliance with organizational policies and regulatory standards. Implementing row-level security enhances data privacy by allowing users to access only the data they are authorized to view, thus maintaining control over sensitive information. Using dynamic data masking further protects sensitive data by preventing unauthorized viewing, while still allowing necessary analysis. Endorsing the warehouse will indicate that it's trustworthy, but doesn't protect the data. Granting authorized users the Viewer role might seem like a safe option but does not ensure that only authorized users can access sensitive data.\n\nExplore end-to-end analytics with Microsoft Fabric - Training | Microsoft Learn\nSecure a Microsoft Fabric data warehouse - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Security & Access Control (RLS/DDM)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q42",
    "type": "multi_select",
    "text": "Your company uses Microsoft Fabric to manage data analytics solutions. The marketing department needs to share reports with external partners.\n\nYou need to ensure that reports can be shared with external partners without compromising sensitive data.\n\nEach correct answer presents part of the solution. Which three actions should you take?",
    "options": [
      {
        "id": "A",
        "text": "Assign external partners a Viewer role."
      },
      {
        "id": "B",
        "text": "Implement row-level security."
      },
      {
        "id": "C",
        "text": "Restrict workspace sharing settings."
      },
      {
        "id": "D",
        "text": "Share reports via email attachments."
      },
      {
        "id": "E",
        "text": "Set data source credentials to a fixed identity."
      },
      {
        "id": "F",
        "text": "Configure a Power BI app."
      }
    ],
    "correctOptionId": "B",
    "correctOptionIds": [
      "B",
      "E",
      "F"
    ],
    "selectCount": 3,
    "domain": "domain1",
    "topic": "Security & Access Control (RLS/DDM)",
    "difficulty": "Medium",
    "explanation": "Implementing row-level security is crucial for controlling data visibility based on user identity. Switching to a fixed identity ensures that external partners have access to the necessary data without exposing sensitive information. Using Power BI apps enables secure sharing of reports with external partners. Assigning a viewer role allows external partners to view reports without modification access, aligning with the goal of secure sharing, however sharing via Power BI App is more restrictive hence why you should not grant viewer role. Restricting workspace sharing settings might seem like a way to control data sharing, but it does not directly address the need for secure sharing with external partners. Sharing reports via email attachments can lead to data security issues, as it may result in unauthorized access or data leakage, which is contrary to the goal.\n\nEnable and use Microsoft Fabric - Training | Microsoft Learn\nManage Fabric security - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Security & Access Control (RLS/DDM)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q43",
    "type": "multiple_choice",
    "text": "You use Microsoft Power BI Desktop to create a Power BI semantic model.\n\nYou need to recommend a solution to collaborate with another Power BI modeler. The solution must ensure that you can both work on different parts of the model simultaneously. The solution must provide the most efficient and productive way to collaborate on the same model.\n\nWhat should you recommend?",
    "options": [
      {
        "id": "A",
        "text": "Save your work as a PBIX file and email the file to the other modeler."
      },
      {
        "id": "B",
        "text": "Save your work as a PBIX file and publish the file to a Fabric workspace. Add the other modeler as member to the workspace."
      },
      {
        "id": "C",
        "text": "Save your work as a PBIX file to Microsoft OneDrive and share the file with the other modeler."
      },
      {
        "id": "D",
        "text": "Save your work as a Power BI Project (PBIP). Initialize a Git repository with version control."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Source Control & Git Integration",
    "difficulty": "Medium",
    "explanation": "Saving your Power BI work as a PBIP enables you to save the work as individual plain text files in a simple, intuitive folder structure, which can be checked into a source control system such as Git. This will enable multiple developers to work on different parts of the model simultaneously.\n\nEmailing a Power BI model back and forth is not efficient for collaboration. Saving a Power BI model as a PBIX file to OneDrive eases developers access, but only one developer can have the file open at time. Publishing a PBIX file to a shared workspace does allow for developers to live connect and edit the model simultaneously however it is not the most efficient or productive option, and PBIP.\n\nPower BI Desktop projects (PBIP) - Power BI | Microsoft Learn\n\nManage the analytics development lifecycle - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Source Control & Git Integration",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q44",
    "type": "multiple_choice",
    "text": "You have a semantic model that loads data from an Azure SQL database and is synced via Fabric deployment pipelines to three workspaces named Development, Test, and Production.\n\nYou need to reduce the size of the query requests sent to the Azure SQL database when full semantic model refreshes occur in the Development or Test workspaces.\n\nWhat should you do for the deployment pipeline?",
    "options": [
      {
        "id": "A",
        "text": "Add a parameter to filter the data."
      },
      {
        "id": "B",
        "text": "Configure row-level security (RLS)."
      },
      {
        "id": "C",
        "text": "Connect either workspace to an Azure Data Lake Storage Gen2 account."
      },
      {
        "id": "D",
        "text": "Configure incremental refresh."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Deployment Pipelines & ALM",
    "difficulty": "Medium",
    "explanation": "Adding a parameter to filter the data allows you to configure the parameter in dev and test to not load all the data. Configuring row level security changes the access and impacts the consuming users ability to view the data, it does not change the load. Connecting a workspace to ADLS to Gen 2 is around logging not loading data from Azure SQL. Incremental refresh changes the loading however the stem states full model refresh so we need all the data.\n\nCreate deployment rules for Fabric's Application lifecycle management (ALM) - Microsoft Fabric | Microsoft Learn\n\nManage the analytics development lifecycle - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Deployment Pipelines & ALM",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q45",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace.\n\nReport authors create reports in Microsoft Power BI Desktop. All reports must connect to a Microsoft SQL Server database named SalesDW.\n\nYou need to standardize and streamline the workflow for creating new reports. The workflow must meet the following requirements:\n\nPredefine the server and database connection.\nEnable the authors to select the tables that they need.\nRequire the authors to authenticate by using their own credentials.\nWhat should you create?",
    "options": [
      {
        "id": "A",
        "text": "a Power BI Desktop (.pbix) file"
      },
      {
        "id": "B",
        "text": "a Power BI Project (.pbip) file"
      },
      {
        "id": "C",
        "text": "a Power BI template (.pbit) file"
      },
      {
        "id": "D",
        "text": "a Power BI data source (.pbids) file"
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Reusable Assets (PBIDS/PBIP)",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n1.2 Maintain the analytics development lifecycle\n\nWhat This Item Tests:\n\nCreate and update reusable assets, including Power BI data source (.pbids) files\n\nAdditional Reading:\n\nCreate reusable Power BI assets\nManage development lifecycle for Power BI assets\nIntroduction\nRationale:\n\nA Power BI data source (.pbids) file is used to predefine a connection to a data source and launch Power BI Desktop with that connection already configured. Authors authenticate by using their own credentials and select the tables they want to load, which meets the requirement to standardize the connection, while excluding report pages, queries, and semantic model artifacts. A Power BI Project (.pbip) file contains report and semantic model definitions for source-controlled development and, therefore, includes artifacts that must not be distributed. A Power BI template (.pbit) file packages report layout, queries, and semantic model metadata, which violates the requirement to exclude report and model content. A shared semantic model removes the need to connect directly to the SQL Server database, and, therefore does not meet the requirement to standardize the initial SQL Server connection for new reports.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Reusable Assets (PBIDS/PBIP)",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q46",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace named Sales-Prod that is assigned to a Fabric capacity. The workspace contains a semantic model named SalesModel that is used by production Microsoft Power BI reports.\n\nUsers of an external tool cannot deploy metadata changes to SalesModel.\n\nWhat should you configure?",
    "options": [
      {
        "id": "A",
        "text": "Grant the external tool users the Admin role on the workspace."
      },
      {
        "id": "B",
        "text": "Enable the tenant setting that allows users to create Fabric items."
      },
      {
        "id": "C",
        "text": "Set the XMLA endpoint to Read Write on the capacity that hosts the workspace."
      },
      {
        "id": "D",
        "text": "Download the semantic model as a PBIX file and republish the file to the workspace."
      }
    ],
    "correctOptionId": "C",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "XMLA Endpoint Management",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n1.2 Maintain the analytics development lifecycle\n\nWhat This Item Tests:\n\nDeploy and manage semantic models by using the XMLA endpoint\n\nAdditional Reading:\n\nTroubleshoot XMLA endpoint connectivity\n\nRationale:\n\nSetting the XMLA endpoint to Read Write enables external tools to deploy metadata changes to semantic models in a Fabric capacity; Downloading and republishing a PBIX file is not required for metadata deployment and disrupts the development lifecycle; Tenant settings for creating Fabric items are unrelated to XMLA access; Granting Admin permissions alone does not enable write operations without the XMLA endpoint set to Read Write.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - XMLA Endpoint Management",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q47",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace named Sales-Dev in the West US Azure region that contains a lakehouse and a Microsoft Power BI semantic model.\n\nYou have an Azure DevOps Git repository located in the West Europe Azure region.\n\nYou need to connect the workspace to the repository.\n\nWhat should you do?",
    "options": [
      {
        "id": "A",
        "text": "Create a workspace identity."
      },
      {
        "id": "B",
        "text": "Disable workspace outbound protection."
      },
      {
        "id": "C",
        "text": "Update the workspace region to match the repository region."
      },
      {
        "id": "D",
        "text": "Enable the tenant setting that allows exporting items to Git repositories in other geographical locations."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Source Control & Git Integration",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n1.2 Maintain the analytics development lifecycle\n\nWhat This Item Tests:\n\nConfigure version control for a workspace\n\nAdditional Reading:\n\nTroubleshoot lifecycle management issues\nEnable and use Microsoft Fabric\nRationale:\n\nConnecting a Fabric workspace to a Git repository in a different Azure region requires enabling the tenant setting that allows exporting items to Git repositories in other geographical locations; Workspace regions cannot be changed after creation; Outbound protection settings do not affect Git integration across regions; Workspace identity is used for authentication scenarios and does not enable cross-region Git connectivity.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Source Control & Git Integration",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q48",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace that contains:\n\nA lakehouse named SalesLH that hosts a Delta table named FactSales\nA data warehouse named SalesWH that loads data from SalesLH\nA Microsoft Power BI semantic model named SalesModel built on SalesWH\nSalesModel is shared to other workspaces and used by multiple reports.\n\nYou plan to rename a column in SalesModel and republish the model.\n\nYou need to identify downstream reports and workspaces that depend on SalesModel and might be affected..\n\nWhat should you use?",
    "options": [
      {
        "id": "A",
        "text": "data lineage view"
      },
      {
        "id": "B",
        "text": "Dataflow Gen2"
      },
      {
        "id": "C",
        "text": "Fabric IQ"
      },
      {
        "id": "D",
        "text": "The SQL analytics endpoint"
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Lineage & Impact Analysis",
    "difficulty": "Medium",
    "explanation": "Objective:\n\n1.2 Maintain the analytics development lifecycle\n\nWhat This Item Tests:\n\nPerform impact analysis of downstream dependencies from lakehouses, warehouses, dataflows, and semantic models\n\nAdditional Reading:Semantic model impact analysis\n\nSemantic model best practices for data agent\nBest practices for getting the best performance with Dataflow Gen2\n\nRationale:\n\nThe data lineage view provides visibility into upstream and downstream dependencies, allowing you to identify reports and workspaces that rely on a semantic model and assess the impact of schema changes; Dataflow Gen2 is used for data transformation and does not provide dependency tracking; The SQL analytics endpoint enables querying data but does not show lineage relationships; Fabric IQ is not used for impact analysis of data dependencies.",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Lineage & Impact Analysis",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q49",
    "type": "multiple_choice",
    "text": "Your organization uses Microsoft Fabric for data analytics.\n\nYou need to manage the semantic models with external tools due to the size.\n\nWhat should you do?",
    "options": [
      {
        "id": "A",
        "text": "Enable incremental refresh for the semantic models."
      },
      {
        "id": "B",
        "text": "Enable large semantic model storage format."
      },
      {
        "id": "C",
        "text": "Enable read-only in the XMLA Endpoint settings."
      },
      {
        "id": "D",
        "text": "Enable read-write in the XMLA Endpoint settings."
      }
    ],
    "correctOptionId": "D",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "XMLA Endpoint Management",
    "difficulty": "Medium",
    "explanation": "To enable write operations on semantic models from external tools, it is necessary to configure the XMLA Endpoint settings to allow read-write access. Enabling large semantic model storage format focuses on optimizing data storage and performance rather than enabling write capabilities. Enabling read-only access in the XMLA Endpoint settings allows data consumption but does not permit write operations. Enabling incremental refresh aids in data management but does not directly enable write operations on semantic models.\n\nManage a Power BI semantic model using XMLA endpoint - Training | Microsoft Learn",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - XMLA Endpoint Management",
    "isCustom": true
  },
  {
    "id": "mslearn-set2-q50",
    "type": "multiple_choice",
    "text": "You have a Fabric workspace that contains a semantic model and five reports that use the model.\n\nYou plan to share the semantic model with another workspace and use the model in five additional reports in the new workspace.\n\nYou need to analyze the downstream dependencies of the semantic model. The solution must minimize administrative effort.\n\nFrom the workspace, you open the semantic model.\n\nWhat should you do next?",
    "options": [
      {
        "id": "A",
        "text": "Select Impact analysis."
      },
      {
        "id": "B",
        "text": "Select Lineage."
      },
      {
        "id": "C",
        "text": "Select Security."
      },
      {
        "id": "D",
        "text": "Select View related."
      }
    ],
    "correctOptionId": "A",
    "correctOptionIds": null,
    "selectCount": null,
    "domain": "domain1",
    "topic": "Lineage & Impact Analysis",
    "difficulty": "Medium",
    "explanation": "You should select Impact analysis because it automatically identifies and summarizes all downstream dependencies of the semantic model, including reports and usage across workspaces, which is essential before sharing the model and reusing it in additional reports. Impact analysis provides a clear view of affected items and dependency scope with minimal administrative effort, whereas Lineage offers a more manual, visual relationship view without consolidated impact insights, Security is focused on permissions, and View related does not provide a comprehensive dependency or impact assessment.\n\nImpact analysis",
    "msLearnUrl": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
    "msLearnTitle": "Microsoft Learn - Lineage & Impact Analysis",
    "isCustom": true
  }
];
