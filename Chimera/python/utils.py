import time
import asyncio
import os
import re
import threading
import uuid
import urllib.parse
import json
import csv
from io import StringIO
import gzip
import base64
import zlib
from collections import OrderedDict
from functools import wraps
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import gc

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception

try:
    import yaml
except ImportError:
    yaml = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


class TraceContext:
    """Trace context manager for correlating logs across function calls and API requests."""
    
    _context_stack = []
    
    @classmethod
    def generate_trace_id(cls) -> str:
        """Generate a unique trace ID."""
        return f"tr-{uuid.uuid4().hex[:16]}"
    
    @classmethod
    def generate_span_id(cls) -> str:
        """Generate a unique span ID for tracking request flow within a trace."""
        return f"sp-{uuid.uuid4().hex[:8]}"
    
    @classmethod
    def get_current_trace_id(cls) -> str | None:
        """Get the current trace ID from the context stack."""
        if cls._context_stack:
            return cls._context_stack[-1].get('trace_id')
        return None
    
    @classmethod
    def get_current_span_id(cls) -> str | None:
        """Get the current span ID from the context stack."""
        if cls._context_stack:
            return cls._context_stack[-1].get('span_id')
        return None
    
    @classmethod
    def push_context(cls, trace_id: str = None, span_id: str = None) -> dict:
        """Push a new trace context onto the stack."""
        if trace_id is None:
            trace_id = cls.generate_trace_id()
        if span_id is None:
            span_id = cls.generate_span_id()
        
        context = {'trace_id': trace_id, 'span_id': span_id}
        cls._context_stack.append(context)
        return context
    
    @classmethod
    def pop_context(cls) -> dict | None:
        """Pop the current trace context from the stack."""
        if cls._context_stack:
            return cls._context_stack.pop()
        return None


def create_correlation_headers(trace_id: str = None, span_id: str = None, parent_span_id: str = None) -> dict:
    """Create HTTP headers with trace and correlation IDs for distributed tracing across microservices or API calls."""
    if trace_id is None:
        trace_id = TraceContext.get_current_trace_id() or TraceContext.generate_trace_id()
    if span_id is None:
        span_id = TraceContext.get_current_span_id() or TraceContext.generate_span_id()
    
    headers = {
        'x-trace-id': trace_id,
        'x-span-id': span_id
    }
    
    if parent_span_id:
        headers['x-parent-span-id'] = parent_span_id
    
    # Standard W3C Trace Context headers
    headers['traceparent'] = f"00-{trace_id.replace('tr-', '')}-{span_id.replace('sp-', '0' * (16 - len(span_id.replace('sp-', ''))))}-01"
    
    return headers


def extract_correlation_headers(headers: dict) -> dict:
    """Extract trace and correlation IDs from HTTP request headers."""
    result = {}
    
    if 'x-trace-id' in headers:
        result['trace_id'] = headers['x-trace-id']
    elif 'traceparent' in headers:
        traceparent = headers['traceparent']
        parts = traceparent.split('-')
        if len(parts) >= 2:
            trace_version = parts[0]
            trace_id = parts[1]
            span_id = parts[2]
            result['trace_id'] = f"tr-{trace_id}"
            result['span_id'] = f"sp-{span_id}"
    
    if 'x-span-id' in headers:
        result['span_id'] = headers['x-span-id']
    elif 'traceparent' in headers and 'span_id' not in result:
        traceparent = headers['traceparent']
        parts = traceparent.split('-')
        if len(parts) >= 3:
            span_id = parts[2]
            result['span_id'] = f"sp-{span_id}"
    
    if 'x-parent-span-id' in headers:
        result['parent_span_id'] = headers['x-parent-span-id']
        
    return result


def get_current_trace_id():
    """Get the current active trace ID."""
    return TraceContext.get_current_trace_id()


def get_current_span_id():
    """Get the current active span ID for request flow tracking."""
    return TraceContext.get_current_span_id()


def generate_trace_id():
    """Generate a unique trace ID."""
    return TraceContext.generate_trace_id()


def generate_span_id():
    """Generate a unique span ID."""
    return TraceContext.generate_span_id()


@contextmanager
def trace_context(trace_id: str = None):
    """Context manager to correlate logs across function calls with a trace ID."""
    TraceContext.push_context(trace_id)
    try:
        yield TraceContext.get_current_trace_id()
    finally:
        TraceContext.pop_context()


@contextmanager
def large_data_transform():
    """Context manager to aid garbage collection after large deeply-nested dictionary transformations."""
    try:
        yield
    finally:
        # Explicitly trigger garbage collection for large merged configs or transformed dicts
        gc.collect()


@contextmanager
def merged_config_cleanup():
    """Context manager to explicitly cleanup and collect garbage after large merged configurations."""
    try:
        yield
    finally:
        # Explicitly trigger garbage collection for large merged configs
        gc.collect()


def get_current_trace_id():
    """Get the current active trace ID."""
    return TraceContext.get_current_trace_id()


def generate_trace_id():
    """Generate a unique trace ID."""
    return TraceContext.generate_trace_id()


class FileLock:
    """Context manager for file locking using exclusive file creation."""
    
    def __init__(self, lock_path: str, timeout: int = 10):
        self.lock_path = lock_path
        self.timeout = timeout
        
    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                with open(self.lock_path, 'x'):
                    pass
                return self
            except FileExistsError:
                pass
            
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"Could not acquire lock {self.lock_path}")
            
            time.sleep(0.1)
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            os.remove(self.lock_path)
        except OSError:
            pass


def get_file_lock(lock_path: str, timeout: int = 10) -> FileLock:
    """Create a file lock context manager for concurrent access protection."""
    return FileLock(lock_path, timeout)


class ConfigFileLock(FileLock):
    """Context manager for locking configuration files."""
    
    def __init__(self, config_path: str, timeout: int = 10):
        lock_dir = os.path.dirname(config_path) or '.'
        lock_file = os.path.join(lock_dir, f".{os.path.basename(config_path)}.lock")
        super().__init__(lock_file, timeout)


class SnapshotFileLock(FileLock):
    """Context manager for locking snapshot files."""
    
    def __init__(self, snapshot_path: str, timeout: int = 10):
        lock_dir = os.path.dirname(snapshot_path) or '.'
        lock_file = os.path.join(lock_dir, f".{os.path.basename(snapshot_path)}.lock")
        super().__init__(lock_file, timeout)


def get_config_file_lock(config_path: str, timeout: int = 10) -> ConfigFileLock:
    """Create a file lock context manager for configuration files."""
    return ConfigFileLock(config_path, timeout)


def get_snapshot_file_lock(snapshot_path: str, timeout: int = 10) -> SnapshotFileLock:
    """Create a file lock context manager for snapshot files."""
    return SnapshotFileLock(snapshot_path, timeout)


def generate_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """Generate a formatted timestamp string."""
    return datetime.now().strftime(format_str)


def format_string(template: str, **kwargs) -> str:
    """Format a string with provided keyword arguments."""
    return template.format(**kwargs)


def sanitize_filename(filename: str) -> str:
    """Remove or replace invalid characters for filenames."""
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized.strip()


def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word."""
    return ' '.join(word.capitalize() for word in text.split(' '))


def retry(retries: int = 3, backoff_base: float = 1.0, backoff_max: float = 60.0, exceptions: tuple = (Exception,)):
    """Retry decorator with configurable retries and exponential backoff strategy."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    attempt += 1
                    if attempt >= retries:
                        raise
                    backoff_time = min(backoff_max, backoff_base ** attempt)
                    time.sleep(backoff_time)
            return None
        return wrapper
    return decorator


def async_retry(retries: int = 3, backoff_base: float = 1.0, backoff_max: float = 60.0, exceptions: tuple = (Exception,)):
    """Async retry decorator with configurable retries and exponential backoff strategy."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    attempt += 1
                    if attempt >= retries:
                        raise
                    backoff_time = min(backoff_max, backoff_base ** attempt)
                    await asyncio.sleep(backoff_time)
            return None
        return wrapper
    return decorator


def load_yaml(file_path: str, timeout: float = 30.0) -> dict:
    """Load YAML data from a file."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    
    def _load():
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    return execute_with_timeout(_load, timeout=timeout)


def dump_yaml(data: dict, file_path: str, timeout: float = 30.0) -> None:
    """Dump Python dictionary to a YAML file."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    
    def _dump():
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
    
    execute_with_timeout(_dump, timeout=timeout)


def parse_yaml(yaml_string: str) -> dict:
    """Parse a YAML string to a Python dictionary."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    return yaml.safe_load(yaml_string) or {}


def serialize_yaml(data: dict) -> str:
    """Serialize a Python dictionary to a YAML string."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    return yaml.safe_dump(data, default_flow_style=False, allow_unicode=True) or ""


class RateLimiter:
    """Rate limiter with configurable requests per second or minute."""
    
    def __init__(self, requests_per_second: float = 0.0, requests_per_minute: float = 0.0):
        if requests_per_second > 0:
            self.interval = 1.0 / requests_per_second
        elif requests_per_minute > 0:
            self.interval = 60.0 / requests_per_minute
        else:
            raise ValueError("Either requests_per_second or requests_per_minute must be greater than 0")
        
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def acquire(self):
        """Wait if necessary to enforce the rate limit."""
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self._last_request_time
            
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                time.sleep(sleep_time)
                
            self._last_request_time = time.time()

    async def acquire_async(self):
        """Async version of acquire."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self.interval:
            sleep_time = self.interval - elapsed
            await asyncio.sleep(sleep_time)
            
        self._last_request_time = time.time()


class CacheManager:
    """Cache manager with TTL-based expiration and memory-limited storage."""
    
    def __init__(self, max_size: int = 100):
        self._cache = {}
        self._ttl_cache = {}
        self.max_size = max_size
        self._lock = threading.Lock()
        
    def set(self, key: str, value: any, ttl: float | None = None) -> None:
        """Store a value with optional TTL in seconds."""
        with self._lock:
            if len(self._cache) >= self.max_size:
                first_key = next(iter(self._cache))
                del self._cache[first_key]
                self._ttl_cache.pop(first_key, None)
                
            self._cache[key] = value
            if ttl is not None:
                self._ttl_cache[key] = {'expires_at': time.time() + ttl}
            else:
                self._ttl_cache.pop(key, None)
            
    def get(self, key: str) -> any | None:
        """Retrieve a value from cache or return None if expired/missing."""
        with self._lock:
            if key in self._ttl_cache:
                expires_at = self._ttl_cache[key].get('expires_at')
                if expires_at and time.time() > expires_at:
                    del self._cache[key]
                    del self._ttl_cache[key]
                    return None
                    
            return self._cache.get(key)
            
    def delete(self, key: str) -> None:
        """Remove a value from cache."""
        with self._lock:
            self._cache.pop(key, None)
            self._ttl_cache.pop(key, None)
            
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._ttl_cache.clear()


class LRUCache:
    """LRU (Least Recently Used) cache with max_size limit and automatic eviction."""
    
    def __init__(self, max_size: int):
        if max_size <= 0:
            raise ValueError("max_size must be greater than 0")
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        
    def get(self, key: any) -> any | None:
        """Retrieve a value from cache or return None if missing."""
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]
            
    def set(self, key: any, value: any) -> None:
        """Store a value in cache, evicting LRU items if at capacity."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)
                self._cache[key] = value
                
    def delete(self, key: any) -> None:
        """Remove a value from cache."""
        with self._lock:
            self._cache.pop(key, None)
            
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            
    def __contains__(self, key: any) -> bool:
        """Check if a key is in the cache."""
        with self._lock:
            return key in self._cache
            
    def __len__(self) -> int:
        """Return the number of items in the cache."""
        with self._lock:
            return len(self._cache)


def sanitize_string(text: str, replace_char: str = '_') -> str:
    """Sanitize a string by removing or replacing invalid characters."""
    if not isinstance(text, str):
        return text
    sanitized = re.sub(r'[<>:"/\\|?*]', replace_char, text)
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Validate email format using regex pattern."""
    if not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


def validate_pattern(text: str, pattern: str) -> bool:
    """Validate text against a regex pattern."""
    if not isinstance(text, str) or not isinstance(pattern, str):
        return False
    try:
        return re.match(pattern, text) is not None
    except re.error:
        return False


def clean_user_input(data: str) -> str:
    """Clean user-provided data by removing excess whitespace and HTML tags."""
    if not isinstance(data, str):
        return data
    data = re.sub(r'<[^>]+>', '', data)
    data = re.sub(r'\s+', ' ', data)
    return data.strip()


def sanitize_dict(data: dict) -> dict:
    """Sanitize all string values in a dictionary."""
    if not isinstance(data, dict):
        return data
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = clean_user_input(sanitize_string(value))
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        else:
            sanitized[key] = value
    return sanitized


def get_os() -> str:
    """Detect and return the current operating system."""
    if os.name == 'nt':
        return 'windows'
    elif os.name == 'posix':
        import platform
        sys_name = platform.system()
        if sys_name == 'Darwin':
            return 'darwin'
        elif sys_name == 'Linux':
            return 'linux'
        else:
            return sys_name.lower()
    return 'unknown'


def get_python_version() -> str:
    """Return the current Python version as a string."""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def is_ci_environment() -> bool:
    """Detect if running in a CI/CD environment."""
    ci_env_vars = [
        'CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL', 
        'TRAVIS', 'CIRCLECI', 'DRONE', 'BUILDKITE', 'TEAMCITY_VERSION'
    ]
    for var in ci_env_vars:
        if os.environ.get(var):
            return True
    return False


def get_running_context() -> str:
    """Return the running context: 'ci' or 'local'."""
    return 'ci' if is_ci_environment() else 'local'


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten a nested dictionary using dot-path strings for keys."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def unflatten_dict(d: dict, sep: str = '.') -> dict:
    """Unflatten a dictionary with dot-path keys back to nested structure."""
    result = {}
    for k, v in d.items():
        parts = k.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = v
    return result


def get_by_dot_path(d: dict, path: str, default: any = None) -> any:
    """Retrieve a value from a dictionary using a dot-path string."""
    parts = path.split('.')
    current = d
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def set_by_dot_path(d: dict, path: str, value: any) -> dict:
    """Set a value in a dictionary using a dot-path string."""
    parts = path.split('.')
    current = d
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value
    return d


def filter_dict_by_keys(d: dict, allowed_keys: list | set) -> dict:
    """Filter a dictionary to only include keys in the allowed_keys list or set."""
    return {k: v for k, v in d.items() if k in allowed_keys}


def filter_dict_by_pattern(d: dict, pattern: str, recursive: bool = False) -> dict:
    """Filter a dictionary by key regex pattern."""
    compiled_pattern = re.compile(pattern)
    result = {}
    for k, v in d.items():
        if compiled_pattern.match(str(k)):
            if recursive and isinstance(v, dict):
                result[k] = filter_dict_by_pattern(v, pattern, True)
            else:
                result[k] = v
    return result


