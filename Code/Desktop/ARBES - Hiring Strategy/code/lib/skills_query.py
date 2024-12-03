from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
import chromadb
import json
import os
import pandas as pd

distance_threshold = .6


def create_skills_matrix_with_distances(skills_dict):
    """
    Create a DataFrame showing the best (smallest) distance scores between entities and skills 
    based on ChromaDB similarity search.
    
    Args:
        skills_dict (dict): Dictionary of skills categorized by priority level
                           Format: {
                               'Critical': ['skill1', 'skill2'],
                               'Required': ['skill3', 'skill4'],
                               'Preferred': ['skill5', 'skill6'],
                               'Optional': ['skill7', 'skill8']
                           }
        
    Returns:
        pandas.DataFrame: Matrix of entities and their best skill distances with priority level prefixes
    """
    # Load environment variables
    load_dotenv()

    # Initialize ChromaDB client with persistence
    client = chromadb.PersistentClient(path="../entity_skills_db")

    # Initialize the OpenAI embedding function
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-large"
    )

    # Get existing collection
    collection = client.get_collection(
        name="entity_skills",
        embedding_function=embedding_function
    )

    # Get the total count of items in the collection
    collection_size = collection.count()

    # Dictionary to store all results
    all_entity_skills = {}
    
    # Create a mapping of all skills to their priority levels
    skill_priority_map = {
        skill: priority
        for priority, skills in skills_dict.items()
        for skill in skills
    }
    
    # Get all skills across all priority levels
    all_skills = [skill for skills in skills_dict.values() for skill in skills]
    
    # Query each skill
    for skill in all_skills:
        results = collection.query(
            query_texts=[skill],
            n_results=collection_size,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results for this skill
        for entity_metadata, distance in zip(
            results['metadatas'][0],
            results['distances'][0]
        ):
            entity_id = entity_metadata.get('entity_name')
            
            # Initialize dictionary for new entity if needed
            if entity_id not in all_entity_skills:
                all_entity_skills[entity_id] = {}
            
            # Get the column name
            priority = skill_priority_map[skill]
            column_name = f"{priority}_{skill}"
            
            # Update the distance if it's either not set yet or if this one is smaller
            current_distance = all_entity_skills[entity_id].get(column_name, None)
            if current_distance is None or distance < current_distance:
                all_entity_skills[entity_id][column_name] = round(distance, 2)
    
    # Convert to DataFrame
    df = pd.DataFrame.from_dict(all_entity_skills, orient='index')
    
    # Reset index and rename it to entity_id
    df.index.name = 'entity_id'
    df.reset_index(inplace=True)
    
    return df

def calculate_scores(df):
    """
    Calculate scores for priority columns while preserving other columns.
    Adds total score and rank columns, sorts by total score descending.
    
    Rules:
    - 'Critical' prefix & True value = 20
    - 'Required' prefix & True value = 10
    - 'Preferred' prefix & True value = 7
    - 'Optional' prefix & True value = 3
    - All other columns preserved as-is
    - 'total_priority_score' column added with sum of priority scores
    - 'rank' column added based on total_priority_score
    - Result sorted by total_priority_score descending
    
    Parameters:
    df (pandas.DataFrame): Input DataFrame with boolean columns
    
    Returns:
    pandas.DataFrame: New DataFrame with scores, total, and rank
    """
    # Define priority prefixes
    priority_prefixes = ['Critical', 'Required', 'Preferred', 'Optional']
    
    # Create a copy of the input DataFrame
    result_df = df.copy()
    
    # Track which columns are priority columns for summing later
    priority_columns = []
    
    # Process each column in the source DataFrame
    for col in df.columns:
        # Check if column starts with any of our priority prefixes
        if any(col.startswith(prefix) for prefix in priority_prefixes):
            new_values = pd.Series(0, index=df.index)
            
            if col.startswith('Critical'):
                new_values[df[col]] = 20
            elif col.startswith('Required'):
                new_values[df[col]] = 10
            elif col.startswith('Preferred'):
                new_values[df[col]] = 7
            elif col.startswith('Optional'):
                new_values[df[col]] = 3
                
            result_df[col] = new_values
            priority_columns.append(col)
    
    # Add total column that sums only priority-based scores
    result_df['total_priority_score'] = result_df[priority_columns].sum(axis=1)
    
    # Sort by total_priority_score descending
    result_df = result_df.sort_values('total_priority_score', ascending=False)
    
    # Add rank column (1-based ranking)
    result_df['rank'] = range(1, len(result_df) + 1)
    
    # Reorder columns to put rank first, then entity_id, then rest
    cols = ['rank', 'entity_id'] + [col for col in result_df.columns if col not in ['rank', 'entity_id']]
    result_df = result_df[cols]
    
    return result_df

def create_skills_matrix(skills_dict, distance_threshold=distance_threshold):
    """
    Create a DataFrame showing which entities possess which skills based on ChromaDB similarity search.
    Skills are categorized by priority level and reflected in column names.
    
    Args:
        skills_dict (dict): Dictionary of skills categorized by priority level
                           Format: {
                               'Critical': ['skill1', 'skill2'],
                               'Required': ['skill3', 'skill4'],
                               'Preferred': ['skill5', 'skill6'],
                               'Optional': ['skill7', 'skill8']
                           }
        distance_threshold (float): Maximum distance to consider a skill match (default: .8)
        
    Returns:
        pandas.DataFrame: Matrix of entities and their skills with priority level prefixes
    """
    # Load environment variables
    load_dotenv()

    # Initialize ChromaDB client with persistence
    client = chromadb.PersistentClient(path="../entity_skills_db")

    # Initialize the OpenAI embedding function
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-large"
    )

    try:
        # Get existing collection
        collection = client.get_collection(
            name="entity_skills",
            embedding_function=embedding_function
        )

        # Get the total count of items in the collection
        collection_size = collection.count()
        
        # Dictionary to store all results
        all_entity_skills = {}
        
        # Create a mapping of all skills to their priority levels
        skill_priority_map = {
            skill: priority
            for priority, skills in skills_dict.items()
            for skill in skills
        }
        
        # Get all skills across all priority levels
        all_skills = [skill for skills in skills_dict.values() for skill in skills]
        
        # Query each skill
        for skill in all_skills:
            results = collection.query(
                query_texts=[skill],
                n_results=collection_size,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results for this skill
            for entity_metadata, distance in zip(
                results['metadatas'][0],
                results['distances'][0]
            ):
                entity_id = entity_metadata.get('entity_name')
                
                # Initialize entity in dictionary if not present
                if entity_id not in all_entity_skills:
                    # Initialize with prefixed column names
                    all_entity_skills[entity_id] = {
                        f"{priority}_{skill}": False
                        for priority, skills in skills_dict.items()
                        for skill in skills
                    }
                
                # Mark skill as True if distance is below threshold
                if distance < distance_threshold:
                    priority = skill_priority_map[skill]
                    all_entity_skills[entity_id][f"{priority}_{skill}"] = True
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(all_entity_skills, orient='index')
        
        # Reset index and rename it to entity_id
        df.index.name = 'entity_id'
        df.reset_index(inplace=True)
        
        return df

    except Exception as e:
        print(f"Error accessing collection: {str(e)}")
        raise


def summarize_create_skills_matrix(df):
    """
    Analyzes a dataframe containing requirement columns and adds summary statistics columns.
    Returns a new dataframe with entity_id as first column followed by analysis columns.
    
    Parameters:
    df (pandas.DataFrame): DataFrame with requirement columns (Critical_, Required_, etc.)
                         and an entity_id column
    
    Returns:
    pandas.DataFrame: Original data with additional analysis columns
    """
    # Create a copy to avoid modifying the original DataFrame
    result = df.copy()
    
    # Define the requirement categories and their prefixes
    categories = {
        'Critical': 'Critical_',
        'Required': 'Required_',
        'Preferred': 'Preferred_',
        'Optional': 'Optional_'
    }
    
    # For each category, create summary columns
    for category, prefix in categories.items():
        # Get all columns for this category
        category_cols = [col for col in df.columns if col.startswith(prefix)]
        
        if category_cols:
            # Calculate if all requirements are met
            result[f'{category.lower()}_all_met'] = result[category_cols].all(axis=1)
            
            # Calculate ratio of requirements met
            met_count = result[category_cols].sum(axis=1)
            total_count = len(category_cols)
            result[f'{category.lower()}_ratio_met'] = met_count.astype(str) + '/' + str(total_count)
            
            # Calculate percentage of requirements met
            result[f'{category.lower()}_percent_met'] = (met_count / total_count * 100).round(1)
    
    # Reorder columns to put entity_id first, followed by analysis columns, then the rest
    analysis_cols = [col for col in result.columns if any(
        x in col for x in ['_all_met', '_ratio_met', '_percent_met']
    )]
    other_cols = [col for col in result.columns if col not in analysis_cols and col != 'entity_id']
    
    # Construct final column order
    final_cols = ['entity_id'] + analysis_cols + other_cols
    
    # Reorder columns
    result = result[final_cols]
    
    return result    



def create_skills_skill_matrix(skills_dict, distance_threshold=distance_threshold):
    """
    Create a DataFrame showing which entities possess which skills based on ChromaDB similarity search.
    Returns the actual matching skill text from the database instead of boolean values.
    
    Args:
        skills_dict (dict): Dictionary of skills categorized by priority level
                           Format: {
                               'Critical': ['skill1', 'skill2'],
                               'Required': ['skill3', 'skill4'],
                               'Preferred': ['skill5', 'skill6'],
                               'Optional': ['skill7', 'skill8']
                           }
        distance_threshold (float): Maximum distance to consider a skill match (default: .8)
        
    Returns:
        pandas.DataFrame: Matrix of entities and their skills with priority level prefixes,
                        containing the actual matching skill text instead of boolean values
    """
    # Load environment variables
    load_dotenv()

    # Initialize ChromaDB client with persistence
    client = chromadb.PersistentClient(path="../entity_skills_db")

    # Initialize the OpenAI embedding function
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-large"
    )

    try:
        # Get existing collection
        collection = client.get_collection(
            name="entity_skills",
            embedding_function=embedding_function
        )

        # Get the total count of items in the collection
        collection_size = collection.count()
        
        # Dictionary to store all results
        all_entity_skills = {}
        
        # Create a mapping of all skills to their priority levels
        skill_priority_map = {
            skill: priority
            for priority, skills in skills_dict.items()
            for skill in skills
        }
        
        # Get all skills across all priority levels
        all_skills = [skill for skills in skills_dict.values() for skill in skills]
        
        # Query each skill
        for skill in all_skills:
            results = collection.query(
                query_texts=[skill],
                n_results=collection_size,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results for this skill
            for doc, entity_metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                entity_id = entity_metadata.get('entity_name')
                
                # Initialize entity in dictionary if not present
                if entity_id not in all_entity_skills:
                    # Initialize with empty lists for each skill
                    all_entity_skills[entity_id] = {
                        f"{priority}_{skill}": []
                        for priority, skills in skills_dict.items()
                        for skill in skills
                    }
                
                # Add skill text to list if distance is below threshold
                if distance < distance_threshold:
                    priority = skill_priority_map[skill]
                    all_entity_skills[entity_id][f"{priority}_{skill}"].append(doc)
        
        # Convert lists to comma-separated strings
        for entity_id in all_entity_skills:
            for column in all_entity_skills[entity_id]:
                skills_list = all_entity_skills[entity_id][column]
                all_entity_skills[entity_id][column] = '; '.join(skills_list) if skills_list else ''
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(all_entity_skills, orient='index')
        
        # Reset index and rename it to entity_id
        df.index.name = 'entity_id'
        df.reset_index(inplace=True)
        
        return df

    except Exception as e:
        print(f"Error accessing collection: {str(e)}")
        raise