import dearpygui.dearpygui as dpg

def evaluate_callback():
    resume_text = dpg.get_value("resume_input")
    job_text = dpg.get_value("job_description_input")
    
    # Example evaluation result - replace with your actual evaluation logic
    sample_result = "Evaluation Results:\n\n" + \
                   "Summary Analysis:\n" + \
                   "- Found relevant experience in Python development\n" + \
                   "- Strong match in database knowledge\n" + \
                   "- Communication skills evident in resume"
    
    dpg.set_value("results_text", sample_result)
    
    # Clear existing rows by deleting all table rows except the header
    if dpg.does_item_exist("results_table"):
        children = dpg.get_item_children("results_table")[1]  # [1] gets the row children
        for child in children:
            dpg.delete_item(child)
    
    # Add new rows with sample data
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
        ["Certifications", "3/4", "Good"]
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
    strategy_text = dpg.get_value("strategy_input")
    job_text = dpg.get_value("strategy_job_text")
    
    strategy_result = "Strategy Evaluation Results:\n\n" + \
                     "✓ Approach Viability: Strong\n" + \
                     "✓ Key Points Addressed: 90%\n" + \
                     "✓ Preparation Level: High\n\n" + \
                     "Strategic Analysis:\n" + \
                     "- Clear understanding of role requirements\n" + \
                     "- Well-structured approach to interviews\n" + \
                     "- Good alignment with company values"
    
    dpg.set_value("strategy_results", strategy_result)

# Initialize DearPyGUI
dpg.create_context()
dpg.create_viewport(title="Multi-Feature Application", width=1400, height=800)

# Create the main window
with dpg.window(label="Multi-Feature Application", tag="primary_window"):
    with dpg.tab_bar():
        # Tab 1 - Resume Matcher
        with dpg.tab(label="Resume Matcher"):
            dpg.add_text("Enter resume text and job description below:")
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                # Left column - Resume
                with dpg.group():
                    dpg.add_text("Resume Text")
                    with dpg.child_window(width=500, height=600):
                        dpg.add_input_text(
                            tag="resume_input",
                            multiline=True,
                            width=480,
                            height=580
                        )
                
                dpg.add_spacer(width=10)
                
                # Middle column - Job Description
                with dpg.group():
                    dpg.add_text("Job Description")
                    with dpg.child_window(width=500, height=600):
                        dpg.add_input_text(
                            tag="job_description_input",
                            multiline=True,
                            width=480,
                            height=580,
                            callback=update_strategy_job_description
                        )

                dpg.add_spacer(width=10)
                
                # Right column - Results
                with dpg.group():
                    dpg.add_text("Evaluation Results")
                    with dpg.child_window(width=500, height=600):
                        # Text summary at the top
                        dpg.add_text(
                            tag="results_text",
                            default_value="Results will appear here after evaluation...",
                            wrap=380
                        )
                        
                        dpg.add_spacer(height=10)
                        dpg.add_separator()
                        dpg.add_spacer(height=10)
                        
                        # Detailed results table
                        dpg.add_text("Detailed Analysis")
                        with dpg.table(tag="results_table", 
                                     header_row=True,
                                     borders_innerH=True,
                                     borders_outerH=True,
                                     borders_innerV=True,
                                     borders_outerV=True,
                                     width=480,
                                     height=400):  # Added fixed height
                            
                            dpg.add_table_column(label="Category", width_fixed=True, width=150)
                            dpg.add_table_column(label="Score", width_fixed=True, width=100)
                            dpg.add_table_column(label="Assessment", width_fixed=True, width=150)
                            
                            # Initial empty row
                            with dpg.table_row():
                                dpg.add_text("Awaiting evaluation...")
                                dpg.add_text("-")
                                dpg.add_text("-")
            
            dpg.add_spacer(height=10)
            
            # Add evaluate button centered
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=600)
                dpg.add_button(
                    label="Evaluate Match",
                    callback=evaluate_callback,
                    width=200,
                    height=40
                )

        # Tab 2 - Strategy Evaluations
        with dpg.tab(label="Strategy Evaluations"):
            dpg.add_text("Develop and evaluate your interview strategy based on the job description:")
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                # Left column - Strategy Input
                with dpg.group():
                    dpg.add_text("Your Strategy")
                    with dpg.child_window(width=500, height=600):
                        dpg.add_input_text(
                            tag="strategy_input",
                            multiline=True,
                            width=480,
                            height=580,
                            hint="Enter your interview strategy and preparation plans..."
                        )
                
                # Add spacing between columns
                dpg.add_spacer(width=10)
                
                # Middle column - Job Description (Read-only)
                with dpg.group():
                    dpg.add_text("Job Description (from Tab 1)")
                    with dpg.child_window(width=500, height=600):
                        dpg.add_input_text(
                            tag="strategy_job_text",
                            multiline=True,
                            width=480,
                            height=580,
                            readonly=True
                        )
                
                # Add spacing between columns
                dpg.add_spacer(width=10)
                
                # Right column - Strategy Results
                with dpg.group():
                    dpg.add_text("Strategy Evaluation")
                    with dpg.child_window(width=500, height=600):
                        dpg.add_text(
                            tag="strategy_results",
                            default_value="Strategy evaluation results will appear here...",
                            wrap=380
                        )
            
            # Add spacing before button
            dpg.add_spacer(height=10)
            
            # Add evaluate strategy button centered
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=600)
                dpg.add_button(
                    label="Evaluate Strategy",
                    callback=evaluate_strategy,
                    width=200,
                    height=40
                )

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