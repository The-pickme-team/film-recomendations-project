"""Password hashing utilities using argon2."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError


class PasswordService:
    """Service for hashing and verifying passwords using Argon2."""

    def __init__(self) -> None:
        """Initialize password hasher with recommended settings."""
        self.hasher = PasswordHasher(
            time_cost=2,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
        )

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password.

        Args:
            password: The plaintext password to hash.

        Returns:
            The hashed password.
        """
        return self.hasher.hash(password)

    def verify_password(self, password: str, hash_: str) -> bool:
        """Verify a plaintext password against a hash.

        Args:
            password: The plaintext password to verify.
            hash_: The hashed password to verify against.

        Returns:
            True if the password matches the hash, False otherwise.
        """
        try:
            self.hasher.verify(hash_, password)
            return True
        except (VerifyMismatchError, InvalidHash):
            return False

    def check_needs_rehash(self, hash_: str) -> bool:
        """Check if a password hash needs to be rehashed.

        Args:
            hash_: The hashed password to check.

        Returns:
            True if the hash should be updated with current parameters.
        """
        return self.hasher.check_needs_rehash(hash_)


password_service = PasswordService()
