import re
from datetime import datetime
from typing import Dict, List, Optional, Any

class ApacheLogParser:
    """Parser for Apache log format"""
    PATTERN = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(.*?)\] \"(.*?)\" (\d{3}) (\d+) \"(.*?)\" \"(.*?)\"'
    
    @classmethod
    def parse_line(cls, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line"""
        match = re.match(cls.PATTERN, line)
        if match:
            ip, timestamp_str, request, status, size, referer, user_agent = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
                log_level = 'INFO' if int(status) < 400 else 'ERROR'
                return {
                    'timestamp': timestamp,
                    'log_level': log_level,
                    'source': 'apache',
                    'message': request,
                    'additional_fields': {
                        'ip': ip,
                        'status': int(status),
                        'size': int(size),
                        'referer': referer,
                        'user_agent': user_agent
                    }
                }
            except (ValueError, TypeError) as e:
                return None
        return None

class LogParserFactory:
    """Factory to create appropriate log parser"""
    @staticmethod
    def detect_format(lines: List[str]) -> Optional[str]:
        """Detect log format from sample lines"""
        for line in lines[:10]:  # Check first 10 lines
            if re.match(ApacheLogParser.PATTERN, line):
                return 'apache'
        return None

    @classmethod
    def get_parser(cls, format: str):
        """Get parser for the specified format"""
        if format == 'apache':
            return ApacheLogParser()
        raise ValueError(f"Unsupported log format: {format}")