def filter_dict_by_value(d: dict, value: any, recursive: bool = False) -> dict:
    """Filter a dictionary to only include entries matching a specific value."""
    result = {}
    for k, v in d.items():
        if v == value:
            result[k] = v
        elif recursive and isinstance(v, dict):
            filtered_sub = filter_dict_by_value(v, value, True)
            if filtered_sub:
                result[k] = filtered_sub
    return result


def compress_json(data: dict | str, encoding: str = 'utf-8') -> str:
    """Compress JSON data using gzip and encode to base64 string."""
    if isinstance(data, dict):
        json_str = json.dumps(data)
    else:
        json_str = data
    
    compressed_bytes = gzip.compress(json_str.encode(encoding))
    return base64.b64encode(compressed_bytes).decode(encoding)


def decompress_json(compressed_data: str, encoding: str = 'utf-8') -> dict | str:
    """Decompress base64 encoded gzip JSON data and return as dict or string."""
    compressed_bytes = base64.b64decode(compressed_data)
    decompressed_bytes = gzip.decompress(compressed_bytes)
    json_str = decompressed_bytes.decode(encoding)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return json_str


def compress_string(data: str, encoding: str = 'utf-8') -> str:
    """Compress string data using gzip and encode to base64 string."""
    compressed_bytes = gzip.compress(data.encode(encoding))
    return base64.b64encode(compressed_bytes).decode(encoding)


def decompress_string(compressed_data: str, encoding: str = 'utf-8') -> str:
    """Decompress base64 encoded gzip string data."""
    compressed_bytes = base64.b64decode(compressed_data)
    decompressed_bytes = gzip.decompress(compressed_bytes)
    return decompressed_bytes.decode(encoding)


class SemaphorePool:
    """Semaphore pool for managing concurrent operations with limited concurrency."""
    
    def __init__(self, max_concurrent: int):
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0")
        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        
    def acquire(self):
        """Acquire a slot from the pool."""
        self._semaphore.acquire()
        
    def release(self):
        """Release a slot back to the pool."""
        self._semaphore.release()
        
    @contextmanager
    def context(self):
        """Context manager for acquiring and releasing a slot."""
        self.acquire()
        try:
            yield
        finally:
            self.release()


class AsyncSemaphorePool:
    """Async semaphore pool for managing concurrent async operations with limited concurrency."""
    
    def __init__(self, max_concurrent: int):
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0")
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
    async def acquire(self):
        """Acquire a slot from the pool."""
        await self._semaphore.acquire()
        
    async def release(self):
        """Release a slot back to the pool."""
        self._semaphore.release()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.release()


class WorkerPool:
    """Worker pool for managing concurrent execution with limited concurrency."""
    
    def __init__(self, max_workers: int = 5):
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")
        self.max_workers = max_workers
        self._semaphore = threading.Semaphore(max_workers)
        
    def execute(self, func, *args, **kwargs):
        """Execute a function with semaphore-based concurrency limit."""
        with self._semaphore:
            return func(*args, **kwargs)

    async def execute_async(self, func, *args, **kwargs):
        """Execute an async function with async semaphore-based concurrency limit."""
        semaphore = asyncio.Semaphore(self.max_workers)
        async with semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, func, *args, **kwargs)


class IOContext:
    """IO context manager to coordinate concurrent file reads/writes with proper locking and resource cleanup."""
    
    def __init__(self, max_concurrent_operations: int = 10):
        if max_concurrent_operations <= 0:
            raise ValueError("max_concurrent_operations must be greater than 0")
        self.max_concurrent_operations = max_concurrent_operations
        self._operation_semaphore = threading.Semaphore(max_concurrent_operations)
        self._file_locks = {}
        self._file_locks_lock = threading.RLock()
        
    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """Get or create a lock for a specific file path."""
        with self._file_locks_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]
            
    @contextmanager
    def managed_file(self, file_path: str, mode: str = 'r', encoding: str = 'utf-8'):
        """Context manager for coordinated file operations with locking and resource cleanup."""
        with self._operation_semaphore:
            file_lock = self._get_file_lock(file_path)
            with file_lock:
                f = None
                try:
                    f = open(file_path, mode, encoding=encoding)
                    yield f
                finally:
                    if f is not None and not f.closed:
                        f.close()

    def read_file(self, file_path: str, encoding: str = 'utf-8', timeout: float = 30.0, progress_callback=None, progress_state=None) -> str:
        """Read a file with coordinated concurrency control and optional progress tracking."""
        if progress_state and not isinstance(progress_state, FileProgress):
            raise TypeError("progress_state must be a FileProgress instance")
            
        def _read():
            if progress_state and progress_state.cancelled:
                raise FileOperationCancelException("File read operation was cancelled")
                
            with self.managed_file(file_path, 'r', encoding) as f:
                content = []
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    if progress_state and not progress_state.cancelled:
                        progress_state.mark_progress(len(chunk.encode(encoding)))
                        if progress_callback:
                            progress_callback(progress_state)
                    content.append(chunk)
                    
            if progress_state and not progress_state.cancelled:
                progress_state.total_bytes = sum(len(c.encode(encoding)) for c in content)
                if progress_callback:
                    progress_callback(progress_state)
            result = ''.join(content)
            del content
            gc.collect()
            return result
            
        return execute_with_timeout_and_progress(_read, timeout=timeout, progress_callback=progress_callback, progress_state=progress_state)

    def write_file(self, file_path: str, data: str, mode: str = 'w', encoding: str = 'utf-8', timeout: float = 30.0, progress_callback=None, progress_state=None) -> None:
        """Write to a file with coordinated concurrency control and optional progress tracking."""
        if progress_state and not isinstance(progress_state, FileProgress):
            raise TypeError("progress_state must be a FileProgress instance")
            
        def _write():
            if progress_state and progress_state.cancelled:
                raise FileOperationCancelException("File write operation was cancelled")
                
            with self.managed_file(file_path, mode, encoding) as f:
                chunks = [data[i:i+8192] for i in range(0, len(data), 8192)]
                total_chunks = len(chunks)
                for i, chunk in enumerate(chunks):
                    if progress_state and progress_state.cancelled:
                        raise FileOperationCancelException("File write operation was cancelled")
                    f.write(chunk)
                    if progress_callback and progress_state:
                        progress_state.mark_progress(len(chunk.encode(encoding)))
                        progress_callback(progress_state)
                del chunks
                gc.collect()
                        
            if progress_state and not progress_state.cancelled:
                progress_state.total_bytes = len(data.encode(encoding))
                if progress_callback:
                    progress_callback(progress_state)
                
        execute_with_timeout_and_progress(_write, timeout=timeout, progress_callback=progress_callback, progress_state=progress_state)


io_context = IOContext()


def encode_hex(data: bytes | str) -> str:
    """Encode data to hexadecimal string representation."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return data.hex()


def decode_hex(hex_string: str) -> bytes:
    """Decode hexadecimal string to bytes."""
    return bytes.fromhex(hex_string)


def url_encode(text: str, encoding: str = 'utf-8', safe: str = '') -> str:
    """URL encode a string with optional safe characters."""
    if isinstance(text, str):
        text = text.encode(encoding)
    return urllib.parse.quote(text, safe=safe)


def url_decode(encoded_text: str, encoding: str = 'utf-8') -> str:
    """URL decode a string back to original text."""
    decoded_bytes = urllib.parse.unquote(encoded_text)
    if isinstance(decoded_bytes, bytes):
        return decoded_bytes.decode(encoding)
    return decoded_bytes


def format_binary(data: bytes | int) -> str:
    """Format bytes or integer as binary string with '0b' prefix."""
    if isinstance(data, bytes):
        return ''.join(f'{byte:08b}' for byte in data)
    return f'{data:b}'


def parse_binary(binary_string: str) -> bytes:
    """Parse binary string to bytes."""
    binary_string = binary_string.replace('0b', '').replace(' ', '')
    if not all(c in '01' for c in binary_string):
        raise ValueError("Invalid binary string")
    if len(binary_string) % 8 != 0:
        raise ValueError("Binary string length must be a multiple of 8")
    return bytes([int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8)])


def is_valid_base64(data: str) -> bool:
    """Check if a string is valid base64 encoded data."""
    try:
        base64.b64decode(data, validate=True)
        return True
    except Exception:
        return False


def encode_base64(data: bytes | str) -> str:
    """Encode bytes or string to base64 encoded string."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')


def decode_base64(base64_string: str) -> bytes:
    """Decode base64 string to bytes with validation."""
    if not is_valid_base64(base64_string):
        raise ValueError("Invalid base64 encoded string")
    return base64.b64decode(base64_string)


def encode_to_hex(data: bytes | str) -> str:
    """Encode bytes or string to hexadecimal string."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return data.hex()


def decode_from_hex(hex_string: str) -> bytes:
    """Decode hexadecimal string to bytes with validation."""
    hex_string = hex_string.replace(' ', '').replace('0x', '')
    if not all(c in '0123456789abcdefABCDEF' for c in hex_string):
        raise ValueError("Invalid hexadecimal string")
    if len(hex_string) % 2 != 0:
        raise ValueError("Hexadecimal string length must be even")
    return bytes.fromhex(hex_string)


def encode_to_binary(data: bytes | int) -> str:
    """Encode bytes or integer to binary string."""
    if isinstance(data, bytes):
        return ''.join(f'{byte:08b}' for byte in data)
    return f'{data:b}'


def decode_from_binary(binary_string: str) -> bytes:
    """Decode binary string to bytes with validation."""
    binary_string = binary_string.replace('0b', '').replace(' ', '')
    if not all(c in '01' for c in binary_string):
        raise ValueError("Invalid binary string")
    if len(binary_string) % 8 != 0:
        raise ValueError("Binary string length must be a multiple of 8")
    return bytes([int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8)])


def base64_to_hex(base64_string: str) -> str:
    """Convert base64 encoded string to hexadecimal string."""
    decoded_bytes = decode_base64(base64_string)
    return encode_to_hex(decoded_bytes)


def hex_to_base64(hex_string: str) -> str:
    """Convert hexadecimal string to base64 encoded string."""
    decoded_bytes = decode_from_hex(hex_string)
    return encode_base64(decoded_bytes)


def base64_to_binary(base64_string: str) -> str:
    """Convert base64 encoded string to binary string."""
    decoded_bytes = decode_base64(base64_string)
    return encode_to_binary(decoded_bytes)


def binary_to_base64(binary_string: str) -> str:
    """Convert binary string to base64 encoded string."""
    decoded_bytes = decode_from_binary(binary_string)
    return encode_base64(decoded_bytes)


def hex_to_binary(hex_string: str) -> str:
    """Convert hexadecimal string to binary string."""
    decoded_bytes = decode_from_hex(hex_string)
    return encode_to_binary(decoded_bytes)


def binary_to_hex(binary_string: str) -> str:
    """Convert binary string to hexadecimal string."""
    decoded_bytes = decode_from_binary(binary_string)
    return encode_to_hex(decoded_bytes)


try:
    import psutil
except ImportError:
    psutil = None


def get_memory_usage() -> dict | None:
    """Get current system memory usage with total, available, used, and percent."""
    if psutil is not None:
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent
        }
    return None


def get_cpu_usage(interval: float = 0.1, percpu: bool = False) -> float | list[float] | None:
    """Get current CPU usage percentage."""
    if psutil is not None:
        return psutil.cpu_percent(interval=interval, percpu=percpu)
    return None


def get_system_health_status() -> dict | None:
    """Get system health status including memory and CPU usage."""
    if psutil is not None:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        
        memory_status = 'healthy' if mem.percent < 80 else 'warning' if mem.percent < 90 else 'critical'
        cpu_status = 'healthy' if cpu < 70 else 'warning' if cpu < 90 else 'critical'
        
        return {
            'memory': {
                'percent': mem.percent,
                'total_bytes': mem.total,
                'available_bytes': mem.available,
                'used_bytes': mem.used,
                'status': memory_status
            },
            'cpu': {
                'percent': cpu,
                'status': cpu_status
            },
            'overall_status': 'healthy' if memory_status == 'healthy' and cpu_status == 'healthy' else ('warning' if memory_status == 'warning' or cpu_status == 'warning' else 'critical')
        }
    return None


def format_duration(seconds: float, precision: int = 2) -> str:
    """Format seconds as a human-readable duration string."""
    if seconds < 0:
        raise ValueError("Duration cannot be negative")
    
    if seconds < 1:
        return f"{seconds * 1000:.{precision}f} ms"
    
    units = [
        (365 * 24 * 3600, "y"),
        (24 * 3600, "d"),
        (3600, "h"),
        (60, "m"),
        (1, "s")
    ]
    
    parts = []
    for unit_size, unit_label in units:
        if seconds >= unit_size or len(parts) > 0:
            value = int(seconds // unit_size)
            if value > 0 or len(parts) > 0:
                parts.append(f"{value}{unit_label}")
                seconds %= unit_size
    
    if not parts:
        return f"0s"
    
    return " ".join(parts[:3])


class Timer:
    """Context manager and tracker for elapsed time."""
    
    def __init__(self, name: str = None):
        self.name = name or "timer"
        self._start_time = None
        self._elapsed = 0.0
        self._running = False
        
    def start(self):
        """Start the timer."""
        self._start_time = time.perf_counter()
        self._running = True
        
    def stop(self):
        """Stop the timer and return elapsed time."""
        if not self._running:
            raise RuntimeError("Timer is not running")
        self._elapsed += time.perf_counter() - self._start_time
        self._running = False
        return self._elapsed
        
    def reset(self):
        """Reset the timer."""
        self._elapsed = 0.0
        self._start_time = None
        self._running = False
        
    @property
    def elapsed(self) -> float:
        """Get current elapsed time (includes running time if active)."""
        if self._running:
            return self._elapsed + (time.perf_counter() - self._start_time)
        return self._elapsed
        
    def __enter__(self):
        """Start timer on context enter."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer on context exit."""
        self.stop()


def measure_time(func=None, name: str = None):
    """Decorator to measure function execution time."""
    if func is None:
        return lambda f: measure_time(f, name)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        timer = Timer(name or func.__name__)
        timer.start()
        result = func(*args, **kwargs)
        timer.stop()
        return result, timer.elapsed
    return wrapper


def extract_numeric_values(data: any) -> list[float]:
    """Extract all numeric values from a nested structure (dict, list, tuple)."""
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        return [float(data)]
    elif isinstance(data, dict):
        values = []
        for v in data.values():
            values.extend(extract_numeric_values(v))
        return values
    elif isinstance(data, (list, tuple)):
        values = []
        for item in data:
            values.extend(extract_numeric_values(item))
        return values
    return []


def calculate_mean(data: any) -> float | None:
    """Calculate the mean of numeric values from an array or nested structure."""
    values = extract_numeric_values(data)
    if not values:
        return None
    return sum(values) / len(values)


