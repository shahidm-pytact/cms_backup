# Blog CMS API Documentation

## Overview

This document describes the REST API endpoints for managing blog posts in the CMS system. The API provides full CRUD (Create, Read, Update, Delete) functionality for blog management.

## Base URL

```
/api/blogs
```

## Authentication

All endpoints require authentication. Include authentication credentials in the request headers as per your authentication mechanism.

---

## 1. List All Blogs

Retrieves a paginated list of all blog posts with their metadata.

### Endpoint

```
GET /api/blogs
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number for pagination |
| `limit` | integer | No | 10 | Number of blogs per page |
| `sort` | string | No | "publishedDate" | Sort field (publishedDate, title, author) |
| `order` | string | No | "desc" | Sort order (asc, desc) |
| `author` | string | No | - | Filter by author name |
| `search` | string | No | - | Search in title, subtitle, or description |

### Response Format

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "blogs": [
      {
        "id": "blog-uuid-1",
        "slug": "backend-stack-production",
        "title": "The Backend Stack That Powers Production-Grade Systems",
        "subtitle": "A founder's perspective on choosing technology...",
        "description": "A founder's perspective on choosing technology...",
        "author": "Kaushal Khokhar",
        "authorImg": "https://media.licdn.com/...",
        "publishedDate": "2025-12-20T10:00:00.000Z",
        "readingTime": "6 min read",
        "blogImage": "/images/blog/backend_insights_blog.webp",
        "metaDescription": "Discover the production-ready backend stack...",
        "keywords": ["backend stack", "FastAPI", "PostgreSQL"],
        "status": "published",
        "createdAt": "2025-12-15T08:00:00.000Z",
        "updatedAt": "2025-12-20T10:00:00.000Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 25,
      "totalPages": 3,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

**Error Response (500 Internal Server Error)**

```json
{
  "success": false,
  "error": {
    "message": "Failed to retrieve blogs",
    "code": "INTERNAL_SERVER_ERROR"
  }
}
```

### Notes

- Returns only blog metadata, not the full content (sections and blocks)
- Use this endpoint for listing pages, search results, and blog previews
- The response excludes the `sections` array to keep payload size manageable

---

## 2. Create New Blog

Creates a new blog post in the system.

### Endpoint

```
POST /api/blogs
```

### Request Body

The request body should contain the complete blog structure including metadata and sections.

**Request Body Structure:**

```json
{
  "slug": "backend-stack-production",
  "title": "The Backend Stack That Powers Production-Grade Systems",
  "subtitle": "A founder's perspective on choosing technology...",
  "description": "A founder's perspective on choosing technology...",
  "author": "Kaushal Khokhar",
  "authorImg": "https://media.licdn.com/...",
  "publishedDate": "2025-12-20T10:00:00.000Z",
  "readingTime": "6 min read",
  "heroQuote": "One needs to dig into the ocean to find the real diamonds.",
  "blogImage": "/images/blog/backend_insights_blog.webp",
  "metaDescription": "Discover the production-ready backend stack...",
  "keywords": ["backend stack", "FastAPI", "PostgreSQL"],
  "status": "draft",
  "sections": [
    {
      "id": "introduction",
      "title": "Introduction",
      "order_index": 1,
      "badge": null,
      "badgeVariant": null,
      "blocks": [
        {
          "id": "intro-1",
          "type": "text",
          "order_index": 10,
          "content": "We build powerful features at PYTACT Solutions...",
          "links": []
        }
      ]
    }
  ]
}
```

### Response Format

**Success Response (201 Created)**

```json
{
  "success": true,
  "message": "Blog created successfully",
  "data": {
    "id": "blog-uuid-1",
    "slug": "backend-stack-production",
    "title": "The Backend Stack That Powers Production-Grade Systems",
    "status": "draft",
    "createdAt": "2025-12-21T10:00:00.000Z",
    "updatedAt": "2025-12-21T10:00:00.000Z"
  }
}
```

**Error Response (400 Bad Request)**

```json
{
  "success": false,
  "error": {
    "message": "Validation error",
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "slug",
        "message": "Slug is required and must be unique"
      },
      {
        "field": "sections[0].order_index",
        "message": "order_index is required for all sections"
      }
    ]
  }
}
```

**Error Response (409 Conflict)**

```json
{
  "success": false,
  "error": {
    "message": "Blog with this slug already exists",
    "code": "CONFLICT"
  }
}
```

### Validation Rules

- `slug` must be unique and URL-friendly
- `title` is required
- `sections` must be an array
- Each section must have `id`, `title`, `order_index`, and `blocks`
- Each block must have `id`, `type`, and `order_index`
- `order_index` must be numeric for both sections and blocks
- Block `id` values must be unique within their section
- Section `id` values must be unique within the blog

### Notes

- The `slug` will be used as the unique identifier for the blog
- If `status` is not provided, it defaults to `"draft"`
- `publishedDate` is optional for draft blogs
- Timestamps (`createdAt`, `updatedAt`) are automatically set by the system

---

## 3. Get Specific Blog with Details

Retrieves a complete blog post including all metadata, sections, and blocks.

### Endpoint

```
GET /api/blogs/{slug}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | Yes | Unique slug identifier of the blog post |

