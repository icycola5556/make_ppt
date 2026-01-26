#!/bin/bash

# Agent Skill 安装脚本
# 用法: ./install-skill.sh <skill-name> <github-repo>
# 示例: ./install-skill.sh ui-ux-pro nextlevelbuilder/ui-ux-pro-max-skill

set -e

SKILL_NAME=$1
GITHUB_REPO=$2
SKILLS_DIR=".agent/skills"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示使用说明
show_usage() {
    echo "Usage: ./install-skill.sh <skill-name> <github-repo> [branch]"
    echo ""
    echo "Examples:"
    echo "  ./install-skill.sh ui-ux-pro nextlevelbuilder/ui-ux-pro-max-skill"
    echo "  ./install-skill.sh excalidraw skillcreatorai/cc-excalidraw-skill main"
    echo ""
    echo "Commands:"
    echo "  install   - Install a new skill"
    echo "  update    - Update an existing skill"
    echo "  list      - List all installed skills"
    echo "  remove    - Remove a skill"
}

# 检查参数
if [ -z "$SKILL_NAME" ]; then
    show_usage
    exit 1
fi

# 创建 skills 目录（如果不存在）
mkdir -p "$SKILLS_DIR"

# 安装 skill
install_skill() {
    local name=$1
    local repo=$2
    local branch=${3:-main}
    
    echo -e "${YELLOW}📦 Installing skill: $name${NC}"
    echo -e "${YELLOW}📍 From: https://github.com/$repo${NC}"
    
    # 检查是否已存在
    if [ -d "$SKILLS_DIR/$name" ]; then
        echo -e "${RED}❌ Skill '$name' already exists!${NC}"
        echo -e "${YELLOW}💡 Use 'update' command to update it.${NC}"
        exit 1
    fi
    
    # 克隆仓库
    cd "$SKILLS_DIR"
    
    # 尝试克隆指定分支
    if git clone -b "$branch" "https://github.com/${repo}.git" "$name" 2>/dev/null; then
        echo -e "${GREEN}✅ Skill '$name' installed successfully!${NC}"
    else
        # 如果指定分支失败，尝试默认分支
        echo -e "${YELLOW}⚠️  Branch '$branch' not found, trying default branch...${NC}"
        if git clone "https://github.com/${repo}.git" "$name"; then
            echo -e "${GREEN}✅ Skill '$name' installed successfully!${NC}"
        else
            echo -e "${RED}❌ Failed to install skill '$name'${NC}"
            exit 1
        fi
    fi
    
    cd ../..
    
    # 检查 SKILL.md 是否存在
    if [ -f "$SKILLS_DIR/$name/SKILL.md" ]; then
        echo -e "${GREEN}✓ SKILL.md found${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: SKILL.md not found in this repository${NC}"
    fi
    
    # 显示 skill 信息
    echo ""
    echo -e "${GREEN}📋 Skill Information:${NC}"
    echo -e "  Name: $name"
    echo -e "  Location: $SKILLS_DIR/$name"
    if [ -f "$SKILLS_DIR/$name/SKILL.md" ]; then
        # 尝试提取 skill 描述
        description=$(grep -A 1 "^description:" "$SKILLS_DIR/$name/SKILL.md" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')
        if [ -n "$description" ]; then
            echo -e "  Description: $description"
        fi
    fi
}

# 更新 skill
update_skill() {
    local name=$1
    
    if [ ! -d "$SKILLS_DIR/$name" ]; then
        echo -e "${RED}❌ Skill '$name' not found!${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}🔄 Updating skill: $name${NC}"
    
    cd "$SKILLS_DIR/$name"
    
    if [ -d ".git" ]; then
        git pull origin
        echo -e "${GREEN}✅ Skill '$name' updated successfully!${NC}"
    else
        echo -e "${RED}❌ '$name' is not a git repository. Cannot update.${NC}"
        echo -e "${YELLOW}💡 Consider reinstalling it.${NC}"
        exit 1
    fi
    
    cd ../..
}

# 列出所有 skills
list_skills() {
    echo -e "${GREEN}📚 Installed Skills:${NC}"
    echo ""
    
    if [ ! -d "$SKILLS_DIR" ]; then
        echo -e "${YELLOW}No skills directory found.${NC}"
        exit 0
    fi
    
    for skill_dir in "$SKILLS_DIR"/*/ ; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            echo -e "${GREEN}▸ $skill_name${NC}"
            
            # 检查是否是 git 仓库
            if [ -d "$skill_dir/.git" ]; then
                cd "$skill_dir"
                remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "N/A")
                last_update=$(git log -1 --format=%cd --date=short 2>/dev/null || echo "N/A")
                echo -e "  Source: $remote_url"
                echo -e "  Last Update: $last_update"
                cd - > /dev/null
            fi
            
            # 显示描述
            if [ -f "$skill_dir/SKILL.md" ]; then
                description=$(grep -A 1 "^description:" "$skill_dir/SKILL.md" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')
                if [ -n "$description" ]; then
                    echo -e "  Description: $description"
                fi
            fi
            echo ""
        fi
    done
}

# 删除 skill
remove_skill() {
    local name=$1
    
    if [ ! -d "$SKILLS_DIR/$name" ]; then
        echo -e "${RED}❌ Skill '$name' not found!${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}🗑️  Removing skill: $name${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$SKILLS_DIR/$name"
        echo -e "${GREEN}✅ Skill '$name' removed successfully!${NC}"
    else
        echo -e "${YELLOW}❌ Cancelled.${NC}"
    fi
}

# 主逻辑
case "$SKILL_NAME" in
    list)
        list_skills
        ;;
    update)
        if [ -z "$GITHUB_REPO" ]; then
            echo -e "${RED}❌ Please specify skill name to update${NC}"
            echo "Usage: ./install-skill.sh update <skill-name>"
            exit 1
        fi
        update_skill "$GITHUB_REPO"
        ;;
    remove)
        if [ -z "$GITHUB_REPO" ]; then
            echo -e "${RED}❌ Please specify skill name to remove${NC}"
            echo "Usage: ./install-skill.sh remove <skill-name>"
            exit 1
        fi
        remove_skill "$GITHUB_REPO"
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        if [ -z "$GITHUB_REPO" ]; then
            echo -e "${RED}❌ Please specify GitHub repository${NC}"
            show_usage
            exit 1
        fi
        install_skill "$SKILL_NAME" "$GITHUB_REPO" "${3:-main}"
        ;;
esac
