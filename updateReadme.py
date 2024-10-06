import os
import re

def read_metadata_from_file(file_path):
    metadata = {}
    with open(file_path, 'r') as file:
        content = file.read()
        metadata['Title'] = re.search(r'Title: (.+)', content).group(1)
        metadata['Author'] = re.search(r'Author: (.+)', content).group(1)
        metadata['Created On'] = re.search(r'Created On: (.+)', content).group(1)
        metadata['Tags'] = re.search(r'Tags: (.+)', content).group(1)
        metadata['Related Links'] = re.search(r'Related Links: (.+)', content).group(1)
    return metadata

def generate_markdown_table(directory):
    markdown_table = f"## {directory}\n\n"
    markdown_table += "| File | Title | Author | Created On | Tags | Related Links |\n"
    markdown_table += "|------|-------|--------|------------|------|---------------|\n"
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                relative_path = f"{directory}/{file_path.split('/')[-1]}"
                link = f"[{file}]({relative_path})"
                metadata = read_metadata_from_file(file_path)
                markdown_table += f"| {link} | {metadata['Title']} | {metadata['Author']} | {metadata['Created On']} | {metadata['Tags']} | {metadata['Related Links']} |\n"
    
    return markdown_table

def update_readme_with_tables(directory_list):
    readme_path = "README.md"
    with open(readme_path, 'r') as file:
        readme_content = file.read()
    
    for directory in directory_list:
        # Generate the new table for the directory
        new_table = generate_markdown_table(directory)
        
        # Find the existing table in the README.md
        existing_table_start = re.search(f"## {directory}\n\n", readme_content)
        if existing_table_start:
            existing_table_end = re.search(r"\n\n## ", readme_content[existing_table_start.end():])
            if existing_table_end:
                existing_table_end = existing_table_start.end() + existing_table_end.start()
            else:
                existing_table_end = len(readme_content)
            
            # Replace the existing table with the new table
            readme_content = readme_content[:existing_table_start.start()] + new_table + readme_content[existing_table_end:]
        else:
            # If the directory section doesn't exist, append the new table
            readme_content += f"\n\n{new_table}"
    
    with open(readme_path, 'w') as file:
        file.write(readme_content)

if __name__ == "__main__":
    directory_list = [
        "Research",
        "Math",
        "Technologies",
        "General",
    ]
    
    update_readme_with_tables(directory_list)
    
    print("README.md updated with directory tables")