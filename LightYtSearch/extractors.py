"""
YouTube data extractors for parsing and extracting search results.
"""

import re
import json
from bs4 import BeautifulSoup

from .utils import colors

class YTInitialDataExtractor:
    """
    Extracts the initial data from a YouTube page using multiple methods.
    The ytInitialData contains all the search results and metadata.
    """
    
    def __init__(self, html_content: str, debug_mode: bool = False):
        """
        Initialize the extractor with HTML content
        
        Args:
            html_content (str): Raw HTML content from YouTube search page
            debug_mode (bool): Whether to print additional debug information
        """
        self.html_content = html_content
        self.debug_mode = debug_mode
        self.last_extraction_method = "Unknown"
    
    def _validate_ytdata(self, data):
        if not isinstance(data, dict):
            return False
        
        # First level validation
        expected_keys = ['responseContext', 'contents', 'header', 'metadata', 'trackingParams']
        found_keys = [key for key in expected_keys if key in data]
        
        # If we have at least 2 of these keys, it's likely a valid response
        if len(found_keys) >= 2:
            return True
            
        # Additional check for nested contents structure
        if 'contents' in data:
            contents = data['contents']
            
            # Check for known content structures
            if isinstance(contents, dict):
                content_types = list(contents.keys())
                valid_types = [
                    'twoColumnSearchResultsRenderer',
                    'twoColumnBrowseResultsRenderer',
                    'twoColumnWatchNextResults',
                    'sectionListRenderer',
                    'richGridRenderer'
                ]
                if any(t in content_types for t in valid_types):
                    return True
                
            # Alternative content structure as a list
            elif isinstance(contents, list) and len(contents) > 0:
                return True
        
        if self.debug_mode and 'contents' in data:
            print(f"{colors.fg.error}Content validation failed. Found keys: {colors.fg.yellow}{list(data.keys())}{colors.reset}")
        
        # Fallback check for result items
        return 'items' in data or 'estimatedResults' in data

    def _extract_with_regex(self, html_content):
        patterns = [
            # Standard format
            r'var\s+ytInitialData\s*=\s*({.+?})(?:;|<\/script>)',
            # Window assignment format
            r'window\["ytInitialData"\]\s*=\s*({.+?})(?:;|<\/script>)',
            # Simple assignment format
            r'ytInitialData\s*=\s*({.+?})(?:;|<\/script>)',
            # JSON inside script with JSON type
            r'<script[^>]+>\s*ytInitialData\s*=\s*({.+?})(?:;|<\/script>)',
            # More relaxed pattern
            r'\bytInitialData\b\s*=\s*({.+?})(?=;\s*(?:var|const|let|<\/script>))'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.finditer(pattern, html_content, re.DOTALL)
            
            for match in matches:
                try:
                    # Get the matched JSON string
                    json_str = match.group(1).strip()
                    
                    # Check for unclosed JSON and try to fix common issues
                    if json_str.count('{') != json_str.count('}'):
                        if self.debug_mode:
                            print(f"{colors.fg.warning}Unbalanced braces in JSON, attempting to repair{colors.reset}")
                        continue
                        
                    data = json.loads(json_str)
                    if self._validate_ytdata(data):
                        self.last_extraction_method = f"Regex Pattern {i+1}"
                        return data
                    
                except json.JSONDecodeError:
                    # Continue to next match if JSON is invalid
                    continue

        return None

    def _extract_from_script_tag(self, html_content):
        """Extract ytInitialData directly from script tags"""
        soup = BeautifulSoup(html_content, "html.parser")
        
        # First look for the dedicated script with just ytInitialData
        scripts = soup.find_all("script")
        
        for script in scripts:
            script_content = script.string
            if not script_content:
                continue
                
            if "ytInitialData" in script_content:
                # Try multiple extraction approaches
                extraction_methods = [
                    # Method 1: Standard assignment
                    (r'var\s+ytInitialData\s*=\s*({.+?});', 'Standard Assignment'),
                    # Method 2: Window assignment
                    (r'window\["ytInitialData"\]\s*=\s*({.+?});', 'Window Assignment'),
                    # Method 3: Simple assignment
                    (r'ytInitialData\s*=\s*({.+?});', 'Simple Assignment'),
                    # Method 4: JSON string assignment
                    (r'ytInitialData\s*=\s*\'(.+?)\';', 'String Assignment')
                ]
                
                for pattern, method_name in extraction_methods:
                    match = re.search(pattern, script_content, re.DOTALL)
                    if match:
                        try:
                            if "'" in pattern:  # String format needs unescaping
                                json_str = bytes(match.group(1), 'utf-8').decode('unicode_escape')
                            else:
                                json_str = match.group(1)
                                
                            data = json.loads(json_str)
                            if self._validate_ytdata(data):
                                self.last_extraction_method = f"Script Tag ({method_name})"
                                return data
                        except:
                            continue
        
        return None

    def _extract_balanced_json(self, text):
        """Extract a balanced JSON object from text, handling nested structures properly"""
        if not text:
            return None
            
        # Find the start of ytInitialData
        start_idx = text.find("ytInitialData")
        if start_idx == -1:
            return None
            
        # Find an opening brace after ytInitialData
        brace_idx = text.find("{", start_idx)
        if brace_idx == -1:
            return None
            
        # Track brace nesting level
        level = 0
        in_string = False
        escape_next = False
        end_idx = -1
        
        for i in range(brace_idx, len(text)):
            char = text[i]
            
            # Handle string literals
            if char == '"' and not escape_next:
                in_string = not in_string
            elif char == '\\' and not escape_next:
                escape_next = True
                continue
                
            if not in_string:
                if char == '{':
                    level += 1
                elif char == '}':
                    level -= 1
                    if level == 0:
                        end_idx = i + 1
                        break
                        
            escape_next = False
            
        if end_idx != -1:
            json_str = text[brace_idx:end_idx]
            try:
                data = json.loads(json_str)
                if self._validate_ytdata(data):
                    return data
            except:
                pass
                
        return None

    def extract(self, save_raw=False, output_path='output.json'):
        """
        Extract YouTube initial data using multiple methods
        
        Args:
            save_raw (bool): Whether to save the raw data to disk
            output_path (str): Path to save the extracted data
            
        Returns:
            dict: The extracted YouTube data or None if extraction failed
        """
        # Reset extraction method
        self.last_extraction_method = "Failed"
        
        # Try regex extraction first (fastest method)
        data = self._extract_with_regex(self.html_content)
        if data:
            if save_raw:
                self._save_json(data, output_path)
            return data
        
        # Try direct script tag extraction
        data = self._extract_from_script_tag(self.html_content)
        if data:
            if save_raw:
                self._save_json(data, output_path)
            return data
        
        # Try balanced JSON extraction as a last resort
        start_idx = self.html_content.find("ytInitialData")
        if start_idx != -1:
            text_after = self.html_content[start_idx:]
            data = self._extract_balanced_json(text_after)
            if data:
                self.last_extraction_method = "Balanced JSON Parser"
                if save_raw:
                    self._save_json(data, output_path)
                return data
        
        if self.debug_mode:
            print(f"{colors.fg.error}All extraction methods failed{colors.reset}")
            
        return None
    
    def _save_json(self, data, output_path='output.json'):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"{colors.fg.success}Data saved to {colors.fg.info}{output_path}{colors.reset}")
        except Exception as e:
            print(f"{colors.fg.error}Error saving JSON: {str(e)}{colors.reset}")