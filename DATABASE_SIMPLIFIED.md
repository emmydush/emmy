# Simplified Database Workflow

## Core Concept

Our system uses one database but keeps each business's data separate through automatic filtering.

## How It Works - Step by Step

```mermaid
flowchart TD
    A[User Logs In] --> B{Valid Password?}
    B -- No --> C[Show Error]
    B -- Yes --> D[Select Business]
    
    D --> E[Set Business Context<br/>in Session]
    
    E --> F[User Requests Data<br/>e.g. "Show Products"]
    
    F --> G[Application Adds<br/>Business Filter<br/>Automatically]
    
    G --> H[Database Query<br/>WITH BUSINESS FILTER]
    
    H --> I[Return Only<br/>This Business's Data]
    
    I --> J[Display to User]
    
    style A fill:#e3f2fd
    style E fill:#e8f5e8
    style G fill:#fff3e0
    style H fill:#ffebee
```

## What This Means

### For the Database
- **One physical database** stores ALL businesses' data
- **Each table has a `business_id` column** to identify which business each record belongs to
- **Automatic filtering** ensures users only see their business's data

### Example Table Structure
```
Products Table
┌─────────────┬──────────────┬─────────────┬─────────────┐
│ product_id  │ business_id  │ name        │ price       │
├─────────────┼──────────────┼─────────────┼─────────────┤
│ 1           │ 101          │ Laptop      │ 1200.00     │  ← Business A
│ 2           │ 101          │ Mouse       │ 25.00       │  ← Business A
│ 3           │ 102          │ Laptop      │ 1100.00     │  ← Business B
│ 4           │ 102          │ Keyboard    │ 75.00       │  ← Business B
└─────────────┴──────────────┴─────────────┴─────────────┘
```

### When Business A Requests Products
```sql
-- What actually happens:
SELECT * FROM products WHERE business_id = 101;

-- What Business A sees:
┌─────────────┬──────────────┬─────────────┬─────────────┐
│ product_id  │ business_id  │ name        │ price       │
├─────────────┼──────────────┼─────────────┼─────────────┤
│ 1           │ 101          │ Laptop      │ 1200.00     │
│ 2           │ 101          │ Mouse       │ 25.00       │
└─────────────┴──────────────┴─────────────┴─────────────┘
```

### When Business B Requests Products
```sql
-- What actually happens:
SELECT * FROM products WHERE business_id = 102;

-- What Business B sees:
┌─────────────┬──────────────┬─────────────┬─────────────┐
│ product_id  │ business_id  │ name        │ price       │
├─────────────┼──────────────┼─────────────┼─────────────┤
│ 3           │ 102          │ Laptop      │ 1100.00     │
│ 4           │ 102          │ Keyboard    │ 75.00       │
└─────────────┴──────────────┴─────────────┴─────────────┘
```

## Key Benefits

1. **Data Isolation**: Businesses never see each other's data
2. **Automatic Security**: No risk of forgetting to add business filters
3. **Efficient Storage**: One database serves all businesses
4. **Easy Management**: Centralized database administration
5. **Scalable Design**: Can support many businesses efficiently

## Behind the Scenes

The system automatically handles business context through:
1. **Session Storage**: Business ID stored when user selects a business
2. **Middleware**: Automatically adds business filters to all queries
3. **Database Queries**: All SELECT, INSERT, UPDATE, DELETE operations include business context
4. **Access Control**: Different user roles (regular, admin, superadmin) have different access levels

This approach ensures that your business data stays private and secure while benefiting from a shared, efficiently-managed infrastructure.