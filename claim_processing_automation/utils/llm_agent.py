import json
import logging
from typing import Dict, Any, List, Optional, Union
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
import re
from config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class ClaimExtraction(BaseModel):
    """Structured claim data model for LLM extraction."""
    
    # Personal Information
    claimant_name: Optional[str] = Field(description="Full name of the person filing the claim")
    claimant_phone: Optional[str] = Field(description="Phone number of the claimant")
    claimant_email: Optional[str] = Field(description="Email address of the claimant")
    claimant_address: Optional[str] = Field(description="Address of the claimant")
    
    # Policy Information
    policy_number: Optional[str] = Field(description="Insurance policy number")
    policy_holder_name: Optional[str] = Field(description="Name of the policy holder")
    insurance_company: Optional[str] = Field(description="Name of the insurance company")
    
    # Vehicle Information
    vehicle_make: Optional[str] = Field(description="Make of the vehicle")
    vehicle_model: Optional[str] = Field(description="Model of the vehicle")
    vehicle_year: Optional[int] = Field(description="Year of the vehicle")
    vehicle_vin: Optional[str] = Field(description="Vehicle Identification Number (VIN)")
    license_plate: Optional[str] = Field(description="License plate number")
    
    # Incident Information
    incident_date: Optional[str] = Field(description="Date of the incident (YYYY-MM-DD format)")
    incident_time: Optional[str] = Field(description="Time of the incident")
    incident_location: Optional[str] = Field(description="Location where the incident occurred")
    incident_description: Optional[str] = Field(description="Description of what happened")
    
    # Damage and Claims
    damage_description: Optional[str] = Field(description="Description of the damage")
    estimated_damage_amount: Optional[float] = Field(description="Estimated cost of damages")
    claim_amount: Optional[float] = Field(description="Amount being claimed")
    
    # Other Party Information (if applicable)
    other_party_name: Optional[str] = Field(description="Name of other party involved")
    other_party_insurance: Optional[str] = Field(description="Other party's insurance company")
    other_party_policy: Optional[str] = Field(description="Other party's policy number")
    
    # Documentation
    police_report_number: Optional[str] = Field(description="Police report number if applicable")
    witness_names: Optional[List[str]] = Field(default=[], description="Names of witnesses")
    witness_contacts: Optional[List[str]] = Field(default=[], description="Contact information for witnesses")
    
    # Medical Information (if applicable)
    injuries_reported: Optional[bool] = Field(description="Whether any injuries were reported")
    medical_treatment_required: Optional[bool] = Field(description="Whether medical treatment was required")
    hospital_name: Optional[str] = Field(description="Name of hospital if medical treatment was sought")
    
    # Additional Information
    additional_notes: Optional[str] = Field(description="Any additional relevant information")
    confidence_score: Optional[float] = Field(description="Confidence score of the extraction (0.0 to 1.0)")
    
    @validator('incident_date')
    def validate_date(cls, v):
        if v:
            try:
                # Try to parse and reformat the date
                parsed_date = datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                # If parsing fails, return the original value for manual review
                return v
        return v
    
    @validator('estimated_damage_amount', 'claim_amount')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Amount cannot be negative')
        return v


class DocumentClassification(BaseModel):
    """Model for document type classification."""
    
    document_type: str = Field(description="Type of document: insurance_card, drivers_license, accident_report, police_report, medical_report, repair_estimate, photos, other")
    confidence: float = Field(description="Confidence score for the classification (0.0 to 1.0)")
    relevant_sections: List[str] = Field(default=[], description="List of relevant sections or text snippets")
    key_identifiers: List[str] = Field(default=[], description="Key identifiers that led to this classification")


