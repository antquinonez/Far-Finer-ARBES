import os
import sys
import dearpygui.dearpygui as dpg
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))

from lib.AI.FFAnthropicCached import FFAnthropicCached
from lib.AI.FFAnthropic import FFAnthropic
from lib.AI.utils.utils import fix_json_from_codeblock, wrap_multiline


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
    response = wrap_multiline(response, width=65, initial_indent="")
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

    print(type)
    print(response)

    empty_data = [
        ["No data", "--", "--","--","--", "--"]
    ]

    table_data = response.get('evaluation', empty_data)

    # Set gui field values
    dpg.set_value("candidate_name", response['candidate_name'])
    dpg.set_value("overall_score", response['overall_score'])   

    if dpg.does_item_exist("results_table"):
        children = dpg.get_item_children("results_table")[1]
        for child in children:
            dpg.delete_item(child)
        
    for requirement, _, need_type, score, weight, evaluation in table_data:
        with dpg.table_row(parent="results_table"):
            dpg.add_text(requirement)
            # dpg.add_text(requirement_category)
            dpg.add_text(need_type)
            dpg.add_text(score)
            dpg.add_text(weight)
            dpg.add_text(evaluation)


def populate_skills_table():
    # Sample skills data - you can modify this or load from a file
    skills_data = [
        ("Entry", "Technical", "Programming", "0-2 years of practical experience"),
        ("Junior", "Technical", "Programming", "2-4 years of practical experience"),
        ("Mid", "Technical", "Programming", "4-6 years of practical experience"),
        ("Senior", "Technical", "Programming", "6-8 years of practwefwefwefwefwefwe fwe fwe f ef ical experience"),
        ("Lead", "Technical", "Programming", "8+ years of practical experience"),
        ("Entry", "Soft Skills", "Communication", "Basic writtfwefwefen and verbal communication"),
        ("Mid", "Soft Skills", "Communication", "Clear communication with team members"),
        ("Senior", "Soft Skills", "Communication", "Can communicate complex ideas effectively"),
        ("Entry", "Domain", "Industry", "Basic understanding of industry concepts"),
        ("Mid", "Domain", "Industry", "Good working knowledge of industry practices"),
        ("Senior", "Domain", "Industry", "Deep industry expertise and thought leadership")
    ]
    
    # Clear existing rows if any
    if dpg.does_item_exist("skills_table"):
        children = dpg.get_item_children("skills_table")[1]
        for child in children:
            dpg.delete_item(child)
    
    # Add new rows
    for skill_exp, _, category, definition in skills_data:
        with dpg.table_row(parent="skills_table"):
            dpg.add_text(skill_exp)
            # dpg.add_text(type_)
            dpg.add_text(category)
            dpg.add_text(definition)


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
                with dpg.group(width=400):
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
                # had been 830 for 80 char wrap
                # This is the bounding box
                with dpg.group(width=690):
                    button = dpg.add_button(
                        label="Create Role Evaluation",
                        callback=evaluate_callback,
                        width=-1,
                        height=25
                    )
                    dpg.bind_item_theme(button, global_theme)
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Evaluation Results")

                    with dpg.child_window(width=-1, height=504, border=True):
                        with dpg.group(horizontal=True):
                            # had been 600 for 80 char wrap
                            # This is the textbox for the Evaluation results
                            with dpg.child_window(width=450, height=-1, border=True):
                                dpg.add_input_text(
                                    default_value="Results will appear here after evaluation...",
                                    tag="results_text",
                                    multiline=True,
                                    readonly=False,
                                    width=-1,
                                    height=-1
                                )
                            
                            dpg.add_spacer(width=5)
                            
                            with dpg.group():
                                dpg.add_text("Candidate Name")
                                dpg.add_input_text(
                                    tag="candidate_name", 
                                    width=180,
                                    height=22
                                )
                                
                                dpg.add_spacer(height=5)
                                
                                dpg.add_text("Date")
                                dpg.add_input_text(
                                    tag="evaluation_date",
                                    default_value=date.today().strftime("%Y-%m-%d"),
                                    width=180,
                                    height=22
                                )
                                
                                dpg.add_spacer(height=5)
                                
                                dpg.add_text("Overall Score (To Role)")
                                dpg.add_input_text(
                                    tag="overall_score", 
                                    width=180,
                                    height=22
                                )
            
            dpg.add_spacer(height=10)
            
            # Detailed Analysis table
            dpg.add_text("Detailed Analysis")
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
                    dpg.add_table_column(label="Requirement", width_fixed=True, init_width_or_weight=250)
                    # dpg.add_table_column(label="Requirement Category", width_fixed=True, init_width_or_weight=250)
                    dpg.add_table_column(label="Need Type", width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label="Score", width_fixed=True, init_width_or_weight=55)
                    dpg.add_table_column(label="Weight", width_fixed=True, init_width_or_weight=55)
                    dpg.add_table_column(label="Evaluation", width_fixed=False, init_width_or_weight=550)
                    
                    with dpg.table_row():
                        dpg.add_text("Awaiting evaluation...")
                        dpg.add_text("")
                        dpg.add_text("")
                        dpg.add_text("")
                        dpg.add_text("")
                        dpg.add_text("")
        
        # Right side - Skills Table
        with dpg.group():
            dpg.add_text("Skills Definition")
            with dpg.child_window(width=-1, height=875, border=True):
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
                    dpg.add_table_column(label="Skill Experience", width_fixed=True, init_width_or_weight=130)
                    # dpg.add_table_column(label="Type", width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label="Category", width_fixed=True, init_width_or_weight=100)
                    dpg.add_table_column(label="Definition/Explanation", width_fixed=False, init_width_or_weight=150)

# Populate the skills table with initial data
populate_skills_table()

# Setup viewport and show
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()