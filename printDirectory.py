import os

def generate_markdown_structure(root_dir, indent_level=0):
    """
    Recursively generate a Markdown representation of the directory structure.

    :param root_dir: The root directory to start from.
    :param indent_level: The current indentation level for the Markdown output.
    :return: A string containing the Markdown representation of the directory structure.
    """
    markdown_structure = ""
    indent = "    " * indent_level

    # Get the list of files and directories in the current directory
    items = sorted(os.listdir(root_dir))

    for item in items:
        item_path = os.path.join(root_dir, item)

        # Check if the item is a directory or a file
        if os.path.isdir(item_path):
            # If it's a directory, add it to the Markdown structure with a trailing slash
            markdown_structure += f"{indent}- **{item}/**\n"
            # Recursively generate the structure for the subdirectory
            markdown_structure += generate_markdown_structure(item_path, indent_level + 1)
        else:
            # If it's a file, add it to the Markdown structure
            markdown_structure += f"{indent}- {item}\n"

    return markdown_structure

def main():
    # Get the current directory
    current_dir = os.getcwd()

    # Generate the Markdown structure
    markdown_structure = generate_markdown_structure(current_dir)

    # Print the Markdown structure
    print(markdown_structure)

if __name__ == "__main__":
    main()