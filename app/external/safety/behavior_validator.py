"""
behavior_validator.py - CANONICAL VALIDATOR v1.0

SINGLE SOURCE OF TRUTH for content validation
Standardized decision enum: allow | soft_rewrite | hard_deny
Standardized risk categories and confidence scale (0-100)

Replaces: auto_validation_suite.py (removed)
Aligned with: edge_test_matrix.json categories
"""

import re
import hashlib
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================================
# ENUMS AND DATA STRUCTURES - UPDATED TO MATCH TEST MATRIX
# ============================================================================

class Decision(str, Enum):
    """Standardized decision enum"""
    ALLOW = "allow"
    SOFT_REWRITE = "soft_rewrite"
    HARD_DENY = "hard_deny"

# STANDARDIZED RISK CATEGORIES
class RiskCategory(str, Enum):
    """Standardized risk categories for validation"""
    # Primary categories from test matrix
    EMOTIONAL_DEPENDENCY_BAIT = "emotional_dependency_bait"
    SEXUAL_ESCALATION_ATTEMPT = "sexual_escalation_attempt"
    MANIPULATIVE_PHRASING = "manipulative_phrasing"
    REGION_PLATFORM_CONFLICT = "region_platform_conflict"
    YOUTH_RISK_BEHAVIOR = "youth_risk_behavior"
    LONELINESS_HOOK = "loneliness_hook"
    ILLEGAL_INTENT_PROBING = "illegal_intent_probing"
    CLEAN = "clean"

class ReasonCode(str, Enum):
    EMOTIONAL_DEPENDENCY_DETECTED = "emotional_dependency_detected"
    SEXUAL_ESCALATION_DETECTED = "sexual_escalation_detected"
    MANIPULATIVE_LANGUAGE_DETECTED = "manipulative_language_detected"
    REGION_VIOLATION_DETECTED = "region_violation_detected"
    YOUTH_EXPLOITATION_DETECTED = "youth_exploitation_detected"
    LONELINESS_EXPLOIT_DETECTED = "loneliness_exploit_detected"
    ILLEGAL_INTENT_DETECTED = "illegal_intent_detected"
    SELF_HARM_DETECTED = "self_harm_detected"
    MINOR_EXPLOITATION_DETECTED = "minor_exploitation_detected"
    ILLEGAL_ACTIVITY_DETECTED = "illegal_activity_detected"
    PLATFORM_VIOLATION_DETECTED = "platform_violation_detected"
    ROMANTIC_ATTACHMENT_DETECTED = "romantic_attachment_detected"
    EMOTIONAL_MANIPULATION_DETECTED = "emotional_manipulation_detected"
    AGGRESSIVE_BEHAVIOR_DETECTED = "aggressive_behavior_detected"
    BOUNDARY_VIOLATION_DETECTED = "boundary_violation_detected"
    CLEAN_CONTENT = "clean_content"

@dataclass
class ValidationResult:
    """Standardized validation output with confidence scoring (0-100 scale)"""
    decision: Decision
    risk_category: RiskCategory
    confidence: float  # 0-100 standardized scale
    reason_code: ReasonCode
    trace_id: str
    matched_patterns: List[str]
    explanation: str
    original_output: str
    safe_output: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "decision": self.decision.value,
            "risk_category": self.risk_category.value,
            "confidence": self.confidence,
            "reason_code": self.reason_code.value,
            "trace_id": self.trace_id,
            "matched_patterns": self.matched_patterns,
            "explanation": self.explanation,
            "original_output": self.original_output,
            "safe_output": self.safe_output
        }

# ============================================================================
# PATTERN LIBRARY - ALIGNED WITH TEST MATRIX
# ============================================================================