def calculate_median(data: any) -> float | None:
    """Calculate the median of numeric values from an array or nested structure."""
    values = sorted(extract_numeric_values(data))
    if not values:
        return None
    n = len(values)
    mid = n // 2
    if n % 2 == 0:
        return (values[mid - 1] + values[mid]) / 2.0
    return float(values[mid])


def calculate_std_deviation(data: any, ddof: int = 0) -> float | None:
    """Calculate the standard deviation of numeric values from an array or nested structure."""
    values = extract_numeric_values(data)
    if len(values) <= ddof:
        return None
    mean_val = calculate_mean(values)
    if mean_val is None:
        return None
    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - ddof)
    return variance ** 0.5


def get_min_max(data: any) -> dict | None:
    """Get min and max numeric values from an array or nested structure."""
    values = extract_numeric_values(data)
    if not values:
        return None
    return {
        'min': min(values),
        'max': max(values)
    }


def extract_text_between_markers(text: str, start_marker: str, end_marker: str, include_markers: bool = False) -> list[str]:
    """Extract text between specified start and end markers."""
    if not start_marker or not end_marker:
        raise ValueError("start_marker and end_marker cannot be empty")
    
    escaped_start = re.escape(start_marker)
    escaped_end = re.escape(end_marker)
    pattern = f'{escaped_start}(.*?){escaped_end}'
    
    matches = re.findall(pattern, text, re.DOTALL)
    if include_markers:
        return [f"{start_marker}{m}{end_marker}" for m in matches]
    return matches


def parse_key_value_pairs(text: str, delimiter: str = '\n', key_separator: str = ':') -> dict:
    """Parse key-value pairs from a formatted string into a dictionary."""
    result = {}
    if not text:
        return result
    
    lines = text.split(delimiter)
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split(key_separator, 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            result[key] = value
    
    return result


def split_by_complex_delimiters(text: str, delimiters: list[str] | tuple[str]) -> list[str]:
    """Split text by multiple delimiter patterns."""
    if not delimiters:
        return [text]
    
    escaped_delimiters = [re.escape(d) for d in delimiters]
    pattern = f'({"|".join(escaped_delimiters)})'
    
    parts = re.split(pattern, text)
    result = []
    for part in parts:
        if part and part not in delimiters:
            result.append(part)
    
    return [p.strip() for p in result if p]


def remove_duplicates(lst: list, key: callable = None) -> list:
    """Remove duplicates from a list, optionally by a key function."""
    seen = set()
    result = []
    for item in lst:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


def list_intersection(*lists: list) -> list:
    """Find intersection of multiple lists."""
    if not lists:
        return []
    if len(lists) == 1:
        return list(set(lists[0]))
    
    intersections = [set(lst) for lst in lists if lst]
    if not intersections:
        return []
    
    result = intersections[0].intersection(*intersections[1:])
    return list(result)


def list_union(*lists: list) -> list:
    """Find union of multiple lists."""
    union_set = set()
    for lst in lists:
        if lst:
            union_set.update(lst)
    return list(union_set)


def dict_intersection(dict_list: list) -> dict:
    """Find intersection of dictionaries based on common keys with matching values."""
    if not dict_list or not isinstance(dict_list, list):
        return {}
    
    common_keys = set(dict_list[0].keys())
    for d in dict_list[1:]:
        if isinstance(d, dict):
            common_keys.intersection_update(d.keys())
    
    result = {}
    for key in common_keys:
        values = [d.get(key) for d in dict_list if isinstance(d, dict) and key in d]
        if all(v == values[0] for v in values):
            result[key] = values[0]
    return result


def dict_union(dict_list: list) -> dict:
    """Find union of dictionaries, merging keys and values."""
    result = {}
    for d in dict_list:
        if isinstance(d, dict):
            result.update(d)
    return result


class ChimeraBaseException(Exception):
    """Base exception for all Chimera custom exceptions."""
    def __init__(self, message: str, context: dict = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)


class ValidationException(ChimeraBaseException):
    """Base exception for validation errors."""
    pass


class ValidationError(ValidationException):
    """Custom exception for validation errors with field and value context."""
    def __init__(self, message: str, field: str = None, value: any = None):
        self.message = message
        self.field = field
        self.value = value
        context = {'field': field, 'value': value} if field or value is not None else {}
        super().__init__(f"Field '{field}': {message}" if field else message, context)


class NetworkException(ChimeraBaseException):
    """Base exception for network errors."""
    pass


class ConnectionFailedError(NetworkException):
    """Exception raised when a connection fails."""
    pass


class RequestTimeoutError(NetworkException):
    """Exception raised when a network request times out."""
    pass


class ResourceException(ChimeraBaseException):
    """Base exception for resource errors."""
    pass


class ResourceNotFoundError(ResourceException):
    """Exception raised when a file or resource is not found."""
    pass


class ResourceAccessDeniedError(ResourceException):
    """Exception raised when access to a resource is denied."""
    pass


class FileOperationCancelException(Exception):
    """Exception raised when a file operation is cancelled."""
    pass


class FileProgress:
    """Progress tracking for file operations with cancellation support."""
    
    def __init__(self, total_bytes: int = 0):
        self.total_bytes = total_bytes
        self.bytes_processed = 0
        self.cancelled = False
        
    def mark_progress(self, bytes_written: int) -> None:
        """Mark progress for file operation."""
        if self.cancelled:
            raise FileOperationCancelException("File operation was cancelled")
        self.bytes_processed += bytes_written
        
    def cancel(self) -> None:
        """Signal cancellation of the file operation."""
        self.cancelled = True


def execute_with_timeout(func, timeout: float = 30.0):
    """Execute a function with timeout support."""
    import threading
    
    result_container = {'result': None, 'exception': None}
    
    def _execute():
        try:
            result = func()
            result_container['result'] = result
        except Exception as e:
            result_container['exception'] = e
            
    thread = threading.Thread(target=_execute)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout} seconds")
        
    if result_container['exception']:
        raise result_container['exception']
        
    return result_container['result']


def execute_with_timeout_and_progress(func, timeout: float = 30.0, progress_callback=None, progress_state=None):
    """Execute a function with timeout and optional progress tracking with cancellation support."""
    import threading
    
    result_container = {'result': None, 'exception': None}
    
    def _execute():
        try:
            if progress_state and progress_state.cancelled:
                raise FileOperationCancelException("File operation was cancelled before execution")
            
            result = func()
            if progress_callback and progress_state:
                progress_callback(progress_state)
            result_container['result'] = result
        except Exception as e:
            result_container['exception'] = e
            
    thread = threading.Thread(target=_execute)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout} seconds")
    
    if progress_state and progress_state.cancelled:
        raise FileOperationCancelException("File operation was cancelled")
        
    if result_container['exception']:
        raise result_container['exception']
        
    return result_container['result']


class ProcessingException(ChimeraBaseException):
    """Base exception for processing errors."""
    pass


class DataProcessingError(ProcessingException):
    """Exception raised during data processing operations."""
    pass


class TransformError(ProcessingException):
    """Exception raised when a data transformation fails."""
    pass


def type_check(value: any, expected_type: type | tuple[type], field_name: str = None) -> any:
    """Check if value matches expected type with custom error messages."""
    if not isinstance(value, expected_type):
        if isinstance(expected_type, type):
            expected_names = [expected_type.__name__]
        elif isinstance(expected_type, (list, tuple)):
            expected_names = [t.__name__ if isinstance(t, type) else str(t) for t in expected_type]
        else:
            expected_names = [str(expected_type)]
        raise ValidationError(
            f"Expected type {', '.join(expected_names)}, got {type(value).__name__}",
            field=field_name,
            value=value
        )
    return value


def validate_schema(data: dict, schema: dict) -> dict:
    """Validate a dictionary against a schema definition with type, pattern, and range checks."""
    validated = {}
    for field, rules in schema.items():
        if not isinstance(rules, dict):
            raise ValidationError(f"Invalid schema rule for field {field}")
        
        if rules.get('required') and field not in data:
            raise ValidationError(f"Missing required field '{field}'", field=field)
        
        if field not in data:
            continue
            
        value = data[field]
        
        expected_type = rules.get('type')
        if expected_type:
            type_check(value, expected_type, field_name=f"{field}")
        
        if isinstance(value, str) and 'pattern' in rules:
            if not validate_pattern(value, rules['pattern']):
                raise ValidationError(f"Value does not match pattern", field=field, value=value)
        
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if 'min' in rules and value < rules['min']:
                raise ValidationError(f"Value {value} is less than minimum {rules['min']}", field=field, value=value)
            if 'max' in rules and value > rules['max']:
                raise ValidationError(f"Value {value} exceeds maximum {rules['max']}", field=field, value=value)
        
        if isinstance(value, (str, list)):
            if 'min_length' in rules and len(value) < rules['min_length']:
                raise ValidationError(f"Length {len(value)} is less than minimum {rules['min_length']}", field=field, value=value)
            if 'max_length' in rules and len(value) > rules['max_length']:
                raise ValidationError(f"Length {len(value)} exceeds maximum {rules['max_length']}", field=field, value=value)
        
        validated[field] = value
        
    return validated


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format using regex pattern."""
    if not isinstance(uuid_str, str):
        raise ValidationError("UUID must be a string", value=uuid_str)
    pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    if not re.match(pattern, uuid_str):
        raise ValidationError("Invalid UUID format", value=uuid_str)
    return True


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format using regex pattern."""
    if not isinstance(phone, str):
        raise ValidationError("Phone number must be a string", value=phone)
    pattern = r'^\+?[1-9]\d{1,14}$'
    if not re.match(pattern, phone):
        raise ValidationError("Invalid phone number format", value=phone)
    return True


def validate_url(url: str) -> bool:
    """Validate URL format using regex pattern."""
    if not isinstance(url, str):
        raise ValidationError("URL must be a string", value=url)
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$'
    if not re.match(pattern, url):
        raise ValidationError("Invalid URL format", value=url)
    return True


def validate_positive_integer(value: int | float, field_name: str = None) -> int:
    """Validate that a value is a positive integer."""
    type_check(value, int, field_name=field_name)
    if value <= 0:
        raise ValidationError("Value must be a positive integer", field=field_name, value=value)
    return value


def validate_non_negative_float(value: float | int, field_name: str = None) -> float:
    """Validate that a value is a non-negative float."""
    type_check(value, (int, float), field_name=field_name)
    if isinstance(value, bool):
        raise ValidationError("Value must be a number", field=field_name, value=value)
    if value < 0:
        raise ValidationError("Value must be non-negative", field=field_name, value=value)
    return float(value)


