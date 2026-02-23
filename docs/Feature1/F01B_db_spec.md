# CMS DB DESIGN

## Blog CMS JSON Structure Documentation

---

### 1. Overview

This document defines the **standardized JSON structure** used to store blog content inside the `content` (JSONB) field of the `blogs` table.

The system follows a **Single-Table + JSON Architecture** where:

- **Blog metadata** is stored in structured database columns.
- **Full blog content** (sections + blocks) is stored inside a JSON field.
- **Ordering** is controlled using `order_index` at both section and block levels.

This structure is designed to be:

- **CMS-friendly**
- **Frontend-aligned**
- **Easy to render**
- **Version-safe**
- **Scalable** for marketing and content platforms

---

### 2. Database Context

#### Table: `blogs`

| Field | Purpose |
|-------|---------|
| `id` | Unique blog identifier |
| `slug` | Unique URL identifier |
| `title` | Blog title |
| `subtitle` | Optional subtitle |
| `description` | Listing description |
| `meta_description` | SEO description |
| `keywords` | SEO keywords |
| `hero_quote` | Hero highlight text |
| `blog_image` | Featured image URL |
| `reading_time` | Estimated read time |
| `status` | `draft` / `published` |
| `content` | JSON blog structure |
| `published_at` | Publish timestamp |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

---

### 3. JSON Content Structure

The `content` field must follow this structure.

#### Top-Level Schema

```json
{
  "sections": []
}
```

---

### 4. Section Object Structure

Each blog contains **multiple sections**.

```json
{
  "id": "string",
  "title": "string",
  "order_index": number,
  "blocks": [],
  "badge": "string (optional)",
  "badgeVariant": "string (optional)"
}
```

#### Section Fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String | Unique section identifier |
| `title` | String | Section heading |
| `order_index` | Number | Controls section ordering |
| `blocks` | Array | List of blocks inside section |
| `badge` | String (optional) | Badge text displayed with section title |
| `badgeVariant` | String (optional) | Badge variant (e.g., "accent", "primary") |

#### Ordering Rule

- Use **gap-based ordering** (1, 2, 3…)
- Allows inserting new sections without renumbering

---

### 5. Block Object Structure

Each section contains **multiple blocks**.

```json
{
  "id": "string",
  "type": "block_type",
  "order_index": number,
  "...block-specific fields"
}
```

#### Block Fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String | Unique block identifier |
| `type` | String | Block type (text, list, code, etc.) |
| `order_index` | Number | Controls block order |

#### Ordering Rule

- Use **gap-based ordering** (10, 20, 30…)
- Sorting should always be done by `order_index`

---

### 6. Supported Block Types and Structures

#### 6.1 Text Block

```json
{
  "id": "intro-1",
  "type": "text",
  "order_index": 10,
  "content": "Paragraph text"
}
```

**Optional:**

```json
"links": [
  {
    "text": "case study",
    "url": "https://example.com",
    "external": true
  }
]
```

**Example:**

```json
"blocks": [
  {
    "id": "intro-1",
    "type": "text",
    "content": "We build powerful features at PYTACT Solutions with an AI driven development process.",
    "links": [
      {
        "text": "case study",
        "url": "https://pytact.com/caseStudy/case-study-01",
        "external": true
      }
    ]
  }
]
```

---

#### 6.2 Code Block

```json
{
  "id": "view-code",
  "type": "code",
  "order_index": 30,
  "language": "sql",
  "code": "SQL OR CODE CONTENT"
}
```

---

#### 6.3 List Block

```json
{
  "id": "view-problems-list",
  "type": "list",
  "order_index": 50,
  "variant": "bullet",
  "items": [
    "Item 1",
    "Item 2"
  ]
}
```

**Variant Options:**
- `"bullet"` - Bullet point list
- `"number"` - Numbered list

---

#### 6.4 Highlight Block

```json
{
  "id": "intro-highlight",
  "type": "highlight",
  "order_index": 2,
  "content": "Important highlighted text",
  "variant": "primary"
}
```

**Variant Options:**
- `"primary"` - Primary highlight style
- `"accent"` - Accent highlight style

---

#### 6.5 Quote Block

```json
{
  "id": "intro-quote",
  "type": "quote",
  "order_index": 20,
  "content": "Build a dashboard for an org-admin."
}
```

---

#### 6.6 Image Block

```json
{
  "id": "intent-image",
  "type": "image",
  "order_index": 30,
  "src": "/images/blog/lovable-blog/lovable-blog-intent.png",
  "alt": "Diagram showing raw prompt transforming into structured intent JSON",
  "caption": "Raw prompt transforms into structured intent before any LLM is called."
}
```

**Fields:**
- `src` - Image URL path (required)
- `alt` - Alternative text for accessibility (required)
- `caption` - Image caption text (optional)

---

#### 6.7 Cards Block

```json
{
  "id": "stack-cards",
  "type": "cards",
  "order_index": 40,
  "columns": 4,
  "items": [
    {
      "title": "FastAPI",
      "description": "REST API service",
      "iconName": "Server"
    },
    {
      "title": "PostgreSQL",
      "description": "Primary Database",
      "iconName": "Database"
    }
  ]
}
```

**Fields:**
- `columns` - Number of columns for grid layout (required)
- `items` - Array of card objects (required)
  - `title` - Card title (required)
  - `description` - Card description (required)
  - `iconName` - Icon identifier (optional)

---

#### 6.8 Steps Block

```json
{
  "id": "layered-steps",
  "type": "steps",
  "order_index": 50,
  "title": "A conceptual layered breakdown may look like this:",
  "variant": "number",
  "steps": [
    "Intent Parsing Layer",
    "Context & State Engine",
    "Constraint & Design System Layer"
  ]
}
```

