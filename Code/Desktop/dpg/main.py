import dearpygui.dearpygui as dpg

def evaluate_callback():
    resume_text = dpg.get_value("resume_input")
    job_text = dpg.get_value("job_description_input")
    # Add your evaluation logic here
    print("Resume:", resume_text)
    print("Job Description:", job_text)

# Initialize DearPyGUI
dpg.create_context()
dpg.create_viewport(title="Resume Job Matcher", width=1000, height=800)

# Create the main window
with dpg.window(label="Resume Job Matcher", tag="primary_window"):
    # Add instructions
    dpg.add_text("Enter resume text and job description below:")
    dpg.add_spacer(height=5)
    
    # Create layout with two columns
    with dpg.group(horizontal=True):
        # Left column - Resume
        with dpg.group():
            dpg.add_text("Resume Text")
            # Create child window for scrolling
            with dpg.child_window(width=450, height=500):
                dpg.add_input_text(
                    tag="resume_input",
                    multiline=True,
                    width=430,
                    height=480
                )
        
        # Add some spacing between columns
        dpg.add_spacer(width=10)
        
        # Right column - Job Description
        with dpg.group():
            dpg.add_text("Job Description")
            # Create child window for scrolling
            with dpg.child_window(width=450, height=500):
                dpg.add_input_text(
                    tag="job_description_input",
                    multiline=True,
                    width=430,
                    height=480
                )
    
    # Add spacing before button
    dpg.add_spacer(height=10)
    
    # Add evaluate button
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