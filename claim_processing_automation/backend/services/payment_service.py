import logging
from typing import Dict, Any, Optional, List
import stripe
from datetime import datetime, timedelta
from config.settings import settings
from backend.models.database import Payment, PaymentStatus, Claim
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class PaymentProcessor:
    """Comprehensive Stripe payment processing service."""
    
    def __init__(self):
        """Initialize the payment processor."""
        self.stripe_secret_key = settings.stripe_secret_key
        self.stripe_publishable_key = settings.stripe_publishable_key
        self.webhook_secret = settings.stripe_webhook_secret
        
        # Set Stripe API key
        stripe.api_key = self.stripe_secret_key
    
    async def create_payment_intent(
        self, 
        claim_id: int, 
        amount: float, 
        currency: str = "usd",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Payment Intent for claim payment.
        
        Args:
            claim_id: ID of the claim being paid
            amount: Payment amount in the smallest currency unit (cents for USD)
            currency: Currency code (default: "usd")
            metadata: Additional metadata to attach to the payment
            
        Returns:
            Dictionary containing payment intent details
        """
        try:
            # Convert amount to cents (Stripe expects smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Prepare metadata
            payment_metadata = {
                "claim_id": str(claim_id),
                "source": "claim_processing_automation",
                "created_at": datetime.now().isoformat()
            }
            
            if metadata:
                payment_metadata.update(metadata)
            
            # Create Payment Intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=payment_metadata,
                automatic_payment_methods={
                    'enabled': True,
                },
                capture_method='automatic',  # Auto-capture when authorized
                confirmation_method='automatic'
            )
            
            logger.info(f"Created Payment Intent {payment_intent.id} for claim {claim_id}")
            
            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount,
                "amount_cents": amount_cents,
                "currency": currency,
                "status": payment_intent.status,
                "metadata": payment_metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "stripe_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment intent.
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            
        Returns:
            Dictionary containing confirmation results
        """
        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            logger.info(f"Payment Intent {payment_intent_id} confirmed with status: {payment_intent.status}")
            
            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "status": payment_intent.status,
                "amount_received": payment_intent.amount_received,
                "charges": [
                    {
                        "id": charge.id,
                        "amount": charge.amount,
                        "status": charge.status,
                        "receipt_url": charge.receipt_url
                    }
                    for charge in payment_intent.charges.data
                ]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "stripe_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error confirming payment: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    async def process_claim_payment(
        self, 
        db: Session,
        claim_id: int, 
        amount: float,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a payment for an approved claim.
        
        Args:
            db: Database session
            claim_id: ID of the claim to pay
            amount: Payment amount
            payment_method_id: Optional payment method ID
            
        Returns:
            Dictionary containing payment processing results
        """
        try:
            # Create payment intent
            payment_result = await self.create_payment_intent(
                claim_id=claim_id,
                amount=amount,
                metadata={
                    "payment_type": "claim_payout",
                    "auto_processed": "true"
                }
            )
            
            if not payment_result["success"]:
                return payment_result
            
            # Save payment record to database
            payment = Payment(
                claim_id=claim_id,
                stripe_payment_intent_id=payment_result["payment_intent_id"],
                amount=amount,
                currency="USD",
                status=PaymentStatus.PROCESSING,
                payment_method="stripe_transfer"
            )
            
            db.add(payment)
            db.commit()
            
            logger.info(f"Payment record created for claim {claim_id}")
            
            return {
                "success": True,
                "payment_id": payment.id,
                "payment_intent_id": payment_result["payment_intent_id"],
                "client_secret": payment_result["client_secret"],
                "amount": amount,
                "status": "processing"
            }
            
        except Exception as e:
            logger.error(f"Error processing claim payment: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "error_type": "processing_error"
            }
    
    async def create_refund(
        self, 
        payment_intent_id: str, 
        amount: Optional[float] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment.
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            amount: Refund amount (if None, full refund)
            reason: Reason for refund
            
        Returns:
            Dictionary containing refund results
        """
        try:
            # Get the payment intent to find the charge
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not payment_intent.charges.data:
                return {
                    "success": False,
                    "error": "No charges found for this payment intent",
                    "error_type": "no_charges"
                }
            
            # Get the latest charge
            charge = payment_intent.charges.data[0]
            
            # Create refund
            refund_params = {
                "charge": charge.id,
                "reason": reason
            }
            
            if amount:
                refund_params["amount"] = int(amount * 100)  # Convert to cents
            
            refund = stripe.Refund.create(**refund_params)
            
            logger.info(f"Refund {refund.id} created for payment {payment_intent_id}")
            
            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount / 100,  # Convert back to dollars
                "status": refund.status,
                "reason": refund.reason
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "stripe_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating refund: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    async def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Webhook payload
            sig_header: Stripe signature header
            
        Returns:
            Dictionary containing webhook processing results
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            logger.info(f"Received Stripe webhook: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                return await self._handle_payment_success(event['data']['object'])
            
            elif event['type'] == 'payment_intent.payment_failed':
                return await self._handle_payment_failure(event['data']['object'])
            
            elif event['type'] == 'payment_intent.canceled':
                return await self._handle_payment_cancellation(event['data']['object'])
            
            elif event['type'] == 'charge.dispute.created':
                return await self._handle_dispute_created(event['data']['object'])
            
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {"success": True, "message": "Event acknowledged but not processed"}
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            return {
                "success": False,
                "error": "Invalid payload",
                "error_type": "invalid_payload"
            }
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return {
                "success": False,
                "error": "Invalid signature",
                "error_type": "invalid_signature"
            }
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "processing_error"
            }
    
    async def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        try:
            payment_intent_id = payment_intent['id']
            claim_id = payment_intent['metadata'].get('claim_id')
            
            if not claim_id:
                logger.warning(f"No claim_id in payment intent metadata: {payment_intent_id}")
                return {"success": True, "message": "No claim_id found"}
            
            # Here you would update the database payment status
            # This requires a database session which would be injected
            logger.info(f"Payment succeeded for claim {claim_id}, payment intent {payment_intent_id}")
            
            return {
                "success": True,
                "message": "Payment success processed",
                "claim_id": claim_id,
                "payment_intent_id": payment_intent_id
            }
            
        except Exception as e:
            logger.error(f"Error handling payment success: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _handle_payment_failure(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        try:
            payment_intent_id = payment_intent['id']
            claim_id = payment_intent['metadata'].get('claim_id')
            failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            
            logger.warning(f"Payment failed for claim {claim_id}: {failure_reason}")
            
            return {
                "success": True,
                "message": "Payment failure processed",
                "claim_id": claim_id,
                "payment_intent_id": payment_intent_id,
                "failure_reason": failure_reason
            }
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _handle_payment_cancellation(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cancelled payment webhook."""
        try:
            payment_intent_id = payment_intent['id']
            claim_id = payment_intent['metadata'].get('claim_id')
            
            logger.info(f"Payment cancelled for claim {claim_id}")
            
            return {
                "success": True,
                "message": "Payment cancellation processed",
                "claim_id": claim_id,
                "payment_intent_id": payment_intent_id
            }
            
        except Exception as e:
            logger.error(f"Error handling payment cancellation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _handle_dispute_created(self, dispute: Dict[str, Any]) -> Dict[str, Any]:
        """Handle dispute creation webhook."""
        try:
            dispute_id = dispute['id']
            charge_id = dispute['charge']
            amount = dispute['amount'] / 100  # Convert from cents
            reason = dispute['reason']
            
            logger.warning(f"Dispute created: {dispute_id} for charge {charge_id}, amount: ${amount}, reason: {reason}")
            
            return {
                "success": True,
                "message": "Dispute creation processed",
                "dispute_id": dispute_id,
                "charge_id": charge_id,
                "amount": amount,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error handling dispute creation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get the status of a payment intent.
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            
        Returns:
            Dictionary containing payment status information
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,  # Convert from cents
                "currency": payment_intent.currency,
                "created": payment_intent.created,
                "metadata": payment_intent.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "stripe_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error retrieving payment status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    async def list_payments(
        self, 
        limit: int = 10, 
        starting_after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List recent payment intents.
        
        Args:
            limit: Maximum number of payments to return
            starting_after: Pagination cursor
            
        Returns:
            Dictionary containing list of payments
        """
        try:
            params = {"limit": limit}
            if starting_after:
                params["starting_after"] = starting_after
            
            payment_intents = stripe.PaymentIntent.list(**params)
            
            return {
                "success": True,
                "payments": [
                    {
                        "id": pi.id,
                        "status": pi.status,
                        "amount": pi.amount / 100,
                        "currency": pi.currency,
                        "created": pi.created,
                        "metadata": pi.metadata
                    }
                    for pi in payment_intents.data
                ],
                "has_more": payment_intents.has_more
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error listing payments: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "stripe_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error listing payments: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    def calculate_processing_fee(self, amount: float) -> Dict[str, float]:
        """
        Calculate Stripe processing fees.
        
        Args:
            amount: Payment amount
            
        Returns:
            Dictionary containing fee calculations
        """
        # Stripe fees: 2.9% + $0.30 per transaction (US cards)
        percentage_fee = amount * 0.029
        fixed_fee = 0.30
        total_fee = percentage_fee + fixed_fee
        net_amount = amount - total_fee
        
        return {
            "gross_amount": amount,
            "percentage_fee": percentage_fee,
            "fixed_fee": fixed_fee,
            "total_fee": total_fee,
            "net_amount": net_amount,
            "fee_percentage": (total_fee / amount) * 100 if amount > 0 else 0
        }


# Global payment processor instance
payment_processor = PaymentProcessor()