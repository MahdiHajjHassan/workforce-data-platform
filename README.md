# HR Data Platform

> [!CAUTION]
> **Confidential enterprise work.** I worked with critical HR information at Thales. This public explanation uses independent examples, with no Thales implementation or data and no employer endorsement. Diagrams explain the architecture without disclosing employer systems or records.

## Turn enterprise HR records into reporting and usable datasets

This platform connects HR information to three audiences: analysts building workforce reports, business teams receiving approved data, and AI teams preparing model training. At Thales, I delivered the ingestion, transformation and analytical structures behind these uses for critical HR information covering tens of thousands of employees worldwide.

**My contribution:** ETL pipelines, SQL transformations, data modeling, reporting and dataset delivery. I also translated business requirements into technical work, coordinated engineers and interns, and supported deployment and production troubleshooting.

**Tools:** SQL Server · T-SQL · Talend ETL · Power BI · DAX · SSAS

<picture>
  <source media="(prefers-color-scheme: dark) and (max-width: 540px)" srcset="assets/workforce-story-v5-mobile-dark.svg">
  <source media="(max-width: 540px)" srcset="assets/workforce-story-v5-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/workforce-story-v5-dark.svg">
  <img src="assets/workforce-story-v5-light.svg" alt="Source HR records feed a shared workforce, country, department and job model. Three deliveries use that model: HR reporting, controlled sharing, and datasets for AI model training." width="680">
</picture>

### What the platform delivers

| User | Output | Decisions the output supports |
| --- | --- | --- |
| HR analyst | Workforce reports with shared populations, categories and measures. | Understand headcount and workforce composition using agreed definitions. |
| Authorized business team | Selected records and fields within the team's access. | Work with the information relevant to its operational responsibilities. |
| AI team | Prepared HR datasets for model training. | Use enterprise data supplied for an approved training purpose. |

An HR analyst might need headcount by country and employment category, while an operations team needs department and assignment information. Both depend on the same business definitions, but their delivered fields and access differ.

### My delivery responsibilities

- **Build the data path:** connect source inputs to Talend ingestion, SQL transformations and analytical models.
- **Define usable outputs:** translate reporting requirements into dimensions, measures and datasets for each audience.
- **Coordinate delivery:** clarify requirements with the product owner and discuss architecture with the technical lead.
- **Support the running platform:** validate changes, assist deployment and investigate production issues.

<details>
<summary><strong>Engineering details: data layers, reporting, and access rules</strong></summary>

### How records become analytical data

| Layer | Responsibility |
| --- | --- |
| Staging | Receive source inputs and check their structure. |
| Operational data store (ODS) | Standardize types, keys and relationships across sources. |
| Data warehouse | Organize business facts, dimensions and required history. |
| Semantic / cube layer | Define shared measures and dimensions consumed by reports. |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/data-platform-v2-dark.svg">
  <img src="assets/data-platform-v2-light.svg" alt="HR architecture: source systems feed staging, an operational data store, a warehouse, and a semantic layer before audience-specific delivery." width="500">
</picture>

### Output definitions and access

A report's population, categories and calculations determine what its numbers mean. A delivered dataset also needs an explicit scope: which records, which fields and which recipient. Workforce counts, operational data and AI training datasets therefore share a modeled foundation while retaining their own delivery rules.

My work covered preparing and supplying training datasets. The model-training team uses that delivery in its own workflow.

### Explore the engineering decisions

- [Architecture and access rules](https://github.com/MahdiHajjHassan/workforce-data-platform/blob/main/docs/architecture.md)
- [My delivery responsibilities](https://github.com/MahdiHajjHassan/workforce-data-platform/blob/main/docs/delivery.md)
- [Permission-aware development datasets](https://github.com/MahdiHajjHassan/policy-aware-data-generator)

</details>

[Back to my portfolio](https://github.com/MahdiHajjHassan)
