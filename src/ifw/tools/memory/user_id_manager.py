# ifw/tools/memory/user_id_manager.py
import hashlib
import getpass
import socket
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class UserIDManager:
    """
    Manages persistent user ID for memory operations.
    Stores user ID in the existing .ifw.env file.
    """

    def __init__(self):
        self.env_file_path = Path.home() / ".ifw.env"
        self._user_id = None

    def _generate_user_id(self) -> str:
        """
        Generate a consistent user ID based on username + hostname.
        Returns a 12-character hex string.
        """
        try:
            username = getpass.getuser()
            hostname = socket.gethostname()
            unique_string = f"{username}@{hostname}"

            # Create MD5 hash and take first 12 characters
            hash_object = hashlib.md5(unique_string.encode())
            user_id = hash_object.hexdigest()[:12]

            logger.debug(f"Generated user ID '{user_id}' from '{unique_string}'")
            return user_id

        except Exception as e:
            logger.warning(f"Failed to generate user ID from system info: {e}")
            # Fallback to a simple default
            return "default_user"

    def _read_env_file(self) -> dict:
        """Read and parse the .ifw.env file."""
        env_vars = {}

        if not self.env_file_path.exists():
            logger.debug(f"Env file does not exist: {self.env_file_path}")
            return env_vars

        try:
            with open(self.env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

            logger.debug(f"Read {len(env_vars)} variables from env file")
            return env_vars

        except Exception as e:
            logger.error(f"Error reading env file {self.env_file_path}: {e}")
            return env_vars

    def _write_env_file(self, env_vars: dict) -> None:
        """Write environment variables to the .ifw.env file."""
        try:
            # Ensure the directory exists
            self.env_file_path.parent.mkdir(exist_ok=True)

            with open(self.env_file_path, "w") as f:
                f.write("# Infraware CLI Configuration\n")
                f.write("# This file stores persistent configuration for the CLI\n\n")

                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            logger.debug(f"Wrote {len(env_vars)} variables to env file")

        except Exception as e:
            logger.error(f"Error writing env file {self.env_file_path}: {e}")
            raise

    def get_user_id(self) -> str:
        """
        Get the persistent user ID. Creates one if it doesn't exist.

        Returns:
            str: The user ID for memory operations
        """
        # Return cached value if already loaded
        if self._user_id is not None:
            return self._user_id

        # Read current env file
        env_vars = self._read_env_file()

        # Check if USER_ID already exists
        if "USER_ID" in env_vars and env_vars["USER_ID"]:
            self._user_id = env_vars["USER_ID"]
            logger.debug(f"Using existing user ID: {self._user_id}")
            return self._user_id

        # Generate new user ID
        self._user_id = self._generate_user_id()

        # Add to env vars and save
        env_vars["USER_ID"] = self._user_id
        self._write_env_file(env_vars)

        logger.info(f"Created new persistent user ID: {self._user_id}")
        return self._user_id

    def reset_user_id(self) -> str:
        """
        Force regeneration of user ID. Useful for testing or troubleshooting.

        Returns:
            str: The new user ID
        """
        env_vars = self._read_env_file()
        self._user_id = self._generate_user_id()
        env_vars["USER_ID"] = self._user_id
        self._write_env_file(env_vars)

        logger.info(f"Reset user ID to: {self._user_id}")
        return self._user_id

    def get_user_info(self) -> dict:
        """
        Get information about the current user ID setup.

        Returns:
            dict: User ID information for debugging
        """
        try:
            username = getpass.getuser()
            hostname = socket.gethostname()
            unique_string = f"{username}@{hostname}"

            return {
                "user_id": self.get_user_id(),
                "username": username,
                "hostname": hostname,
                "source_string": unique_string,
                "env_file": str(self.env_file_path),
                "env_file_exists": self.env_file_path.exists(),
            }
        except Exception as e:
            return {"user_id": self.get_user_id(), "error": str(e)}


# Global instance for easy access
_user_id_manager = None


def get_user_id_manager() -> UserIDManager:
    """Get the global UserIDManager instance."""
    global _user_id_manager
    if _user_id_manager is None:
        _user_id_manager = UserIDManager()
    return _user_id_manager


def get_persistent_user_id() -> str:
    """
    Convenience function to get the persistent user ID.
    This is the main function that memory tools should use.

    Returns:
        str: The persistent user ID for memory operations
    """
    return get_user_id_manager().get_user_id()


def debug_user_id_info() -> dict:
    """
    Get debug information about user ID setup.
    Useful for troubleshooting.

    Returns:
        dict: Debug information
    """
    return get_user_id_manager().get_user_info()
