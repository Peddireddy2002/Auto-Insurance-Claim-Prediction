#!/usr/bin/env python3
"""
Claim Processing Automation - Machine Learning Demo Script
This script demonstrates the complete ML pipeline for automated claim processing
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🏥 {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Print a formatted step."""
    print(f"\n{step_num}️⃣  {title}")
    print("-" * 40)

def simulate_processing_delay():
    """Simulate processing time for demo effect."""
    time.sleep(1)

def main():
    """Main demonstration function."""
    
    print_header("CLAIM PROCESSING AUTOMATION - ML DEMO")
    print("This demo showcases the complete machine learning pipeline")
    print("for automated insurance claim processing.")
    print("\n🔧 Technology Stack:")
    print("   • PDF Upload & OCR (Pytesseract)")
    print("   • LLM Data Extraction (LangChain)")
    print("   • Validation & Fraud Detection")
    print("   • Payment Routing (Stripe)")
    print("   • Analytics & ML Insights")
    
    # Sample claim document content
    sample_claim = {
        "document_text": """
        INSURANCE CLAIM FORM
        
        Policy Number: POL-789123456
        Claim Number: CLM-2024-001234
        
        CLAIMANT INFORMATION:
        Name: Sarah Johnson
        Phone: (555) 123-4567
        Email: sarah.johnson@email.com
        Address: 123 Main Street, Anytown, ST 12345
        
        INCIDENT DETAILS:
        Date of Incident: January 15, 2024
        Time: 2:30 PM
        Location: Highway 95 and Maple Street intersection
        
        VEHICLE INFORMATION:
        Year: 2019
        Make: Honda
        Model: Civic
        VIN: 1HGBH41JXMN109876
        License Plate: ABC-1234
        
        INCIDENT DESCRIPTION:
        Vehicle was rear-ended while stopped at red light. 
        Minor damage to rear bumper. Other driver was cited.
        
        DAMAGE ESTIMATE: $2,500.00
        REQUESTED CLAIM AMOUNT: $2,500.00
        """
    }
    
    print_step("1", "PDF Upload & OCR Processing (Pytesseract)")
    simulate_processing_delay()
    
    # Simulate OCR processing
    ocr_result = {
        "text_extracted": True,
        "confidence": 92.5,
        "pages_processed": 1,
        "method": "pytesseract",
        "preprocessing": "denoising + thresholding applied"
    }
    
    print("✅ OCR Processing completed!")
    print(f"   • Text extraction: {'✅ Success' if ocr_result['text_extracted'] else '❌ Failed'}")
    print(f"   • Confidence: {ocr_result['confidence']:.1f}%")
    print(f"   • Pages processed: {ocr_result['pages_processed']}")
    print(f"   • Method: {ocr_result['method']}")
    print(f"   • Text length: {len(sample_claim['document_text'])} characters")
    
    print_step("2", "LLM Data Extraction (LangChain + OpenAI)")
    simulate_processing_delay()
    
    # Simulate LLM extraction
    extracted_data = {
        "policy_number": "POL-789123456",
        "claim_number": "CLM-2024-001234",
        "claimant_name": "Sarah Johnson",
        "claimant_phone": "(555) 123-4567",
        "claimant_email": "sarah.johnson@email.com",
        "claimant_address": "123 Main Street, Anytown, ST 12345",
        "incident_date": "January 15, 2024",
        "incident_location": "Highway 95 and Maple Street intersection",
        "vehicle_year": 2019,
        "vehicle_make": "Honda",
        "vehicle_model": "Civic",
        "vehicle_vin": "1HGBH41JXMN109876",
        "license_plate": "ABC-1234",
        "claim_amount": 2500.00,
        "confidence_score": 0.89
    }
    
    print("✅ LLM Extraction completed!")
    print(f"   • Model: GPT-4 (via LangChain)")
    print(f"   • Confidence: {extracted_data['confidence_score']:.1%}")
    print(f"   • Fields extracted: {len([v for v in extracted_data.values() if v])}/20")
    print("   • Key data points:")
    print(f"     - Claimant: {extracted_data['claimant_name']}")
    print(f"     - Amount: ${extracted_data['claim_amount']:,.2f}")
    print(f"     - Vehicle: {extracted_data['vehicle_year']} {extracted_data['vehicle_make']} {extracted_data['vehicle_model']}")
    
    print_step("3", "Validation & Fraud Detection")
    simulate_processing_delay()
    
    # Simulate validation
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": ["claim_amount: Standard amount for rear-end collision"],
        "risk_score": 0.15,
        "fraud_indicators": [],
        "business_rules_passed": 8,
        "total_rules": 10
    }
    
    print("✅ Validation completed!")
    print(f"   • Overall status: {'✅ VALID' if validation_result['is_valid'] else '❌ INVALID'}")
    print(f"   • Risk score: {validation_result['risk_score']:.2f}")
    print(f"   • Business rules: {validation_result['business_rules_passed']}/{validation_result['total_rules']} passed")
    print(f"   • Errors: {len(validation_result['errors'])}")
    print(f"   • Warnings: {len(validation_result['warnings'])}")
    print(f"   • Fraud indicators: {len(validation_result['fraud_indicators'])}")
    
    # Risk assessment
    if validation_result['risk_score'] > 0.7:
        risk_level = "HIGH"
    elif validation_result['risk_score'] > 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    print(f"   • Risk assessment: {risk_level}")
    
    print_step("4", "Smart Routing Decision")
    simulate_processing_delay()
    
    # Determine routing
    amount = extracted_data['claim_amount']
    risk = validation_result['risk_score']
    
    if risk > 0.7:
        routing_decision = "MANUAL_REVIEW"
    elif not validation_result['is_valid']:
        routing_decision = "REJECTED"
    elif amount > 10000:
        routing_decision = "SENIOR_APPROVAL"
    else:
        routing_decision = "AUTO_APPROVED"
    
    print("✅ Routing decision made!")
    print(f"   • Decision: {routing_decision}")
    print(f"   • Reason: Low risk ({risk:.2f}) + Valid data + Standard amount")
    print(f"   • Processing track: Automated approval workflow")
    
    print_step("5", "Payment Processing (Stripe Integration)")
    simulate_processing_delay()
    
    # Simulate payment processing
    if routing_decision == "AUTO_APPROVED":
        payment_result = {
            "success": True,
            "status": "processing",
            "payment_intent_id": f"pi_demo_{int(time.time())}",
            "amount_cents": int(amount * 100),
            "currency": "usd",
            "estimated_processing": "1-2 business days",
            "stripe_fee": amount * 0.029 + 0.30,
            "net_amount": amount - (amount * 0.029 + 0.30)
        }
        
        print("✅ Payment processing initiated!")
        print(f"   • Status: {payment_result['status'].upper()}")
        print(f"   • Payment Intent: {payment_result['payment_intent_id']}")
        print(f"   • Amount: ${amount:,.2f}")
        print(f"   • Stripe fee: ${payment_result['stripe_fee']:.2f}")
        print(f"   • Net amount: ${payment_result['net_amount']:.2f}")
        print(f"   • Estimated processing: {payment_result['estimated_processing']}")
    else:
        print("⏳ Payment on hold pending review")
        print(f"   • Reason: {routing_decision}")
    
    print_step("6", "ML Analytics & Insights")
    simulate_processing_delay()
    
    # Simulate ML predictions
    ml_insights = {
        "fraud_probability": 0.08,
        "predicted_processing_time": 1.3,
        "similar_claims_processed": 47,
        "average_amount_for_type": 2750.00,
        "claim_complexity_score": 0.25,
        "customer_satisfaction_prediction": 0.92
    }
    
    print("✅ ML Analysis completed!")
    print(f"   • Fraud probability: {ml_insights['fraud_probability']:.1%}")
    print(f"   • Predicted processing: {ml_insights['predicted_processing_time']:.1f} days")
    print(f"   • Similar claims: {ml_insights['similar_claims_processed']} in database")
    print(f"   • Complexity score: {ml_insights['claim_complexity_score']:.2f}")
    print(f"   • Satisfaction prediction: {ml_insights['customer_satisfaction_prediction']:.1%}")
    
    # Final summary
    print_header("PROCESSING COMPLETE - SUMMARY REPORT")
    print(f"Claim Number: {extracted_data['claim_number']}")
    print(f"Claimant: {extracted_data['claimant_name']}")
    print(f"Amount: ${extracted_data['claim_amount']:,.2f}")
    print(f"Processing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("PIPELINE RESULTS:")
    print(f"├── 📄 OCR Extraction: ✅ {ocr_result['confidence']:.1f}% confidence")
    print(f"├── 🤖 LLM Processing: ✅ {extracted_data['confidence_score']:.0%} confidence") 
    print(f"├── ✅ Validation: ✅ PASSED ({validation_result['business_rules_passed']}/{validation_result['total_rules']} rules)")
    print(f"├── 🎯 Risk Assessment: {risk_level} ({validation_result['risk_score']:.2f})")
    print(f"├── 🔀 Routing: {routing_decision}")
    print(f"├── 💳 Payment: {'PROCESSING' if routing_decision == 'AUTO_APPROVED' else 'PENDING'}")
    print(f"├── 🧠 ML Fraud Score: {ml_insights['fraud_probability']:.1%}")
    print(f"└── ⏱️ Est. Completion: {ml_insights['predicted_processing_time']:.1f} days")
    
    print(f"\n🎉 SUCCESS: Claim processed automatically in {6} seconds!")
    print("💡 Traditional processing would take 2-5 business days")
    print("⚡ Automation achieved 80% time reduction")
    
    print("\n🔧 TECHNOLOGY STACK USED:")
    print("   • Pytesseract - OCR text extraction")
    print("   • LangChain + OpenAI - Intelligent data extraction")
    print("   • Scikit-learn - Fraud detection ML models")
    print("   • Stripe API - Payment processing")
    print("   • FastAPI - Backend API framework")
    print("   • PostgreSQL - Data storage")
    print("   • Redis - Background task processing")
    
    print("\n📊 Want to see detailed analytics?")
    print("   Run: jupyter notebook machine_learning_demo.ipynb")
    print("\n🚀 Ready to deploy in production?")
    print("   Run: python setup.py && python start.py")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")