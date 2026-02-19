"""Blog CMS module constants."""
# Error Messages
ERROR_BLOG_NOT_FOUND = "Blog not found"
ERROR_DUPLICATE_BLOG_SLUG = "Blog with this slug already exists"
ERROR_BLOG_VALIDATION_ERROR = "Validation error"
ERROR_EMPTY_REQUEST_BODY = "Request body cannot be empty. Please provide at least one field to update."
ERROR_INVALID_SECTION_STRUCTURE = "Section must have id, title, order_index, and blocks"
ERROR_INVALID_BLOCK_STRUCTURE = "Block must have id, type, and order_index"
ERROR_DUPLICATE_SECTION_ID = "Section IDs must be unique within a blog"
ERROR_DUPLICATE_BLOCK_ID = "Block IDs must be unique within a section"

# Success Messages
SUCCESS_BLOG_CREATED = "Blog created successfully"
SUCCESS_BLOG_RETRIEVED = "Blog retrieved successfully"
SUCCESS_BLOGS_RETRIEVED = "Blogs retrieved successfully"
SUCCESS_BLOG_UPDATED = "Blog updated successfully"
SUCCESS_BLOG_DELETED = "Blog deleted successfully"

# Error Codes
ERROR_CODE_BLOG_NOT_FOUND = "BLOG_NOT_FOUND"
ERROR_CODE_DUPLICATE_BLOG_SLUG = "DUPLICATE_BLOG_SLUG"
ERROR_CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_CODE_CONFLICT = "CONFLICT"

# Status Values
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"

# Sort Fields
SORT_FIELD_PUBLISHED_DATE = "publishedDate"
SORT_FIELD_TITLE = "title"
SORT_FIELD_AUTHOR = "author"
SORT_FIELD_CREATED_AT = "createdAt"
SORT_FIELD_UPDATED_AT = "updatedAt"

# Sort Orders
SORT_ORDER_ASC = "asc"
SORT_ORDER_DESC = "desc"