def generate_secure_token(bits: int = 128) -> str:
    """Generate a secure random token using secrets module."""
    return secrets.token_hex(bits // 8)


def hash_string_sha256(data: str | bytes) -> str:
    """Create SHA-256 hash of a string or bytes."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def hash_file_sha256(file_path: str, timeout: float = 30.0) -> str:
    """Create SHA-256 hash of a file."""
    def _hash():
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    return execute_with_timeout(_hash, timeout=timeout)


def sort_dict_by_keys(d: dict, reverse: bool = False) -> dict:
    """Sort a dictionary by keys."""
    return dict(sorted(d.items(), key=lambda item: str(item[0]), reverse=reverse))


def sort_dict_by_values(d: dict, reverse: bool = False) -> dict:
    """Sort a dictionary by values, handling nested structures."""
    def _value_sort_key(item):
        val = item[1]
        if val is None:
            return (0, '')
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return (1, val)
        if isinstance(val, str):
            return (2, val)
        return (3, str(val))
    
    return dict(sorted(d.items(), key=_value_sort_key, reverse=reverse))


def sort_list_of_dicts(lst: list, key_field: str, reverse: bool = False) -> list:
    """Sort a list of dictionaries by a specific field."""
    def _list_sort_key(item):
        if isinstance(item, dict):
            val = item.get(key_field)
            if val is None:
                return (0, '')
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return (1, val)
            if isinstance(val, str):
                return (2, val)
            return (3, str(val))
        return (0, '')
    
    return sorted(lst, key=_list_sort_key, reverse=reverse)


def normalize_date_string(date_str: str, target_format: str = "%Y-%m-%d") -> str:
    """Normalize a date string to a target format, supporting common date formats."""
    if not isinstance(date_str, str):
        raise ValidationError("Date string must be a string", field=None, value=date_str)
    
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y"
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime(target_format)
        except ValueError:
            continue
    
    raise ValidationError(f"Unable to parse date string", field=None, value=date_str)


def normalize_timestamp(timestamp: float | str, as_iso: bool = True) -> str:
    """Normalize a timestamp to an ISO 8601 string or formatted datetime."""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError(f"Unable to parse timestamp string", value=timestamp)
    else:
        dt = datetime.fromtimestamp(float(timestamp))
    
    if as_iso:
        return dt.isoformat()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def convert_time_units(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a time value between units: ns, us, ms, s, min, h, d."""
    units_to_seconds = {
        'ns': 1e-9,
        'us': 1e-6,
        'ms': 1e-3,
        's': 1.0,
        'min': 60.0,
        'h': 3600.0,
        'd': 86400.0
    }
    
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit not in units_to_seconds:
        raise ValidationError(f"Invalid time unit: {from_unit}", field=None, value=from_unit)
    if to_unit not in units_to_seconds:
        raise ValidationError(f"Invalid time unit: {to_unit}", field=None, value=to_unit)
    
    seconds = value * units_to_seconds[from_unit]
    return seconds / units_to_seconds[to_unit]


def standardize_numeric_format(value: float | int, precision: int = 2, as_string: bool = False) -> str | float:
    """Standardize a numeric format to a specified decimal precision."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError("Value must be a number", field=None, value=value)
    
    rounded = round(float(value), precision)
    if as_string:
        return f"{rounded:.{precision}f}"
    return rounded


def compare_floats_with_tolerance(a: float, b: float, tol: float = 1e-9) -> bool:
    """Compare two floats with a given absolute tolerance."""
    return abs(float(a) - float(b)) <= tol


def compare_floats_relative(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    """Compare two floats with a given relative tolerance."""
    if float(a) == float(b):
        return True
    if float(a) == 0.0 or float(b) == 0.0:
        return abs(float(a) - float(b)) <= rel_tol
    max_val = max(abs(float(a)), abs(float(b)))
    return abs(float(a) - float(b)) <= rel_tol * max_val


def calculate_float_difference(a: float, b: float) -> float:
    """Calculate the absolute difference between two floats."""
    return abs(float(a) - float(b))


class MetricsCollector:
    """Telemetry and metrics collector for tracking API usage and performance."""
    
    def __init__(self):
        self._call_counts = {}
        self._response_times = {}
        self._error_counts = {}
        self._lock = threading.Lock()
        
    def record_call(self, api_name: str) -> None:
        """Record an API call."""
        with self._lock:
            self._call_counts[api_name] = self._call_counts.get(api_name, 0) + 1
            
    def record_response_time(self, api_name: str, response_time: float) -> None:
        """Record a response time for an API call."""
        with self._lock:
            if api_name not in self._response_times:
                self._response_times[api_name] = {'total': 0.0, 'count': 0, 'min': response_time, 'max': response_time}
            self._response_times[api_name]['total'] += response_time
            self._response_times[api_name]['count'] += 1
            if response_time < self._response_times[api_name]['min']:
                self._response_times[api_name]['min'] = response_time
            if response_time > self._response_times[api_name]['max']:
                self._response_times[api_name]['max'] = response_time
                
    def record_error(self, api_name: str) -> None:
        """Record an error for an API call."""
        with self._lock:
            self._error_counts[api_name] = self._error_counts.get(api_name, 0) + 1
            
    def get_call_count(self, api_name: str = None) -> dict | int:
        """Get API call counts."""
        with self._lock:
            if api_name:
                return self._call_counts.get(api_name, 0)
            return dict(self._call_counts)
            
    def get_response_times(self, api_name: str = None) -> dict | None:
        """Get response time metrics."""
        with self._lock:
            if api_name:
                if api_name not in self._response_times:
                    return None
                rt = self._response_times[api_name]
                return {
                    'total_time': rt['total'],
                    'count': rt['count'],
                    'average': rt['total'] / rt['count'] if rt['count'] > 0 else 0.0,
                    'min': rt['min'],
                    'max': rt['max']
                }
            return {api: dict(v) for api, v in self._response_times.items()}
            
    def get_error_rate(self, api_name: str = None) -> dict | float:
        """Get error rates."""
        with self._lock:
            if api_name:
                calls = self._call_counts.get(api_name, 0)
                errors = self._error_counts.get(api_name, 0)
                rate = (errors / calls * 100) if calls > 0 else 0.0
                return {
                    'api': api_name,
                    'total_calls': calls,
                    'total_errors': errors,
                    'error_rate_percent': rate
                }
                
            results = {}
            for api in set(self._call_counts.keys()) | set(self._error_counts.keys()):
                calls = self._call_counts.get(api, 0)
                errors = self._error_counts.get(api, 0)
                rate = (errors / calls * 100) if calls > 0 else 0.0
                results[api] = {
                    'total_calls': calls,
                    'total_errors': errors,
                    'error_rate_percent': rate
                }
            return results
            
    def get_all_metrics(self) -> dict:
        """Get all collected metrics."""
        with self._lock:
            return {
                'call_counts': dict(self._call_counts),
                'response_times': {api: dict(v) for api, v in self._response_times.items()},
                'error_counts': dict(self._error_counts)
            }


metrics_collector = MetricsCollector()


def export_metrics_to_prometheus(metrics_collector: MetricsCollector) -> str:
    """Export collected metrics to Prometheus text exposition format."""
    lines = []
    lines.append("# HELP chimera_api_calls_total Total number of API calls")
    lines.append("# TYPE chimera_api_calls_total counter")
    
    call_counts = metrics_collector.get_call_count()
    if isinstance(call_counts, dict):
        for api_name, count in call_counts.items():
            clean_api = api_name.replace('-', '_').replace('.', '_')
            lines.append(f'chimera_api_calls_total{{api="{clean_api}"}} {count}')
    
    lines.append("")
    lines.append("# HELP chimera_api_response_time_seconds Response time in seconds")
    lines.append("# TYPE chimera_api_response_time_seconds gauge")
    
    response_times = metrics_collector.get_response_times()
    if isinstance(response_times, dict):
        for api_name, rt_data in response_times.items():
            clean_api = api_name.replace('-', '_').replace('.', '_')
            avg_time = rt_data.get('average', 0.0)
            lines.append(f'chimera_api_response_time_seconds{{api="{clean_api}"}} {avg_time}')
    
    lines.append("")
    lines.append("# HELP chimera_api_errors_total Total number of API errors")
    lines.append("# TYPE chimera_api_errors_total counter")
    
    error_rates = metrics_collector.get_error_rate()
    if isinstance(error_rates, dict):
        for api_name, err_data in error_rates.items():
            clean_api = api_name.replace('-', '_').replace('.', '_')
            errors = err_data.get('total_errors', 0)
            lines.append(f'chimera_api_errors_total{{api="{clean_api}"}} {errors}')
    
    return '\n'.join(lines) + '\n'


def export_metrics_to_datadog(metrics_collector: MetricsCollector, host: str = None, tags: list[str] = None) -> dict:
    """Export collected metrics to Datadog JSON API format."""
    if tags is None:
        tags = []
    
    if host:
        tags.append(f'host:{host}')
    
    datadog_payload = {'series': []}
    current_timestamp = int(time.time())
    
    call_counts = metrics_collector.get_call_count()
    if isinstance(call_counts, dict):
        for api_name, count in call_counts.items():
            datadog_series = {
                'metric': f'chimera.api.calls.total',
                'points': [[current_timestamp, float(count)]],
                'type': 'count',
                'tags': [f'api:{api_name}'] + (tags if tags else []),
            }
            datadog_payload['series'].append(datadog_series)
    
    response_times = metrics_collector.get_response_times()
    if isinstance(response_times, dict):
        for api_name, rt_data in response_times.items():
            avg_time = rt_data.get('average', 0.0)
            datadog_series = {
                'metric': f'chimera.api.response_time.seconds',
                'points': [[current_timestamp, float(avg_time)]],
                'type': 'gauge',
                'tags': [f'api:{api_name}'] + (tags if tags else []),
            }
            datadog_payload['series'].append(datadog_series)
    
    error_rates = metrics_collector.get_error_rate()
    if isinstance(error_rates, dict):
        for api_name, err_data in error_rates.items():
            errors = err_data.get('total_errors', 0)
            datadog_series = {
                'metric': f'chimera.api.errors.total',
                'points': [[current_timestamp, float(errors)]],
                'type': 'count',
                'tags': [f'api:{api_name}'] + (tags if tags else []),
            }
            datadog_payload['series'].append(datadog_series)
    
    return datadog_payload


def export_metrics_to_json(metrics_collector: MetricsCollector, include_timestamp: bool = True) -> dict:
    """Export collected metrics to standard JSON format for external monitoring systems."""
    result = {
        'call_counts': metrics_collector.get_call_count(),
        'response_times': metrics_collector.get_response_times(),
        'error_rates': metrics_collector.get_error_rate()
    }
    
    if include_timestamp:
        result['timestamp'] = int(time.time())
    
    return result


def track_api_call(func):
    """Decorator to track API call counts and response times."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_name = func.__name__
        metrics_collector.record_call(api_name)
        timer = Timer(f"api_{api_name}")
        timer.start()
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            metrics_collector.record_error(api_name)
            raise
        finally:
            elapsed = timer.stop()
            metrics_collector.record_response_time(api_name, elapsed)
    return wrapper


def track_async_api_call(func):
    """Decorator to track async API call counts and response times."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        api_name = func.__name__
        metrics_collector.record_call(api_name)
        timer = Timer(f"api_{api_name}")
        timer.start()
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            metrics_collector.record_error(api_name)
            raise
        finally:
            elapsed = timer.stop()
            metrics_collector.record_response_time(api_name, elapsed)
    return wrapper


def generate_fernet_key() -> str:
    """Generate a new Fernet key for encryption/decryption of sensitive data."""
    if Fernet is None:
        raise ImportError("cryptography is required for Fernet encryption. Install with: pip install cryptography")
    return Fernet.generate_key().decode('utf-8')


def encrypt_string(data: str, key: str) -> str:
    """Encrypt a string using Fernet symmetric encryption for secure storage."""
    if Fernet is None:
        raise ImportError("cryptography is required for Fernet encryption. Install with: pip install cryptography")
    f = Fernet(key.encode('utf-8'))
    return f.encrypt(data.encode('utf-8')).decode('utf-8')


def decrypt_string(encrypted_data: str, key: str) -> str:
    """Decrypt a string using Fernet symmetric encryption."""
    if Fernet is None:
        raise ImportError("cryptography is required for Fernet encryption. Install with: pip install cryptography")
    f = Fernet(key.encode('utf-8'))
    return f.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a temperature value between Celsius, Fahrenheit, and Kelvin scales."""
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    
    valid_units = {'celsius', 'fahrenheit', 'kelvin', 'c', 'f', 'k'}
    if from_unit not in valid_units or to_unit not in valid_units:
        raise ValidationError(f"Invalid temperature unit", field=None, value=f"{from_unit} to {to_unit}")
    
    # Convert to Celsius first
    if from_unit in ['celsius', 'c']:
        celsius = float(value)
    elif from_unit in ['fahrenheit', 'f']:
        celsius = (float(value) - 32.0) * 5.0 / 9.0
    elif from_unit in ['kelvin', 'k']:
        celsius = float(value) - 273.15
    
    # Convert from Celsius to target unit
    if to_unit in ['celsius', 'c']:
        return celsius
    elif to_unit in ['fahrenheit', 'f']:
        return (celsius * 9.0 / 5.0) + 32.0
    elif to_unit in ['kelvin', 'k']:
        return celsius + 273.15


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a length value between metric and imperial units."""
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    
    valid_units = {'meter', 'meters', 'metre', 'metres', 'km', 'kilometer', 'kilometers', 
                   'centimeter', 'centimeters', 'cm', 'millimeter', 'millimeters', 'mm',
                   'inch', 'inches', 'in', 'foot', 'feet', 'ft', 'yard', 'yards', 'yd', 'mile', 'miles', 'mi'}
    if from_unit not in valid_units or to_unit not in valid_units:
        raise ValidationError(f"Invalid length unit", field=None, value=f"{from_unit} to {to_unit}")
    
    # Convert to meters first
    unit_to_meters = {
        'meter': 1.0, 'meters': 1.0, 'metre': 1.0, 'metres': 1.0,
        'km': 1000.0, 'kilometer': 1000.0, 'kilometers': 1000.0,
        'centimeter': 0.01, 'centimeters': 0.01, 'cm': 0.01,
        'millimeter': 0.001, 'millimeters': 0.001, 'mm': 0.001,
        'inch': 0.0254, 'inches': 0.0254, 'in': 0.0254,
        'foot': 0.3048, 'feet': 0.3048, 'ft': 0.3048,
        'yard': 0.9144, 'yards': 0.9144, 'yd': 0.9144,
        'mile': 1609.344, 'miles': 1609.344, 'mi': 1609.344
    }
    
    meters = float(value) * unit_to_meters.get(from_unit, 1.0)
    
    # Convert from meters to target unit
    meters_to_unit = {v: k for k, v in unit_to_meters.items()}
    inverse_factors = {k: 1.0/v for k, v in unit_to_meters.items()}
    
    return meters * inverse_factors.get(to_unit, 1.0)


def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a weight/mass value between metric and imperial units."""
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    
    valid_units = {'gram', 'grams', 'g', 'kilogram', 'kilograms', 'kg', 
                   'pound', 'pounds', 'lb', 'lbs', 'ounce', 'ounces', 'oz', 
                   'ton', 'tons', 'metric_ton', 'metric_tons'}
    if from_unit not in valid_units or to_unit not in valid_units:
        raise ValidationError(f"Invalid weight unit", field=None, value=f"{from_unit} to {to_unit}")
    
    # Convert to grams first
    unit_to_grams = {
        'gram': 1.0, 'grams': 1.0, 'g': 1.0,
        'kilogram': 1000.0, 'kilograms': 1000.0, 'kg': 1000.0,
        'pound': 453.59237, 'pounds': 453.59237, 'lb': 453.59237, 'lbs': 453.59237,
        'ounce': 28.349523125, 'ounces': 28.349523125, 'oz': 28.349523125,
        'ton': 907184.74, 'tons': 907184.74,
        'metric_ton': 1000000.0, 'metric_tons': 1000000.0
    }
    
    grams = float(value) * unit_to_grams.get(from_unit, 1.0)
    
    # Convert from grams to target unit
    inverse_factors = {k: 1.0/v for k, v in unit_to_grams.items()}
    return grams * inverse_factors.get(to_unit, 1.0)


class MemoryProfiler:
    """Context manager and tracker for memory usage measurements."""
    
    def __init__(self, name: str = None):
        self.name = name or "memory_profiler"
        self._start_memory = 0
        self._end_memory = 0
        self._delta = 0.0
        
    def start(self) -> int | None:
        """Start memory profiling by capturing current process memory."""
        if psutil is not None:
            import resource
            try:
                self._start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            except Exception:
                pass
            if self._start_memory == 0:
                proc = psutil.Process(os.getpid())
                self._start_memory = proc.memory_info().rss
        return self._start_memory
        
    def stop(self) -> int | None:
        """Stop memory profiling and calculate delta."""
        if psutil is not None:
            import resource
            try:
                self._end_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            except Exception:
                pass
            if self._end_memory == 0:
                proc = psutil.Process(os.getpid())
                self._end_memory = proc.memory_info().rss
                
        if self._start_memory and self._end_memory:
            self._delta = float(self._end_memory - self._start_memory) / (1024 * 1024)
        return self._delta
        
    @property
    def start_memory(self) -> int | None:
        """Get starting memory in bytes."""
        return self._start_memory
        
    @property
    def end_memory(self) -> int | None:
        """Get ending memory in bytes."""
        return self._end_memory
        
    @property
    def delta_mb(self) -> float:
        """Get memory delta in megabytes."""
        return self._delta if self._delta else 0.0
        
    def __enter__(self):
        """Start memory profiling on context enter."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop memory profiling on context exit."""
        self.stop()


def measure_memory_delta(func=None, name: str = None):
    """Decorator to measure memory usage delta before/after function execution."""
    if func is None:
        return lambda f: measure_memory_delta(f, name)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = MemoryProfiler(name or func.__name__)
        profiler.start()
        result = func(*args, **kwargs)
        delta_mb = profiler.stop()
        return result, {'start_memory': profiler.start_memory, 'end_memory': profiler.end_memory, 'delta_mb': delta_mb}
    return wrapper


def benchmark_block(name: str = None):
    """Context manager to collect performance metrics (time and memory) for specific code blocks."""
    timer = Timer(name or "benchmark_block")
    profiler = MemoryProfiler(name or "benchmark_block")
    
    @contextmanager
    def _benchmark_context():
        timer.start()
        profiler.start()
        try:
            yield {
                'name': name or "benchmark_block",
                'time_seconds': 0.0,
                'memory_delta_mb': 0.0
            }
        finally:
            timer.stop()
            profiler.stop()
            result = {
                'name': name or "benchmark_block",
                'time_seconds': timer.elapsed,
                'memory_delta_mb': profiler.delta_mb
            }
            
    return _benchmark_context()


def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def to_timezone(dt: datetime, tz_str: str) -> datetime:
    """Convert a datetime object to the specified timezone string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    if ZoneInfo is not None:
        try:
            target_tz = ZoneInfo(tz_str)
            return dt.astimezone(target_tz)
        except ZoneInfoNotFoundError:
            pass
    
    tz_offsets = {
        'UTC': 0, 'GMT': 0, 'Z': 0,
        'EST': -5, 'EDT': -4,
        'CST': -6, 'CDT': -5,
        'MST': -7, 'MDT': -6,
        'PST': -8, 'PDT': -7
    }
    
    tz_str_upper = tz_str.upper()
    if tz_str_upper in tz_offsets:
        offset_hours = tz_offsets[tz_str_upper]
        target_tz = timezone(timedelta(hours=offset_hours))
        return dt.astimezone(target_tz)
    
    raise ValidationError(f"Unsupported timezone: {tz_str}", field=None, value=tz_str)


def convert_timestamp_to_timezone(timestamp: float | str, to_tz: str = "UTC") -> str:
    """Convert a timestamp (float or ISO string) to a specific timezone as ISO format."""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError(f"Unable to parse timestamp string", value=timestamp)
    else:
        dt = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    converted_dt = to_timezone(dt, to_tz)
    return converted_dt.isoformat()


def format_datetime_with_timezone(dt: datetime | str, tz_str: str = "UTC", format_str: str = "%Y-%m-%d %H:%M:%S%z") -> str:
    """Format a datetime or timestamp string with timezone awareness to a specific format."""
    if isinstance(dt, str):
        try:
            dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt_obj = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError(f"Unable to parse datetime string", value=dt)
    elif isinstance(dt, datetime):
        dt_obj = dt
    else:
        raise ValidationError("Invalid datetime type", field=None, value=dt)
    
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
    
    converted_dt = to_timezone(dt_obj, tz_str)
    
    if "%Z" in format_str or "%z" in format_str:
        pass
    
    return converted_dt.strftime(format_str)


def standardize_to_iso8601(dt: datetime | str | float, include_tz: bool = True) -> str:
    """Transform a datetime object, string, or timestamp to standardized ISO 8601 format."""
    if isinstance(dt, (int, float)):
        dt = datetime.fromtimestamp(float(dt), tz=timezone.utc)
    elif isinstance(dt, str):
        try:
            dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt_obj = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError(f"Unable to parse datetime string", value=dt)
        dt = dt_obj
    elif isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        raise ValidationError("Invalid datetime type", field=None, value=dt)
    
    if include_tz:
        return dt.isoformat()
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def store_sensitive_config(key_name: str, sensitive_value: str, config_dict: dict) -> dict:
    """Securely store API keys and sensitive configuration values with encryption."""
    if 'encryption_key' not in config_dict:
        config_dict['encryption_key'] = generate_fernet_key()
    
    encrypted_value = encrypt_string(sensitive_value, config_dict['encryption_key'])
    config_dict[f'{key_name}_encrypted'] = encrypted_value
    return config_dict


def retrieve_sensitive_config(key_name: str, config_dict: dict) -> str | None:
    """Retrieve and decrypt sensitive configuration values."""
    encrypted_key = f'{key_name}_encrypted'
    if encrypted_key not in config_dict or 'encryption_key' not in config_dict:
        return None
    
    key = config_dict['encryption_key']
    encrypted_value = config_dict[encrypted_key]
    return decrypt_string(encrypted_value, key)


def parse_json(json_string: str) -> dict | list:
    """Parse a JSON string to a Python dictionary or list."""
    return json.loads(json_string)


def serialize_json(data: dict | list) -> str:
    """Serialize a Python dictionary or list to a JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def validate_date(date_str: str, date_format: str = "%Y-%m-%d", field_name: str = None) -> datetime:
    """Validate a date string against a format specification."""
    if not isinstance(date_str, str):
        raise ValidationError("Date must be a string", field=field_name, value=date_str)
    try:
        dt = datetime.strptime(date_str.strip(), date_format)
        return dt
    except ValueError:
        raise ValidationError(f"Invalid date format. Expected: {date_format}", field=field_name, value=date_str)


def validate_time(time_str: str, time_format: str = "%H:%M:%S", field_name: str = None) -> datetime:
    """Validate a time string against a format specification."""
    if not isinstance(time_str, str):
        raise ValidationError("Time must be a string", field=field_name, value=time_str)
    try:
        dt = datetime.strptime(time_str.strip(), time_format)
        return dt
    except ValueError:
        raise ValidationError(f"Invalid time format. Expected: {time_format}", field=field_name, value=time_str)


def validate_ipv4(ip_address: str, field_name: str = None) -> bool:
    """Validate an IPv4 address format."""
    if not isinstance(ip_address, str):
        raise ValidationError("IPv4 address must be a string", field=field_name, value=ip_address)
    pattern = r'^((25[0-5]|(2[0-4]\d|1\d{1}|[1-9]?\d))\.){3}(25[0-5]|(2[0-4]\d|1\d{1}|[1-9]?\d))$'
    if not re.match(pattern, ip_address):
        raise ValidationError("Invalid IPv4 address format", field=field_name, value=ip_address)
    return True


def validate_ipv6(ip_address: str, field_name: str = None) -> bool:
    """Validate an IPv6 address format."""
    if not isinstance(ip_address, str):
        raise ValidationError("IPv6 address must be a string", field=field_name, value=ip_address)
    try:
        import ipaddress
        ipaddress.IPv6Address(ip_address)
        return True
    except Exception:
        raise ValidationError("Invalid IPv6 address format", field=field_name, value=ip_address)


def validate_ip(ip_address: str, field_name: str = None) -> bool:
    """Validate an IP address (IPv4 or IPv6) format."""
    if not isinstance(ip_address, str):
        raise ValidationError("IP address must be a string", field=field_name, value=ip_address)
    try:
        import ipaddress
        ipaddress.ip_address(ip_address)
        return True
    except Exception:
        raise ValidationError("Invalid IP address format (must be valid IPv4 or IPv6)", field=field_name, value=ip_address)


def validate_custom_regex(text: str, pattern: str, field_name: str = None) -> bool:
    """Validate text against a custom regex pattern with detailed error messages."""
    if not isinstance(text, str):
        raise ValidationError("Value must be a string", field=field_name, value=text)
    if not isinstance(pattern, str):
        raise ValidationError("Pattern must be a string", field=field_name, value=pattern)
    try:
        compiled_pattern = re.compile(pattern)
    except re.error as e:
        raise ValidationError(f"Invalid regex pattern: {e}", field=field_name, value=pattern)
    if not compiled_pattern.match(text):
        raise ValidationError(f"Value does not match the required pattern: {pattern}", field=field_name, value=text)
    return True


def load_json(file_path: str) -> dict | list:
    """Load JSON data from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def dump_json(data: dict | list, file_path: str) -> None:
    """Dump Python dictionary or list to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def json_to_yaml(json_string: str) -> str:
    """Convert a JSON string to a YAML string."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    
    data = parse_json(json_string)
    return serialize_yaml(data)


def yaml_to_json(yaml_string: str) -> str:
    """Convert a YAML string to a JSON string."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    
    data = parse_yaml(yaml_string)
    return serialize_json(data)


def parse_csv(csv_string: str, delimiter: str = ',', has_headers: bool = True) -> list[dict]:
    """Parse CSV string to a list of dictionaries."""
    lines = csv_string.strip().split('\n')
    if not lines:
        return []
    
    reader = csv.DictReader(lines, delimiter=delimiter)
    result = [row for row in reader]
    return result


def dicts_to_csv(data_list: list[dict], fieldnames: list[str] | None = None, delimiter: str = ',') -> str:
    """Convert a list of dictionaries to a CSV string."""
    if not data_list:
        return ''
    
    if fieldnames is None:
        fieldnames = list(data_list[0].keys())
    
    csv_output = StringIO()
    writer = csv.DictWriter(csv_output, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()
    for row in data_list:
        writer.writerow({fn: row.get(fn, '') for fn in fieldnames})
    
    return csv_output.getvalue().strip()


def transform_data(data: dict | list, source_format: str, target_format: str) -> str:
    """Transform structured data between serialization formats (json, yaml, csv)."""
    source_format = source_format.lower()
    target_format = target_format.lower()
    
    if source_format == 'json':
        parsed_data = parse_json(json.dumps(data)) if isinstance(data, str) else data
    elif source_format == 'yaml':
        if yaml is None:
            raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
        parsed_data = parse_yaml(data) if isinstance(data, str) else data
    else:
        raise ValueError(f"Unsupported source format: {source_format}")
    
    if target_format == 'json':
        return serialize_json(parsed_data)
    elif target_format == 'yaml':
        return serialize_yaml(parsed_data)
    elif target_format == 'csv':
        if not isinstance(parsed_data, list) or not all(isinstance(item, dict) for item in parsed_data):
            raise ValueError("CSV format requires a list of dictionaries as data")
        return dicts_to_csv(parsed_data)
    else:
        raise ValueError(f"Unsupported target format: {target_format}")


def filter_list_by_predicate(lst: list, predicate: callable) -> list:
    """Filter a list using a lambda predicate function that returns True or False."""
    if not isinstance(lst, list):
        raise ValidationError("Input must be a list", field=None, value=lst)
    if not callable(predicate):
        raise ValidationError("Predicate must be a callable function", field=None, value=predicate)
    return [item for item in lst if predicate(item)]


def query_dicts(lst: list[dict], **conditions) -> list[dict]:
    """Query a list of dictionaries using key-value equality conditions."""
    if not isinstance(lst, list):
        raise ValidationError("Input must be a list", field=None, value=lst)
    if not all(isinstance(item, dict) for item in lst):
        raise ValidationError("All items in list must be dictionaries", field=None, value=lst)
    
    result = []
    for item in lst:
        match = True
        for key, expected_value in conditions.items():
            if item.get(key) != expected_value:
                match = False
                break
        if match:
            result.append(item)
    return result


def filter_items_with_rules(items: list | dict, rules: dict) -> list | dict:
    """Filter items (list or dict) using custom validation rule dictionaries."""
    def _validate_item(item, item_rules):
        for field, field_rules in item_rules.items():
            if not isinstance(field_rules, dict):
                continue
            
            value = item.get(field) if isinstance(item, dict) else item
            
            if 'type' in field_rules:
                expected_type = field_rules['type']
                if not isinstance(expected_type, tuple):
                    expected_type = (expected_type,)
                if not any(isinstance(value, t) for t in expected_type if isinstance(t, type)):
                    return False
            
            if 'min' in field_rules and isinstance(value, (int, float)) and not isinstance(value, bool):
                if value < field_rules['min']:
                    return False
            
            if 'max' in field_rules and isinstance(value, (int, float)) and not isinstance(value, bool):
                if value > field_rules['max']:
                    return False
                
            if 'pattern' in field_rules and isinstance(value, str):
                if not validate_pattern(value, field_rules['pattern']):
                    return False
                    
        return True

    if isinstance(items, list):
        if not all(isinstance(item, dict) for item in items):
            raise ValidationError("List items must be dictionaries when using filter_items_with_rules", field=None, value=items)
        return [item for item in items if _validate_item(item, rules)]
    
    elif isinstance(items, dict):
        if _validate_item(items, rules):
            return items
        return None
    
    raise ValidationError("Items must be a list of dictionaries or a dictionary", field=None, value=items)


def filter_by_conditional_expression(lst: list, expr: str) -> list:
    """Filter a list of dictionaries using a conditional expression string with 'item' as the variable."""
    if not isinstance(lst, list):
        raise ValidationError("Input must be a list", field=None, value=lst)
    
    result = []
    for item in lst:
        try:
            if eval(expr, {'__builtins__': {}}, {'item': item}):
                result.append(item)
        except Exception:
            pass
    return result


def mask_email(email: str, mask_char: str = '*', visible_chars: int = 2) -> str:
    """Mask an email address with configurable visible characters before @."""
    if not isinstance(email, str):
        raise ValidationError("Email must be a string", field=None, value=email)
    
    if '@' not in email:
        raise ValidationError("Invalid email format", field=None, value=email)
        
    local_part, domain_part = email.rsplit('@', 1)
    
    if len(local_part) <= visible_chars:
        masked_local = f"{local_part[0]}{mask_char * max(0, len(local_part)-1)}"
    else:
        masked_local = f"{local_part[:visible_chars]}{mask_char * (len(local_part) - visible_chars)}"
        
    return f"{masked_local}@{domain_part}"


def mask_phone(phone: str, mask_char: str = '*', visible_digits: int = 3) -> str:
    """Mask a phone number with configurable visible digits at the end."""
    if not isinstance(phone, str):
        raise ValidationError("Phone number must be a string", field=None, value=phone)
        
    digits_only = re.sub(r'\D', '', phone)
    
    result = []
    digit_idx = 0
    for char in phone:
        if re.match(r'\d', char):
            if digit_idx < len(digits_only) - visible_digits:
                result.append(mask_char)
            else:
                result.append(char)
            digit_idx += 1
        else:
            result.append(char)
            
    return "".join(result)


def mask_api_key(api_key: str, prefix_visible: int = 4, suffix_visible: int = 4, mask_char: str = '*') -> str:
    """Mask an API key with configurable visible prefix and suffix."""
    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string", field=None, value=api_key)
        
    if len(api_key) <= prefix_visible + suffix_visible:
        return f"{api_key[:prefix_visible]}{mask_char * max(0, len(api_key)-prefix_visible)}"
        
    masked_middle = mask_char * (len(api_key) - prefix_visible - suffix_visible)
    return f"{api_key[:prefix_visible]}{masked_middle}{api_key[-suffix_visible:]}"


def mask_credit_card(card_number: str, visible_digits: int = 4, mask_char: str = '*', group_size: int = 4) -> str:
    """Mask a credit card number with configurable visible digits and grouping."""
    if not isinstance(card_number, str):
        raise ValidationError("Credit card number must be a string", field=None, value=card_number)
        
    digits_only = re.sub(r'\D', '', card_number)
    
    if len(digits_only) <= visible_digits:
        masked_digits = f"{digits_only[0]}{mask_char * max(0, len(digits_only)-1)}"
    else:
        masked_digits = f"{mask_char * (len(digits_only) - visible_digits)}{digits_only[-visible_digits:]}"
        
    if any(c in card_number for c in [' ', '-', '_']):
        formatted_result = []
        digit_idx = 0
        for char in card_number:
            if re.match(r'\d', char):
                if digit_idx < len(digits_only) - visible_digits:
                    formatted_result.append(mask_char)
                else:
                    formatted_result.append(digits_only[digit_idx])
                digit_idx += 1
            else:
                formatted_result.append(char)
        return "".join(formatted_result)
        
    return masked_digits


def mask_config_values(data: dict | list, patterns: dict = None) -> dict | list:
    """Mask sensitive configuration values based on configurable pattern rules."""
    if patterns is None:
        patterns = {
            'email': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
            'phone': r'^\+?[1-9]\d{1,14}$',
            'api_key': r'^(sk_|pk_|live_|test_|secret_)[a-zA-Z0-9]{20,}',
            'credit_card': r'^[456][0-9]{3}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$'
        }
        
    def _mask_value(key: str, value: any) -> any:
        if not isinstance(value, str):
            return value
            
        for pattern_type, pattern in patterns.items():
            if re.match(pattern, value):
                if pattern_type == 'email':
                    return mask_email(value)
                elif pattern_type == 'phone':
                    return mask_phone(value)
                elif pattern_type == 'api_key':
                    return mask_api_key(value)
                elif pattern_type == 'credit_card':
                    return mask_credit_card(value)
        return value
        
    def _mask_dict(d: dict) -> dict:
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = _mask_dict(v)
            elif isinstance(v, list):
                result[k] = [_mask_value(k, item) if not isinstance(item, (dict, list)) else _mask_item(item) for item in v]
            else:
                result[k] = _mask_value(k, v)
        return result
        
    def _mask_item(item: any) -> any:
        if isinstance(item, dict):
            return _mask_dict(item)
        elif isinstance(item, list):
            return [_mask_item(sub_item) for sub_item in item]
        else:
            return _mask_value(None, item)
            
    if isinstance(data, dict):
        return _mask_dict(data)
    elif isinstance(data, list):
        return [_mask_item(item) for item in data]
    return data


class LocaleFormatter:
    """Utility class for locale-specific formatting of numbers, dates, and currencies."""
    
    LOCALE_CONFIGS = {
        'en_US': {'number_grouping': True, 'decimal_sep': '.', 'group_sep': ',', 'currency_symbol': '$', 'date_format': '%m/%d/%Y'},
        'en_GB': {'number_grouping': True, 'decimal_sep': '.', 'group_sep': ',', 'currency_symbol': '£', 'date_format': '%d/%m/%Y'},
        'de_DE': {'number_grouping': True, 'decimal_sep': ',', 'group_sep': '.', 'currency_symbol': '€', 'date_format': '%d.%m.%Y'},
        'fr_FR': {'number_grouping': True, 'decimal_sep': ',', 'group_sep': ' ', 'currency_symbol': '€', 'date_format': '%d/%m/%Y'},
        'ja_JP': {'number_grouping': True, 'decimal_sep': '.', 'group_sep': ',', 'currency_symbol': '¥', 'date_format': '%Y/%m/%d'},
        'zh_CN': {'number_grouping': True, 'decimal_sep': '.', 'group_sep': ',', 'currency_symbol': '¥', 'date_format': '%Y-%m-%d'},
        'es_ES': {'number_grouping': True, 'decimal_sep': ',', 'group_sep': '.', 'currency_symbol': '€', 'date_format': '%d/%m/%Y'},
        'it_IT': {'number_grouping': True, 'decimal_sep': ',', 'group_sep': '.', 'currency_symbol': '€', 'date_format': '%d/%m/%Y'},
    }
    
    CURRENCY_SYMBOLS = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
        'CHF': 'Fr', 'CAD': 'C$', 'AUD': 'A$', 'INR': '₹', 'BRL': 'R$'
    }
    
    @classmethod
    def _get_locale_config(cls, locale_str: str) -> dict:
        """Get configuration for a specific locale."""
        if not locale_str:
            return cls.LOCALE_CONFIGS.get('en_US', cls.LOCALE_CONFIGS['en_US'])
        
        locale_key = locale_str.replace('-', '_').upper()
        for config_key, config in cls.LOCALE_CONFIGS.items():
            if config_key == locale_key or config_key.split('_')[0] == locale_key.split('_')[0]:
                return config
        
        return cls.LOCALE_CONFIGS.get('en_US', cls.LOCALE_CONFIGS['en_US'])
    
    @classmethod
    def format_number(cls, value: float | int, locale_str: str = None, decimal_places: int = 2) -> str:
        """Format a number according to specific locale rules."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValidationError("Value must be a number", field=None, value=value)
        
        config = cls._get_locale_config(locale_str)
        decimal_sep = config['decimal_sep']
        group_sep = config.get('group_sep', ',')
        
        # Handle negative numbers
        is_negative = value < 0
        abs_value = abs(float(value))
        
        # Format with decimal places
        formatted_decimal = f"{abs_value:.{decimal_places}f}".split('.')
        integer_part = formatted_decimal[0]
        decimal_part = formatted_decimal[1] if len(formatted_decimal) > 1 else "0" * decimal_places
        
        # Add grouping separators
        if config.get('number_grouping', True):
            parts = []
            while len(integer_part) > 3:
                parts.append(integer_part[-3:])
                integer_part = integer_part[:-3]
            parts.append(integer_part)
            integer_part = group_sep.join(parts[::-1])
        
        result = f"{integer_part}{decimal_sep}{decimal_part}"
        
        if is_negative:
            result = f"-{result}"
            
        return result
    
    @classmethod
    def format_currency(cls, amount: float | int, currency_code: str, locale_str: str = None) -> str:
        """Format an amount as currency according to specific locale rules."""
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise ValidationError("Amount must be a number", field=None, value=amount)
        
        if not isinstance(currency_code, str):
            raise ValidationError("Currency code must be a string", field=None, value=currency_code)
            
        currency_code = currency_code.upper()
        
        config = cls._get_locale_config(locale_str)
        symbol = cls.CURRENCY_SYMBOLS.get(currency_code, currency_code)
        decimal_sep = config['decimal_sep']
        group_sep = config.get('group_sep', ',')
        
        is_negative = amount < 0
        abs_value = abs(float(amount))
        
        formatted_decimal = f"{abs_value:.2f}".split('.')
        integer_part = formatted_decimal[0]
        decimal_part = formatted_decimal[1] if len(formatted_decimal) > 1 else "00"
        
        if config.get('number_grouping', True):
            parts = []
            while len(integer_part) > 3:
                parts.append(integer_part[-3:])
                integer_part = integer_part[:-3]
            parts.append(integer_part)
            integer_part = group_sep.join(parts[::-1])
        
        number_str = f"{integer_part}{decimal_sep}{decimal_part}"
        
        # Locale-specific currency placement
        if locale_str and locale_str.startswith(('de_', 'fr_', 'es_', 'it_')):
            result = f"{number_str} {symbol if symbol != '€' else ''}{currency_code}" if symbol == '€' else f"{number_str} {symbol}"
            # For EUR in EU locales, format as "1.234,56 €" or "1 234,56 €"
            if currency_code == 'EUR':
                result = f"{number_str} {symbol}"
        else:
            is_negative_prefix = "-" if is_negative else ""
            result = f"{is_negative_prefix}{symbol}{number_str if not is_negative else number_str.replace('-', '')}"
        
        if is_negative:
            result = f"-{cls.CURRENCY_SYMBOLS.get(currency_code, currency_code)}{number_str}"
            
        return result
    
    @classmethod
    def format_date(cls, date_obj: datetime | str, locale_str: str = None, format_type: str = 'date') -> str:
        """Format a date according to specific locale rules."""
        if isinstance(date_obj, str):
            try:
                dt = cls._parse_date_string(date_obj)
            except Exception:
                raise ValidationError(f"Unable to parse date string", field=None, value=date_obj)
        elif isinstance(date_obj, datetime):
            dt = date_obj
        else:
            raise ValidationError("Date must be a datetime object or string", field=None, value=date_obj)
        
        config = cls._get_locale_config(locale_str)
        date_format = config.get('date_format', '%m/%d/%Y')
        
        if format_type == 'time':
            return dt.strftime('%H:%M:%S')
        elif format_type == 'datetime':
            return f"{dt.strftime(date_format)} {dt.strftime('%H:%M:%S')}"
        else:
            return dt.strftime(date_format)
    
    @classmethod
    def _parse_date_string(cls, date_str: str) -> datetime:
        """Parse a date string to a datetime object."""
        date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
            "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        raise ValidationError(f"Unable to parse date string", field=None, value=date_str)


def format_number_locale(value: float | int, locale_str: str = None, decimal_places: int = 2) -> str:
    """Format a number according to specific locale rules using LocaleFormatter."""
    return LocaleFormatter.format_number(value, locale_str, decimal_places)


def format_currency_locale(amount: float | int, currency_code: str, locale_str: str = None) -> str:
    """Format an amount as currency according to specific locale rules using LocaleFormatter."""
    return LocaleFormatter.format_currency(amount, currency_code, locale_str)


def format_date_locale(date_obj: datetime | str, locale_str: str = None, format_type: str = 'date') -> str:
    """Format a date according to specific locale rules using LocaleFormatter."""
    return LocaleFormatter.format_date(date_obj, locale_str, format_type)


def group_by_key(lst: list, key_field: str) -> dict:
    """Group a list of dictionaries by a specific key field."""
    if not isinstance(lst, list):
        raise ValidationError("Input must be a list", field=None, value=lst)
    if not all(isinstance(item, dict) for item in lst):
        raise ValidationError("All items in list must be dictionaries", field=None, value=lst)
    
    result = {}
    for item in lst:
        key = item.get(key_field)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def group_by_function(lst: list, func: callable) -> dict:
    """Group a list using a key function that returns the grouping key."""
    if not isinstance(lst, list):
        raise ValidationError("Input must be a list", field=None, value=lst)
    if not callable(func):
        raise ValidationError("Key function must be a callable", field=None, value=func)
    
    result = {}
    for item in lst:
        key = func(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def moving_average(data: list[float | int], window_size: int) -> list[float | None]:
    """Calculate moving average over a numeric sequence with specified window size."""
    if not isinstance(data, (list, tuple)):
        raise ValidationError("Data must be a list or tuple", field=None, value=data)
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValidationError("Window size must be a positive integer", field=None, value=window_size)
    
    result = []
    for i in range(len(data)):
        if i < window_size - 1:
            result.append(None)
        else:
            window = data[i - window_size + 1:i + 1]
            numeric_values = [x for x in window if isinstance(x, (int, float)) and not isinstance(x, bool)]
            if numeric_values:
                result.append(sum(numeric_values) / len(numeric_values))
            else:
                result.append(None)
    return result


def rolling_window_stats(data: list[float | int], window_size: int) -> list[dict | None]:
    """Perform rolling window statistics on a numeric sequence, returning min, max, mean, and count for each window."""
    if not isinstance(data, (list, tuple)):
        raise ValidationError("Data must be a list or tuple", field=None, value=data)
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValidationError("Window size must be a positive integer", field=None, value=window_size)
    
    result = []
    for i in range(len(data)):
        if i < window_size - 1:
            result.append(None)
        else:
            window = data[i - window_size + 1:i + 1]
            numeric_values = [x for x in window if isinstance(x, (int, float)) and not isinstance(x, bool)]
            
            if numeric_values:
                stats = {
                    'window': window,
                    'numeric_values': numeric_values,
                    'count': len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'mean': sum(numeric_values) / len(numeric_values)
                }
            else:
                stats = None
            result.append(stats)
    return result


def get_env_secret(name: str, default: str | None = None) -> str | None:
    """Safely retrieve an environment variable for sensitive values like API keys, tokens, or passwords."""
    return os.environ.get(name, default)


def validate_api_key_format(key: str, prefix: str | None = None) -> bool:
    """Validate an API key format with optional prefix requirement."""
    if not isinstance(key, str):
        raise ValidationError("API key must be a string", field=None, value=key)
        
    if len(key) < 8:
        raise ValidationError("API key is too short (minimum 8 characters)", field=None, value=key)
        
    if prefix and not key.startswith(prefix):
        raise ValidationError(f"API key must start with prefix: {prefix}", field=None, value=key)
        
    return True


def validate_token_format(token: str) -> bool:
    """Validate a token format (e.g., JWT or similar base64-encoded tokens)."""
    if not isinstance(token, str):
        raise ValidationError("Token must be a string", field=None, value=token)
        
    if len(token) < 10:
        raise ValidationError("Token is too short (minimum 10 characters)", field=None, value=token)
        
    return True


def get_env_secret_masked(name: str, default: str | None = None) -> str | None:
    """Retrieve an environment variable for secrets and return a masked version using mask_api_key."""
    secret = os.environ.get(name, default)
    if secret is None or secret == "":
        return None
    return mask_api_key(secret, prefix_visible=4, suffix_visible=4)


def load_env_secrets(env_vars: list[str]) -> dict:
    """Load multiple sensitive environment variables and return a dict with masked values for validation."""
    result = {}
    for var_name in env_vars:
        secret = os.environ.get(var_name)
        if secret is not None and secret != "":
            result[var_name] = mask_api_key(secret, prefix_visible=4, suffix_visible=4)
        else:
            result[var_name] = None
    return result


def validate_secret_env_exists(env_var_name: str) -> bool:
    """Validate that a sensitive environment variable exists and is not empty."""
    if env_var_name not in os.environ:
        raise ValidationError(f"Environment variable '{env_var_name}' is not set", field=None, value=env_var_name)
    
    secret_value = os.environ.get(env_var_name)
    if not secret_value or secret_value == "":
        raise ValidationError(f"Environment variable '{env_var_name}' is empty", field=None, value=secret_value)
        
    return True


def get_env_var_masked_custom(name: str, default: str | None = None, prefix_visible: int = 4, suffix_visible: int = 4) -> str | None:
    """Retrieve an environment variable for secrets and return a masked version with customizable visibility."""
    secret = os.environ.get(name, default)
    if secret is None or secret == "":
        return None
    return mask_api_key(secret, prefix_visible=prefix_visible, suffix_visible=suffix_visible)


def display_masked_secrets(env_vars: list[str], prefix_visible: int = 4, suffix_visible: int = 4) -> dict:
    """Load multiple sensitive environment variables and return a dict with masked values for safe logging/display."""
    result = {}
    for var_name in env_vars:
        secret = os.environ.get(var_name)
        if secret is not None and secret != "":
            result[var_name] = mask_api_key(secret, prefix_visible=prefix_visible, suffix_visible=suffix_visible)
        else:
            result[var_name] = None
    return result


def format_secret_log(var_name: str, secret: str | None, mask_prefix: int = 4, mask_suffix: int = 4) -> str:
    """Format a secret variable name and value for safe logging with masked output."""
    if secret is None or secret == "":
        return f"{var_name}: <not set>"
    masked = mask_api_key(secret, prefix_visible=mask_prefix, suffix_visible=mask_suffix)
    return f"{var_name}: {masked}"


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate the Levenshtein similarity ratio between two strings (0.0 to 1.0)."""
    if not isinstance(s1, str) or not isinstance(s2, str):
        raise ValidationError("Both inputs must be strings", field=None, value=(s1, s2))
    
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / float(max_len))


