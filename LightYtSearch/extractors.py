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
    
    def _validate_ytdata(self, data):
        if not isinstance(data, dict):
            return False
        
        # First level validation
        expected_keys = ['responseContext', 'contents']
        found_keys = [key for key in expected_keys if key in data]
        
        if len(found_keys) < 1:
            if self.debug_mode:
                print(f"{colors.fg.error}Data validation failed: missing required keys. Found: {colors.fg.yellow}{list(data.keys())}{colors.reset}")
            return False
        
        # Second level validation - check structure of contents
        content_types = []
        if 'contents' in data:
            contents = data['contents']
            
            # Check for known content structures
            if isinstance(contents, dict):
                content_types = list(contents.keys())
                valid_types = [
                    'twoColumnSearchResultsRenderer',
                    'twoColumnBrowseResultsRenderer',
                    'twoColumnWatchNextResults',
                    'sectionListRenderer'
                ]
                if any(t in content_types for t in valid_types):
                    return True
                
            # Alternative content structure as a list
            elif isinstance(contents, list) and len(contents) > 0:
                return True
        
        if self.debug_mode and 'contents' in data:
            print(f"{colors.fg.error}Content validation failed. Found content types: {colors.fg.yellow}{content_types}{colors.reset}")
        
        # Fallback validation - just check for responseContext which is always present
        return 'responseContext' in data

    def _extract_with_regex(self, html_content):
        patterns = [
            r'var\s+ytInitialData\s*=\s*({.+?});',
            r'window\["ytInitialData"\]\s*=\\s*({.+?});',
            r'ytInitialData\s*=\s*({.+?});'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))

                    if self._validate_ytdata(data):
                        if self.debug_mode:
                            print(f"{colors.fg.success}Extraction successful using regex method{colors.reset}")

                            # Debug info about data structure
                            if 'contents' in data:
                                if isinstance(data['contents'], dict):
                                    print(f"{colors.fg.info}Content keys: {colors.fg.yellow}{list(data['contents'].keys())}{colors.reset}")
                                elif isinstance(data['contents'], list):
                                    print(f"{colors.fg.info}Content is a list with {colors.fg.yellow}{len(data['contents'])}{colors.fg.info} items{colors.reset}")

                        return data
                    
                except json.JSONDecodeError as e:
                    if self.debug_mode:
                        print(f"{colors.fg.error}JSON decode error: {str(e)}{colors.reset}")
                    pass

        return None

    def _extract_balanced_json(self, text):
        brace_count = 0
        in_string = False
        escape_next = False
        json_str = ""
        
        for char in text:
            if char == '\\' and not escape_next:
                escape_next = True
                json_str += char
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                
            escape_next = False
            
            if not in_string:
                if char == '{':
                    if brace_count == 0 and not json_str:
                        json_str += char
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_str:
                        json_str += char
                        break
            
            if json_str:
                json_str += char
                
        return json_str if json_str.startswith('{') and json_str.endswith('}') else None

    def _extract_with_bs4(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        for script in soup.find_all("script"):
            if script.string and "ytInitialData" in script.string:

                # Method 1: Direct JSON extraction
                try:
                    start_markers = [
                        "var ytInitialData = ", 
                        "ytInitialData = ", 
                        "window[\"ytInitialData\"] = "
                    ]

                    for marker in start_markers:
                        pos = script.string.find(marker)
                        if pos != -1:
                            json_str = script.string[pos + len(marker):].split(";")[0]
                            data = json.loads(json_str)
                            if self._validate_ytdata(data):
                                if self.debug_mode:
                                    print(f"{colors.fg.success}Extraction successful using BeautifulSoup direct method{colors.reset}")
                                return data        
                except:
                    pass

                # Method 2: Balanced JSON extraction
                try:
                    start_pos = script.string.find("ytInitialData")
                    if start_pos != -1:
                        json_str = self._extract_balanced_json(script.string[start_pos:])
                        if json_str:
                            data = json.loads(json_str)
                            if self._validate_ytdata(data):
                                if self.debug_mode:
                                    print(f"{colors.fg.success}Extraction successful using balanced JSON method{colors.reset}")
                                return data
                except:
                    pass

                # Method 3: Escaped JSON extraction
                try:
                    if "ytInitialData = '" in script.string:
                        data_str = script.string.split("ytInitialData = '")[1].split("';")[0]
                        data_str = bytes(data_str, 'utf-8').decode('unicode_escape')
                        data = json.loads(data_str)
                        if self._validate_ytdata(data):
                            if self.debug_mode:
                                print(f"{colors.fg.success}Extraction successful using escaped JSON method{colors.reset}")
                            return data
                except:
                    continue
        return None

    def _save_json(self, data, output_path='output.json'):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"{colors.fg.success}Data saved to {colors.fg.info}{output_path}{colors.reset}")
        except Exception as e:
            print(f"{colors.fg.error}Error saving JSON: {str(e)}{colors.reset}")

    def extract(self, save_raw=False, output_path='output.json'):
        """
        Extract YouTube initial data using multiple methods
        
        Args:
            save_raw (bool): Whether to save the raw data to disk
            output_path (str): Path to save the extracted data
            
        Returns:
            dict: The extracted YouTube data or None if extraction failed
        """
        # Try different extraction methods
        data = self._extract_with_regex(self.html_content)
        if data:
            if save_raw:
                self._save_json(data, output_path)
            
            if self.debug_mode and 'contents' in data:
                self._analyze_contents_structure(data['contents'])
                
            return data
            
        data = self._extract_with_bs4(self.html_content)
        if data:
            if save_raw:
                self._save_json(data, output_path)
            
            if self.debug_mode and 'contents' in data:
                self._analyze_contents_structure(data['contents'])
                
            return data
            
        return None
        
    def _analyze_contents_structure(self, contents):
        """Analyze and print the structure of YouTube contents for debugging"""
        if isinstance(contents, dict):
            print(f"{colors.fg.info}Contents is a dictionary with keys: {colors.fg.yellow}{list(contents.keys())}{colors.reset}")
            
            # Check for section list renderer
            if 'sectionListRenderer' in contents:
                sections = contents['sectionListRenderer'].get('contents', [])
                print(f"{colors.fg.info}Found {colors.fg.cyan}{len(sections)}{colors.fg.info} sections in sectionListRenderer{colors.reset}")
                
                # Analyze first few sections
                for i, section in enumerate(sections[:3]):
                    section_type = next(iter(section.keys()), "unknown")
                    print(f"{colors.fg.info}  Section {i+1} type: {colors.fg.teal}{section_type}{colors.reset}")
                    
                    if section_type == 'itemSectionRenderer':
                        items = section['itemSectionRenderer'].get('contents', [])
                        print(f"{colors.fg.info}    Contains {colors.fg.cyan}{len(items)}{colors.fg.info} items{colors.reset}")
                        
                        # Show first few item types
                        item_types = [next(iter(item.keys()), "unknown") for item in items[:5]]
                        print(f"{colors.fg.info}    First few item types: {colors.fg.yellow}{item_types}{colors.reset}")
            
            # Check for two column search results
            elif 'twoColumnSearchResultsRenderer' in contents:
                primary = contents['twoColumnSearchResultsRenderer'].get('primaryContents', {})
                if 'sectionListRenderer' in primary:
                    sections = primary['sectionListRenderer'].get('contents', [])
                    print(f"{colors.fg.info}Found {colors.fg.cyan}{len(sections)}{colors.fg.info} sections in twoColumnSearchResultsRenderer{colors.reset}")
        
        elif isinstance(contents, list):
            print(f"{colors.fg.info}Contents is a list with {colors.fg.cyan}{len(contents)}{colors.fg.info} items{colors.reset}")
            
            # Show types of first few items
            for i, item in enumerate(contents[:3]):
                item_type = next(iter(item.keys()), "unknown") if isinstance(item, dict) else type(item).__name__
                print(f"{colors.fg.info}  Item {i+1} type: {colors.fg.teal}{item_type}{colors.reset}")