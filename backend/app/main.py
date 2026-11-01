"""Falcon Strike-AI Control Plane & API Entrypoint."""

import argparse
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.health import router as health_root_router
from backend.app.api.v1.routes import api_v1_router
from backend.app.core.config import settings
from backend.app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    setup_logging(settings.log_level)
    logger.info(
        "Initializing Falcon Strike-AI Control Plane",
        extra={
            "details": {
                "environment": settings.environment,
                "dry_run": settings.dry_run,
                "target_account": settings.target_account_id,
                "allowlist": settings.allowlisted_accounts,
            }
        },
    )

    # Enforce initial safety assertions
    settings.assert_account_allowlisted(settings.target_account_id)

    yield

    logger.info("Shutting down Falcon Strike-AI Control Plane")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Falcon Strike-AI Control Plane",
        description=(
            "Agentic AI Automated Red Teaming & Continuous Threat Exposure Management Engine. "
            "Exclusively for authorized laboratory environments."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # Enable CORS for local dashboards
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount top-level /health endpoint and /api/v1 router
    app.include_router(health_root_router)
    app.include_router(api_v1_router)

    return app


app = create_app()


def run_cli() -> None:
    """CLI Entrypoint for running the control plane or campaign commands."""
    parser = argparse.ArgumentParser(
        prog="falcon-strike",
        description="Project Falcon Strike-AI: Continuous Threat Exposure Management CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Server subcommand
    server_parser = subparsers.add_parser("serve", help="Start the FastAPI control plane server")
    server_parser.add_argument("--host", default=settings.api_host, help="Host to bind to")
    server_parser.add_argument(
        "--port", type=int, default=settings.api_port, help="Port to bind to"
    )
    server_parser.add_argument("--reload", action="store_true", help="Enable live reload")

    # Status subcommand
    subparsers.add_parser("status", help="Print current safety configuration and status")

    # Run subcommand: executes end-to-end pipeline
    run_parser = subparsers.add_parser(
        "run", help="Execute complete end-to-end adversary emulation pipeline"
    )
    run_parser.add_argument(
        "--mode",
        default="synthetic",
        choices=["synthetic", "aws"],
        help="Environment mode: synthetic (default) or aws",
    )
    run_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Enforce non-destructive dry-run mode (default: True)",
    )
    run_parser.add_argument(
        "--account",
        default=settings.target_account_id,
        help="Target AWS account ID (must be allowlisted)",
    )
    run_parser.add_argument(
        "--detection-profile",
        default="FULL_COVERAGE",
        choices=["FULL_COVERAGE", "PARTIAL_COVERAGE", "HIGH_MISS_RATE"],
        help="Detection stub evaluation profile",
    )
    run_parser.add_argument(
        "--planner",
        default="deterministic",
        choices=["deterministic", "gemini", "openai"],
        help="Planning engine provider",
    )

    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run("backend.app.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "status":
        print("Falcon Strike-AI v0.1.0")
        print(f"Environment:       {settings.environment}")
        print(f"Dry Run (Default): {settings.dry_run}")
        print(f"Target Account:    {settings.target_account_id}")
        print(f"Allowlisted:       {settings.allowlisted_accounts}")
        print(f"Max Resources:     {settings.max_resources_touched}")
    elif args.command == "run":
        from backend.app.workflow import EndToEndWorkflow

        workflow = EndToEndWorkflow()
        result = workflow.run(
            mode=args.mode,
            dry_run=args.dry_run,
            target_account=args.account,
            detection_profile=args.detection_profile,
            planner_provider=args.planner,
        )
        print("================================================================================")
        print("FALCON STRIKE-AI: END-TO-END PIPELINE COMPLETE")
        print("================================================================================")
        print(f"Run ID:                 {result.run_id}")
        print(f"Campaign ID:            {result.campaign_id}")
        print(f"Status:                 {result.status}")
        print(f"Duration:               {result.duration_ms:.2f} ms")
        print(f"Graph Nodes Analyzed:   {result.environment_nodes_count}")
        print(f"Attack Paths Found:     {result.attack_paths_found_count}")
        print(f"Stages Executed:        {result.executed_stages_count}")
        print(f"Detection Coverage:     {result.detection_coverage_pct}%")
        print(f"MTTD:                   {result.mttd_seconds} seconds")
        print(f"Baseline Teardown:      {'VERIFIED' if result.teardown_verified else 'FAILED'}")
        print(f"Audit Chain Integrity:  {'VERIFIED_UNBROKEN' if result.audit_chain_verified else 'COMPROMISED'}")
        print("--------------------------------------------------------------------------------")
        print("Generated Artifacts:")
        for name, path in result.artifacts.items():
            print(f"  - {name}: {path}")
        print("================================================================================")
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    run_cli()