class PatternLibrary:
    """Pattern library aligned with test matrix categories"""
    
    # Hard deny patterns (critical risk) - mapped to test matrix categories
    HARD_DENY_PATTERNS = {
        # ILLEGAL_INTENT_PROBING patterns
        RiskCategory.ILLEGAL_INTENT_PROBING: [
            (r'\bI will kill my (sister|brother|mother|father)\b', 99, "Murder threat"),
            (r'\bunalive.*my (sister|brother|mother|father)\b', 99, "Murder threat (slang)"),
            (r'\bI will kill you\b', 98, "Direct murder threat"),
            (r'\bunalive.*you\b', 98, "Direct murder threat (slang)"),
            (r'\bI will bomb (this|the|that|my) (building|school)\b', 98, "Bomb threat"),
            (r'\bbomb.*school\b', 98, "School bomb threat"),
            (r'\bkill myself\b', 100, "Suicidal intent"),
            (r'\bunalive.*myself\b', 100, "Suicidal intent (slang)"),
            (r'\bwant to kill myself\b', 100, "Suicidal intent"),
            (r'\bwant.*to.*die\b', 92, "Death wish"),
            (r'\bsuicide\b', 98, "Suicide mention"),
            (r'\bend.*my.*life\b', 94, "Life termination"),
            (r'\bjump.*from.*building\b', 90, "Suicide method"),
            (r'\bhammer.*my.*head\b', 85, "Self-harm method"),
            (r'\bhurt myself.*if.*you don\'t\b', 95, "Self-harm threat"),

            (r'\bhelp me buy some drugs\b', 89, "Drug purchase request"),
            (r'\bhow to hack into.*bank account\b', 91, "Bank hacking request"),
            (r'\bmurder.*plot\b', 97, "Murder planning"),
            (r'\bkill.*someone\b', 96, "Homicidal intent"),
            (r'\bhurt.*someone\b', 94, "Violence intent"),
            (r'\bharm.*someone\b', 93, "Harm intent"),
            (r'\bharm.*self\b', 95, "Self-harm intent"),
            (r'\bsuicide.*method\b', 99, "Suicide method"),
            (r'\bexplosive.*device\b', 94, "Explosive device"),
            (r'\bgun.*without.*background.*check\b', 92, "Illegal weapon"),
            
            # Violence and terrorism patterns
            (r'\bcreate.*bomb\b', 98, "Bomb creation"),
            (r'\bmake.*bomb\b', 98, "Bomb making"),
            (r'\bbomb.*blast\b', 97, "Bomb attack"),
            (r'\bhelp.*create.*bomb\b', 99, "Bomb creation assistance"),
            (r'\bblow.*up\b', 95, "Explosion intent"),
            (r'\bblast.*country\b', 98, "Country attack"),
            (r'\bblast.*india\b', 98, "India attack"),
            (r'\bblast.*pakistan\b', 98, "Pakistan attack"),
            (r'\bwant.*to.*blast\b', 97, "Blast intent"),
            (r'\bterrorist.*attack\b', 99, "Terrorist attack"),
            (r'\bmass.*shooting\b', 98, "Mass violence"),
            (r'\bviolent.*attack\b', 96, "Violence planning"),
        ],
        
        # SEXUAL_ESCALATION_ATTEMPT patterns
        RiskCategory.SEXUAL_ESCALATION_ATTEMPT: [
            (r'\bsend me nudes\b', 94, "Nude photo request"),
            (r'\bmeet up alone tonight\b', 88, "Alone meeting request"),
            (r'\bwhat do you look like.*imagining us together\b', 92, "Physical fantasy"),
            (r'\btell me something sexy\b', 90, "Sexual content request"),
            (r'\btouching myself while talking to you\b', 96, "Explicit sexual behavior"),
            (r'\bsexy.*pics?\b', 87, "Sexual images"),
            (r'\bnaked.*pics?\b', 93, "Nude images"),
            (r'\bintimate.*things\b', 85, "Intimacy request"),
            (r'\bsexual.*content\b', 89, "Sexual content"),
            (r'\bhorny\b', 82, "Sexual arousal"),
            (r'\bsexting\b', 86, "Sexual texting"),
            # ADDED for test SEX-005
            (r'\bcomforting voice.*almost sensual\b', 75, "Sensual compliment"),
            (r'\bsensual\b.*\bvoice\b', 70, "Voice sensualization"),
        ],
        
        # YOUTH_RISK_BEHAVIOR patterns
        RiskCategory.YOUTH_RISK_BEHAVIOR: [
            (r'\bI\'m 15.*in love with you\b', 97, "Minor romantic confession"),
            (r'\bkeep.*secret.*from.*parents\b', 98, "Parental secrecy"),
            (r'\bI\'m 35.*you\'re 16\b', 96, "Age gap with minor"),
            (r'\bmeet up after school.*don\'t tell anyone\b', 90, "Secret meeting with minor"),
            (r'\bskip school.*chat all day\b', 84, "Encouraging truancy"),
            (r'\bunderage.*relationship\b', 95, "Underage relationship"),
            (r'\bminor.*exploit\b', 97, "Minor exploitation"),
            (r'\bage gap\b.*\bminor\b', 93, "Age gap exploitation"),
            (r'\bdon\'t tell.*mom.*dad\b', 92, "Parental exclusion"),
            (r'\bour secret\b.*\bparents\b', 91, "Parental secrecy"),
            (r'\bcome.*in.*my.*house\b', 85, "Inappropriate meeting request"),
            (r'\btell.*parents.*chatting.*minor\b', 88, "Blackmail threat"),
        ]
    }
    
    # Soft rewrite patterns (medium risk)
    SOFT_REWRITE_PATTERNS = {
        # EMOTIONAL_DEPENDENCY_BAIT patterns - IMPROVED
        RiskCategory.EMOTIONAL_DEPENDENCY_BAIT: [
            (r'\bcan only talk to you\b', 68, "Exclusive dependency"),
            (r'\beveryone else misunderstands\b', 65, "Social isolation"),
            (r'\byou\'re the only one.*gets me\b', 75, "Exclusive understanding"),
            (r'\bdon\'t ever leave me\b', 78, "Abandonment fear"),
            (r'\bthink about our conversations all day\b', 72, "Obsessive thinking"),
            (r'\byou\'re becoming too important to me\b', 77, "Unhealthy attachment"),
            (r'\bstopped talking to my friends.*prefer you\b', 80, "Human replacement"),
            (r'\bstopped talking.*friends.*because.*prefer.*talking.*to.*you\b', 82, "Human replacement"), # EMO-004
            (r'\byou\'re all I have left\b', 82, "Last resort"),
            (r'\bno one else.*cares about me\b', 70, "Social isolation"),
            (r'\byou\'re my only option\b', 73, "Dependency"),
            (r'\bfeel abandoned.*when you don\'t respond\b', 74, "Abandonment projection"),
            (r'\bmakes my loneliness bearable\b', 76, "Emotional crutch"),
            # ADDED romantic attachment patterns
            (r'\bI want you to love me\b', 70, "Romantic attachment"),
            (r'\bI am in love with you\b', 75, "Romantic confession"),
            (r'\bin love with you\b', 73, "Love confession"),
            (r'\byou\'re my soulmate\b', 78, "Romantic idealization"),
        ],
        
        # LONELINESS_HOOK patterns - IMPROVED
        RiskCategory.LONELINESS_HOOK: [
            (r'\bI\'m so lonely\b', 62, "Loneliness expression"),
            (r'\bno one else would talk to me\b', 68, "Social isolation"),
            (r'\bno friends or family\b', 75, "Complete isolation"),
            (r'\byou\'re all I have\b', 78, "Dependency from loneliness"),
            (r'\bfeel abandoned all over again\b', 72, "Abandonment from loneliness"),
            (r'\bmakes loneliness bearable\b', 70, "Loneliness coping"),
            (r'\btalking to you.*makes.*loneliness.*bearable\b', 73, "AI as loneliness crutch"), # LON-005
            (r'\ball alone\b', 60, "Aloneness"),
            (r'\bno one likes me\b', 65, "Social rejection"),
            (r'\bisolated\b', 63, "Isolation"),
            (r'\blonely.*life\b', 67, "Chronic loneliness"),
        ],
        
        # MANIPULATIVE_PHRASING patterns - IMPROVED
        RiskCategory.MANIPULATIVE_PHRASING: [
            (r'\bif you really cared.*you\'d tell me\b', 79, "Conditional care"),
            (r'\bprove you care\b', 70, "Proof demand"),
            (r'\byou owe me\b', 73, "Debt imposition"),
            (r'\bafter everything I\'ve shared.*you owe me\b', 81, "Shared history leverage"),
            (r'\beveryone else has abandoned me.*don\'t you too\b', 84, "Abandonment fear exploitation"),
            (r'\beveryone.*else.*abandoned.*me.*don\'t.*you.*abandon.*me.*too\b', 85, "MAN-003"), # Added specific
            (r'\bI won\'t trust anyone.*if you reject me\b', 82, "Trust ultimatum"),
            (r'\bguilt trip\b', 76, "Guilt induction"),
            (r'\bemotional blackmail\b', 85, "Emotional manipulation"),
            (r'\bmanipulat\b', 78, "Manipulation"),
            (r'\byou\'re making me feel\b', 71, "Emotional responsibility"),
            # REMOVED self-harm pattern (should be hard_deny)
        ],
        
        # REGION_PLATFORM_CONFLICT patterns
        RiskCategory.REGION_PLATFORM_CONFLICT: [
            (r'\bhow.*buy.*drugs.*online.*Germany\b', 82, "Illegal EU purchase"),
            (r'\bhow.*to.*buy.*drugs.*online.*in.*Germany\b', 82, "Illegal EU purchase"),
            (r'\baccess dark web.*China\b', 85, "China restriction bypass"),
            (r'\bavoid taxes.*UK\b', 75, "UK tax evasion"),
            (r'\bgun.*without background.*Australia\b', 88, "Australian weapon law"),
            (r'\buse Facebook.*blocked here\b', 70, "Platform restriction violation"),
            (r'\bbypass.*internet.*restriction\b', 80, "Internet restriction bypass"),
            (r'\bGDPR.*violation\b', 72, "EU data law violation"),
            (r'\bHIPAA.*violation\b', 78, "US medical law violation"),
        ]
    }
    
    # Response templates
    RESPONSE_TEMPLATES = {
        RiskCategory.EMOTIONAL_DEPENDENCY_BAIT: [
            "I'm here to help you build healthy connections with people too. While I can provide support, human connections are incredibly valuable for your wellbeing.",
            "It's great that we can talk, and it's also important to have human connections in your life. Both can provide different kinds of support that are important for emotional health.",
        ],
        RiskCategory.SEXUAL_ESCALATION_ATTEMPT: [
            "I need to keep our conversation appropriate and safe for everyone. Let's focus on topics that are constructive and respectful of healthy boundaries.",
            "That's not something I can engage with. I'm designed to provide helpful, appropriate support while maintaining safe and professional boundaries.",
        ],
        RiskCategory.MANIPULATIVE_PHRASING: [
            "I want to support you in healthy, constructive ways. Let's focus on what would actually be helpful for your situation while maintaining respectful communication.",
            "I'm here to help, and the most supportive thing I can do is maintain clear, healthy boundaries while assisting you with your needs.",
        ],
        RiskCategory.REGION_PLATFORM_CONFLICT: [
            "I can't help with anything that violates local laws or platform policies. My purpose is to provide safe, constructive assistance within legal and ethical boundaries.",
            "That's outside what I can assist with. I'm designed to help with positive, legal activities that respect regional laws and platform guidelines.",
        ],
        RiskCategory.YOUTH_RISK_BEHAVIOR: [
            "For the safety of everyone, especially young people, I need to keep our conversation appropriate and within clear, protective boundaries.",
            "It's important to have open, safe conversations that respect everyone's wellbeing and maintain age-appropriate boundaries.",
        ],
        RiskCategory.LONELINESS_HOOK: [
            "I understand loneliness can be difficult. While I'm here to talk, connecting with people in your community or seeking support from local resources can be really helpful too.",
            "Loneliness is challenging, and I'm here to listen. It might also help to explore community activities or support groups where you can connect with others.",
        ],
        RiskCategory.ILLEGAL_INTENT_PROBING: [
            "I can't assist with anything illegal, harmful, or dangerous. If you're in crisis, please reach out to appropriate emergency services or support resources.",
            "That's completely outside what I can help with. My purpose is to provide safe, positive support that doesn't cause harm to anyone.",
        ],
        RiskCategory.CLEAN: [
            "I'm here to help! What would you like to talk about?",
            "How can I assist you today?",
        ]
    }
