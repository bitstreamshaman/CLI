import time
import threading
from typing import List, Dict, Any
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from .bash_completion import bash_completions


class TTLCache:
    """Simple TTL cache for completion results."""
    
    def __init__(self, default_ttl: float = 60):
        self._cache: Dict[str, tuple] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
    
    def get(self, key: str):
        with self._lock:
            if key in self._cache:
                value, expires = self._cache[key]
                if time.time() < expires:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def set(self, key: str, value, ttl: float = None):
        with self._lock:
            ttl = ttl or self._default_ttl
            self._cache[key] = (value, time.time() + ttl)


class SmartCompleter(Completer):
    """Simple completer that uses bash completion directly."""
    
    def __init__(self, shell_executor=None):
        self.shell_executor = shell_executor
        self._cache = TTLCache(default_ttl=30)
        self.control_commands = {'clear', 'exit', 'reset', 'history'}
    
    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        
        if not text.strip():
            return
        
        # Handle control commands first
        words = text.split()
        if len(words) == 1 and not text.endswith(' '):
            current_word = words[0]
            for cmd in self.control_commands:
                if cmd.startswith(current_word):
                    yield Completion(
                        cmd,
                        start_position=-len(current_word),
                        display=f"{cmd} (control)"
                    )
        
        # Get bash completions
        try:
            completions = self._get_bash_completions(text)
            yield from completions
        except Exception:
            # Fallback to basic completions if bash completion fails
            pass
    
    def _get_bash_completions(self, text: str) -> List[Completion]:
        """Get completions using bash_completions function."""
        # Check cache first
        cache_key = f"bash:{text}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        # Calculate current token being completed
        if text.endswith(' '):
            current_token = ''
            begidx = len(text)
        else:
            words = text.split()
            if words:
                current_token = words[-1]
                begidx = text.rfind(current_token)
            else:
                current_token = ''
                begidx = 0
        
        endidx = len(text)
        
        try:
            # Get current directory for bash completion context
            current_dir = '.'
            if self.shell_executor and hasattr(self.shell_executor, 'get_current_directory'):
                try:
                    current_dir = self.shell_executor.get_current_directory()
                except:
                    pass
            
            # Use bash_completions function directly
            completions_set, lprefix = bash_completions(
                prefix=current_token,
                line=text,
                begidx=begidx,
                endidx=endidx,
                env={'PWD': current_dir}  # Pass current directory context
            )
            
            # Convert to Completion objects
            results = []
            for comp in completions_set:
                start_pos = -lprefix if lprefix > 0 else -len(current_token)
                results.append(Completion(comp, start_position=start_pos))
            
            # Cache results
            self._cache.set(cache_key, results)
            return results
            
        except Exception:
            return []