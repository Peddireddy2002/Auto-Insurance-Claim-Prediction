import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException
from config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class ValidationResult:
    """Class to hold validation results."""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.corrections = {}
        self.risk_score = 0.0
        self.fraud_indicators = []
    
    def add_error(self, field: str, message: str):
        """Add a validation error."""
        self.is_valid = False
        self.errors.append({"field": field, "message": message})
    
    def add_warning(self, field: str, message: str):
        """Add a validation warning."""
        self.warnings.append({"field": field, "message": message})
    
    def add_correction(self, field: str, original: Any, corrected: Any):
        """Add a suggested correction."""
        self.corrections[field] = {"original": original, "corrected": corrected}
    
    def add_fraud_indicator(self, indicator: str, severity: str, details: str):
        """Add a fraud indicator."""
        self.fraud_indicators.append({
            "indicator": indicator,
            "severity": severity,  # low, medium, high
            "details": details
        })
        
        # Increase risk score based on severity
        severity_scores = {"low": 0.1, "medium": 0.3, "high": 0.5}
        self.risk_score += severity_scores.get(severity, 0.1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "corrections": self.corrections,
            "risk_score": min(self.risk_score, 1.0),  # Cap at 1.0
            "fraud_indicators": self.fraud_indicators,
            "validation_timestamp": datetime.now().isoformat()
        }