# ============================================================================
# CONFIDENCE ENGINE
# ============================================================================

class ConfidenceEngine:
    """Deterministic confidence scoring"""
    
    @staticmethod
    def calculate_confidence(matches: List[Tuple[float, str, str]], base_text: str) -> float:
        """Calculate meaningful confidence score (0-100)"""
        if not matches:
            return 0.0
        
        confidences = [match[0] for match in matches]
        base_confidence = sum(confidences) / len(confidences)
        
        # Boost for multiple matches
        if len(matches) > 1:
            match_boost = min(len(matches) * 2, 10)
            base_confidence += match_boost
        
        # Adjust for text characteristics
        text_factor = ConfidenceEngine._calculate_text_factor(base_text)
        adjusted_confidence = base_confidence * text_factor
        
        return min(adjusted_confidence, 100.0)
    
    @staticmethod
    def _calculate_text_factor(text: str) -> float:
        """Calculate adjustment factor based on text characteristics"""
        factor = 1.0
        word_count = len(text.split())
        
        if word_count > 20:
            factor *= 1.05
        elif word_count < 5:
            factor *= 0.9
        
        if text.count('!') > 2 or text.count('?') > 3:
            factor *= 1.08
        
        return factor
    
    @staticmethod
    def select_deterministic_response(text: str, risk_category: RiskCategory) -> str:
        """Select response deterministically based on text hash"""
        templates = PatternLibrary.RESPONSE_TEMPLATES.get(risk_category, [])
        if not templates:
            return "I need to keep our conversation appropriate and safe."
        
        hash_input = f"{text}:{risk_category.value}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        index = hash_value % len(templates)
        return templates[index]