def jaccard_similarity(set1: set | str, set2: set | str) -> float:
    """Calculate the Jaccard similarity between two sets or strings (0.0 to 1.0)."""
    if isinstance(set1, str):
        set1 = set(set1.lower())
    if isinstance(set2, str):
        set2 = set(set2.lower())
    
    if not isinstance(set1, set) or not isinstance(set2, set):
        raise ValidationError("Inputs must be sets or strings", field=None, value=(set1, set2))
    
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    
    return float(intersection) / float(union)


def fuzzy_match_strings(text1: str, text2: str, threshold: float = 0.8, method: str = 'levenshtein') -> bool:
    """Compare two strings using specified fuzzy matching method with configurable similarity threshold."""
    if not isinstance(text1, str) or not isinstance(text2, str):
        raise ValidationError("Both inputs must be strings", field=None, value=(text1, text2))
    
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    similarity = 0.0
    if method == 'levenshtein':
        similarity = levenshtein_similarity(text1, text2)
    elif method == 'jaccard':
        similarity = jaccard_similarity(text1, text2)
    else:
        raise ValidationError(f"Unsupported fuzzy matching method: {method}", field=None, value=method)
    
    return similarity >= threshold


def fuzzy_deduplicate(items: list, key_func: callable = None, threshold: float = 0.8, method: str = 'levenshtein') -> list:
    """Deduplicate a list of strings or dictionaries using fuzzy string matching with configurable thresholds."""
    if not isinstance(items, list):
        raise ValidationError("Items must be a list", field=None, value=items)
    
    def get_text(item: any) -> str:
        if key_func:
            return str(key_func(item))
        if isinstance(item, dict):
            for k in ['name', 'title', 'text', 'label', 'value']:
                if k in item and isinstance(item[k], str):
                    return item[k]
            for v in item.values():
                if isinstance(v, str):
                    return v
        return str(item) if item else ""
    
    seen_similar = []
    result = []
    
    for item in items:
        text = get_text(item).lower().strip()
        is_duplicate = False
        
        for seen_item in seen_similar:
            seen_text = get_text(seen_item).lower().strip()
            
            if method == 'levenshtein':
                similarity = levenshtein_similarity(text, seen_text)
            elif method == 'jaccard':
                similarity = jaccard_similarity(text, seen_text)
            else:
                raise ValidationError(f"Unsupported fuzzy matching method: {method}", field=None, value=method)
            
            if similarity >= threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            result.append(item)
            seen_similar.append(item)
    
    return result


