import re

def reformat_markdown(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    in_code_block = False
    code_block_content = []
    code_block_lang = ""
    
    # Heuristic to detect if a code block is actually just text/formulas that can be unpacked
    # or if it should be kept as a distinct block. 
    # The user wants "compact". Removing the box around text saves space.
    # We will unpack code blocks if they seem to be just styled text.
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Remove Horizontal Rules to save vertical space
        if re.match(r'^[-=]{3,}$', stripped):
            continue
            
        # 2. Handle Code Blocks
        if stripped.startswith('```'):
            if in_code_block:
                # End of code block
                in_code_block = False
                
                # Analyze content to decide whether to keep as code block or unpack
                content_str = "\n".join(code_block_content)
                
                # Heuristics for "keep as code block":
                # - Contains typical code symbols that rely on monospace: alignment charts, tables drawn with characters
                # - Python/Code syntax
                # - Explicit complex formulas that need isolation
                
                # Heuristics for "unpack":
                # - Mostly text (Chinese characters)
                # - "步骤" (Steps), "符号" (Symbols), "例子" (Examples)
                
                is_table = any('|' in l for l in code_block_content) and any('-|-' in l or '|-' in l for l in code_block_content)
                is_unicode_table = '━━' in content_str
                
                if is_table or is_unicode_table:
                    # Keep tables as is, they need monospace
                    new_lines.append(f"```{code_block_lang}")
                    new_lines.extend(code_block_content)
                    new_lines.append("```")
                elif "步骤" in content_str or "符号" in content_str or "优点" in content_str or "例题" in content_str:
                    # Unpack these text blocks into blockquotes or just text
                    # Use blockquote > for visual distinction but less space than code block
                    for c_line in code_block_content:
                        new_lines.append(f"> {c_line}")
                elif len(code_block_content) < 10 and not code_block_lang:
                     # Short un-languaged blocks -> Blockquotes
                    for c_line in code_block_content:
                        new_lines.append(f"> {c_line}")
                else:
                    # Default: keep as code block for safety
                    new_lines.append(f"```{code_block_lang}")
                    new_lines.extend(code_block_content)
                    new_lines.append("```")
                
                code_block_content = []
                code_block_lang = ""
            else:
                # Start of code block
                in_code_block = True
                code_block_lang = stripped.replace('```', '').strip()
            continue
            
        if in_code_block:
            code_block_content.append(line.rstrip())
            continue

        # 3. Compact Empty Lines
        # If current line is empty and previous added line was empty, skip
        if not stripped:
            if new_lines and not new_lines[-1].strip():
                continue
            if not new_lines: # Formatting at start of file
                continue
                
        new_lines.append(line.rstrip())

    # Final cleanup of new_lines
    final_lines = []
    for line in new_lines:
        # Compact headers: Remove excessive space before headers
        if line.lstrip().startswith('#'):
             # Ensure exactly one empty line before header if not at start
             if final_lines and final_lines[-1].strip():
                 final_lines.append("")
        
        final_lines.append(line)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(final_lines))

if __name__ == "__main__":
    reformat_markdown(
        "/Users/bisuv/Documents/internProject/pptgen_workflow/docs/机器学习期末考试完整复习指南.md",
        "/Users/bisuv/Documents/internProject/pptgen_workflow/docs/机器学习期末考试完整复习指南_紧凑版.md"
    )
    print("Reformatting complete.")
