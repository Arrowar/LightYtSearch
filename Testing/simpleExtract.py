"""
Simple YouTube data extraction test script.
Demonstrates different extraction techniques for YouTube initial data.
"""

import re
import json
import httpx
from bs4 import BeautifulSoup
from ua_generator import generate

class YouTubeDataExtractor:
    def __init__(self):
        self.headers = {
            "User-Agent": generate().text,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def _validate_ytdata(self, data):
        if not isinstance(data, dict):
            return False
        
        valid_keys = [
            ('contents', 'twoColumnSearchResultsRenderer'),
            ('contents', 'twoColumnBrowseResultsRenderer'),
            ('contents', 'twoColumnWatchNextResults'),
            ('responseContext', 'serviceTrackingParams'),
        ]
        
        for main_key, sub_key in valid_keys:
            if main_key in data:
                if sub_key is None or sub_key in data[main_key]:
                    return True
        return False

    def _extract_with_regex(self, html_content):
        pattern = r'var\s+ytInitialData\s*=\s*({.+?});'
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if self._validate_ytdata(data):
                    print("Extraction successful using regex method")
                    return data
            except json.JSONDecodeError:
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
                                print("Extraction successful using BeautifulSoup direct method")
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
                                print("Extraction successful using balanced JSON method")
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
                            print("Extraction successful using escaped JSON method")
                            return data
                except:
                    continue
        return None

    def extract(self, query):
        url = "https://www.youtube.com/results"
        params = {"search_query": query}
        
        try:
            response = httpx.get(url, params=params, headers=self.headers, timeout=5)
            print(response.status_code)
            html_content = response.text
            
            # Try different extraction methods
            data = self._extract_with_regex(html_content)
            if data:
                return data
                
            data = self._extract_with_bs4(html_content)
            if data:
                return data
                
            return None
            
        except Exception:
            return None

if __name__ == "__main__":
    extractor = YouTubeDataExtractor()
    data = extractor.extract(input("Query: ").strip())
    print("Extraction successful" if data else "Extraction failed")