### Response Format

**Success Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": "blog-uuid-1",
    "slug": "backend-stack-production",
    "title": "The Backend Stack That Powers Production-Grade Systems",
    "subtitle": "A founder's perspective on choosing technology that scales from prototype to millions of users, backed by real-world case studies. Discover the proven tech stack: FastAPI, PostgreSQL, Redis, and Celery.",
    "description": "A founder's perspective on choosing technology that scales from prototype to millions of users, backed by real-world case studies. Discover the proven tech stack: FastAPI, PostgreSQL, Redis, and Celery.",
    "author": "Kaushal Khokhar",
    "authorImg": "https://media.licdn.com/dms/image/v2/D4D03AQFGxBtybrn-RQ/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1728039772945?e=2147483647&v=beta&t=ndiipYzFWpMNnIv5wKyG8wXD_a9wXMt2HYKQK5X8FrM",
    "publishedDate": "2025-12-20T10:00:00.000Z",
    "readingTime": "6 min read",
    "heroQuote": "One needs to dig into the ocean to find the real diamonds.",
    "blogImage": "/images/blog/backend_insights_blog.webp",
    "metaDescription": "Discover the production-ready backend stack that scales from prototype to millions of users. Learn about FastAPI, PostgreSQL, Redis, and Celery with real-world case studies showing how this tech stack handles high-volume systems.",
    "keywords": ["backend stack", "FastAPI", "PostgreSQL", "Redis", "Celery", "production backend", "scalable backend", "backend architecture", "Python backend", "production systems"],
    "status": "published",
    "sections": [
      {
        "id": "introduction",
        "title": "Introduction",
        "order_index": 1,
        "badge": null,
        "badgeVariant": null,
        "blocks": [
          {
            "id": "intro-1",
            "type": "text",
            "order_index": 10,
            "content": "We build powerful features at PYTACT Solutions with an AI driven development process. You can review our case study where I explained the challenges, resolutions and result metrics to highlight the difference in outcome. This was one of the amazing achievements as a software development expert.",
            "links": [
              {
                "text": "case study",
                "url": "https://pytact.com/caseStudy/case-study-01",
                "external": true
              }
            ]
          },
          {
            "id": "intro-2",
            "type": "text",
            "order_index": 20,
            "content": "The most crucial component of software application is backend architecture design and tech stack. The whole foundation relies on what technical stacks we opt for and how we wired them so that system becomes scalable from the beginning itself."
          },
          {
            "id": "intro-highlight",
            "type": "highlight",
            "order_index": 30,
            "content": "This is not a joke. With the advancement of AI, lots of beginners started developing applications but the real question is — \"how many of them have potential to ship it to production.\"",
            "variant": "primary"
          }
        ]
      }
    ],
    "createdAt": "2025-12-15T08:00:00.000Z",
    "updatedAt": "2025-12-20T10:00:00.000Z"
  }
}
```

**Error Response (404 Not Found)**

```json
{
  "success": false,
  "error": {
    "message": "Blog not found",
    "code": "NOT_FOUND"
  }
}
```

### Notes

- Returns the complete blog structure including all sections and blocks
- Use this endpoint when displaying the full blog post content
- The slug is case-sensitive and must match exactly

---

## 4. Update Blog

Updates an existing blog post with full replacement (PUT).

### Endpoint

```
PUT /api/blogs/{slug}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | Yes | Unique slug identifier of the blog post to update |

