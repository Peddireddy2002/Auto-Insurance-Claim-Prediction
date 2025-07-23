import stripe

# Set your Stripe secret key here or via environment variable
stripe.api_key = "sk_test_..."

def route_to_stripe(data: dict):
    amount = data.get("amount", 0)
    if amount > 0:
        # Dummy payment intent creation
        # In production, handle exceptions and security
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe expects cents
            currency="usd",
            payment_method_types=["card"],
        )
        return {"status": "routed", "payment_intent": intent.id}
    return {"status": "not routed", "reason": "No amount provided"}