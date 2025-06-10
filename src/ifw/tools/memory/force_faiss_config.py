# Monkey patch the entire mem0 module before it gets imported anywhere
def force_faiss_config():
    """Force the mem0_memory tool to use HuggingFace embeddings by patching at module level."""
    
    # Import mem0 first to patch it
    from mem0 import Memory as Mem0Memory
    
    # Store original from_config method
    original_from_config = Mem0Memory.from_config
    
    @classmethod
    def patched_from_config(cls, config_dict=None, **kwargs):
        """Patched from_config that always uses HuggingFace embeddings for FAISS."""
        
        # If it's a FAISS config, override with our HuggingFace config
        if (config_dict and 
            config_dict.get("vector_store", {}).get("provider") == "faiss"):
            
            faiss_config = {
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "embedding_dims": 384
                    }
                },
                "llm": {
                    "provider": "anthropic",
                    "config": {
                        "model": "claude-3-5-haiku-20241022",
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    }
                },
                "vector_store": {
                    "provider": "faiss",
                    "config": {
                        "embedding_model_dims": 384,
                        "path": "./mem0_faiss_db"
                    }
                }
            }
            
            return original_from_config(faiss_config, **kwargs)
        
        # For non-FAISS configs, use original
        return original_from_config(config_dict, **kwargs)
    
    # Apply the patch
    Mem0Memory.from_config = patched_from_config