"""
Indian E-Commerce Customer Retention Intelligence System
Retention Recommendation Engine (Phase 7.3)

Transparent, rule-based recommendation generator using verified customer signals,
churn probabilities, and RFM persona assignments.

Strict Rules:
- No invented customer behavior or fabricated claims.
- No ungrounded revenue savings promises.
- Recommendations are grounded strictly in empirical signals.
- Every rule provides Category, Suggested Action, Reason, Evidence, and Priority.
"""

from typing import List, Optional
from backend.app.schemas.ml import (
    ChurnPredictionResponse,
    RawCustomerFeatures,
    RetentionRecommendationItem,
    RetentionRecommendationsResponse,
    SegmentationResponse,
)


class RetentionRecommendationEngine:
    """
    Evaluates business rules against customer attributes and predictions to produce
    prioritized, explainable retention interventions.
    """

    @classmethod
    def generate_recommendations(
        cls,
        features: RawCustomerFeatures,
        churn_pred: Optional[ChurnPredictionResponse] = None,
        segment: Optional[SegmentationResponse] = None,
    ) -> RetentionRecommendationsResponse:
        """Generates prioritized, rule-based retention actions."""
        recs: List[RetentionRecommendationItem] = []

        # Extract core signals
        churn_prob = churn_pred.churn_probability if churn_pred else 0.50
        is_churn_risk = churn_prob >= 0.50
        cluster_id = segment.cluster_id if segment else features.cluster_id

        # ----------------------------------------------------------------------
        # Rule 1: High-Value Loyalist Retention (Cluster 0)
        # ----------------------------------------------------------------------
        if cluster_id == 0 or features.hist_delivered_order_value_inr >= 15000.0:
            spend = features.hist_delivered_order_value_inr
            priority = "HIGH" if churn_prob >= 0.35 else "MEDIUM"
            recs.append(RetentionRecommendationItem(
                category="Loyalty Rewards",
                suggested_action="Enroll customer in Premium VIP tier with dedicated support and zero-fee express shipping.",
                reason="High-value champion customer requires proactive relationship management to preserve lifetime value.",
                evidence=f"Delivered spend: ₹{spend:,.2f}, Persona: Champions (Cluster {cluster_id}), Churn Prob: {churn_prob:.1%}.",
                priority=priority,
            ))

        # ----------------------------------------------------------------------
        # Rule 2: Zero Delivered-Purchase Activation (Cluster 2)
        # ----------------------------------------------------------------------
        if cluster_id == 2 or features.hist_delivered_order_count == 0:
            order_cnt = features.hist_order_count
            cancel_cnt = features.hist_cancelled_order_count
            recs.append(RetentionRecommendationItem(
                category="First-Purchase Onboarding",
                suggested_action="Provide dedicated first-order concierge assistance, COD assurance, and clear delivery timeline guarantees.",
                reason="Account has zero fulfilled deliveries; building initial platform trust is the primary retention prerequisite.",
                evidence=f"Delivered orders: 0, Total attempts: {order_cnt}, Cancelled: {cancel_cnt}.",
                priority="HIGH",
            ))

        # ----------------------------------------------------------------------
        # Rule 3: Lapsed Customer Win-Back (Cluster 1 or High Recency Drift)
        # ----------------------------------------------------------------------
        recency = features.recency_days or 0.0
        if cluster_id == 1 or recency >= 90.0 or (features.velocity_ratio_30_90 is not None and features.velocity_ratio_30_90 == 0.0):
            priority = "HIGH" if is_churn_risk else "MEDIUM"
            recs.append(RetentionRecommendationItem(
                category="Re-engagement",
                suggested_action="Dispatch personalized re-engagement campaign featuring curated new arrivals in previously viewed categories.",
                reason="Customer shows substantial recency decay and declining purchasing momentum over the past 90 days.",
                evidence=f"Recency: {recency:.1f} days, Momentum ratio (30/90): {features.velocity_ratio_30_90 or 0.0:.2f}, Cluster {cluster_id}.",
                priority=priority,
            ))

        # ----------------------------------------------------------------------
        # Rule 4: Delivery Delay Friction Resolution
        # ----------------------------------------------------------------------
        avg_delay = features.hist_average_delivery_delay_days or 0.0
        delay_score = features.delay_friction_score or 0.0
        if avg_delay >= 3.0 or delay_score >= 1.0:
            recs.append(RetentionRecommendationItem(
                category="Delivery Experience",
                suggested_action="Prioritize customer logistics routing to top-tier courier partner and issue SLA breach courtesy credit.",
                reason="Customer has experienced repeated delivery delays beyond promised SLA windows, elevating churn risk.",
                evidence=f"Average delivery delay: {avg_delay:.1f} days, Delay friction score: {delay_score:.2f}.",
                priority="HIGH",
            ))

        # ----------------------------------------------------------------------
        # Rule 5: Reverse Logistics & Product Quality Friction
        # ----------------------------------------------------------------------
        return_rate = features.hist_return_rate or 0.0
        if return_rate >= 0.20:
            ret_cnt = features.hist_returned_order_count
            recs.append(RetentionRecommendationItem(
                category="Return & Quality Resolution",
                suggested_action="Implement pre-dispatch item inspection and provide sizing/fit guide support before shipping.",
                reason="Elevated return rate indicates dissatisfaction with delivered item specifications or packaging.",
                evidence=f"Return rate: {return_rate:.1%}, Returned order count: {ret_cnt}.",
                priority="MEDIUM",
            ))

        # ----------------------------------------------------------------------
        # Rule 6: Pre-Fulfillment Cancellation Friction
        # ----------------------------------------------------------------------
        cancel_rate = features.hist_cancellation_rate or 0.0
        if cancel_rate >= 0.20:
            canc_cnt = features.hist_cancelled_order_count
            recs.append(RetentionRecommendationItem(
                category="Fulfillment Reliability",
                suggested_action="Conduct seller lead-time audit and introduce automated order confirmation via WhatsApp/SMS.",
                reason="High cancellation frequency signals hesitation or excessive processing delays before dispatch.",
                evidence=f"Cancellation rate: {cancel_rate:.1%}, Cancelled orders: {canc_cnt}.",
                priority="MEDIUM",
            ))

        # ----------------------------------------------------------------------
        # Rule 7: Discount Sensitivity (Cluster 4 or High Discount Usage)
        # ----------------------------------------------------------------------
        if cluster_id == 4 or (features.hist_discounted_order_count >= 3 and features.hist_average_discount_amount_inr >= 200.0):
            recs.append(RetentionRecommendationItem(
                category="Personalized Value Bundles",
                suggested_action="Offer value bundles, flash seasonal discounts, and cashback incentives on category essentials.",
                reason="Customer is highly responsive to promotional pricing and demonstrates price-conscious purchasing patterns.",
                evidence=f"Persona: Recent Low-Ticket (Cluster {cluster_id}), Discounted orders: {features.hist_discounted_order_count}.",
                priority="MEDIUM",
            ))

        # ----------------------------------------------------------------------
        # Rule 8: Steady Core Repeater Engagement (Cluster 3)
        # ----------------------------------------------------------------------
        if cluster_id == 3 and not is_churn_risk:
            recs.append(RetentionRecommendationItem(
                category="Loyalty Rewards",
                suggested_action="Enable recurring replenishment reminders and grant milestone loyalty points on upcoming orders.",
                reason="Consistent repeat customer with steady purchasing habits benefits from seamless replenishment perks.",
                evidence=f"Delivered orders: {features.hist_delivered_order_count}, Cluster 3 Steady Core Repeater.",
                priority="LOW",
            ))

        # Fallback if no specific condition triggered
        if not recs:
            recs.append(RetentionRecommendationItem(
                category="Customer Care",
                suggested_action="Send standard customer satisfaction check-in and share platform newsletter updates.",
                reason="Customer metrics are balanced within normative ranges with no acute operational friction.",
                evidence=f"Tenure: {features.customer_tenure_days:.0f} days, Churn probability: {churn_prob:.1%}.",
                priority="LOW",
            ))

        # Determine overall top priority
        priorities = [r.priority for r in recs]
        top_priority = "HIGH" if "HIGH" in priorities else ("MEDIUM" if "MEDIUM" in priorities else "LOW")

        return RetentionRecommendationsResponse(
            recommendations=recs,
            total_recommendations=len(recs),
            top_priority=top_priority,
        )
