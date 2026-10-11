# HR Data Platform | Data Layers and Access Rules

> [!CAUTION]
> **Confidential enterprise work.** I worked with critical HR information at Thales. This public explanation uses independent examples, with no Thales implementation or data and no employer endorsement. Diagrams explain the architecture without disclosing employer systems or records.

This architecture connects source records to workforce reports, controlled business datasets, and inputs for AI model training. Each layer has a distinct job.

## Data layers

| Layer | Purpose | Engineering decisions |
| --- | --- | --- |
| Staging | Receive source inputs. | Input structure, validation, and load tracking. |
| Operational data store (ODS) | Make records consistent across sources. | Data types, keys, relationships, and transformation rules. |
| Data warehouse | Organize facts and dimensions for analysis. | Business definitions and historical representation where required. |
| Semantic / cube layer | Define calculations used by reports. | Measures, dimensions, and reporting consistency. |

A report's headcount depends on an agreed population and categories. Standardizing incoming records is one step; defining what the report counts is another.

## Three output types

| Output | User | Access rules |
| --- | --- | --- |
| HR reports and dashboards | HR analysts and business audiences. | Permitted countries and reporting roles. |
| Controlled sharing datasets | Authorized downstream teams. | Approved purpose, records, and fields. |
| HR datasets for AI model training | AI teams. | Approved training purpose and permitted data scope. |

Record selection and field selection are separate decisions. A recipient may be allowed to see workforce counts for one country without receiving identity or financial fields.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MahdiHajjHassan/workforce-data-platform/main/assets/audience-scope-dark.svg">
  <img alt="Role, country scope, and data contract jointly determine the permitted records and attributes in an audience-specific view." src="https://raw.githubusercontent.com/MahdiHajjHassan/workforce-data-platform/main/assets/audience-scope-light.svg" width="500">
</picture>

## Change review

A source change can affect ingestion, transformations, relationships, and reporting calculations. A recipient change can affect the records and fields delivered. Review follows the change through to the report or dataset the audience receives.

Validation covers source reconciliation, transformation rules, consistent business definitions, and access rules for the output.

[Project overview](https://github.com/MahdiHajjHassan/workforce-data-platform/blob/main/README.md) · [My delivery responsibilities](https://github.com/MahdiHajjHassan/workforce-data-platform/blob/main/docs/delivery.md)
