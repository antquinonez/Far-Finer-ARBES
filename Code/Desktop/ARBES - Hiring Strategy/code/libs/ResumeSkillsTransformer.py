import json
from typing import Dict, List, Any
from copy import deepcopy
import logging
import time as time


# Configure logging
logger = logging.getLogger(__name__)

class ResumeSkillsTransformer:
    """Transforms and combines various skill evaluations into a unified format."""
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize transformer with evaluation data.
        
        Args:
            data (Dict[str, Any]): Complete evaluation data including metadata,
                                  content, and summary sections
        """
        self.data = deepcopy(data)
        self.skills_df = {"value": []}
        self.added_skills = set()  # Track added skills
        logger.debug(f"Initialized transformer with data structure: {list(data.keys())}")

    def get_stage_data(self) -> Dict:
        """Get the evaluation data from content section."""
        logger.debug(f"Getting stage data from data structure with keys: {list(self.data.keys())}")
        stage_data = self.data.get("content", {})
        logger.debug(f"Retrieved stage data: {json.dumps(stage_data, indent=2)}")
        return stage_data

    def add_skill(self, skill_dict: Dict[str, Any]) -> None:
        """Add a skill to skills_df if it hasn't been added before."""
        skill_name = skill_dict["skill"].lower()  # Normalize skill name
        
        # If skill hasn't been added before, add it
        if skill_name not in self.added_skills:
            self.skills_df["value"].append(skill_dict)
            self.added_skills.add(skill_name)
            logger.debug(f"Added new skill: {json.dumps(skill_dict, indent=2)}")
        else:
            # If skill exists and new score is higher, update the existing entry
            for existing_skill in self.skills_df["value"]:
                if existing_skill["skill"].lower() == skill_name:
                    if skill_dict.get("score", 0) > existing_skill.get("score", 0):
                        old_skill = existing_skill.copy()
                        existing_skill.update(skill_dict)
                        logger.debug(f"Updated existing skill {skill_name}")
                        logger.debug(f"Old skill: {json.dumps(old_skill, indent=2)}")
                        logger.debug(f"New skill: {json.dumps(existing_skill, indent=2)}")
                    break

    def transform_generic_skills(self) -> None:
        """Transform skills_generic_df data into standardized format."""
        stage_data = self.get_stage_data()
        
        generic_skills = stage_data.get("skills_generic_df", {}).get("value", [])

        # process foundational technology skills as additional generic_skills
        foundational_skills = stage_data.get("skills_technology_foundational_df", {}).get("value", [])
        generic_skills.extend(foundational_skills)
        
        logger.debug(f"Processing {len(generic_skills)} generic skills")
        logger.debug(f"Raw generic skills: {json.dumps(generic_skills, indent=2)}")
        
        for skill_entry in generic_skills:
            try:
                # Add main skill
                self.add_skill({
                    "skill": skill_entry["skill"],
                    "type": "main",
                    "score": skill_entry.get("score", 5)
                })
                # Add generic skills
                for generic_skill in skill_entry.get("skill_generic", []):
                    self.add_skill({
                        "skill": generic_skill,
                        "type": "generic",
                        "score": 5
                    })
            except Exception as e:
                logger.error(f"Error processing generic skill {skill_entry}: {str(e)}", 
                            exc_info=True)

    def transform_listed_skills(self) -> None:
        """Transform skills_listed_df data into standardized format."""
        stage_data = self.get_stage_data()
        listed_skills = stage_data.get("skills_listed_df", {}).get("value", [])
        logger.debug(f"Processing {len(listed_skills)} listed skills")
        logger.debug(f"Raw listed skills: {json.dumps(listed_skills, indent=2)}")
        
        for skill_entry in listed_skills:
            try:
                # Add category skill
                self.add_skill({
                    "skill": skill_entry["skill"],
                    "type": "category",
                    "sub_type": "listed",
                    "score": 5
                })
                # Add technology skills
                for tech in skill_entry.get("technologies", []):
                    self.add_skill({
                        "skill": tech,
                        "type": "technology",
                        "sub_type": "listed",
                        "score": 5
                    })
            except Exception as e:
                logger.error(f"Error processing listed skill {skill_entry}: {str(e)}", 
                            exc_info=True)

    def transform_software_skills(self) -> None:
        """Transform skills_listed_df data into standardized format."""
        stage_data = self.get_stage_data()
        listed_skills = stage_data.get("skills_software_df", {}).get("value", [])
        logger.debug(f"Processing {len(listed_skills)} software skill collections")
        logger.debug(f"Raw listed skills: {json.dumps(listed_skills, indent=2)}")
        
        for skill_entry in listed_skills:
            try:
                # Add category skill
                self.add_skill({
                    "skill": skill_entry["skill"],
                    "type": "category",
                    "sub_type": "software",
                    "score": 5
                })
                # Add technology skills
                for tech in skill_entry.get("technologies", []):
                    self.add_skill({
                        "skill": tech,
                        "type": "technology",
                        "sub_type": "software",
                        "score": 5
                    })
            except Exception as e:
                logger.error(f"Error processing listed skill {skill_entry}: {str(e)}", 
                            exc_info=True)


    def transform_detailed_skills(self) -> None:
        """Transform skills_detailed_df data into standardized format."""
        stage_data = self.get_stage_data()
        detailed_skills = stage_data.get("skills_detailed_df", {}).get("value", [])
        logger.debug(f"Processing {len(detailed_skills)} detailed skills")
        logger.debug(f"Raw detailed skills: {json.dumps(detailed_skills, indent=2)}")
        
        for skill_entry in detailed_skills:
            try:
                # Add category skill
                self.add_skill({
                    "skill": skill_entry["skill"],
                    "type": "category",
                    "sub_type": "detailed",
                    "score": 7
                })
                # Add technology skills
                for tech in skill_entry.get("technologies", []):
                    self.add_skill({
                        "skill": tech,
                        "type": "technology",
                        "sub_type": "detailed",
                        "score": 7
                    })
            except Exception as e:
                logger.error(f"Error processing detailed skill {skill_entry}: {str(e)}", 
                            exc_info=True)

    def transform_verified_skills(self) -> None:
        """Transform skills_verified_df data into standardized format."""
        stage_data = self.get_stage_data()
        verified_skills = stage_data.get("skills_verified_df", {}).get("value", [])
        logger.debug(f"Processing {len(verified_skills)} verified skills")
        logger.debug(f"Raw verified skills: {json.dumps(verified_skills, indent=2)}")
        
        for skill_entry in verified_skills:
            try:
                # Add high-level skill
                self.add_skill({
                    "skill": skill_entry["skill"],
                    "type": "high-level",
                    "sub_type": "verified",
                    "score": 10
                })
                # Add technology skills
                for tech in skill_entry.get("technologies", []):
                    self.add_skill({
                        "skill": tech,
                        "type": "technology",
                        "sub_type": "verified",
                        "score": 10
                    })
            except Exception as e:
                logger.error(f"Error processing verified skill {skill_entry}: {str(e)}", 
                            exc_info=True)

    def transform_alt_names(self) -> None:
        """Transform skills_alt_names_df data into standardized format."""
        stage_data = self.get_stage_data()
        alt_names = stage_data.get("skills_alt_names_df", {}).get("value", [])
        logger.debug(f"Processing {len(alt_names)} alternate name entries")
        
        for alt_entry in alt_names:
            # Add main skill with its score
            self.add_skill({
                "skill": alt_entry["skill"],
                "type": "main",
                "score": alt_entry.get("score", 5),
                "label": alt_entry.get("label", ""),
                "source": alt_entry.get("source", []),
                "source_detail": alt_entry.get("source_detail", [])
            })
            # Add alternate names
            for alt_name in alt_entry.get("skill_alt", []):
                self.add_skill({
                    "skill": alt_name,
                    "type": "alternate",
                    "main_skill": alt_entry["skill"],
                    "score": alt_entry.get("score", 5),
                    "label": alt_entry.get("label", ""),
                    "source": alt_entry.get("source", []),
                    "source_detail": alt_entry.get("source_detail", [])
                })

    def transform_non_technical_skills(self) -> None:
        """Transform skills_non_technical_df data into standardized format."""
        stage_data = self.get_stage_data()
        non_tech_skills = stage_data.get("skills_non_technical_df", {}).get("value", [])
        logger.debug(f"Processing {len(non_tech_skills)} non-technical skills")
        logger.debug(f"Raw non-technical skills: {json.dumps(non_tech_skills, indent=2)}")
        
        for skill_entry in non_tech_skills:
            try:
                self.add_skill({
                    "skill": skill_entry["skill"],
                    "type": "non-technical",
                    "source": skill_entry.get("source", ""),
                    "source_detail": skill_entry.get("source_detail", []),
                    "score": 5
                })
            except Exception as e:
                logger.error(f"Error processing non-technical skill {skill_entry}: {str(e)}", 
                            exc_info=True)


    def transform_eligible_roles(self) -> None:
        """Transform skills_non_technical_df data into standardized format."""
        stage_data = self.get_stage_data()
        roles = stage_data.get("eligible_roles_df", {}).get("value", [])
        logger.debug(f"Processing {len(roles)} eligible roles")
        logger.debug(f"Raw eligible roles: {json.dumps(roles, indent=2)}")
        
        for role in roles:
            logger.debug(f"roles: {roles}")
            # time.sleep(10)

            try:
                self.add_skill({
                    "skill": role["role"],
                    "type": "eligible role",
                    # "source": roles.get("source", ""),
                    # "source_detail": roles.get("source_detail", []),
                    "score": 10
                })

                # time.sleep(10)
            except Exception as e:
                logger.error(f"Error processing eligible_roles_df role {role}: {str(e)}", 
                            exc_info=True)

    def create_integrated_json(self) -> Dict[str, Any]:
        """Create the final integrated JSON with all transformations."""
        logger.info("Starting skills transformation and integration")
        
        try:
            logger.debug("Initial skills_df state:")
            logger.debug(f"skills_df: {json.dumps(self.skills_df, indent=2)}")
            
            # Perform all skills transformations
            logger.debug("Starting eligible roles transformation")
            self.transform_eligible_roles()
            
            logger.debug("Starting non-technical skills transformation")
            self.transform_non_technical_skills()
            
            logger.debug("Starting verified skills transformation")
            self.transform_verified_skills()
            
            logger.debug("Starting detailed skills transformation")
            self.transform_detailed_skills()
            
            logger.debug("Starting listed skills transformation")
            self.transform_listed_skills()

            logger.debug("Starting software skills transformation")
            self.transform_software_skills()

            logger.debug("Starting generic skills transformation")
            self.transform_generic_skills()
            
            logger.debug("Starting alternate names transformation")
            self.transform_alt_names()
            
            logger.debug(f"Transformed {len(self.skills_df['value'])} total skills")
            logger.debug(f"Final skills_df state: {json.dumps(self.skills_df, indent=2)}")
            
            # Create new integrated JSON structure with sorted content
            logger.debug("Building integrated JSON structure")
            non_skills_content = {k: v for k, v in sorted(self.data.get("content", {}).items()) 
                                if not k.startswith("skills_")}
            
            integrated_json = {
                "metadata": self.data.get("metadata", {}),
                "overall_evaluation": self.data.get("overall_evaluation", {}),
                "content": {
                    **non_skills_content,
                    "skills_df": self.skills_df
                },
                "summary": self.data.get("summary", {})
            }
            
            logger.debug("Final integrated JSON structure:")
            logger.debug(f"Keys: {list(integrated_json.keys())}")
            logger.debug(f"Content keys: {list(integrated_json['content'].keys())}")
            logger.debug(f"Number of skills: {len(integrated_json['content'].get('skills_df', {}).get('value', []))}")
            
            logger.info("Successfully created integrated JSON")
            return integrated_json
            
        except Exception as e:
            logger.error(f"Error creating integrated JSON: {str(e)}", exc_info=True)
            raise