"""Email template loader and renderer."""
import os
from pathlib import Path
from typing import Dict


class EmailTemplateLoader:
    """Load and render email templates."""
    
    def __init__(self):
        """Initialize template loader with templates directory."""
        # Get the directory where this file is located
        current_dir = Path(__file__).parent
        self.templates_dir = current_dir / "templates"
    
    def load_template(self, template_name: str) -> str:
        """Load HTML template from file.
        
        Args:
            template_name: Name of template file (e.g., "welcome.html")
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def render_template(self, template_name: str, context: Dict[str, str]) -> str:
        """Render template with context variables.
        
        Args:
            template_name: Name of template file (e.g., "welcome.html")
            context: Dictionary of variables to replace in template
            
        Returns:
            Rendered HTML string
        """
        template = self.load_template(template_name)
        
        # Simple template variable replacement
        # Replace {{variable}} with context values
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        
        return rendered
    
    def get_text_version(self, html_content: str) -> str:
        """Extract plain text version from HTML (simple implementation).
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text version
        """
        # Simple HTML to text conversion
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