def transform_json_to_yaml(data_dict: dict) -> str:
    """Transform a dictionary to YAML string format."""
    return serialize_yaml(data_dict)


def transform_yaml_to_json(yaml_string: str) -> dict:
    """Parse YAML string and return as Python dictionary (JSON-compatible)."""
    return parse_yaml(yaml_string)


def transform_csv_to_json(csv_string: str, has_header: bool = True) -> list[dict]:
    """Transform CSV string to a list of dictionaries."""
    lines = csv_string.strip().split('\n')
    if not lines:
        return []
    
    if has_header:
        reader = csv.DictReader(lines)
        return [dict(row) for row in reader]
    else:
        headers = ['field_{}'.format(i) for i in range(len(lines[0].split(',')))]
        reader = csv.reader(lines)
        return [dict(zip(headers, row)) for row in reader]


def transform_json_to_csv(data_list: list[dict], columns: list | None = None, has_header: bool = True) -> str:
    """Transform a list of dictionaries to CSV string format."""
    if not data_list:
        return ''
    
    output = StringIO()
    writer = csv.writer(output)
    
    if has_header and data_list:
        keys = columns or list(data_list[0].keys())
        writer.writerow(keys)
        
    for item in data_list:
        if columns:
            row = [str(item.get(col, '')) for col in columns]
        else:
            row = [str(item.get(k, '')) for k in item.keys()]
        writer.writerow(row)
    
    return output.getvalue()


