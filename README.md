# Workforce data platform

I work on the data engineering behind HR reporting and controlled data sharing: bringing information from different sources into a consistent structure and making the right view available to each audience.

This repository is an anonymized overview of my professional experience. The diagram uses a common reference architecture; it does not reproduce an employer's system. Source code and internal data are confidential.

## How the data becomes useful

~~~mermaid
flowchart TD
    Sources["Different source systems"] --> Staging["Staging: receive inputs"]
    Staging --> ODS["Operational store: standardize records"]
    ODS --> Warehouse["Warehouse: organize business data"]
    Warehouse --> Semantic["Semantic layer: define reporting measures"]
    Semantic --> Dashboards["Interactive HR dashboards"]
    Warehouse --> Sharing["Approved data-sharing views"]
    Warehouse --> Downstream["Authorized downstream datasets"]
    Scope["Role and country access rules"] -.-> Dashboards
    Scope -.-> Sharing
    Scope -.-> Downstream
~~~

The layers turn different inputs into consistent business information. The outputs serve different needs: HR reporting, approved exchanges with other organizations, and preparation for authorized analytics or model-training consumers. Role and country rules limit each audience's access; having one platform does not give everyone the same view.

## My contribution

I handle implementation across ingestion, transformation, data modeling, and delivery. I work with the product owner on requirements, discuss architecture with the technical lead, and coordinate execution with other engineers and interns.

For an HR team, this means usable reporting and controlled sharing without relying on each team to reconcile source systems independently.

## Technical detail

- [Architecture and delivery boundaries](docs/architecture.md): each layer's purpose and where access restrictions apply.
- [Implementation responsibilities](docs/delivery.md): translating requirements into pipelines, reporting structures, and recipient views.
- [Synthetic-data reference design](https://github.com/MahdiHajjHassan/policy-aware-data-generator): a separate public example of recipient-specific development data.

[Mahdi Hajj Hassan](https://github.com/MahdiHajjHassan)
