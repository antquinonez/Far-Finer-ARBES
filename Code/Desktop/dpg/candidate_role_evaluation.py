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
dpg.create_viewport(title="Resume Evaluation", width=1400, height=900)

# Add theme and color configurations
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button, [41, 120, 204])  # Blue color for normal state
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [54, 141, 227])  # Lighter blue for hover
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [27, 98, 171])  # Darker blue for click
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)  # Rounded corners
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 6)  # Padding

# Create the main window
with dpg.window(label="Resume Evaluation", tag="primary_window", width=900, height=900):
    # Main horizontal layout with fixed widths
    with dpg.group(horizontal=True):
        # Left side - Resume and Job Description (fixed width)
        with dpg.group(width=550):
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
        with dpg.group(width=800):
            # Button at top
            button = dpg.add_button(
                label="Create Role Evaluation",
                callback=evaluate_callback,
                width=-1,
                height=25
            )
            dpg.bind_item_theme(button, global_theme)
            
            dpg.add_spacer(height=5)
            dpg.add_text("Evaluation Results")

            # Results area with box around both text and fields
            with dpg.child_window(width=-1, height=504, border=True):
                with dpg.group(horizontal=True):
                    # Results text box
                    with dpg.child_window(width=600, height=-1, border=True):
                        dpg.add_input_text(
                            default_value="Results will appear here after evaluation...",
                            tag="results_text",
                            multiline=True,
                            readonly=False,
                            width=-1,
                            height=-1
                        )
                    
                    dpg.add_spacer(width=5)
                    
                    # Info fields group
                    with dpg.group():
                        # Candidate Name
                        dpg.add_text("Candidate Name")
                        dpg.add_input_text(
                            tag="candidate_name", 
                            width=150,
                            height=22
                        )
                        
                        dpg.add_spacer(height=5)
                        
                        # Date
                        dpg.add_text("Date")
                        dpg.add_input_text(
                            tag="evaluation_date",
                            default_value=date.today().strftime("%Y-%m-%d"),
                            width=150,
                            height=22
                        )
                        
                        dpg.add_spacer(height=5)
                        
                        # Overall Score
                        dpg.add_text("Overall Score")
                        dpg.add_input_text(
                            tag="overall_score", 
                            width=150,
                            height=22
                        )
    
    dpg.add_spacer(height=10)
    
    # Detailed Analysis table
    dpg.add_text("Detailed Analysis")
    with dpg.child_window(width=-1, height=250, border=True):
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
            dpg.add_table_column(label="Requirement Category", width_fixed=True, init_width_or_weight=250)
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

# Setup viewport and show
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()