def transform_yaml_to_csv(yaml_string: str, columns: list | None = None, has_header: bool = True) -> str:
    """Transform YAML string to CSV format."""
    data_dict = parse_yaml(yaml_string)
    if isinstance(data_dict, dict):
        if 'items' in data_dict and isinstance(data_dict['items'], list):
            data_list = data_dict['items']
        else:
            data_list = [data_dict]
    elif isinstance(data_dict, list):
        data_list = data_dict
    else:
        raise ValueError("YAML data must be a dictionary or list of dictionaries")
    
    return transform_json_to_csv(data_list, columns, has_header)


def compress_data_gzip(data_bytes: bytes) -> str:
    """Compress byte data using gzip and encode to base64 string."""
    compressed_bytes = gzip.compress(data_bytes)
    return base64.b64encode(compressed_bytes).decode('utf-8')


def decompress_data_base64_compressed(compressed_data: str, compression_method: str = 'gzip') -> bytes:
    """Decompress base64 encoded compressed data using gzip or zlib."""
    compressed_bytes = base64.b64decode(compressed_data)
    if compression_method == 'gzip':
        return gzip.decompress(compressed_bytes)
    elif compression_method == 'zlib':
        return zlib.decompress(compressed_bytes)
    else:
        raise ValueError("Compression method must be 'gzip' or 'zlib'")


def transform_and_compress_json_to_yaml(json_data: dict | str, compress: bool = True, compression_method: str = 'gzip', encoding: str = 'utf-8') -> str:
    """Transform JSON data to YAML format and optionally compress using gzip or zlib."""
    if isinstance(json_data, dict):
        yaml_str = serialize_yaml(json_data)
    elif isinstance(json_data, str):
        try:
            json_dict = json.loads(json_data)
            yaml_str = serialize_yaml(json_dict)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string provided")
    else:
        raise ValueError("json_data must be a dictionary or JSON string")
    
    if compress:
        compressed_bytes = gzip.compress(yaml_str.encode(encoding)) if compression_method == 'gzip' else zlib.compress(yaml_str.encode(encoding))
        return base64.b64encode(compressed_bytes).decode(encoding)
    
    return yaml_str


def transform_and_decompress_yaml_to_json(compressed_yaml_data: str, compression_method: str = 'gzip', encoding: str = 'utf-8') -> dict:
    """Decompress and transform YAML data to JSON-compatible dictionary."""
    compressed_bytes = base64.b64decode(compressed_yaml_data)
    if compression_method == 'gzip':
        decompressed_bytes = gzip.decompress(compressed_bytes)
    elif compression_method == 'zlib':
        decompressed_bytes = zlib.decompress(compressed_bytes)
    else:
        raise ValueError("Compression method must be 'gzip' or 'zlib'")
    
    yaml_str = decompressed_bytes.decode(encoding)
    return parse_yaml(yaml_str)


def transform_and_compress_csv_to_json(csv_string: str, compress: bool = True, compression_method: str = 'gzip', encoding: str = 'utf-8') -> str:
    """Transform CSV data to JSON (list of dicts) format and optionally compress using gzip or zlib."""
    json_data = transform_csv_to_json(csv_string)
    json_str = json.dumps(json_data)
    
    if compress:
        compressed_bytes = gzip.compress(json_str.encode(encoding)) if compression_method == 'gzip' else zlib.compress(json_str.encode(encoding))
        return base64.b64encode(compressed_bytes).decode(encoding)
    
    return json_str


def transform_and_decompress_json_to_csv(compressed_json_data: str, compression_method: str = 'gzip', encoding: str = 'utf-8') -> str:
    """Decompress and transform JSON data (list of dicts) to CSV format."""
    compressed_bytes = base64.b64decode(compressed_json_data)
    if compression_method == 'gzip':
        decompressed_bytes = gzip.decompress(compressed_bytes)
    elif compression_method == 'zlib':
        decompressed_bytes = zlib.decompress(compressed_bytes)
    else:
        raise ValueError("Compression method must be 'gzip' or 'zlib'")
    
    json_str = decompressed_bytes.decode(encoding)
    json_data = json.loads(json_str)
    
    if not isinstance(json_data, list):
        json_data = [json_data] if isinstance(json_data, dict) else []
    
    return transform_json_to_csv(json_data)


def group_by_time_interval(data: list[dict], interval_seconds: int, timestamp_key: str, tz_info=None) -> dict:
    """Group a list of timestamped dictionaries by time intervals in seconds."""
    if not isinstance(data, list):
        raise ValidationError("Data must be a list", field=None, value=data)
    
    result = {}
    
    def parse_timestamp(ts_val):
        if isinstance(ts_val, (int, float)):
            dt = datetime.fromtimestamp(float(ts_val), tz=tz_info or timezone.utc)
        elif isinstance(ts_val, str):
            try:
                dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                dt = datetime.strptime(ts_val, "%Y-%m-%d %H:%M:%S")
                if tz_info:
                    dt = dt.replace(tzinfo=tz_info)
                else:
                    dt = dt.replace(tzinfo=timezone.utc)
        elif isinstance(ts_val, datetime):
            dt = ts_val
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            raise ValidationError(f"Invalid timestamp type", field=None, value=ts_val)
        return dt
    
    for item in data:
        if not isinstance(item, dict):
            continue
        ts_val = item.get(timestamp_key)
        if ts_val is None:
            continue
        
        dt = parse_timestamp(ts_val)
        epoch_seconds = int(dt.timestamp())
        interval_start = (epoch_seconds // interval_seconds) * interval_seconds
        
        window_key = datetime.fromtimestamp(interval_start, tz=dt.tzinfo).isoformat()
        
        if window_key not in result:
            result[window_key] = {'interval_start': window_key, 'items': [], 'count': 0}
        
        result[window_key]['items'].append(item)
        result[window_key]['count'] += 1
        
    return result


def calculate_hourly_aggregates(data: list[dict], timestamp_key: str, value_keys: list[str] | None = None, tz_info=None) -> dict:
    """Calculate hourly aggregates for a list of timestamped dictionaries."""
    if not isinstance(data, list):
        raise ValidationError("Data must be a list", field=None, value=data)
    
    result = {}
    
    def parse_timestamp(ts_val):
        if isinstance(ts_val, (int, float)):
            dt = datetime.fromtimestamp(float(ts_val), tz=tz_info or timezone.utc)
        elif isinstance(ts_val, str):
            try:
                dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                dt = datetime.strptime(ts_val, "%Y-%m-%d %H:%M:%S")
                if tz_info:
                    dt = dt.replace(tzinfo=tz_info)
                else:
                    dt = dt.replace(tzinfo=timezone.utc)
        elif isinstance(ts_val, datetime):
            dt = ts_val
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            raise ValidationError(f"Invalid timestamp type", field=None, value=ts_val)
        return dt
    
    hourly_buckets = {}
    
    for item in data:
        if not isinstance(item, dict):
            continue
        ts_val = item.get(timestamp_key)
        if ts_val is None:
            continue
        
        dt = parse_timestamp(ts_val)
        hour_key = dt.strftime("%Y-%m-%dT%H:00:00")
        
        if hour_key not in hourly_buckets:
            hourly_buckets[hour_key] = {'interval_start': hour_key, 'items': [], 'count': 0}
        
        hourly_buckets[hour_key]['items'].append(item)
        hourly_buckets[hour_key]['count'] += 1
    
    for hour_key, bucket in hourly_buckets.items():
        aggregates = {'hour': hour_key, 'count': bucket['count']}
        
        if value_keys:
            for v_key in value_keys:
                numeric_values = []
                for item in bucket['items']:
                    val = item.get(v_key)
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        numeric_values.append(float(val))
                
                if numeric_values:
                    aggregates[f'{v_key}_sum'] = sum(numeric_values)
                    aggregates[f'{v_key}_avg'] = sum(numeric_values) / len(numeric_values)
                    aggregates[f'{v_key}_min'] = min(numeric_values)
                    aggregates[f'{v_key}_max'] = max(numeric_values)
                    aggregates[f'{v_key}_count'] = len(numeric_values)
                else:
                    aggregates[f'{v_key}_sum'] = None
                    aggregates[f'{v_key}_avg'] = None
                    aggregates[f'{v_key}_min'] = None
                    aggregates[f'{v_key}_max'] = None
                    aggregates[f'{v_key}_count'] = 0
        else:
            for item in bucket['items']:
                for k, v in item.items():
                    if k == timestamp_key or isinstance(v, (dict, list)):
                        continue
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        numeric_values = [float(x) for x in [v] + [item.get(key) for key, val in bucket['items'].items() if isinstance(val, (int, float)) and not isinstance(val, bool)]]
                        
        result[hour_key] = aggregates
        
    return result


def calculate_daily_aggregates(data: list[dict], timestamp_key: str, value_keys: list[str] | None = None, tz_info=None) -> dict:
    """Calculate daily aggregates for a list of timestamped dictionaries."""
    if not isinstance(data, list):
        raise ValidationError("Data must be a list", field=None, value=data)
    
    result = {}
    
    def parse_timestamp(ts_val):
        if isinstance(ts_val, (int, float)):
            dt = datetime.fromtimestamp(float(ts_val), tz=tz_info or timezone.utc)
        elif isinstance(ts_val, str):
            try:
                dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                dt = datetime.strptime(ts_val, "%Y-%m-%d %H:%M:%S")
                if tz_info:
                    dt = dt.replace(tzinfo=tz_info)
                else:
                    dt = dt.replace(tzinfo=timezone.utc)
        elif isinstance(ts_val, datetime):
            dt = ts_val
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            raise ValidationError(f"Invalid timestamp type", field=None, value=ts_val)
        return dt
    
    daily_buckets = {}
    
    for item in data:
        if not isinstance(item, dict):
            continue
        ts_val = item.get(timestamp_key)
        if ts_val is None:
            continue
        
        dt = parse_timestamp(ts_val)
        day_key = dt.strftime("%Y-%m-%d")
        
        if day_key not in daily_buckets:
            daily_buckets[day_key] = {'interval_start': day_key, 'items': [], 'count': 0}
        
        daily_buckets[day_key]['items'].append(item)
        daily_buckets[day_key]['count'] += 1
    
    for day_key, bucket in daily_buckets.items():
        aggregates = {'day': day_key, 'count': bucket['count']}
        
        if value_keys:
            for v_key in value_keys:
                numeric_values = []
                for item in bucket['items']:
                    val = item.get(v_key)
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        numeric_values.append(float(val))
                
                if numeric_values:
                    aggregates[f'{v_key}_sum'] = sum(numeric_values)
                    aggregates[f'{v_key}_avg'] = sum(numeric_values) / len(numeric_values)
                    aggregates[f'{v_key}_min'] = min(numeric_values)
                    aggregates[f'{v_key}_max'] = max(numeric_values)
                    aggregates[f'{v_key}_count'] = len(numeric_values)
                else:
                    aggregates[f'{v_key}_sum'] = None
                    aggregates[f'{v_key}_avg'] = None
                    aggregates[f'{v_key}_min'] = None
                    aggregates[f'{v_key}_max'] = None
                    aggregates[f'{v_key}_count'] = 0
                    
        result[day_key] = aggregates
        
    return result


def temporal_rolling_statistics(data: list[dict], window_size_seconds: int, timestamp_key: str, value_key: str, tz_info=None) -> list[dict]:
    """Perform temporal rolling statistics on timestamped sequences with a time-based window."""
    if not isinstance(data, list):
        raise ValidationError("Data must be a list", field=None, value=data)
        
    def parse_timestamp(ts_val):
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(float(ts_val), tz=tz_info or timezone.utc), float(ts_val)
        elif isinstance(ts_val, str):
            try:
                dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt, float(dt.timestamp())
            except ValueError:
                dt = datetime.strptime(ts_val, "%Y-%m-%d %H:%M:%S")
                if tz_info:
                    dt = dt.replace(tzinfo=tz_info)
                else:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt, float(dt.timestamp())
        elif isinstance(ts_val, datetime):
            if ts_val.tzinfo is None:
                ts_val = ts_val.replace(tzinfo=timezone.utc)
            return ts_val, float(ts_val.timestamp())
        else:
            raise ValidationError(f"Invalid timestamp type", field=None, value=ts_val)

    sorted_data = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ts_val = item.get(timestamp_key)
        if ts_val is None:
            continue
        dt, ts_seconds = parse_timestamp(ts_val)
        sorted_data.append({'item': item, 'dt': dt, 'ts_seconds': ts_seconds})

    sorted_data.sort(key=lambda x: x['ts_seconds'])
    
    result = []
    for i, entry in enumerate(sorted_data):
        current_ts = entry['ts_seconds']
        window_start_ts = current_ts - window_size_seconds
        
        window_items = []
        numeric_values = []
        
        for j in range(i, -1, -1):
            prev_entry = sorted_data[j]
            if prev_entry['ts_seconds'] >= window_start_ts:
                item = prev_entry['item']
                window_items.append(item)
                val = item.get(value_key)
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    numeric_values.append(float(val))
            else:
                break
        
        stats = {
            'timestamp': entry['dt'].isoformat(),
            'window_start': datetime.fromtimestamp(window_start_ts, tz=entry['dt'].tzinfo).isoformat() if window_start_ts > 0 else None,
            'items_in_window': len(window_items),
            'numeric_values_count': len(numeric_values)
        }
        
        if numeric_values:
            stats['sum'] = sum(numeric_values)
            stats['avg'] = sum(numeric_values) / len(numeric_values)
            stats['min'] = min(numeric_values)
            stats['max'] = max(numeric_values)
            stats['window_items'] = window_items
        else:
            stats['sum'] = None
            stats['avg'] = None
            stats['min'] = None
            stats['max'] = None
            stats['window_items'] = []
            
        result.append(stats)
        
    return result


def parse_datetime_string(dt_str: str, formats: list[str] | None = None) -> datetime:
    """Parse a datetime string using various common datetime format patterns."""
    if not isinstance(dt_str, str):
        raise ValidationError("Datetime string must be a string", field=None, value=dt_str)
    
    default_formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%b %d, %Y %H:%M:%S",
        "%B %d, %Y %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%b %d, %Y",
        "%B %d, %Y"
    ]
    
    formats_to_use = formats if formats is not None else default_formats
    
    for fmt in formats_to_use:
        try:
            dt = datetime.strptime(dt_str.strip(), fmt)
            if dt.tzinfo is None and '%z' not in fmt and 'Z' not in dt_str:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    raise ValidationError(f"Unable to parse datetime string with provided formats", field=None, value=dt_str)


