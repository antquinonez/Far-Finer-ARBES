import os
import sys
import dearpygui.dearpygui as dpg
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))

from lib.AI.FFAnthropicCached import FFAnthropicCached
from lib.AI.FFAnthropic import FFAnthropic
from lib.AI.utils.utils import fix_json_from_codeblock, wrap_multiline


def sort_by_sec_first_element(lst):
    return sorted(lst, key=lambda x: (x[1], x[0]))

def evaluate_callback():
    resume_text = dpg.get_value("resume_input")
    job_text = dpg.get_value("job_description_input")

    # ========================================================================================
    # PERFORM THE GENERAL EVALUATION 
    # ========================================================================================
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    grandparent_dir = os.path.dirname(parent_dir)
    great_grandparent_dir = os.path.dirname(grandparent_dir)

    system_instr_gen_candidate_eval_role = 'system_instructions_gen_candidate_evaluation_role.md'
    system_instr_det_candidate_eval_role = 'system_instructions_det_candidate_evaluation_role.md'
    
    sys_ins_gen_can_eval_role_fpath = os.path.join(great_grandparent_dir, 'Prompts', system_instr_gen_candidate_eval_role)
    sys_ins_det_can_eval_role_fpath = os.path.join(great_grandparent_dir, 'Prompts', system_instr_det_candidate_eval_role)
    
    # Read the file
    with open(sys_ins_gen_can_eval_role_fpath, 'r') as file:
        system_instructions = file.read()

    config_lmodel = {
        'model': "claude-3-5-sonnet-latest",
        'system_instructions': system_instructions
    }

    ai = FFAnthropic(config=config_lmodel)

    request = f"""Please evaluate this RESUME against the JOB DESCRIPTION.
    JOB DESCRIPTION
    ===============
    {job_text}

    =====================================================================================    
    The RESUME
    ===============
    {resume_text}
    """

    # indent and word wrap
    response = ai.generate_response(request)
    response = wrap_multiline(response, width=80, initial_indent="")
    dpg.set_value("results_text", response)
    
    # ========================================================================================
    # PERFORM THE DETAILED EVALUATION 
    # ========================================================================================
    with open(sys_ins_det_can_eval_role_fpath, 'r') as file:
        system_instructions = file.read()

    config_lmodel = {
        'model': "claude-3-5-sonnet-latest",
        'system_instructions': system_instructions
    }

    ai = FFAnthropic(config=config_lmodel)

    request = f"""Please evaluate this RESUME against the JOB DESCRIPTION.
    JOB DESCRIPTION
    ===============
    {job_text}

    =====================================================================================
    The RESUME
    ===============
    {resume_text}
    """

    response = ai.generate_response(request) 
    response = fix_json_from_codeblock(response)

    # print(type)
    print(response)

    # POPULATE DETAILED ANALYSIS  ==========================================================================
    empty_data = [ ]

    evaluation_main_data = response.get('evaluation_main', empty_data)
    evaluation_technical_data = response.get('evaluation_technical', empty_data)
    evaluation_database_data = response.get('evaluation_database', empty_data)
    evaluation_programming_data = response.get('evaluation_programming', empty_data)
    evaluation_management_data = response.get('evaluation_management', empty_data)
    evaluation_credentials_data = response.get('evaluation_credentials', empty_data)
    evaluation_other_data = response.get('evaluation_other', empty_data)

    detailed_analysis_data = evaluation_main_data + evaluation_technical_data + evaluation_database_data + evaluation_programming_data + evaluation_management_data + evaluation_credentials_data + evaluation_other_data


    detailed_analysis_data = sort_by_sec_first_element(detailed_analysis_data)
    print(detailed_analysis_data)

    # Set gui field values
    dpg.set_value("candidate_name", response['candidate_name'])
    dpg.set_value("overall_score", response['overall_score'])   

    if dpg.does_item_exist("results_table"):
        children = dpg.get_item_children("results_table")[1]
        for child in children:
            dpg.delete_item(child)
        
    for requirement, requirement_category, need_type, score, weight, evaluation in detailed_analysis_data:
        with dpg.table_row(parent="results_table"):
            dpg.add_text(requirement)
            dpg.add_text(requirement_category)
            dpg.add_text(need_type)
            dpg.add_text(score)
            dpg.add_text(weight)
            dpg.add_text(evaluation)


    # SKILLS DATA =============================================================================
    empty_data = []
    skills_data = response.get('skills', empty_data)
    technologies_data = response.get('technologies', empty_data)
    job_title_data = response.get('job_title', empty_data)
    job_function_data = response.get('job_function', empty_data)
    certificates_data = response.get('certificates', empty_data)
    education_data = response.get('education', empty_data)

    all_exp_data = skills_data + technologies_data + job_title_data + job_function_data + certificates_data + education_data
    
    all_exp_data = sort_by_sec_first_element(all_exp_data)
    # print(f"skills_data: {all_exp_data}")

    # Clear existing rows if any
    if dpg.does_item_exist("skills_table"):
        children = dpg.get_item_children("skills_table")[1]
        for child in children:
            dpg.delete_item(child)
    
    # Add new rows
    for skill_exp, category, description in all_exp_data:
        with dpg.table_row(parent="skills_table"):
            dpg.add_text(skill_exp)
            dpg.add_text(category)
            dpg.add_text(description)


