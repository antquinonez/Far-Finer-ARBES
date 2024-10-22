import dearpygui.dearpygui as dpg

def evaluate_callback():
    resume_text = dpg.get_value("resume_input")
    job_text = dpg.get_value("job_description_input")
    
    sample_result = "Evaluation Results:\n\n" + \
                   "Summary Analysis:\n" + \
                   "- Found relevant experience in Python development\n" + \
                   "- Strong match in database knowledge\n" + \
                   "- Communication skills evident in resume"
    
    dpg.set_value("results_text", sample_result)
    
    if dpg.does_item_exist("results_table"):
        children = dpg.get_item_children("results_table")[1]
        for child in children:
            dpg.delete_item(child)
    
    # Extended sample data to demonstrate scrolling
    table_data = [
        ["Skills Match", "75%", "Strong"],
        ["Experience Level", "Senior", "Perfect Match"],
        ["Education", "Masters", "Exceeds"],
        ["Technical Skills", "8/10", "Strong"],
        ["Soft Skills", "9/10", "Excellent"],
        ["Leadership", "7/10", "Good"],
        ["Project Experience", "85%", "Strong"],
        ["Industry Knowledge", "70%", "Good"],
        ["Tool Proficiency", "90%", "Excellent"],
        ["Certifications", "3/4", "Good"],
        ["Communication", "95%", "Excellent"],
        ["Problem Solving", "85%", "Strong"],
        ["Team Collaboration", "90%", "Excellent"],
        ["Time Management", "80%", "Good"],
        ["Experience Level", "Senior", "Perfect Match"],
        ["Education", "Masters", "Exceeds"],
        ["Technical Skills", "8/10", "Strong"],
        ["Soft Skills", "9/10", "Excellent"],
        ["Leadership", "7/10", "Good"],
        ["Project Experience", "85%", "Strong"],
        ["Industry Knowledge", "70%", "Good"],
        ["Tool Proficiency", "90%", "Excellent"],
        ["Certifications", "3/4", "Good"],
        ["Communication", "95%", "Excellent"],
        ["Problem Solving", "85%", "Strong"],
        ["Team Collaboration", "90%", "Excellent"],
        ["Adaptability", "88%", "Strong"]
    ]
    
    for category, score, assessment in table_data:
        with dpg.table_row(parent="results_table"):
            dpg.add_text(category)
            dpg.add_text(score)
            dpg.add_text(assessment)

def update_strategy_job_description():
    job_text = dpg.get_value("job_description_input")
    dpg.set_value("strategy_job_text", job_text)

def evaluate_strategy():
    if dpg.does_item_exist("strategy_results_table"):
        children = dpg.get_item_children("strategy_results_table")[1]
        for child in children:
            dpg.delete_item(child)
    
    # Sample strategy evaluation data
    strategy_data = [
        ["Role Understanding", "95%", "Excellent"],
        ["Technical Preparation", "85%", "Strong"],
        ["Company Research", "90%", "Excellent"],
        ["Experience Alignment", "88%", "Strong"],
        ["Project Examples", "92%", "Excellent"],
        ["Skills Demonstration", "87%", "Strong"],
        ["Cultural Fit", "93%", "Excellent"],
        ["Soft Skills", "9/10", "Excellent"],
        ["Leadership", "7/10", "Good"],
        ["Project Experience", "85%", "Strong"],
        ["Industry Knowledge", "70%", "Good"],
        ["Tool Proficiency", "90%", "Excellent"],
        ["Certifications", "3/4", "Good"],
        ["Communication", "95%", "Excellent"],
        ["Problem Solving", "85%", "Strong"],
        ["Team Collaboration", "90%", "Excellent"],
        ["Time Management", "80%", "Good"],
        ["Experience Level", "Senior", "Perfect Match"],
        ["Education", "Masters", "Exceeds"],
        ["Technical Skills", "8/10", "Strong"],
        ["Soft Skills", "9/10", "Excellent"],
        ["Leadership", "7/10", "Good"],
        ["Project Experience", "85%", "Strong"],
        ["Industry Knowledge", "70%", "Good"],
        ["Tool Proficiency", "90%", "Excellent"],
        ["Question Preparation", "89%", "Strong"],
        ["Achievement Highlights", "91%", "Excellent"],
        ["Problem Solving Examples", "86%", "Strong"],
        ["Leadership Experience", "84%", "Strong"],
        ["Communication Strategy", "94%", "Excellent"],
        ["Salary Discussion", "88%", "Strong"],
        ["Career Goals", "92%", "Excellent"],
        ["Growth Potential", "90%", "Excellent"]
    ]
    
    for category, score, assessment in strategy_data:
        with dpg.table_row(parent="strategy_results_table"):
            dpg.add_text(category)
            dpg.add_text(score)
            dpg.add_text(assessment)

