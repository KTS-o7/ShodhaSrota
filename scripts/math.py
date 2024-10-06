import datetime
import os

def generate_research_paper_template(doc_title,time_stamp):
    # Create the template
    template = f"""# 🎓{doc_title}
    
## Content 

--- 
## Metadata (Auto-Generated)

- Title: {doc_title}
- Author: (Your Name)
- Created On: {time_stamp}
- Tags: (Add relevant tags)
- Related Links: (Add any related links)
"""
    return template

def save_template_to_file(template, filename):
    with open(filename, 'w') as file:
        file.write(template)

if __name__ == "__main__":
    filename = input("Enter the filename to save the template: ")
    doc_title = filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    folder_path = "./Math"
    os.makedirs(folder_path, exist_ok=True)
    filename = os.path.join(folder_path, f"{filename}_{timestamp}.md")
    
    template = generate_research_paper_template(doc_title, timestamp)
    save_template_to_file(template, filename)
    
    print(f"Template saved to {filename}")