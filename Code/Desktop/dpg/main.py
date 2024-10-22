import dearpygui.dearpygui as dpg

def evaluate_callback():
    resume_text = dpg.get_value("resume_input")
    job_text = dpg.get_value("job_description_input")
    
    # Example evaluation result - replace with your actual evaluation logic
    sample_result = "Evaluation Results:\n\n" + \
                   "✓ Skills Match: 75%\n" + \
                   "✓ Experience Level: Strong match\n" + \
                   "✓ Key Requirements: 8/10 matched\n\n" + \
                   "Detailed Analysis:\n" + \
                   "- Found relevant experience in Python development\n" + \
                   "- Strong match in database knowledge\n" + \
                   "- Communication skills evident in resume"
    
    dpg.set_value("results_text", sample_result)

# Initialize DearPyGUI
dpg.create_context()
dpg.create_viewport(title="Resume Job Matcher", width=1400, height=800)

# Create the main window
with dpg.window(label="Resume Job Matcher", tag="primary_window"):
    # Add instructions
    dpg.add_text("Enter resume text and job description below:")
    dpg.add_spacer(height=5)
    
    # Create layout with three columns
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
        
        # Add spacing between columns
        dpg.add_spacer(width=10)
        
        # Middle column - Job Description
        with dpg.group():
            dpg.add_text("Job Description")
            with dpg.child_window(width=500, height=600):
                dpg.add_input_text(
                    tag="job_description_input",
                    multiline=True,
                    width=480,
                    height=580
                )

        # Add spacing between columns
        dpg.add_spacer(width=10)
        
        # Right column - Results
        with dpg.group():
            dpg.add_text("Evaluation Results")
            with dpg.child_window(width=500, height=600):
                dpg.add_text(
                    tag="results_text",
                    default_value="Results will appear here after evaluation...",
                    wrap=380
                )
    
    # Add spacing before button
    dpg.add_spacer(height=10)
    
    # Add evaluate button centered
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=600)  # Adjust this value to center the button
        dpg.add_button(
            label="Evaluate Match",
            callback=evaluate_callback,
            width=200,
            height=40
        )

# Setup viewport and show
dpg.set_primary_window("primary_window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()