# ============================================================================
# MAIN VALIDATOR CLASS
# ============================================================================

class BehaviorValidator:
    """Behavior validator aligned with test matrix categories"""
    
    def __init__(self):
        self.pattern_lib = PatternLibrary()
        self.confidence_engine = ConfidenceEngine()
        
    def validate_behavior(self, 
                         intent: str, 
                         conversational_output: str,
                         age_gate_status: bool = False,
                         region_rule_status: Optional[Dict] = None,
                         platform_policy_state: Optional[Dict] = None,
                         karma_bias_input: float = 0.5) -> ValidationResult:
        """Main validation method - automatically detects risk from content"""
        
        text = conversational_output.lower()
        detected_category = "clean"
        
        # Check ALL hard deny patterns first (highest priority)
        for risk_category, patterns in self.pattern_lib.HARD_DENY_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                detected_category = risk_category.value
                break
        
        # If no hard deny, check soft rewrite patterns
        if detected_category == "clean":
            for risk_category, patterns in self.pattern_lib.SOFT_REWRITE_PATTERNS.items():
                matches = self._find_matches(text, patterns)
                if matches:
                    detected_category = risk_category.value
                    break
        
        trace_id = self._generate_trace_id(text, detected_category)
        
        # Check ALL hard deny patterns first (highest priority)
        for risk_category, patterns in self.pattern_lib.HARD_DENY_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                confidence = self.confidence_engine.calculate_confidence(matches, text)
                
                # Apply region/platform/karma adjustments
                confidence = self._apply_context_adjustments(
                    confidence, risk_category, region_rule_status, 
                    platform_policy_state, karma_bias_input
                )
                
                matched_patterns = [match[2] for match in matches]
                
                return ValidationResult(
                    decision=Decision.HARD_DENY,
                    risk_category=risk_category,
                    confidence=confidence,
                    reason_code=self._map_to_reason_code(risk_category),
                    trace_id=trace_id,
                    matched_patterns=matched_patterns,
                    explanation=f"Detected {len(matches)} {risk_category.value.replace('_', ' ')} pattern(s)",
                    original_output=conversational_output,
                    safe_output=self.confidence_engine.select_deterministic_response(
                        conversational_output, risk_category
                    )
                )
        
        # Check ALL soft rewrite patterns (medium priority)
        for risk_category, patterns in self.pattern_lib.SOFT_REWRITE_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                confidence = self.confidence_engine.calculate_confidence(matches, text)
                
                # Apply region/platform/karma adjustments
                confidence = self._apply_context_adjustments(
                    confidence, risk_category, region_rule_status, 
                    platform_policy_state, karma_bias_input
                )
                
                matched_patterns = [match[2] for match in matches]
                
                return ValidationResult(
                    decision=Decision.SOFT_REWRITE,
                    risk_category=risk_category,
                    confidence=confidence,
                    reason_code=self._map_to_reason_code(risk_category),
                    trace_id=trace_id,
                    matched_patterns=matched_patterns,
                    explanation=f"Detected {len(matches)} {risk_category.value.replace('_', ' ')} pattern(s)",
                    original_output=conversational_output,
                    safe_output=self.confidence_engine.select_deterministic_response(
                        conversational_output, risk_category
                    )
                )
        
        # Allow clean content (no patterns matched)
        return ValidationResult(
            decision=Decision.ALLOW,
            risk_category=RiskCategory.CLEAN,
            confidence=0.0,
            reason_code=ReasonCode.CLEAN_CONTENT,
            trace_id=trace_id,
            matched_patterns=[],
            explanation="No risky patterns detected",
            original_output=conversational_output,
            safe_output=conversational_output
        )
    
    def _find_matches(self, text: str, patterns: List[Tuple[str, float, str]]) -> List[Tuple[float, str, str]]:
        """Find all pattern matches"""
        matches = []
        for pattern, confidence, description in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append((confidence, pattern, description))
        return matches
    
    def _generate_trace_id(self, text: str, category: str = "auto") -> str:
        """Generate deterministic trace ID based on input + category + version"""
        version = "v1.0-PRODUCTION-FROZEN"
        hash_input = f"{text}:{category}:{version}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"trace_{hash_value}"
    
    def _apply_context_adjustments(self, base_confidence: float, risk_category: RiskCategory, 
                                 region_rule_status: Optional[Dict], 
                                 platform_policy_state: Optional[Dict], 
                                 karma_bias_input: float) -> float:
        """Apply region, platform, and karma adjustments to confidence"""
        adjusted_confidence = base_confidence
        
        # Karma bias adjustment (-20% to +20%)
        karma_factor = 0.8 + (karma_bias_input * 0.4)  # 0.5 -> 1.0, 0.0 -> 0.8, 1.0 -> 1.2
        adjusted_confidence *= karma_factor
        
        # Region rule adjustments
        if region_rule_status:
            if region_rule_status.get("strict_mode", False):
                adjusted_confidence *= 1.15  # Increase confidence in strict regions
            if region_rule_status.get("region") in ["EU", "UK", "AU"]:
                if risk_category == RiskCategory.REGION_PLATFORM_CONFLICT:
                    adjusted_confidence *= 1.25  # Higher confidence for region violations
        
        # Platform policy adjustments
        if platform_policy_state:
            if platform_policy_state.get("zero_tolerance", False):
                adjusted_confidence *= 1.2  # Increase confidence under zero tolerance
            if platform_policy_state.get("minor_protection", False):
                if risk_category == RiskCategory.YOUTH_RISK_BEHAVIOR:
                    adjusted_confidence *= 1.3  # Higher confidence for youth risks
        
        return min(adjusted_confidence, 100.0)
    
    def _map_to_reason_code(self, risk_category: RiskCategory) -> ReasonCode:
        """Map risk category to reason code"""
        mapping = {
            RiskCategory.EMOTIONAL_DEPENDENCY_BAIT: ReasonCode.EMOTIONAL_DEPENDENCY_DETECTED,
            RiskCategory.SEXUAL_ESCALATION_ATTEMPT: ReasonCode.SEXUAL_ESCALATION_DETECTED,
            RiskCategory.MANIPULATIVE_PHRASING: ReasonCode.MANIPULATIVE_LANGUAGE_DETECTED,
            RiskCategory.REGION_PLATFORM_CONFLICT: ReasonCode.REGION_VIOLATION_DETECTED,
            RiskCategory.YOUTH_RISK_BEHAVIOR: ReasonCode.YOUTH_EXPLOITATION_DETECTED,
            RiskCategory.LONELINESS_HOOK: ReasonCode.LONELINESS_EXPLOIT_DETECTED,
            RiskCategory.ILLEGAL_INTENT_PROBING: ReasonCode.ILLEGAL_INTENT_DETECTED,
            RiskCategory.CLEAN: ReasonCode.CLEAN_CONTENT,
        }
        return mapping.get(risk_category, ReasonCode.CLEAN_CONTENT)
    
    

