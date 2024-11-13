import json
from typing import Dict, List, Any
from copy import deepcopy

class ResumeSkillsTransformer:
    def __init__(self, data: Dict[str, Any]):
        self.data = deepcopy(data)
        self.skills_df = {"value": []}
        
    def merge_stages(self) -> None:
        """Merge Stage 2 and 3 attributes into Stage 1"""
        for stage in ["stage_2", "stage_3"]:
            if stage in self.data:
                for key, value in self.data[stage].items():
                    if key in self.data["stage_1"]:
                        # Merge the values - 'value' is a list
                        if isinstance(self.data["stage_1"][key].get("value", []), list):
                            self.data["stage_1"][key]["value"].extend(value.get("value", []))
    
    def transform_generic_skills(self) -> None:
        """Transform skills_generic_df data"""
        generic_skills = self.data["stage_1"].get("skills_generic_df", {}).get("value", [])
        for skill_entry in generic_skills:
            # Add main skill
            self.skills_df["value"].append({
                "skill": skill_entry["skill"],
                "type": "main",
                "score": skill_entry.get("score", 5)
            })
            # Add generic skills
            for generic_skill in skill_entry.get("skill_generic", []):
                self.skills_df["value"].append({
                    "skill": generic_skill,
                    "type": "generic",
                    "score": 5
                })

    def transform_listed_skills(self) -> None:
        """Transform skills_listed_df data"""
        listed_skills = self.data["stage_1"].get("skills_listed_df", {}).get("value", [])
        for skill_entry in listed_skills:
            # Add category skill
            self.skills_df["value"].append({
                "skill": skill_entry["skill"],
                "type": "category",
                "sub_type": "listed",
                "score": 5
            })
            # Add technology skills
            for tech in skill_entry.get("technologies", []):
                self.skills_df["value"].append({
                    "skill": tech,
                    "type": "technology",
                    "sub_type": "listed",
                    "score": 5
                })

    def transform_detailed_skills(self) -> None:
        """Transform skills_detailed_df data"""
        detailed_skills = self.data["stage_1"].get("skills_detailed_df", {}).get("value", [])
        for skill_entry in detailed_skills:
            # Add category skill
            self.skills_df["value"].append({
                "skill": skill_entry["skill"],
                "type": "category",
                "sub_type": "detailed",
                "score": 7
            })
            # Add technology skills
            for tech in skill_entry.get("technologies", []):
                self.skills_df["value"].append({
                    "skill": tech,
                    "type": "technology",
                    "sub_type": "detailed",
                    "score": 7
                })

    def transform_verified_skills(self) -> None:
        """Transform skills_verified_df data"""
        verified_skills = self.data["stage_1"].get("skills_verified_df", {}).get("value", [])
        for skill_entry in verified_skills:
            # Add high-level skill
            self.skills_df["value"].append({
                "skill": skill_entry["skill"],
                "type": "high-level",
                "sub_type": "verified",
                "score": 10
            })
            # Add technology skills
            for tech in skill_entry.get("technologies", []):
                self.skills_df["value"].append({
                    "skill": tech,
                    "type": "technology",
                    "sub_type": "verified",
                    "score": 10
                })

    def transform_alt_names(self) -> None:
        """Transform skills_alt_names_df data"""
        alt_names = self.data["stage_1"].get("skills_alt_names_df", {}).get("value", [])
        for alt_entry in alt_names:
            for alt_name in alt_entry.get("skill_alt", []):
                self.skills_df["value"].append({
                    "skill": alt_name,
                    "type": "technology",
                    "sub_type": "alt_name",
                    "score": 5
                })

    def transform_non_technical_skills(self) -> None:
        """Transform skills_non_technical_df data"""
        non_tech_skills = self.data["stage_1"].get("skills_non_technical_df", {}).get("value", [])
        for skill_entry in non_tech_skills:
            self.skills_df["value"].append({
                "skill": skill_entry["skill"],
                "type": "non-technical",
                "source": skill_entry.get("source", ""),
                "source_detail": skill_entry.get("source_detail", []),
                "score": 5
            })

    def create_integrated_json(self) -> Dict[str, Any]:
        """Create the final integrated JSON with all transformations"""
        # First merge the stages
        self.merge_stages()
        
        # Perform all skills transformations
        self.transform_non_technical_skills()
        self.transform_verified_skills()
        self.transform_detailed_skills()
        self.transform_listed_skills()
        self.transform_generic_skills()
        self.transform_alt_names()
        
        # Create new integrated JSON structure
        integrated_json = {
            "metadata": self.data.get("metadata", {}),
            "overall_evaluation": self.data.get("overall_evaluation", {}),
            "content": {
                # Include all Stage 1 data except the original skills dataframes
                **{k: v for k, v in self.data["stage_1"].items() 
                   if not k.startswith("skills_")},
                # Add the new transformed skills_df
                "skills_df": self.skills_df
            },
            "summary": self.data.get("summary", {})
        }
        
        return integrated_json