**Fields:**
- `title` - Steps section title (optional)
- `variant` - Display variant: `"number"` or `"bullet"` (optional)
- `steps` - Array of step text strings (required)

---

#### 6.9 Step Block

```json
{
  "id": "index-bp1-step",
  "type": "step",
  "order_index": 60,
  "stepNumber": 1,
  "title": "Create Indexes BEFORE Loading Data"
}
```

**Fields:**
- `stepNumber` - Step number (required)
- `title` - Step title (required)

**Note:** Step blocks are typically used within sections to create numbered step-by-step instructions. They can be combined with other block types (like code blocks) to create comprehensive guides.

---

#### 6.10 Comparison Block

```json
{
  "id": "prod-impact-table",
  "type": "comparison",
  "order_index": 70,
  "title": "Real Production Impact",
  "options": {
    "labelA": "Materialized View",
    "labelB": "Summary Table"
  },
  "items": [
    {
      "feature": "Data change for 1 org",
      "optionA": "Recompute all 50k orgs",
      "optionB": "Update 1 org"
    },
    {
      "feature": "CPU usage",
      "optionA": "Very high",
      "optionB": "Very low"
    }
  ]
}
```

**Fields:**
- `title` - Comparison table title (optional)
- `options` - Comparison labels (required)
  - `labelA` - Label for first option (required)
  - `labelB` - Label for second option (required)
- `items` - Array of comparison rows (required)
  - `feature` - Feature name being compared (required)
  - `optionA` - Value for first option (required)
  - `optionB` - Value for second option (required)

---

#### 6.11 Additional Block Types

The following block types are supported but not yet documented with examples. They follow the same base structure with `id`, `type`, and `order_index`:

| Block Type | Purpose |
|------------|---------|
| `tech-stack` | Display technology stack information |
| `metrics` | Display metrics or statistics |
| `case-study` | Case study content block |
| `divider` | Visual divider between sections |
| `cta` | Call-to-action block |
| `problem-solution` | Problem-solution format content |
| `story` | Story/narrative content block |
| `resources` | Resources or links block |
| `author-bio` | Author biography block |
| `visual` | Visual content block |

**Note:** These block types will be documented with full schemas as they are implemented and used in production content.

---

### 7. Ordering Strategy Best Practice

#### Why `order_index` Is Required

- Avoids dependency on array position
- Makes reordering predictable
- Simplifies diff comparison
- Enables partial updates

#### Recommended Numbering Strategy

Use gaps: **1, 2, 3, 4...**

---

### 8. Rendering Rules

**Frontend must:**

- Sort sections by `order_index`
- Sort blocks by `order_index`
- Render blocks based on `type`
- **Never rely on raw array order**

---

### 9. Validation Requirements

**Minimum validation rules:**

- `sections` must be an array
- Every section must contain `id`, `title`, `order_index`, `blocks`
- Every block must contain `id`, `type`, `order_index`
- `order_index` must be numeric
- `id` values must be unique within their level
- Section `badge` and `badgeVariant` are optional
- Block `type` must be one of the supported block types
- Required fields for each block type must be present:
  - **text**: `content` (required), `links` (optional)
  - **code**: `language` (required), `code` (required)
  - **list**: `variant` (required), `items` (required, array)
  - **highlight**: `content` (required), `variant` (optional)
  - **quote**: `content` (required)
  - **image**: `src` (required), `alt` (required), `caption` (optional)
  - **cards**: `columns` (required), `items` (required, array)
  - **steps**: `steps` (required, array), `title` (optional), `variant` (optional)
  - **step**: `stepNumber` (required), `title` (required)
  - **comparison**: `options` (required), `items` (required, array), `title` (optional)

---

### 10. Complete Block Type Reference

| Block Type | Required Fields | Optional Fields |
|------------|----------------|-----------------|
| `text` | `content` | `links` |
| `code` | `language`, `code` | - |
| `list` | `variant`, `items` | - |
| `highlight` | `content` | `variant` |
| `quote` | `content` | - |
| `image` | `src`, `alt` | `caption` |
| `cards` | `columns`, `items` | - |
| `steps` | `steps` | `title`, `variant` |
| `step` | `stepNumber`, `title` | - |
| `comparison` | `options`, `items` | `title` |
| `tech-stack` | *To be documented* | - |
| `metrics` | *To be documented* | - |
| `case-study` | *To be documented* | - |
| `divider` | - | - |
| `cta` | *To be documented* | - |
| `problem-solution` | *To be documented* | - |
| `story` | *To be documented* | - |
| `resources` | *To be documented* | - |
| `author-bio` | *To be documented* | - |
| `visual` | *To be documented* | - |

---

### 11. Development Guidelines

#### Block Type Implementation

When implementing a new block type:

1. **Add to BLOCK_TYPES constant** in frontend code
2. **Document the schema** in this file with:
   - Required fields
   - Optional fields
   - Field types and constraints
   - Example JSON structure
3. **Update validation** to enforce required fields
4. **Create renderer component** in frontend
5. **Test with sample content** before production use

#### Order Index Best Practices

- **Sections**: Use 1, 2, 3, 4... (small gaps allow easy insertion)
- **Blocks**: Use 10, 20, 30, 40... (larger gaps allow insertion between blocks)
- **Never skip order_index** - always assign a value
- **Always sort by order_index** - never rely on array order

#### Data Migration

When updating block structures:

1. **Maintain backward compatibility** where possible
2. **Add new fields as optional** initially
3. **Use migrations** to update existing content if needed
4. **Validate** all existing content after schema changes