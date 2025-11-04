# Database Architecture and Workflow

## System Overview

```mermaid
graph TB
    subgraph "User Access Layer"
        WebUI[Web Interface]
        API[API Interface]
    end

    subgraph "Application Layer"
        Auth[Authentication]
        Controllers[Business Logic Controllers]
        Middleware[Business Context Middleware]
    end

    subgraph "Database Layer"
        DB[(PostgreSQL Database)]
        
        subgraph "Core Tables"
            Users[Users]
            Businesses[Businesses]
            Products[Products]
            Customers[Customers]
            Suppliers[Suppliers]
        end
        
        subgraph "Transaction Tables"
            Sales[Sales]
            Purchases[Purchases]
            Expenses[Expenses]
        end
        
        subgraph "System Tables"
            Logs[System Logs]
            Settings[System Settings]
            Sessions[User Sessions]
        end
        
        subgraph "Admin Tables"
            AdminProfiles[Admin Profiles]
            Roles[Admin Roles]
            Permissions[Permissions]
        end
    end

    WebUI --> Auth
    API --> Auth
    Auth --> Middleware
    Middleware --> Controllers
    Controllers --> DB
    
    Users --> DB
    Businesses --> DB
    Products --> DB
    Customers --> DB
    Suppliers --> DB
    Sales --> DB
    Purchases --> DB
    Expenses --> DB
    Logs --> DB
    Settings --> DB
    Sessions --> DB
    AdminProfiles --> DB
    Roles --> DB
    Permissions --> DB
```

## Multi-tenancy Data Isolation

```mermaid
graph TD
    subgraph "Business A"
        A_Users[Users]
        A_Products[Products]
        A_Customers[Customers]
        A_Sales[Sales]
        A_Purchases[Purchases]
    end
    
    subgraph "Business B"
        B_Users[Users]
        B_Products[Products]
        B_Customers[Customers]
        B_Sales[Sales]
        B_Purchases[Purchases]
    end
    
    subgraph "Database"
        DB[(Shared Database)]
    end
    
    A_Users --> DB
    A_Products --> DB
    A_Customers --> DB
    A_Sales --> DB
    A_Purchases --> DB
    
    B_Users --> DB
    B_Products --> DB
    B_Customers --> DB
    B_Sales --> DB
    B_Purchases --> DB
    
    style A_Users fill:#e1f5fe
    style A_Products fill:#e1f5fe
    style A_Customers fill:#e1f5fe
    style A_Sales fill:#e1f5fe
    style A_Purchases fill:#e1f5fe
    
    style B_Users fill:#f3e5f5
    style B_Products fill:#f3e5f5
    style B_Customers fill:#f3e5f5
    style B_Sales fill:#f3e5f5
    style B_Purchases fill:#f3e5f5
```

## Key Relationships

### User to Business Relationship
```mermaid
graph LR
    User[User] -- "owns" --> Business[Business]
    User -- "works for" --> Business2[Business]
    User -- "works for" --> Business3[Business]
```

### Business Data Hierarchy
```mermaid
graph TD
    Business[Business] --> Products[Products]
    Business --> Customers[Customers]
    Business --> Suppliers[Suppliers]
    Business --> Sales[Sales]
    Business --> Purchases[Purchases]
    Business --> Expenses[Expenses]
    Business --> Branches[Branches]
    
    Products --> Inventory[Inventory]
    Products --> Categories[Categories]
    Products --> Units[Units]
    
    Sales --> SaleItems[Sale Items]
    Purchases --> PurchaseItems[Purchase Items]
    
    Customers --> Transactions[Customer Transactions]
    Suppliers --> Transactions2[Supplier Transactions]
```

## Data Flow Process

```mermaid
sequenceDiagram
    participant U as User
    participant M as Middleware
    participant C as Controllers
    participant DB as Database
    
    U->>M: Login Request
    M->>M: Set Business Context
    M->>C: Authenticated Request
    C->>DB: Query with Business Filter
    DB->>C: Filtered Results
    C->>U: Response
    
    U->>C: Create Product
    C->>DB: Insert with Business ID
    DB->>C: Confirmation
    C->>U: Success Response
```

## Security and Access Control

```mermaid
graph TD
    Login[Login Attempt] --> AuthCheck{Valid Credentials?}
    AuthCheck -- No --> Error[Login Failed]
    AuthCheck -- Yes --> RoleCheck{User Role}
    
    RoleCheck -- Regular User --> BusinessCheck{Has Business?}
    BusinessCheck -- No --> BusinessSetup[Business Setup]
    BusinessCheck -- Yes --> Dashboard[User Dashboard]
    
    RoleCheck -- Admin --> AdminCheck{Is Superuser?}
    AdminCheck -- No --> AdminPanel[Admin Panel]
    AdminCheck -- Yes --> SuperadminPanel[Superadmin Panel]
    
    Dashboard --> Middleware[Business Context Set]
    AdminPanel --> Middleware
    SuperadminPanel --> NoMiddleware[No Business Context]
```

## Database Connection and Configuration

```mermaid
graph LR
    App[Django Application] -->|Database Connection| Pool[Connection Pool]
    Pool -->|PostgreSQL Protocol| DB[PostgreSQL Server]
    
    DB --> Master[Master Database]
    DB --> Replica[Replica Database]
    
    Master -->|Write Operations| Storage[(Data Storage)]
    Replica -->|Read Operations| Storage
    
    style Master fill:#e8f5e8
    style Replica fill:#fff3e0
```

## Backup and Recovery Process

```mermaid
graph TD
    Schedule[Backup Schedule] --> Trigger[Backup Trigger]
    Trigger --> Process[Backup Process]
    Process --> Dump[Database Dump]
    Dump --> Storage[Backup Storage]
    Storage --> Validation[Backup Validation]
    Validation -->|Valid| Complete[Backup Complete]
    Validation -->|Invalid| Retry[Retry Backup]
    
    Recovery[Recovery Request] --> Restore[Restore Process]
    Restore -->|Latest Backup| DB[Database Restore]
    DB --> Verification[Data Verification]
    Verification -->|Success| Live[System Live]
    Verification -->|Failed| Rollback[Rollback]
```