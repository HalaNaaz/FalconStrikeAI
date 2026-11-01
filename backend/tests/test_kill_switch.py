"""Unit tests for emergency kill switch latency and halt coordination (FR-3.6, NFR-S3)."""

import pytest

from backend.app.core.exceptions import FalconSecurityException
from backend.app.orchestrator.execution_engine import ExecutionEngine
from backend.app.orchestrator.kill_switch import EmergencyKillSwitch
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.policies.rules import is_global_kill_switch_active
from backend.app.techniques.models import AttackTactic


@pytest.fixture
def test_kill_switch() -> EmergencyKillSwitch:
    """Provide a fresh isolated EmergencyKillSwitch instance."""
    ks = EmergencyKillSwitch()
    yield ks
    # Cleanup: make sure global flag is reset
    try:
        ks.reset("ADMIN_EMERGENCY_RESET_KEY_SECURE_2026")
    except Exception:
        pass


class TestEmergencyKillSwitch:
    """Test suite for EmergencyKillSwitch."""

    def test_initial_state_inactive(self, test_kill_switch: EmergencyKillSwitch) -> None:
        """Verify kill switch initializes in an inactive state."""
        assert test_kill_switch.is_active() is False
        status = test_kill_switch.get_status()
        assert status["active"] is False
        assert status["total_triggers"] == 0

    def test_trigger_latency_under_two_seconds(
        self, test_kill_switch: EmergencyKillSwitch
    ) -> None:
        """Verify trigger engages immediately and records latency well below 2000ms (NFR-S3)."""
        record = test_kill_switch.trigger(
            reason="Simulated operator emergency override",
            operator_id="sec-admin-01",
            run_id="RUN-EMERGENCY-01",
        )

        assert test_kill_switch.is_active() is True
        assert record.reason == "Simulated operator emergency override"
        assert record.operator_id == "sec-admin-01"
        assert record.run_id == "RUN-EMERGENCY-01"
        # Must be well under 2.0s (2000ms), typically < 1ms
        assert record.response_time_ms < 2000.0
        # Also verify global policy flag is synchronized
        assert is_global_kill_switch_active() is True

    def test_abort_callbacks_fired_on_trigger(
        self, test_kill_switch: EmergencyKillSwitch
    ) -> None:
        """Verify registered abort callbacks are executed immediately upon trigger."""
        callback_called = False
        captured_reason = ""

        def abort_handler(reason: str, run_id: str | None) -> None:
            nonlocal callback_called, captured_reason
            callback_called = True
            captured_reason = reason

        test_kill_switch.register_abort_callback(abort_handler)
        test_kill_switch.trigger(reason="Test Abort Callback")

        assert callback_called is True
        assert captured_reason == "Test Abort Callback"

    def test_reset_requires_authorized_token(
        self, test_kill_switch: EmergencyKillSwitch
    ) -> None:
        """Verify reset requires valid administrative token."""
        test_kill_switch.trigger("Test Trigger")
        assert test_kill_switch.is_active() is True

        # Unauthorized token fails
        with pytest.raises(FalconSecurityException, match="Invalid administrative authorization token"):
            test_kill_switch.reset("INVALID_UNAUTHORIZED_TOKEN")

        assert test_kill_switch.is_active() is True

        # Authorized token succeeds
        res = test_kill_switch.reset("ADMIN_EMERGENCY_RESET_KEY_SECURE_2026")
        assert res is True
        assert test_kill_switch.is_active() is False
        assert is_global_kill_switch_active() is False

    def test_execution_engine_blocks_when_kill_switch_active(
        self, test_kill_switch: EmergencyKillSwitch
    ) -> None:
        """Verify execution engine immediately rejects campaign when kill switch is active."""
        test_kill_switch.trigger("Halt all emulation")
        engine = ExecutionEngine(ks=test_kill_switch)

        plan = CampaignPlan(
            campaign_id="CAMP-HALT",
            run_id="RUN-HALT",
            source_attack_path_id="PATH-01",
            objective="Halt test",
            stages=[
                CampaignStage(
                    stage_id="S1",
                    stage_name="Stage",
                    tactic=AttackTactic.DISCOVERY,
                    technique_id="T1526",
                    technique_name="Discovery",
                    target_resource_id="target",
                    expected_observation="None",
                )
            ],
            selected_techniques=["T1526"],
            risk_summary="None",
            planning_rationale="None",
            approved_by_policy=True,
        )

        with pytest.raises(FalconSecurityException, match="Emergency Kill Switch is ACTIVE"):
            engine.execute_campaign(plan)
