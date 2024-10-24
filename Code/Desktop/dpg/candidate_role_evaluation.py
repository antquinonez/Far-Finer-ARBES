import os
import sys
import dearpygui.dearpygui as dpg

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
    

    # Then read the file
    with open(sys_ins_gen_can_eval_role_fpath, 'r') as file:
        system_instructions = file.read()

    config_lmodel = {
        'model': "claude-3-5-sonnet-latest",
        'system_instructions': system_instructions
    }

    ai= FFAnthropic(config=config_lmodel)

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
    response = wrap_multiline(response, initial_indent="")

   
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

    ai= FFAnthropic(config=config_lmodel)

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

    if dpg.does_item_exist("results_table"):
        children = dpg.get_item_children("results_table")[1]
        for child in children:
            dpg.delete_item(child)
        
    for requirement,requirement_category, need_type, score, weight, evaluation in table_data:
        with dpg.table_row(parent="results_table"):
            dpg.add_text(requirement)
            dpg.add_text(requirement_category)
            dpg.add_text(need_type)
            dpg.add_text(score)
            dpg.add_text(weight)
            dpg.add_text(evaluation)

# Initialize DearPyGUI
dpg.create_context()
dpg.create_viewport(title="Resume Evaluation", width=1400, height=800)

# Create the main window
with dpg.window(label="Resume Evaluation", tag="primary_window", width=1400, height=800):
    # Main horizontal layout
    with dpg.group(horizontal=True):
        # Left side - Resume and Job Description
        with dpg.group(width=700):
            # Resume Text
            dpg.add_text("Resume Text")
            with dpg.child_window(width=-1, height=250, border=True):
                dpg.add_input_text(
                    tag="resume_input",
                    multiline=True,
                    width=-1,
                    height=-1
                )
            
            dpg.add_spacer(height=10)
            
            # Job Description
            dpg.add_text("Job Description")
            with dpg.child_window(width=-1, height=250, border=True):
                dpg.add_input_text(
                    tag="job_description_input",
                    multiline=True,
                    width=-1,
                    height=-1
                )
        
        dpg.add_spacer(width=10)
        
        # Right side - Evaluation ==========================================================
        with dpg.group(width=630):
            # Evaluate button at top
            dpg.add_button(
                label="Create Role Evaluation",
                callback=evaluate_callback,
                width=120,
                height=25
            )
            
            dpg.add_spacer(height=5)
            
            # Evaluation Results - Changed to input_text
            dpg.add_text("Evaluation Results")
            with dpg.child_window(width=-1, height=500, border=True):
                dpg.add_input_text(
                    default_value="Results will appear here after evaluation...",
                    tag="results_text",
                    multiline=True,
                    readonly=False,
                    width=-1,
                    height=-1
                )
    
    dpg.add_spacer(height=10)
    
    # Detailed Analysis table spanning full width
    dpg.add_text("Detailed Analysis")
    with dpg.child_window(width=-1, height=300, border=True):
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
            # Define columns
            dpg.add_table_column(label="Requirement", width_fixed=True, init_width_or_weight=250)
            dpg.add_table_column(label="Requirement Category", width_fixed=True, init_width_or_weight=250)
            dpg.add_table_column(label="Need Type", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Score", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Weight", width_fixed=True, init_width_or_weight=75)
            dpg.add_table_column(label="Evaluation", width_fixed=False, init_width_or_weight=550)
            
            # Initial row
            with dpg.table_row():
                dpg.add_text("Awaiting evaluation...")
                dpg.add_text("")
                dpg.add_text("")
                dpg.add_text("")
                dpg.add_text("")
                dpg.add_text("")

# Setup viewport and show
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()