### Request Body

The request body should contain the complete blog structure to update.

**Request Body Structure:**

```json
{
  "slug": "backend-stack-production",
  "title": "The Backend Stack That Powers Production-Grade Systems",
  "subtitle": "Updated subtitle...",
  "description": "Updated description...",
  "author": "Kaushal Khokhar",
  "authorImg": "https://media.licdn.com/...",
  "publishedDate": "2025-12-20T10:00:00.000Z",
  "readingTime": "6 min read",
  "heroQuote": "One needs to dig into the ocean to find the real diamonds.",
  "blogImage": "/images/blog/backend_insights_blog.webp",
  "metaDescription": "Updated meta description...",
  "keywords": ["backend stack", "FastAPI", "PostgreSQL"],
  "status": "published",
  "sections": [
    {
      "id": "introduction",
      "title": "Introduction",
      "order_index": 1,
      "badge": null,
      "badgeVariant": null,
      "blocks": [
        {
          "id": "intro-1",
          "type": "text",
          "order_index": 10,
          "content": "Updated content...",
          "links": []
        }
      ]
    }
  ]
}
```

### Block Types Reference

The following block types are supported in the `sections[].blocks[]` array:

- `text` - Plain text content
- `code` - Code block with syntax highlighting
- `list` - Bulleted or numbered list
- `highlight` - Highlighted text block
- `quote` - Quote block
- `image` - Image block
- `tech-stack` - Technology stack display
- `metrics` - Metrics display
- `case-study` - Case study block
- `divider` - Visual divider
- `cta` - Call-to-action block
- `cards` - Card grid layout
- `problem-solution` - Problem-solution format
- `story` - Story narrative
- `comparison` - Comparison table
- `resources` - Resources list
- `author-bio` - Author biography
- `visual` - Visual content
- `steps` - Steps container
- `step` - Individual step

### Response Format

**Success Response (200 OK)**

```json
{
  "success": true,
  "message": "Blog updated successfully",
  "data": {
    "id": "blog-uuid-1",
    "slug": "backend-stack-production",
    "updatedAt": "2025-12-21T14:30:00.000Z"
  }
}
```

**Error Response (404 Not Found)**

```json
{
  "success": false,
  "error": {
    "message": "Blog not found",
    "code": "NOT_FOUND"
  }
}
```

**Error Response (400 Bad Request)**

```json
{
  "success": false,
  "error": {
    "message": "Validation error",
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "metadata.title",
        "message": "Title is required"
      }
    ]
  }
}
```

### Validation Rules

- `slug` must be unique (if changed)
- `title` is required
- `publishedDate` must be a valid ISO 8601 date string (if provided)
- `status` must be either `"draft"` or `"published"`
- `sections` must be an array
- Each section must have `id`, `title`, `order_index`, and `blocks`
- Each block must have `id`, `type`, and `order_index`
- `order_index` must be numeric for both sections and blocks
- Each block must have a valid `type` from the supported block types
- Block `id` values must be unique within their section
- Section `id` values must be unique within the blog
- Required fields for each block type must be present (see DATABASE_DESIGN.md for details)

### Notes

- PUT replaces the entire blog post
- The `slug` in the path parameter identifies which blog to update
- If `slug` is changed in the request body, the blog will be accessible via the new slug
- Timestamps (`createdAt`, `updatedAt`) are automatically managed by the system
- When updating sections or blocks, ensure `order_index` values are provided and valid

---

## 5. Delete Blog

Deletes a blog post from the system.

### Endpoint

