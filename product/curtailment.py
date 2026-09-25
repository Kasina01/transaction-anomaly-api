"""
curtailment.py
Automated Decision & Curtailment Policy Engine.
Translates ML anomaly probabilities and BI investigative signals into actionable business mitigations.
Includes zero-key simulated dispatchers for Core Banking, MFA challenges, and Compliance SAR filing.
"""

from datetime import datetime
import uuid
from typing import Dict, List, Any


class CurtailmentDecisionEngine:
    """
    Evaluates risk signals from the Data Science engine (port 8000) and
    BI investigation layer (port 8001) to decide on and dispatch automated
    fraud curtailment actions.
    """

    @staticmethod
    def evaluate(
        fraud_probability: float,
        flagged: bool,
        distress_signals: List[str],
        mule_ring_signals: List[str]
    ) -> Dict[str, str]:
        """
        Determines the appropriate action based on enterprise risk tolerance.
        """
        # Rule 1: High conviction fraud + mule-ring behavioral markers
        if flagged and mule_ring_signals:
            return {
                "action": "FREEZE_ACCOUNT",
                "risk_tier": "CRITICAL",
                "reason": (
                    f"High-conviction fraud probability ({fraud_probability:.2%}) with detected "
                    f"mule-ring coordination signals: {', '.join(mule_ring_signals)}."
                )
            }

        # Rule 2: High conviction fraud + distress / coercion markers
        if flagged and distress_signals:
            return {
                "action": "BLOCK_TRANSACTION",
                "risk_tier": "HIGH_PRIORITY_VICTIM_PROTECTION",
                "reason": (
                    f"High-conviction fraud probability ({fraud_probability:.2%}) with social engineering / "
                    f"customer distress markers: {', '.join(distress_signals)}. Protective block applied."
                )
            }

        # Rule 3: High conviction fraud anomaly without specific text markers
        if flagged or fraud_probability >= 0.90:
            return {
                "action": "BLOCK_TRANSACTION",
                "risk_tier": "HIGH",
                "reason": (
                    f"Severe spatial, velocity, or network anomaly ({fraud_probability:.2%}) "
                    f"exceeding the 90.0% safety threshold."
                )
            }

        # Rule 4: Suspicious / Elevated anomaly requiring friction/verification
        if fraud_probability >= 0.70:
            return {
                "action": "STEP_UP_MFA",
                "risk_tier": "ELEVATED",
                "reason": (
                    f"Elevated anomaly score ({fraud_probability:.2%}). Transaction placed on 10-minute hold "
                    f"pending biometric or SMS one-time passcode confirmation."
                )
            }

        # Rule 5: Normal baseline
        return {
            "action": "AUTO_APPROVE",
            "risk_tier": "LOW",
            "reason": f"Transaction score ({fraud_probability:.2%}) is within standard operating parameters."
        }

    @staticmethod
    def dispatch_simulated_actions(
        action: str,
        transaction_id: str,
        customer_id: str,
        amount: float,
        reason: str
    ) -> List[Dict[str, Any]]:
        """
        Simulates dispatching real-world webhooks and notifications without requiring
        paid external API keys (Twilio, SendGrid, Visa/Mastercard gateways).
        """
        timestamp = datetime.utcnow().isoformat()
        dispatched = []

        if action == "FREEZE_ACCOUNT":
            dispatched.extend([
                {
                    "channel": "CoreBankingGateway",
                    "target": f"account:{customer_id}",
                    "operation": "ACCOUNT_FREEZE_ALL_CHANNELS",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"CB-FRZ-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"customer_id": customer_id, "freeze_debit": True, "freeze_wire": True}
                },
                {
                    "channel": "RegulatoryComplianceService",
                    "target": "SAR_FILING_QUEUE",
                    "operation": "DRAFT_SUSPICIOUS_ACTIVITY_REPORT",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"SAR-DRAFT-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"reason": reason, "recommended_priority": "URGENT"}
                },
                {
                    "channel": "CustomerNotification",
                    "target": f"customer:{customer_id}",
                    "operation": "DISPATCH_SECURITY_ALERT_SMS",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"SMS-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"message": f"Your account has been temporarily locked due to suspicious activity. Please call fraud ops."}
                }
            ])

        elif action == "BLOCK_TRANSACTION":
            dispatched.extend([
                {
                    "channel": "PaymentGateway",
                    "target": f"tx:{transaction_id}",
                    "operation": "DECLINE_AUTHORIZATION",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"PG-DEC-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"transaction_id": transaction_id, "response_code": "59_SUSPECTED_FRAUD"}
                },
                {
                    "channel": "CustomerNotification",
                    "target": f"customer:{customer_id}",
                    "operation": "DISPATCH_DECLINE_NOTIFICATION",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"NOTIF-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"message": f"Transaction of ${amount:,.2f} was declined for your protection. If this was you, reply YES."}
                }
            ])

        elif action == "STEP_UP_MFA":
            dispatched.extend([
                {
                    "channel": "AuthService",
                    "target": f"customer:{customer_id}",
                    "operation": "TRIGGER_PUSH_OTP_CHALLENGE",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"MFA-CHAL-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"timeout_seconds": 600, "channel": "MOBILE_PUSH_BIOMETRIC"}
                },
                {
                    "channel": "PaymentGateway",
                    "target": f"tx:{transaction_id}",
                    "operation": "HOLD_PENDING_VERIFICATION",
                    "status": "SIMULATED_SUCCESS",
                    "reference_id": f"PG-HOLD-{uuid.uuid4().hex[:8].upper()}",
                    "timestamp": timestamp,
                    "payload": {"transaction_id": transaction_id, "hold_minutes": 10}
                }
            ])

        elif action == "AUTO_APPROVE":
            dispatched.append({
                "channel": "PaymentGateway",
                "target": f"tx:{transaction_id}",
                "operation": "AUTHORIZE_AND_SETTLE",
                "status": "SIMULATED_SUCCESS",
                "reference_id": f"PG-AUTH-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": timestamp,
                "payload": {"transaction_id": transaction_id, "amount": amount}
            })

        return dispatched