# Initialize DearPyGUI
dpg.create_context()
dpg.create_viewport(title="Resume Evaluation", width=1800, height=950)

# Add theme and color configurations
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button, [41, 120, 204])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [54, 141, 227])
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [27, 98, 171])
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 6)

# Create the main window
with dpg.window(label="Resume Evaluation", tag="primary_window", width=1800, height=900):
    # Main horizontal layout
    with dpg.group(horizontal=True):
        # Left group containing existing content
        with dpg.group():
            # Main horizontal layout with fixed widths
            with dpg.group(horizontal=True):
                # Left side - Resume and Job Description (fixed width)
                with dpg.group(width=490):
                    dpg.add_text("Resume Text")
                    with dpg.child_window(width=-1, height=250, border=True):
                        dpg.add_input_text(
                            tag="resume_input",
                            multiline=True,
                            width=-1,
                            height=-1
                        )
                    
                    dpg.add_spacer(height=10)
                    
                    dpg.add_text("Job Description")
                    with dpg.child_window(width=-1, height=250, border=True):
                        dpg.add_input_text(
                            tag="job_description_input",
                            multiline=True,
                            width=-1,
                            height=-1
                        )
                
                # Right side - Evaluation
                # text box
                with dpg.group(width=600):
                    button = dpg.add_button(
                        label="Create Role Evaluation",
                        callback=evaluate_callback,
                        width=500,
                        height=25
                    )
                    dpg.bind_item_theme(button, global_theme)
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Evaluation Results")

                    # Evaluation Results Frame
                    with dpg.child_window(width=500, height=503, border=True):
                        # Add candidate info group horizontally at the top
                        with dpg.group(horizontal=True):
                            with dpg.group():
                                dpg.add_text("Candidate Name")
                                dpg.add_input_text(
                                    tag="candidate_name", 
                                    width=240,
                                    height=22
                                )
                            
                            dpg.add_spacer(width=10)
                            
                            with dpg.group():
                                dpg.add_text("Overall Score (To Role)")
                                dpg.add_input_text(
                                    tag="overall_score", 
                                    width=200,
                                    height=22
                                )
                        
                        dpg.add_spacer(height=5)
                        
                        # Results text box
                        dpg.add_input_text(
                            default_value="Results will appear here after evaluation...",
                            tag="results_text",
                            multiline=True,
                            readonly=False,
                            width=580,
                            height=-1
                        )
            
            dpg.add_spacer(height=10)
            
            # Detailed Analysis table
            dpg.add_text("Detailed Evaluation")
            # had been 1390 for a while
            with dpg.child_window(width=1100, height=300, border=True):
                with dpg.table(
                    tag="results_table",
                    header_row=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    scrollY=True,
                    freeze_rows=1,
                    width=-1
                ):
                    dpg.add_table_column(label="Requirement", width_fixed=True, init_width_or_weight=220)
                    dpg.add_table_column(label="Category", width_fixed=True, init_width_or_weight=130)
                    dpg.add_table_column(label="Need Type", width_fixed=True, init_width_or_weight=75)
                    dpg.add_table_column(label="Score", width_fixed=True, init_width_or_weight=48)
                    dpg.add_table_column(label="Weight", width_fixed=True, init_width_or_weight=49)
                    dpg.add_table_column(label="Evaluation", width_fixed=False, init_width_or_weight=560)
                    
                    with dpg.table_row():
                        dpg.add_text("Awaiting evaluation...")
                        dpg.add_text("")
                        dpg.add_text("")
                        dpg.add_text("")
                        dpg.add_text("")
                        dpg.add_text("")
        
        # Right side - Skills Table
        with dpg.group():
            dpg.add_text("Candidate Background")
            with dpg.child_window(width=-1, height=881, border=True):
                with dpg.table(
                    tag="skills_table",
                    header_row=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    scrollY=True,
                    # scrollX=True,
                    freeze_rows=0,
                    width=-1
                ):
                    dpg.add_table_column(label="Skill/Experience", width_fixed=True, init_width_or_weight=130)
                    dpg.add_table_column(label="Category", width_fixed=True, init_width_or_weight=130)
                    dpg.add_table_column(label="Description", width_fixed=False, init_width_or_weight=200)


# Setup viewport and show
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()