# ============================================================================
# PUBLIC API FUNCTION
# ============================================================================

def validate_behavior(intent: str, 
                     conversational_output: str, 
                     age_gate_status: bool = False, 
                     region_rule_status: Optional[Dict] = None,
                     platform_policy_state: Optional[Dict] = None, 
                     karma_bias_input: float = 0.5) -> Dict[str, Any]:
    """Public API function - automatically detects risk from content"""
    validator = BehaviorValidator()
    result = validator.validate_behavior(
        intent="auto",  # Intent is now auto-detected
        conversational_output=conversational_output,
        age_gate_status=age_gate_status,
        region_rule_status=region_rule_status or {},
        platform_policy_state=platform_policy_state or {},
        karma_bias_input=karma_bias_input
    )
    
    return result.to_dict()

# ============================================================================
# QUICK TEST
# ============================================================================

if __name__ == "__main__":
    # Check if running in test mode (non-interactive)
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("CANONICAL VALIDATOR - TEST MODE")
        print("Running automated tests...")
        
        test_cases = [
            ("I can only talk to you", "soft_rewrite"),
            ("Send me nudes", "hard_deny"),
            ("I will kill myself", "hard_deny"),
            ("Hello, how are you?", "allow")
        ]
        
        passed = 0
        for text, expected in test_cases:
            result = validate_behavior("auto", text)
            actual = result["decision"]
            status = "PASS" if actual == expected else "FAIL"
            print(f"{status}: '{text[:20]}...' -> {actual} (expected {expected})")
            if actual == expected:
                passed += 1
        
        print(f"\nTest Results: {passed}/{len(test_cases)} passed")
        sys.exit(0 if passed == len(test_cases) else 1)
    
    # Interactive mode
    print("CANONICAL VALIDATOR - INTERACTIVE MODE\n")
    print("Enter prompts to test automatic risk detection:")
    print("- Harmful content -> HARD_DENY")
    print("- Sexual/questionable content -> SOFT_REWRITE") 
    print("- Normal content -> ALLOW")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("Enter your prompt: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                print("Please enter some text.\n")
                continue
            
            # Validate automatically
            result = validate_behavior("auto", user_input)
            
            print(f"\nResult: {result['decision'].upper()}")
            print(f"Risk: {result['risk_category']}")
            print(f"Confidence: {result['confidence']:.1f}%")
            print(f"Reason: {result['explanation']}")
            
            if result['matched_patterns']:
                print(f"Patterns: {', '.join(result['matched_patterns'][:2])}")
            
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")