# Initialize DearPyGUI
dpg.create_context()
dpg.create_viewport(title="Multi-Feature Application", width=1400, height=800)

# Create the main window
with dpg.window(label="Multi-Feature Application", tag="primary_window"):
    with dpg.tab_bar():
        # Tab 1 - Resume Matcher
        with dpg.tab(label="Resume Matcher"):
            with dpg.group(horizontal=True):
                # Left side - Stacked inputs and button
                with dpg.group(width=400):
                    # Resume input
                    dpg.add_text("Resume Text")
                    with dpg.child_window(height=290):
                        dpg.add_input_text(
                            tag="resume_input",
                            multiline=True,
                            width=-1,
                            height=-1
                        )
                    
                    dpg.add_spacer(height=10)
                    
                    # Job Description input
                    dpg.add_text("Job Description")
                    with dpg.child_window(height=290):
                        dpg.add_input_text(
                            tag="job_description_input",
                            multiline=True,
                            width=-1,
                            height=-1,
                            callback=update_strategy_job_description
                        )
                    
                    dpg.add_spacer(height=10)
                    
                    # Evaluate button below text boxes
                    dpg.add_button(
                        label="Evaluate Match",
                        callback=evaluate_callback,
                        width=-1,
                        height=40
                    )
                
                dpg.add_spacer(width=10)
                
                # Right side - Results with fixed header table
                with dpg.group():
                    dpg.add_text("Evaluation Results")
                    # Summary section
                    with dpg.child_window(height=150):
                        dpg.add_text(
                            tag="results_text",
                            default_value="Results will appear here after evaluation...",
                            wrap=600
                        )
                    
                    dpg.add_spacer(height=5)
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    
                    # Table section with fixed header
                    dpg.add_text("Detailed Analysis")
                    
                    # Create a child window to contain the table with scrolling
                    with dpg.child_window(height=450):
                        # Table with fixed header
                        with dpg.table(tag="results_table", 
                                    header_row=True,
                                    borders_innerH=True,
                                    borders_outerH=True,
                                    borders_innerV=True,
                                    borders_outerV=True,
                                    resizable=True,
                                    scrollY=True,
                                    freeze_rows=1,
                                    height=-1):
                            
                            # Define columns
                            dpg.add_table_column(label="Category", width_fixed=True, init_width_or_weight=200)
                            dpg.add_table_column(label="Score", width_fixed=True, init_width_or_weight=150)
                            dpg.add_table_column(label="Assessment", width_fixed=True, init_width_or_weight=200)
                            
                            # Initial empty row
                            with dpg.table_row():
                                dpg.add_text("Awaiting evaluation...")
                                dpg.add_text("-")
                                dpg.add_text("-")

        # Tab 2 - Strategy Evaluations
        with dpg.tab(label="Strategy Evaluations"):
            dpg.add_text("Develop and evaluate your interview strategy based on the job description:")
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                # Left column - Job Description (Read-only)
                with dpg.group(width=400):  # Fixed width to match Tab 1
                    dpg.add_text("Job Description (from Tab 1)")
                    with dpg.child_window(height=600):
                        dpg.add_input_text(
                            tag="strategy_job_text",
                            multiline=True,
                            width=-1,
                            height=580,
                            readonly=True
                        )
                    
                    # Moved button here, below the job description
                    dpg.add_spacer(height=10)
                    dpg.add_button(
                        label="Evaluate Strategies",
                        callback=evaluate_strategy,
                        width=-1,  # Make button width match container
                        height=40
                    )
                
                dpg.add_spacer(width=10)
                
                # Right column - Results Table
                with dpg.group():
                    dpg.add_text("Strategy Analysis")
                    # Create a child window to contain the table with scrolling
                    with dpg.child_window(height=600):
                        # Table with fixed header
                        with dpg.table(tag="strategy_results_table", 
                                    header_row=True,
                                    borders_innerH=True,
                                    borders_outerH=True,
                                    borders_innerV=True,
                                    borders_outerV=True,
                                    resizable=True,
                                    policy=dpg.mvTable_SizingStretchProp,
                                    scrollY=True,
                                    freeze_rows=1,
                                    height=-1):
                            
                            # Define columns with wider widths
                            dpg.add_table_column(label="Category", width_fixed=True, init_width_or_weight=250)
                            dpg.add_table_column(label="Score", width_fixed=True, init_width_or_weight=200)
                            dpg.add_table_column(label="Assessment", width_fixed=True, init_width_or_weight=250)
                            
                            # Initial empty row
                            with dpg.table_row():
                                dpg.add_text("Awaiting evaluation...")
                                dpg.add_text("-")
                                dpg.add_text("-")

        # Tab 3 - Placeholder for future feature
        with dpg.tab(label="Feature 3"):
            dpg.add_text("Feature 3 content will go here")
            dpg.add_slider_float(label="Sample Slider", min_value=0, max_value=100)

# Setup viewport and show
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()