class LLMAgent:
    """Advanced LLM agent for claim processing and data extraction."""
    
    def __init__(self):
        """Initialize the LLM agent with configuration."""
        self.openai_api_key = settings.openai_api_key
        self.model_name = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        # Initialize output parsers
        self.claim_parser = PydanticOutputParser(pydantic_object=ClaimExtraction)
        self.classification_parser = PydanticOutputParser(pydantic_object=DocumentClassification)
        
        # Initialize fixing parsers for error recovery
        self.claim_fixing_parser = OutputFixingParser.from_llm(
            parser=self.claim_parser, 
            llm=self.llm
        )
        self.classification_fixing_parser = OutputFixingParser.from_llm(
            parser=self.classification_parser, 
            llm=self.llm
        )
    
    def extract_claim_data(self, text: str, document_type: str = "unknown") -> Dict[str, Any]:
        """
        Extract structured claim data from text using LLM.
        
        Args:
            text: Extracted text from document
            document_type: Type of document being processed
            
        Returns:
            Structured claim data as dictionary
        """
        try:
            # Create the prompt template
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=self._get_extraction_prompt(text, document_type))
            ])
            
            # Create the chain
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            
            # Execute the chain
            response = chain.run(text=text, document_type=document_type)
            
            # Parse the response
            try:
                parsed_data = self.claim_fixing_parser.parse(response)
                result = parsed_data.dict()
            except Exception as parse_error:
                logger.warning(f"Failed to parse LLM response, using fallback: {parse_error}")
                result = self._fallback_extraction(text)
            
            # Add metadata
            result["processing_metadata"] = {
                "model_used": self.model_name,
                "extraction_timestamp": datetime.now().isoformat(),
                "document_type": document_type,
                "text_length": len(text)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            return self._fallback_extraction(text)
    
    def classify_document(self, text: str) -> Dict[str, Any]:
        """
        Classify the type of document based on its content.
        
        Args:
            text: Text content of the document
            
        Returns:
            Document classification results
        """
        try:
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=self._get_classification_system_prompt()),
                HumanMessage(content=self._get_classification_prompt(text))
            ])
            
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            response = chain.run(text=text)
            
            try:
                parsed_classification = self.classification_fixing_parser.parse(response)
                return parsed_classification.dict()
            except Exception as parse_error:
                logger.warning(f"Failed to parse classification response: {parse_error}")
                return self._fallback_classification(text)
            
        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            return self._fallback_classification(text)
    
    def validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance extracted data using LLM.
        
        Args:
            extracted_data: Previously extracted data
            
        Returns:
            Validation results and corrections
        """
        try:
            validation_prompt = f"""
            Please validate and correct the following extracted claim data:
            
            {json.dumps(extracted_data, indent=2)}
            
            Check for:
            1. Date format consistency (YYYY-MM-DD)
            2. Phone number format validation
            3. Email address validation
            4. Reasonable amount values
            5. Completeness of required fields
            6. Logical consistency between fields
            
            Provide validation results in the following JSON format:
            {{
                "is_valid": true/false,
                "validation_errors": ["list of specific errors found"],
                "corrections": {{"field_name": "corrected_value"}},
                "completeness_score": 0.0-1.0,
                "confidence_score": 0.0-1.0,
                "missing_critical_fields": ["list of important missing fields"]
            }}
            """
            
            response = self.llm.invoke([HumanMessage(content=validation_prompt)])
            
            # Parse the JSON response
            try:
                validation_result = json.loads(response.content)
                return validation_result
            except json.JSONDecodeError:
                # Fallback validation
                return self._fallback_validation(extracted_data)
            
        except Exception as e:
            logger.error(f"Data validation failed: {str(e)}")
            return self._fallback_validation(extracted_data)
    
    def generate_summary(self, extracted_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the claim.
        
        Args:
            extracted_data: Structured claim data
            
        Returns:
            Summary text
        """
        try:
            summary_prompt = f"""
            Generate a concise, professional summary of this insurance claim:
            
            {json.dumps(extracted_data, indent=2)}
            
            The summary should include:
            - Key claim details (who, what, when, where)
            - Estimated damages
            - Next steps or recommendations
            
            Keep it under 200 words and professional in tone.
            """
            
            response = self.llm.invoke([HumanMessage(content=summary_prompt)])
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return "Summary generation failed. Please review the extracted data manually."
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for claim extraction."""
        return """
        You are an expert insurance claim processor with years of experience in extracting structured data from various insurance documents. Your task is to accurately extract relevant information from text and format it according to the provided schema.

        Guidelines:
        1. Extract only information that is explicitly stated in the text
        2. Do not make assumptions or fill in missing information
        3. Use standard formats for dates (YYYY-MM-DD), phone numbers, and amounts
        4. If information is unclear or ambiguous, mark it as such
        5. Provide confidence scores based on text clarity and completeness
        6. Handle multiple date formats and convert them to YYYY-MM-DD
        7. Extract monetary amounts and remove currency symbols
        
        Be thorough but accurate. It's better to leave a field empty than to guess incorrectly.
        """
    
    def _get_extraction_prompt(self, text: str, document_type: str) -> str:
        """Generate extraction prompt for the given text and document type."""
        return f"""
        Extract insurance claim information from the following text. The document type is: {document_type}
        
        Text to analyze:
        {text}
        
        {self.claim_parser.get_format_instructions()}
        
        Focus on extracting accurate information. If you're unsure about any field, leave it empty rather than guessing.
        """
    
    def _get_classification_system_prompt(self) -> str:
        """Get system prompt for document classification."""
        return """
        You are a document classification expert specializing in insurance-related documents. Your task is to accurately classify documents based on their content and identify key sections.
        
        Document types to classify:
        - insurance_card: Insurance policy cards or certificates
        - drivers_license: Driver's license or identification documents
        - accident_report: Accident or incident reports
        - police_report: Official police reports
        - medical_report: Medical records or treatment reports
        - repair_estimate: Vehicle repair estimates or invoices
        - photos: Photo evidence of damage or incidents
        - other: Any other type of document
        
        Provide high confidence scores only when you're certain about the classification.
        """
    
    def _get_classification_prompt(self, text: str) -> str:
        """Generate classification prompt for the given text."""
        return f"""
        Classify the following document text and identify its type:
        
        {text}
        
        {self.classification_parser.get_format_instructions()}
        
        Analyze the content, structure, and key identifiers to determine the document type.
        """
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns."""
        try:
            # Basic regex-based extraction as fallback
            result = ClaimExtraction()
            
            # Extract basic patterns
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            amount_pattern = r'\$?[\d,]+\.?\d*'
            
            phones = re.findall(phone_pattern, text)
            emails = re.findall(email_pattern, text)
            amounts = re.findall(amount_pattern, text)
            
            if phones:
                result.claimant_phone = phones[0]
            if emails:
                result.claimant_email = emails[0]
            if amounts:
                try:
                    result.claim_amount = float(amounts[0].replace('$', '').replace(',', ''))
                except ValueError:
                    pass
            
            result.confidence_score = 0.3  # Low confidence for fallback
            
            return result.dict()
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {str(e)}")
            return ClaimExtraction().dict()
    
    def _fallback_classification(self, text: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching."""
        try:
            keywords = {
                "insurance_card": ["policy", "coverage", "insured", "premium"],
                "drivers_license": ["license", "driver", "license number", "dl"],
                "accident_report": ["accident", "incident", "collision", "crash"],
                "police_report": ["police", "officer", "report number", "citation"],
                "medical_report": ["medical", "hospital", "doctor", "treatment"],
                "repair_estimate": ["repair", "estimate", "parts", "labor"]
            }
            
            text_lower = text.lower()
            scores = {}
            
            for doc_type, terms in keywords.items():
                score = sum(1 for term in terms if term in text_lower)
                scores[doc_type] = score / len(terms)
            
            best_type = max(scores, key=scores.get) if scores else "other"
            confidence = scores.get(best_type, 0.0)
            
            return {
                "document_type": best_type,
                "confidence": confidence,
                "relevant_sections": [],
                "key_identifiers": []
            }
            
        except Exception as e:
            logger.error(f"Fallback classification failed: {str(e)}")
            return {
                "document_type": "other",
                "confidence": 0.0,
                "relevant_sections": [],
                "key_identifiers": []
            }
    
    def _fallback_validation(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback validation using basic checks."""
        try:
            errors = []
            critical_fields = ["claimant_name", "incident_date", "claim_amount"]
            missing_critical = [field for field in critical_fields if not extracted_data.get(field)]
            
            # Basic validation checks
            if extracted_data.get("claimant_email"):
                if "@" not in extracted_data["claimant_email"]:
                    errors.append("Invalid email format")
            
            if extracted_data.get("claim_amount"):
                try:
                    amount = float(extracted_data["claim_amount"])
                    if amount < 0:
                        errors.append("Claim amount cannot be negative")
                except (ValueError, TypeError):
                    errors.append("Invalid claim amount format")
            
            filled_fields = sum(1 for value in extracted_data.values() if value is not None and value != "")
            total_fields = len(extracted_data)
            completeness_score = filled_fields / total_fields if total_fields > 0 else 0.0
            
            return {
                "is_valid": len(errors) == 0 and len(missing_critical) == 0,
                "validation_errors": errors,
                "corrections": {},
                "completeness_score": completeness_score,
                "confidence_score": 0.5,  # Medium confidence for fallback
                "missing_critical_fields": missing_critical
            }
            
        except Exception as e:
            logger.error(f"Fallback validation failed: {str(e)}")
            return {
                "is_valid": False,
                "validation_errors": ["Validation process failed"],
                "corrections": {},
                "completeness_score": 0.0,
                "confidence_score": 0.0,
                "missing_critical_fields": []
            }


# Global instance
llm_agent = LLMAgent()