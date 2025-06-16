# force_faiss_config.py
def force_faiss_config():
    """Force the mem0_memory tool to use HuggingFace embeddings by patching at module level."""

    from mem0 import Memory as Mem0Memory
    from pathlib import Path

    # Store original from_config method
    original_from_config = Mem0Memory.from_config

    @classmethod
    def patched_from_config(cls, *args, **kwargs):
        """Patched from_config that ALWAYS forces HuggingFace for ANY FAISS config."""

        # Extract config_dict from parameters flexibly
        config_dict = None
        if args:
            config_dict = args[0]
        elif "config_dict" in kwargs:
            config_dict = kwargs["config_dict"]
        elif "config" in kwargs:
            config_dict = kwargs["config"]

        # If there's any mention of FAISS, override it completely
        if config_dict and (
            config_dict.get("vector_store", {}).get("provider") == "faiss"
            or "/faiss" in str(config_dict).lower()
            or "faiss" in str(config_dict).lower()
        ):
            # Ensure .ifw directory exists
            ifw_dir = Path.home() / ".ifw"
            ifw_dir.mkdir(mode=0o700, exist_ok=True)

            # FORCE our configuration
            forced_config = {
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "embedding_dims": 384,
                    },
                },
                "llm": {
                    "provider": "anthropic",
                    "config": {
                        "model": "claude-3-5-haiku-20241022",
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    },
                },
                "vector_store": {
                    "provider": "faiss",
                    "config": {
                        "embedding_model_dims": 384,
                        "path": str(Path.home() / ".ifw" / "mem0_faiss_db"),
                    },
                },
            }

            # Call the original method with the forced config
            # Remove config_dict from kwargs if present to avoid duplicates
            clean_kwargs = {
                k: v for k, v in kwargs.items() if k not in ["config_dict", "config"]
            }
            return original_from_config(forced_config, **clean_kwargs)

        # For non-FAISS config, use original with original parameters
        return original_from_config(*args, **kwargs)

    # Apply the patch
    Mem0Memory.from_config = patched_from_config
