"""Configuration management for Falcon Strike-AI using Pydantic Settings."""

from pathlib import Path
from typing import ClassVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.core.exceptions import (
    AccountNotAllowlistedError,
    AuthorizationTokenError,
    InsecureConfigurationError,
)


class Settings(BaseSettings):
    """Application settings with strict security defaults and environment variable overrides."""

    model_config = SettingsConfigDict(
        env_prefix="FALCON_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Environment & Execution Mode
    environment: str = Field(default="development", description="Runtime environment name")
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")

    # SAFETY INVARIANT: DRY_RUN MUST DEFAULT TO TRUE (NFR-S4)
    dry_run: bool = Field(
        default=True,
        description="Whether the engine runs in safe dry-run mode (default=True)",
    )

    # AWS Account Guardrails (NFR-S1)
    target_account_id: str = Field(
        default="000000000000",
        description="Target AWS Account ID for emulation",
    )
    allowlisted_accounts: list[str] = Field(
        default_factory=lambda: ["000000000000", "123456789012"],
        description="Hard allowlist of permitted laboratory AWS Account IDs",
    )

    # Authorization & Two-Key Controls (NFR-S2)
    auth_token: str | None = Field(
        default=None,
        description="Signed JWT authorization token required to exit dry-run",
    )
    auth_secret_key: str = Field(
        default="falcon-strike-dev-secret-do-not-use-in-production",
        description="Secret key used for HMAC-SHA256 token verification in lab testing",
    )
    api_key: str | None = Field(
        default=None,
        description="Optional master API key for headless service authentication",
    )
    jwt_issuer: str = Field(
        default="falcon-strike-ai",
        description="JWT token issuer identifier",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT cryptographic algorithm",
    )
    jwt_expiration_minutes: int = Field(
        default=60,
        description="Default operator session expiration window in minutes",
    )

    # Insecure fallback blocklist for production guard
    KNOWN_INSECURE_SECRETS: ClassVar[tuple[str, ...]] = (
        "falcon-strike-dev-secret-do-not-use-in-production",
        "test-secret-key-123",
        "changeme",
        "secret",
        "password",
        "default",
        "12345678",
        "admin",
    )

    # Blast-Radius Safety Caps (NFR-S5)
    max_resources_touched: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Hard maximum number of resources permitted to be touched per campaign",
    )
    max_run_duration_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Hard time-box limit for campaign execution",
    )
    resource_tag_key: str = Field(
        default="FalconStrike",
        description="Mandatory tag key applied to all temporary emulation resources",
    )
    resource_tag_value: str = Field(
        default="AdversaryEmulation",
        description="Mandatory tag value applied to all temporary emulation resources",
    )

    # REST Control Plane API Settings
    api_host: str = Field(default="127.0.0.1", description="FastAPI host binding")
    api_port: int = Field(default=8000, description="FastAPI port binding")
    api_debug: bool = Field(default=False, description="FastAPI debug mode")

    # Graph Storage Configuration (Neo4j)
    neo4j_enabled: bool = Field(default=False, description="Enable live Neo4j database driver")
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="", description="Neo4j password")

    # Command & Control (C2) Emulation Settings (FR-4.1)
    c2_sink_host: str = Field(default="127.0.0.1", description="Local C2 sink host")
    c2_sink_http_port: int = Field(default=8443, description="Local C2 HTTPS sink port")
    c2_sink_dns_port: int = Field(default=8053, description="Local C2 DNS sink port")
    c2_beacon_interval_sec: int = Field(
        default=5, ge=1, le=60, description="Beacon interval in seconds"
    )
    c2_beacon_jitter_pct: int = Field(
        default=20, ge=0, le=90, description="Beacon jitter percentage"
    )

    # Audit Logging & Storage (NFR-A1, NFR-A2)
    audit_log_path: Path = Field(
        default=Path("artifacts/logs/audit.jsonl"),
        description="Path to append-only tamper-evident audit log",
    )
    telemetry_enabled: bool = Field(
        default=True, description="Enable OpenTelemetry metrics and traces"
    )

    # Immutable compiled allowlist fallback for security
    COMPILED_SAFE_ACCOUNTS: ClassVar[tuple[str, ...]] = (
        "000000000000",
        "123456789012",
    )

    @field_validator("allowlisted_accounts", mode="before")
    @classmethod
    def parse_allowlist(cls, value: str | list[str]) -> list[str]:
        """Parse comma-separated strings or return list."""
        if isinstance(value, str):
            return [account.strip() for account in value.split(",") if account.strip()]
        return value

    def model_post_init(self, __context: object) -> None:
        """Post-initialization validation hook enforcing production safety checks."""
        super().model_post_init(__context)
        self.validate_production_configuration()

    def validate_production_configuration(self) -> None:
        """Enforce strict production configuration validation.

        In production:
        - auth_secret_key must be configured and not equal any default/fallback value.
        - auth_secret_key must satisfy minimum entropy requirement (>= 32 chars).
        - api_debug must not be enabled.
        Never reveals the actual secret in exceptions or logs.
        """
        env_lower = self.environment.lower().strip()
        if env_lower in ("production", "prod"):
            # 1. Missing or empty secret check
            if not self.auth_secret_key or not self.auth_secret_key.strip():
                raise InsecureConfigurationError(
                    "Production configuration violation: FALCON_AUTH_SECRET_KEY is missing or empty. "
                    "Production deployment requires an explicitly configured, high-entropy secret key."
                )

            # 2. Known default or insecure fallback check
            cleaned_secret = self.auth_secret_key.strip()
            if cleaned_secret in self.KNOWN_INSECURE_SECRETS or "dev" in cleaned_secret.lower():
                raise InsecureConfigurationError(
                    "Production configuration violation: FALCON_AUTH_SECRET_KEY cannot use default or "
                    "development values. Provide an independently generated cryptographic secret."
                )

            # 3. Minimum length / entropy check (>= 32 characters)
            if len(cleaned_secret) < 32:
                raise InsecureConfigurationError(
                    "Production configuration violation: FALCON_AUTH_SECRET_KEY is too short. "
                    "Production requires a minimum key length of 32 characters."
                )

            # 4. Debug mode check
            if self.api_debug:
                raise InsecureConfigurationError(
                    "Production configuration violation: FALCON_API_DEBUG cannot be enabled in production."
                )

    def is_account_allowlisted(self, account_id: str) -> bool:
        """Check if an AWS Account ID is permitted by the compiled or configured allowlist."""
        return account_id in self.allowlisted_accounts or account_id in self.COMPILED_SAFE_ACCOUNTS

    def assert_account_allowlisted(self, account_id: str) -> None:
        """Enforce account allowlist check; raise exception if out of scope (NFR-S1)."""
        if not self.is_account_allowlisted(account_id):
            raise AccountNotAllowlistedError(
                f"Target AWS account '{account_id}' is not in the compiled allowlist. "
                f"Execution strictly blocked. Permitted accounts: {self.allowlisted_accounts}",
                details={"target_account": account_id, "allowlisted": self.allowlisted_accounts},
            )

    def assert_live_execution_permitted(self, account_id: str) -> None:
        """Enforce full two-key safety gate before live emulation can execute (NFR-S2)."""
        self.assert_account_allowlisted(account_id)

        if not self.dry_run:
            if not self.auth_token:
                raise AuthorizationTokenError(
                    "Live execution requested (dry_run=False) but no authorization token provided. "
                    "Two-key confirmation requires a signed JWT in FALCON_AUTH_TOKEN.",
                    details={"target_account": account_id},
                )


# Singleton settings instance
settings = Settings()