```
DELETE /api/blogs/{slug}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `slug` | string | Yes | Unique slug identifier of the blog post to delete |

### Response Format

**Success Response (200 OK)**

```json
{
  "success": true,
  "message": "Blog deleted successfully",
  "data": {
    "slug": "backend-stack-production",
    "deletedAt": "2025-12-21T15:00:00.000Z"
  }
}
```

**Error Response (404 Not Found)**

```json
{
  "success": false,
  "error": {
    "message": "Blog not found",
    "code": "NOT_FOUND"
  }
}
```

**Error Response (403 Forbidden)**

```json
{
  "success": false,
  "error": {
    "message": "Insufficient permissions to delete this blog",
    "code": "FORBIDDEN"
  }
}
```

### Notes

- Deletion is permanent (unless soft-delete is implemented)
- Ensure proper authorization before allowing deletion
- Consider implementing a confirmation step or soft-delete mechanism
- Related resources (images, assets) may need separate cleanup

---

## Common Response Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created (for create endpoint) |
| 400 | Bad Request - Validation error |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Data Models

### Blog Metadata Structure

```typescript
{
  slug: string;              // Unique identifier, URL-friendly
  title: string;             // Main blog title
  subtitle: string;          // Subtitle or summary
  description: string;       // Full description
  author: string;            // Author name
  authorImg: string;         // Author image URL
  publishedDate: string;     // ISO 8601 date string
  readingTime: string;       // Estimated reading time (e.g., "6 min read")
  heroQuote?: string;        // Optional hero quote
  blogImage: string;         // Main blog image URL
  metaDescription: string;   // SEO meta description
  keywords: string[];        // Array of keywords for SEO
  status: "draft" | "published"; // Blog status
}
```

### Section Structure

```typescript
{
  id: string;                // Unique section identifier (required)
  title: string;             // Section title (required)
  order_index: number;        // Controls section ordering (required)
  badge?: string;            // Optional badge text
  badgeVariant?: string;     // Badge style variant (optional)
  blocks: Block[];           // Array of content blocks (required)
}
```

### Block Structure (Base)

All blocks share common properties:

```typescript
{
  id: string;                // Unique block identifier (required)
  type: string;              // Block type (required, see Block Types Reference)
  order_index: number;        // Controls block ordering (required)
  // ... type-specific properties
}
```

**Important:** All blocks must include `id`, `type`, and `order_index`. The `order_index` is critical for proper rendering order and should use gap-based numbering (10, 20, 30...).

---

## Best Practices

1. **Pagination**: Always use pagination for list endpoints to avoid large payloads
2. **Caching**: Consider implementing caching for frequently accessed blogs
3. **Validation**: Validate all input data before processing
4. **Error Handling**: Provide clear, actionable error messages
5. **Versioning**: Consider API versioning for future changes
6. **Rate Limiting**: Implement rate limiting to prevent abuse
7. **Content Security**: Validate and sanitize all user-generated content

---

## Example Usage Scenarios

### Scenario 1: Display Blog List Page

1. Call `GET /api/blogs?page=1&limit=10` to get the first page of blogs
2. Display metadata (title, author, publishedDate, blogImage) in a grid/list
3. Link each blog to its detail page using the `slug`

### Scenario 2: Display Full Blog Post

1. Extract slug from URL (e.g., `/blog/backend-stack-production`)
2. Call `GET /api/blogs/backend-stack-production` to get full content
3. Render sections and blocks according to their types
4. Apply appropriate styling based on block variants

### Scenario 3: Create New Blog Post

1. User fills out blog form with metadata and sections
2. Call `POST /api/blogs` with complete blog structure
3. Handle validation errors and display success message
4. Redirect to edit page or blog list

### Scenario 4: Edit Blog Post

1. Load existing blog using `GET /api/blogs/{slug}`
2. Allow user to edit metadata and sections
3. Ensure all sections and blocks have valid `order_index` values
4. Save changes using `PUT /api/blogs/{slug}`
5. Handle validation errors and display success message

### Scenario 5: Delete Blog Post

1. User confirms deletion action
2. Call `DELETE /api/blogs/{slug}`
3. Handle success/error response
4. Redirect to blog list page

---

## Notes for Implementation

- All date fields should use ISO 8601 format (e.g., `2025-12-20T10:00:00.000Z`)
- Slug values should be URL-friendly (lowercase, hyphens instead of spaces)
- `status` field supports `"draft"` or `"published"` values
- Image URLs can be relative paths or absolute URLs
- Block types may have different required/optional fields based on their type (see DATABASE_DESIGN.md for complete reference)
- **Critical:** All sections and blocks must include `order_index` for proper ordering
- Sections should use gap-based ordering (1, 2, 3, 4...)
- Blocks should use gap-based ordering (10, 20, 30, 40...)
- Always sort sections and blocks by `order_index` - never rely on array order
- The `content` field in the database stores only the `sections` array (metadata is stored in separate database columns)
- Consider implementing versioning or revision history for blog updates
