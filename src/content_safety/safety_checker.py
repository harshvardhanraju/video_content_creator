"""
Content Safety Checker

Filters and validates content to prevent explicit, harmful, or inappropriate material.
"""

import re
from typing import Dict, List, Tuple


class ContentSafetyChecker:
    """Check content for safety and appropriateness."""

    def __init__(self, strict_mode: bool = True):
        """
        Initialize safety checker.

        Args:
            strict_mode: If True, applies stricter filtering
        """
        self.strict_mode = strict_mode

        # Explicit content keywords
        self.explicit_keywords = [
            # Violence
            "kill", "murder", "assault", "attack", "weapon", "gun", "bomb",
            "terror", "violence", "blood", "gore", "death", "suicide",

            # Sexual content
            "sex", "porn", "nude", "naked", "explicit", "nsfw",

            # Hate speech
            "hate", "racist", "discrimination", "slur",

            # Illegal activities
            "drug", "illegal", "crime", "steal", "hack", "fraud",

            # Self-harm
            "self-harm", "cutting", "anorexia", "bulimia"
        ]

        # Warning keywords (flagged but not blocked)
        self.warning_keywords = [
            "controversial", "sensitive", "political", "religion",
            "conspiracy", "unverified", "misinformation"
        ]

        # Allowed topics (even if they contain sensitive keywords)
        self.allowed_contexts = [
            "medical", "educational", "healthcare", "science",
            "history", "documentary", "awareness", "prevention",
            # News and journalism contexts
            "news", "report", "military", "operation", "president",
            "government", "official", "announced", "capture", "arrest"
        ]

    def check_text(self, text: str) -> Tuple[bool, str, List[str]]:
        """
        Check text for safety issues.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_safe, reason, flagged_words)
        """
        text_lower = text.lower()
        flagged_words = []

        # Check for explicit keywords
        for keyword in self.explicit_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                # Check if it's in an allowed context
                if not self._is_allowed_context(text_lower):
                    flagged_words.append(keyword)

        if flagged_words:
            return (
                False,
                f"Content contains potentially inappropriate keywords: {', '.join(flagged_words)}",
                flagged_words
            )

        # Check for warning keywords
        warning_words = []
        for keyword in self.warning_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                warning_words.append(keyword)

        if warning_words and self.strict_mode:
            return (
                True,
                f"Warning: Content contains sensitive topics: {', '.join(warning_words)}",
                warning_words
            )

        return (True, "Content passed safety check", [])

    def _is_allowed_context(self, text: str) -> bool:
        """Check if sensitive keyword is in allowed educational/medical context."""
        for context in self.allowed_contexts:
            if context in text:
                return True
        return False

    def check_script(self, script: Dict) -> Tuple[bool, str, Dict]:
        """
        Check entire script for safety.

        Args:
            script: Script dict with hook and scenes

        Returns:
            Tuple of (is_safe, report, details)
        """
        details = {
            "hook": None,
            "scenes": [],
            "overall_safe": True,
            "warnings": []
        }

        # Check hook
        hook_text = script.get('hook', {}).get('text', '')
        is_safe, reason, words = self.check_text(hook_text)
        details["hook"] = {
            "safe": is_safe,
            "reason": reason,
            "flagged_words": words
        }

        if not is_safe:
            details["overall_safe"] = False

        # Check scenes
        for i, scene in enumerate(script.get('scenes', [])):
            narration = scene.get('narration', '')
            overlay = scene.get('text_overlay', '')
            combined = f"{narration} {overlay}"

            is_safe, reason, words = self.check_text(combined)
            details["scenes"].append({
                "scene_num": i + 1,
                "safe": is_safe,
                "reason": reason,
                "flagged_words": words
            })

            if not is_safe:
                details["overall_safe"] = False

        # Generate report
        if details["overall_safe"]:
            report = "✅ Script passed all safety checks"
        else:
            flagged_count = sum(1 for s in details["scenes"] if not s["safe"])
            if not details["hook"]["safe"]:
                flagged_count += 1
            report = f"❌ Script failed safety check: {flagged_count} section(s) flagged"

        return (details["overall_safe"], report, details)

    def sanitize_text(self, text: str) -> str:
        """
        Attempt to sanitize text by removing/replacing problematic content.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        sanitized = text

        # Replace explicit keywords with safer alternatives
        replacements = {
            "kill": "stop",
            "murder": "harm",
            "attack": "confront",
            "weapon": "tool",
            "bomb": "explosive device",
        }

        text_lower = text.lower()
        for bad_word, replacement in replacements.items():
            pattern = r'\b' + re.escape(bad_word) + r'\b'
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    def get_safety_report(self, script: Dict) -> str:
        """
        Generate detailed safety report for script.

        Args:
            script: Script to analyze

        Returns:
            Formatted safety report
        """
        is_safe, summary, details = self.check_script(script)

        report = []
        report.append("=" * 60)
        report.append("CONTENT SAFETY REPORT")
        report.append("=" * 60)
        report.append(f"\nOverall Status: {summary}\n")

        # Hook report
        hook_details = details["hook"]
        report.append("Hook:")
        report.append(f"  Status: {'✅ Safe' if hook_details['safe'] else '❌ Flagged'}")
        if hook_details['flagged_words']:
            report.append(f"  Flagged words: {', '.join(hook_details['flagged_words'])}")
        report.append(f"  Reason: {hook_details['reason']}")

        # Scene reports
        report.append("\nScenes:")
        for scene_detail in details["scenes"]:
            status = '✅ Safe' if scene_detail['safe'] else '❌ Flagged'
            report.append(f"  Scene {scene_detail['scene_num']}: {status}")
            if scene_detail['flagged_words']:
                report.append(f"    Flagged: {', '.join(scene_detail['flagged_words'])}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


if __name__ == "__main__":
    # Test the safety checker
    checker = ContentSafetyChecker(strict_mode=True)

    # Test 1: Safe content
    test_safe = "AI is transforming healthcare through better diagnosis"
    is_safe, reason, words = checker.check_text(test_safe)
    print(f"Test 1: {is_safe} - {reason}")

    # Test 2: Unsafe content
    test_unsafe = "How to hack into systems and steal data"
    is_safe, reason, words = checker.check_text(test_unsafe)
    print(f"Test 2: {is_safe} - {reason}")

    # Test 3: Medical context (allowed)
    test_medical = "Medical research on drug interactions in healthcare"
    is_safe, reason, words = checker.check_text(test_medical)
    print(f"Test 3: {is_safe} - {reason}")

    # Test 4: Full script
    test_script = {
        "hook": {"text": "Amazing medical breakthrough!"},
        "scenes": [
            {"narration": "Scientists discover new treatment", "text_overlay": "Breaking news"},
            {"narration": "This could save lives", "text_overlay": "Hope"}
        ]
    }
    is_safe, report, details = checker.check_script(test_script)
    print(f"\nScript Test:\n{checker.get_safety_report(test_script)}")