class ClaimValidator:
    """Comprehensive claim validation service."""
    
    def __init__(self):
        """Initialize the validator with configuration."""
        self.max_claim_amount = settings.max_claim_amount
        self.auto_approve_threshold = settings.auto_approve_threshold
        self.manual_review_threshold = settings.manual_review_threshold
    
    def validate_claim(self, claim_data: Dict[str, Any]) -> ValidationResult:
        """
        Perform comprehensive validation of claim data.
        
        Args:
            claim_data: Extracted claim data to validate
            
        Returns:
            ValidationResult object with all validation results
        """
        result = ValidationResult()
        
        try:
            # Basic field validation
            self._validate_required_fields(claim_data, result)
            self._validate_personal_information(claim_data, result)
            self._validate_policy_information(claim_data, result)
            self._validate_incident_information(claim_data, result)
            self._validate_vehicle_information(claim_data, result)
            self._validate_financial_information(claim_data, result)
            
            # Business rule validation
            self._validate_business_rules(claim_data, result)
            
            # Fraud detection
            self._detect_fraud_indicators(claim_data, result)
            
            # Risk assessment
            self._assess_risk(claim_data, result)
            
            logger.info(f"Claim validation completed. Valid: {result.is_valid}, Risk Score: {result.risk_score}")
            
        except Exception as e:
            logger.error(f"Validation process failed: {str(e)}")
            result.add_error("validation_process", f"Validation failed: {str(e)}")
        
        return result
    
    def _validate_required_fields(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate that required fields are present and not empty."""
        required_fields = [
            "claimant_name",
            "incident_date",
            "claim_amount",
            "incident_description"
        ]
        
        for field in required_fields:
            value = claim_data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                result.add_error(field, f"Required field '{field}' is missing or empty")
    
    def _validate_personal_information(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate personal information fields."""
        
        # Validate name
        claimant_name = claim_data.get("claimant_name")
        if claimant_name:
            if len(claimant_name) < 2:
                result.add_error("claimant_name", "Name is too short")
            elif len(claimant_name) > 100:
                result.add_error("claimant_name", "Name is too long")
            elif not re.match(r"^[a-zA-Z\s\-\.\']+$", claimant_name):
                result.add_warning("claimant_name", "Name contains unusual characters")
        
        # Validate email
        claimant_email = claim_data.get("claimant_email")
        if claimant_email:
            try:
                validated_email = validate_email(claimant_email)
                if validated_email.email != claimant_email:
                    result.add_correction("claimant_email", claimant_email, validated_email.email)
            except EmailNotValidError as e:
                result.add_error("claimant_email", f"Invalid email address: {str(e)}")
        
        # Validate phone number
        claimant_phone = claim_data.get("claimant_phone")
        if claimant_phone:
            try:
                parsed_number = phonenumbers.parse(claimant_phone, "US")
                if not phonenumbers.is_valid_number(parsed_number):
                    result.add_error("claimant_phone", "Invalid phone number")
                else:
                    formatted_number = phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
                    )
                    if formatted_number != claimant_phone:
                        result.add_correction("claimant_phone", claimant_phone, formatted_number)
            except NumberParseException:
                result.add_error("claimant_phone", "Unable to parse phone number")
    
    def _validate_policy_information(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate insurance policy information."""
        
        policy_number = claim_data.get("policy_number")
        if policy_number:
            # Basic policy number format validation
            if len(policy_number) < 5:
                result.add_error("policy_number", "Policy number is too short")
            elif len(policy_number) > 50:
                result.add_error("policy_number", "Policy number is too long")
            elif not re.match(r"^[A-Z0-9\-]+$", policy_number.upper()):
                result.add_warning("policy_number", "Policy number format is unusual")
        
        # Validate insurance company
        insurance_company = claim_data.get("insurance_company")
        if insurance_company:
            known_insurers = [
                "State Farm", "GEICO", "Progressive", "Allstate", "USAA",
                "Liberty Mutual", "Farmers", "Nationwide", "American Family",
                "Travelers", "Auto-Owners", "AAA", "Esurance", "The General"
            ]
            
            if not any(insurer.lower() in insurance_company.lower() for insurer in known_insurers):
                result.add_warning("insurance_company", "Insurance company not in common list")
    
    def _validate_incident_information(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate incident-related information."""
        
        # Validate incident date
        incident_date = claim_data.get("incident_date")
        if incident_date:
            try:
                if isinstance(incident_date, str):
                    # Try different date formats
                    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
                    parsed_date = None
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(incident_date, fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_date:
                        result.add_error("incident_date", "Unable to parse incident date")
                    else:
                        # Check if date is reasonable
                        today = date.today()
                        if parsed_date > today:
                            result.add_error("incident_date", "Incident date cannot be in the future")
                        elif parsed_date < today - timedelta(days=365 * 5):  # 5 years ago
                            result.add_warning("incident_date", "Incident date is more than 5 years ago")
                        
                        # Suggest standard format if different
                        standard_format = parsed_date.strftime("%Y-%m-%d")
                        if incident_date != standard_format:
                            result.add_correction("incident_date", incident_date, standard_format)
                
            except Exception as e:
                result.add_error("incident_date", f"Invalid incident date: {str(e)}")
        
        # Validate incident description
        incident_description = claim_data.get("incident_description")
        if incident_description:
            if len(incident_description) < 10:
                result.add_warning("incident_description", "Incident description is very brief")
            elif len(incident_description) > 2000:
                result.add_warning("incident_description", "Incident description is unusually long")
    
    def _validate_vehicle_information(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate vehicle-related information."""
        
        # Validate vehicle year
        vehicle_year = claim_data.get("vehicle_year")
        if vehicle_year:
            try:
                year = int(vehicle_year)
                current_year = datetime.now().year
                
                if year < 1900:
                    result.add_error("vehicle_year", "Vehicle year is too old")
                elif year > current_year + 1:
                    result.add_error("vehicle_year", "Vehicle year cannot be in the future")
                elif year < current_year - 50:
                    result.add_warning("vehicle_year", "Vehicle is very old (classic car?)")
                    
            except (ValueError, TypeError):
                result.add_error("vehicle_year", "Invalid vehicle year format")
        
        # Validate VIN
        vehicle_vin = claim_data.get("vehicle_vin")
        if vehicle_vin:
            # Basic VIN validation (17 characters, no I, O, Q)
            if len(vehicle_vin) != 17:
                result.add_error("vehicle_vin", "VIN must be exactly 17 characters")
            elif not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vehicle_vin.upper()):
                result.add_error("vehicle_vin", "VIN contains invalid characters")
            else:
                # VIN checksum validation (simplified)
                if not self._validate_vin_checksum(vehicle_vin):
                    result.add_warning("vehicle_vin", "VIN checksum validation failed")
        
        # Validate license plate
        license_plate = claim_data.get("license_plate")
        if license_plate:
            if len(license_plate) < 2 or len(license_plate) > 10:
                result.add_warning("license_plate", "License plate length is unusual")
    
    def _validate_financial_information(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate financial amounts and claims."""
        
        # Validate claim amount
        claim_amount = claim_data.get("claim_amount")
        if claim_amount is not None:
            try:
                amount = float(claim_amount)
                
                if amount <= 0:
                    result.add_error("claim_amount", "Claim amount must be positive")
                elif amount > self.max_claim_amount:
                    result.add_error("claim_amount", f"Claim amount exceeds maximum allowed ({self.max_claim_amount})")
                elif amount > self.manual_review_threshold:
                    result.add_warning("claim_amount", "High value claim requires manual review")
                    
            except (ValueError, TypeError):
                result.add_error("claim_amount", "Invalid claim amount format")
        
        # Validate estimated damage amount
        estimated_damage = claim_data.get("estimated_damage_amount")
        claim_amount_val = claim_data.get("claim_amount")
        
        if estimated_damage is not None and claim_amount_val is not None:
            try:
                est_val = float(estimated_damage)
                claim_val = float(claim_amount_val)
                
                if est_val <= 0:
                    result.add_error("estimated_damage_amount", "Estimated damage must be positive")
                elif abs(est_val - claim_val) / max(est_val, claim_val) > 0.5:  # 50% difference
                    result.add_warning(
                        "amount_consistency", 
                        "Large discrepancy between estimated damage and claim amount"
                    )
                    
            except (ValueError, TypeError):
                result.add_error("estimated_damage_amount", "Invalid estimated damage amount format")
    
    def _validate_business_rules(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Validate business-specific rules."""
        
        # Rule 1: Claims filed too quickly after policy start
        # (This would require policy start date, which we don't have in this example)
        
        # Rule 2: Multiple claims from same claimant
        # (This would require database lookup)
        
        # Rule 3: Incident on weekend/holiday might need additional verification
        incident_date = claim_data.get("incident_date")
        if incident_date:
            try:
                if isinstance(incident_date, str):
                    parsed_date = datetime.strptime(incident_date, "%Y-%m-%d").date()
                    if parsed_date.weekday() >= 5:  # Saturday or Sunday
                        result.add_warning("incident_timing", "Incident occurred on weekend")
            except:
                pass  # Date validation already handled elsewhere
        
        # Rule 4: High-risk locations
        incident_location = claim_data.get("incident_location")
        if incident_location:
            high_risk_keywords = ["parking lot", "mall", "downtown", "highway", "construction"]
            location_lower = incident_location.lower()
            
            for keyword in high_risk_keywords:
                if keyword in location_lower:
                    result.add_warning("location_risk", f"Incident in potentially high-risk location: {keyword}")
                    break
    
    def _detect_fraud_indicators(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Detect potential fraud indicators."""
        
        # Indicator 1: Unusually high claim amounts
        claim_amount = claim_data.get("claim_amount")
        if claim_amount:
            try:
                amount = float(claim_amount)
                if amount > 50000:  # High value threshold
                    result.add_fraud_indicator(
                        "high_value_claim",
                        "medium",
                        f"Claim amount of ${amount:,.2f} is unusually high"
                    )
            except:
                pass
        
        # Indicator 2: Inconsistent information
        claimant_name = claim_data.get("claimant_name", "")
        policy_holder = claim_data.get("policy_holder_name", "")
        
        if claimant_name and policy_holder and claimant_name.lower() != policy_holder.lower():
            result.add_fraud_indicator(
                "name_mismatch",
                "low",
                "Claimant name differs from policy holder name"
            )
        
        # Indicator 3: Vague incident description
        incident_description = claim_data.get("incident_description", "")
        if incident_description:
            vague_keywords = ["suddenly", "out of nowhere", "don't remember", "not sure"]
            description_lower = incident_description.lower()
            
            for keyword in vague_keywords:
                if keyword in description_lower:
                    result.add_fraud_indicator(
                        "vague_description",
                        "low",
                        f"Incident description contains vague language: '{keyword}'"
                    )
                    break
        
        # Indicator 4: Round numbers (psychological indicator)
        if claim_amount:
            try:
                amount = float(claim_amount)
                if amount % 1000 == 0 and amount >= 5000:  # Round thousands
                    result.add_fraud_indicator(
                        "round_number",
                        "low",
                        f"Claim amount is a round number: ${amount:,.0f}"
                    )
            except:
                pass
        
        # Indicator 5: Missing critical information
        critical_fields = ["policy_number", "incident_location", "vehicle_vin"]
        missing_critical = [field for field in critical_fields if not claim_data.get(field)]
        
        if len(missing_critical) >= 2:
            result.add_fraud_indicator(
                "missing_information",
                "medium",
                f"Multiple critical fields missing: {', '.join(missing_critical)}"
            )
    
    def _assess_risk(self, claim_data: Dict[str, Any], result: ValidationResult):
        """Perform overall risk assessment."""
        
        # Factor in various risk elements
        risk_factors = []
        
        # High claim amount
        claim_amount = claim_data.get("claim_amount")
        if claim_amount:
            try:
                amount = float(claim_amount)
                if amount > self.manual_review_threshold:
                    risk_factors.append("high_value")
                    result.risk_score += 0.3
            except:
                pass
        
        # Missing information
        total_fields = len(claim_data)
        filled_fields = sum(1 for v in claim_data.values() if v is not None and str(v).strip())
        completeness = filled_fields / total_fields if total_fields > 0 else 0
        
        if completeness < 0.5:
            risk_factors.append("incomplete_information")
            result.risk_score += 0.2
        
        # New vehicle (higher theft risk)
        vehicle_year = claim_data.get("vehicle_year")
        if vehicle_year:
            try:
                year = int(vehicle_year)
                current_year = datetime.now().year
                if year >= current_year - 2:  # Very new vehicle
                    risk_factors.append("new_vehicle")
                    result.risk_score += 0.1
            except:
                pass
        
        # Weekend incident (statistically higher fraud)
        incident_date = claim_data.get("incident_date")
        if incident_date:
            try:
                if isinstance(incident_date, str):
                    parsed_date = datetime.strptime(incident_date, "%Y-%m-%d").date()
                    if parsed_date.weekday() >= 5:
                        risk_factors.append("weekend_incident")
                        result.risk_score += 0.05
            except:
                pass
        
        # Cap risk score at 1.0
        result.risk_score = min(result.risk_score, 1.0)
        
        # Add risk assessment to metadata
        result.corrections["risk_assessment"] = {
            "original": None,
            "corrected": {
                "risk_factors": risk_factors,
                "overall_risk": "high" if result.risk_score > 0.7 else "medium" if result.risk_score > 0.3 else "low",
                "recommended_action": self._get_recommended_action(result.risk_score)
            }
        }
    
    def _get_recommended_action(self, risk_score: float) -> str:
        """Get recommended action based on risk score."""
        if risk_score > 0.8:
            return "Reject or require extensive documentation"
        elif risk_score > 0.6:
            return "Require manual review and additional verification"
        elif risk_score > 0.3:
            return "Standard processing with monitoring"
        else:
            return "Standard processing"
    
    def _validate_vin_checksum(self, vin: str) -> bool:
        """Validate VIN checksum (simplified version)."""
        try:
            # This is a simplified VIN validation
            # In a real system, you'd implement the full VIN checksum algorithm
            
            # Basic character validation
            if len(vin) != 17:
                return False
            
            # Check for invalid characters
            invalid_chars = set('IOQ')
            if any(char.upper() in invalid_chars for char in vin):
                return False
            
            return True
            
        except Exception:
            return False


# Global validator instance
claim_validator = ClaimValidator()