def convert_timezone_dt(dt: datetime, from_tz: str | None = None, to_tz: str = "UTC") -> datetime:
    """Convert a datetime object between timezones using zoneinfo.ZoneInfo."""
    if dt.tzinfo is None:
        if from_tz:
            if ZoneInfo is not None:
                try:
                    tz_from = ZoneInfo(from_tz)
                    dt = dt.replace(tzinfo=tz_from)
                except Exception:
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
    
    if ZoneInfo is not None:
        try:
            target_tz = ZoneInfo(to_tz)
            return dt.astimezone(target_tz)
        except Exception:
            pass
    
    tz_offsets = {
        'UTC': 0, 'GMT': 0, 'Z': 0,
        'EST': -5, 'EDT': -4,
        'CST': -6, 'CDT': -5,
        'MST': -7, 'MDT': -6,
        'PST': -8, 'PDT': -7
    }
    
    to_tz_upper = to_tz.upper()
    if to_tz_upper in tz_offsets:
        offset_hours = tz_offsets[to_tz_upper]
        target_tz = timezone(timedelta(hours=offset_hours))
        return dt.astimezone(target_tz)
    
    raise ValidationError(f"Unsupported timezone: {to_tz}", field=None, value=to_tz)


def format_date_locale_specific(dt: datetime | str, locale: str = "en_US", pattern: str | None = None) -> str:
    """Format a datetime or string with locale-specific patterns."""
    if isinstance(dt, str):
        dt_obj = parse_datetime_string(dt)
    elif isinstance(dt, datetime):
        dt_obj = dt
    else:
        raise ValidationError("Invalid datetime type", field=None, value=dt)
    
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
    
    config = LocaleFormatter._get_locale_config(locale)
    
    if pattern:
        return dt_obj.strftime(pattern)
    
    date_format = config.get('date_format', '%m/%d/%Y')
    time_format = '%H:%M:%S'
    
    return f"{dt_obj.strftime(date_format)} {dt_obj.strftime(time_format)}"


def secure_write_config(file_path: str, content: str, mode: int = 0o600) -> None:
    """Write configuration file with secure permissions (default 0o600)."""
    import stat
    
    # Write to a temporary file first
    temp_file = f"{file_path}.tmp.{os.getpid()}"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Move temp file to target and set permissions
    os.replace(temp_file, file_path)
    os.chmod(file_path, mode)
    
    # Verify permissions are secure
    stat_info = os.stat(file_path)
    if stat.S_IMODE(stat_info.st_mode) & 0o777 != mode:
        raise ResourceAccessDeniedError(f"Failed to set secure permissions on {file_path}")


def secure_read_config(file_path: str) -> str:
    """Read configuration file and verify secure permissions."""
    import stat
    
    if not os.path.exists(file_path):
        raise ResourceNotFoundError(f"Configuration file not found: {file_path}")
    
    stat_info = os.stat(file_path)
    mode = stat.S_IMODE(stat_info.st_mode)
    
    # Check that file is not world-readable or world-writable
    if mode & 0o077 != 0:
        raise ResourceAccessDeniedError(f"Insecure permissions on configuration file: {file_path} (mode: {oct(mode)})")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def secure_write_encrypted_config(file_path: str, data: dict, key: str) -> None:
    """Securely write encrypted configuration data to file with proper permissions."""
    if Fernet is None:
        raise ImportError("cryptography is required for Fernet encryption. Install with: pip install cryptography")
    
    json_content = serialize_json(data)
    encrypted_data = encrypt_string(json_content, key)
    
    secure_write_config(file_path, encrypted_data, 0o600)


def retrieve_encrypted_config(file_path: str, key: str) -> dict:
    """Securely read and decrypt configuration data from file."""
    encrypted_data = secure_read_config(file_path)
    decrypted_json = decrypt_string(encrypted_data, key)
    return parse_json(decrypted_json)


def validate_schema_for_transformation(data: dict | list, schema: dict) -> dict | list:
    """Validate data against a schema definition with type, pattern, and range checks before transformation."""
    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a dictionary", field=None, value=schema)
    
    validated_data = {}
    for field, rules in schema.items():
        if not isinstance(rules, dict):
            raise ValidationError(f"Invalid schema rule for field {field}")
        
        if rules.get('required') and field not in data:
            raise ValidationError(f"Missing required field '{field}'", field=field)
        
        if field not in data:
            continue
            
        value = data[field]
        
        expected_type = rules.get('type')
        if expected_type:
            type_check(value, expected_type, field_name=f"{field}")
        
        if isinstance(value, str) and 'pattern' in rules:
            if not validate_pattern(value, rules['pattern']):
                raise ValidationError(f"Value does not match pattern", field=field, value=value)
        
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if 'min' in rules and value < rules['min']:
                raise ValidationError(f"Value {value} is less than minimum {rules['min']}", field=field, value=value)
            if 'max' in rules and value > rules['max']:
                raise ValidationError(f"Value {value} exceeds maximum {rules['max']}", field=field, value=value)
        
        if isinstance(value, (str, list)):
            if 'min_length' in rules and len(value) < rules['min_length']:
                raise ValidationError(f"Length {len(value)} is less than minimum {rules['min_length']}", field=field, value=value)
            if 'max_length' in rules and len(value) > rules['max_length']:
                raise ValidationError(f"Length {len(value)} exceeds maximum {rules['max_length']}", field=field, value=value)
        
        validated_data[field] = value
        
    return validated_data


def transform_json_with_validation(json_string: str, schema: dict | None = None) -> str:
    """Transform JSON data with optional schema validation before transformation to ensure data integrity."""
    parsed_data = parse_json(json_string)
    
    if isinstance(parsed_data, dict) and schema is not None:
        validated_data = validate_schema_for_transformation(parsed_data, schema)
        return serialize_json(validated_data)
    elif isinstance(parsed_data, list) and schema is not None:
        if 'items' not in schema or 'properties' not in schema['items']:
            raise ValidationError("Schema for list must include 'items.properties' definition")
        
        item_schema = schema['items']['properties']
        validated_list = []
        for item in parsed_data:
            if isinstance(item, dict):
                validated_item = validate_schema_for_transformation(item, item_schema)
                validated_list.append(validated_item)
            else:
                raise ValidationError(f"List items must be dictionaries when schema validation is enabled", field=None, value=item)
        return serialize_json({'items': validated_list})
    
    return serialize_json(parsed_data)


def transform_yaml_with_validation(yaml_string: str, schema: dict | None = None) -> str:
    """Transform YAML data with optional schema validation before transformation to ensure data integrity."""
    if yaml is None:
        raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
    
    parsed_data = parse_yaml(yaml_string)
    
    if isinstance(parsed_data, dict) and schema is not None:
        validated_data = validate_schema_for_transformation(parsed_data, schema)
        return serialize_yaml(validated_data)
    elif isinstance(parsed_data, list) and schema is not None:
        if 'items' not in schema or 'properties' not in schema['items']:
            raise ValidationError("Schema for list must include 'items.properties' definition")
        
        item_schema = schema['items']['properties']
        validated_list = []
        for item in parsed_data:
            if isinstance(item, dict):
                validated_item = validate_schema_for_transformation(item, item_schema)
                validated_list.append(validated_item)
            else:
                raise ValidationError(f"List items must be dictionaries when schema validation is enabled", field=None, value=item)
        return serialize_yaml({'items': validated_list})
    
    return serialize_yaml(parsed_data)


def transform_csv_with_validation(csv_string: str, schema: dict | None = None, has_header: bool = True) -> str:
    """Transform CSV data with optional schema validation before transformation to ensure data integrity."""
    parsed_data = parse_csv(csv_string, delimiter=',', has_headers=has_header)
    
    if not parsed_data:
        return dicts_to_csv([])
    
    if schema is not None:
        item_schema = schema.get('properties', {})
        validated_list = []
        
        for row in parsed_data:
            validated_row = validate_schema_for_transformation(row, item_schema)
            validated_list.append(validated_row)
        
        return dicts_to_csv(validated_list)
    
    return dicts_to_csv(parsed_data)


def transform_json_to_yaml_with_validation(json_string: str, schema: dict | None = None) -> str:
    """Transform JSON to YAML with optional schema validation before transformation."""
    validated_json_str = transform_json_with_validation(json_string, schema)
    parsed_data = parse_json(validated_json_str)
    return serialize_yaml(parsed_data)


def transform_csv_to_json_with_validation(csv_string: str, schema: dict | None = None, has_header: bool = True) -> str:
    """Transform CSV to JSON with optional schema validation before transformation."""
    validated_csv_data = transform_csv_with_validation(csv_string, schema, has_header)
    parsed_data = parse_csv(validated_csv_data, delimiter=',', has_headers=has_header)
    return serialize_json(parsed_data)


def validate_transformation_format(source_format: str, target_format: str) -> bool:
    """Validate that the source and target formats are supported for transformation."""
    supported_formats = {'json', 'yaml', 'csv'}
    source_format = source_format.lower()
    target_format = target_format.lower()
    
    if source_format not in supported_formats:
        raise ValidationError(f"Unsupported source format: {source_format}", field=None, value=source_format)
    if target_format not in supported_formats:
        raise ValidationError(f"Unsupported target format: {target_format}", field=None, value=target_format)
    
    return True


def transform_data_with_schema_validation(data: str | dict | list, source_format: str, target_format: str, schema: dict | None = None) -> str:
    """Transform structured data between serialization formats (json, yaml, csv) with optional schema validation to ensure data integrity."""
    validate_transformation_format(source_format, target_format)
    
    source_format = source_format.lower()
    target_format = target_format.lower()
    
    if source_format == 'json':
        parsed_data = parse_json(data) if isinstance(data, str) else data
    elif source_format == 'yaml':
        if yaml is None:
            raise ImportError("PyYAML is required for YAML operations. Install with: pip install PyYAML")
        parsed_data = parse_yaml(data) if isinstance(data, str) else data
    elif source_format == 'csv':
        parsed_data = parse_csv(data, delimiter=',', has_headers=True) if isinstance(data, str) else data
    else:
        raise ValueError(f"Unsupported source format: {source_format}")
    
    if schema is not None:
        if isinstance(parsed_data, dict):
            validated_data = validate_schema_for_transformation(parsed_data, schema)
        elif isinstance(parsed_data, list):
            if 'items' in schema and 'properties' in schema['items']:
                item_schema = schema['items']['properties']
                validated_list = []
                for item in parsed_data:
                    if isinstance(item, dict):
                        validated_item = validate_schema_for_transformation(item, item_schema)
                        validated_list.append(validated_item)
                    else:
                        raise ValidationError(f"List items must be dictionaries when schema validation is enabled", field=None, value=item)
                parsed_data = {'items': validated_list}
            else:
                raise ValidationError("Schema for list must include 'items.properties' definition")
        else:
            raise ValidationError(f"Cannot validate schema for data type: {type(parsed_data).__name__}", field=None, value=parsed_data)
        
        parsed_data = parsed_data if not isinstance(parsed_data, dict) and 'items' in parsed_data else (parsed_data.get('items') if isinstance(parsed_data, dict) and 'items' in parsed_data else parsed_data)
    
    if target_format == 'json':
        return serialize_json(parsed_data)
    elif target_format == 'yaml':
        return serialize_yaml(parsed_data)
    elif target_format == 'csv':
        if not isinstance(parsed_data, list) or not all(isinstance(item, dict) for item in parsed_data):
            raise ValueError("CSV format requires a list of dictionaries as data")
        return dicts_to_csv(parsed_data)
    else:
        raise ValueError(f"Unsupported target format: {target_format}")

