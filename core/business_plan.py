"""Structured business-plan data with explicit provenance categories."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BusinessPlan:
    title: str
    user_inputs: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    calculations: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        for item in self.evidence:
            if not item.get("source"):
                raise ValueError("every evidence item requires source")

