import re

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    processed_lines = []
    in_code_block = False
    block_content = []
    
    # Patterns to strip
    separator_pattern = re.compile(r'^[-=━_]{3,}$')
    # Decorative icons in headers (Keep functional ones like ✅ ⚠️ 💡)
    # Remove: 📘 📖 📐 🔢 📝 🆚 📊 🔧 🎯 📚 
    icon_pattern = re.compile(r'[📘📖📐🔢📝🆚📊🔧🎯📚]') 
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 1. Skip Separators
        if separator_pattern.match(stripped):
            continue
            
        # 2. Handle Code Blocks (Convert text-blocks to Blockquotes)
        if stripped.startswith('```'):
            if in_code_block:
                # End of block
                in_code_block = False
                # Process collected block content
                # Decide if it's a table or just text
                is_table = any('|' in l for l in block_content) and any('-|-' in l for l in block_content)
                
                if is_table:
                    # Keep tables as Markdown tables (not code block)
                    # But if it was inside a code block, it might not be rendered if we just dump it.
                    # Standard Markdown tables don't need code blocks.
                    processed_lines.extend(block_content)
                else:
                    # Convert to blockquote
                    for bl in block_content:
                        # Remove ASCII box borders if inside the block
                        if separator_pattern.match(bl.strip()):
                            continue
                        processed_lines.append(f"> {bl}")
                
                block_content = []
            else:
                # Start of block
                in_code_block = True
                # Ignore language tag if any
            continue
            
        if in_code_block:
            block_content.append(line.rstrip())
            continue
            
        # 3. Process Normal Lines
        
        # Remove decorative icons from headers
        if line.lstrip().startswith('#'):
            line = icon_pattern.sub('', line)
            # Ensure space after #
            line = re.sub(r'^(#+)([^ ])', r'\1 \2', line)
            
        # Remove "Chapter X" meta-noise if user wants PURE dry goods? 
        # Actually user said "Keep hierarchy", so Chapter headers are important context.
        
        # Filter purely empty lines aggressively later, so just add here
        processed_lines.append(line.rstrip())

    # Post-processing for density
    final_output = []
    last_line_empty = False
    
    for line in processed_lines:
        s_line = line.strip()
        
        # Skip empty lines at start
        if not final_output and not s_line:
            continue
            
        if not s_line:
            if last_line_empty:
                continue # Skip consecutive empty lines
            last_line_empty = True
            final_output.append("")
        else:
            last_line_empty = False
            
            # Special handling for "Header" lines -> Ensure 1 empty line before them
            if s_line.startswith('#'):
                 if final_output and final_output[-1] != "":
                     final_output.append("")
            
            # Special handling for "> " lines (Blockquotes)
            # If previous line was also blockquote, don't add space. 
            # If previous line was regular text, add space? No, "compact".
            
            final_output.append(line)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_output))

if __name__ == "__main__":
    process_file(
        "/Users/bisuv/Documents/internProject/pptgen_workflow/docs/机器学习期末考试完整复习指南.md",
        "/Users/bisuv/Documents/internProject/pptgen_workflow/docs/机器学习期末考试完整复习指南_干货版.md"
    )
    print("Optimization complete.")
