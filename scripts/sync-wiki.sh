#!/bin/bash

# Vidzilla Wiki Sync Script
# Синхронизирует локальные wiki файлы с GitHub Wiki

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/mirvald-space/Vidzilla.wiki.git"
WIKI_DIR="wiki"
TEMP_WIKI_DIR="temp-wiki"

echo -e "${BLUE}🚀 Vidzilla Wiki Sync Tool${NC}"
echo "=================================="

# Check if wiki directory exists
if [ ! -d "$WIKI_DIR" ]; then
    echo -e "${RED}❌ Error: wiki/ directory not found${NC}"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Error: git is not installed${NC}"
    exit 1
fi

# Function to cleanup temp directory
cleanup() {
    if [ -d "$TEMP_WIKI_DIR" ]; then
        echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
        rm -rf "$TEMP_WIKI_DIR"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo -e "${BLUE}📥 Cloning GitHub Wiki repository...${NC}"
if git clone "$REPO_URL" "$TEMP_WIKI_DIR" 2>/dev/null; then
    echo -e "${GREEN}✅ Wiki repository cloned successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Wiki repository doesn't exist yet, will create it${NC}"
    mkdir -p "$TEMP_WIKI_DIR"
    cd "$TEMP_WIKI_DIR"
    git init
    git remote add origin "$REPO_URL"
    cd ..
fi

echo -e "${BLUE}📋 Copying wiki files...${NC}"

# Copy all markdown files
cp "$WIKI_DIR"/*.md "$TEMP_WIKI_DIR/" 2>/dev/null || true

# Create navigation sidebar
echo -e "${BLUE}🧭 Creating navigation sidebar...${NC}"
cat > "$TEMP_WIKI_DIR/_Sidebar.md" << 'EOF'
## 📚 Vidzilla Wiki

### 👥 For Users
* [🏠 Home](Home)
* [🚀 Quick Start](Quick-Start-Guide)
* [🎯 Supported Platforms](Supported-Platforms)
* [❓ FAQ](FAQ)

### 👨‍💻 For Developers
* [🛠️ Installation Guide](Installation-Guide)
* [🏗️ Architecture Overview](Architecture-Overview)

### 🔗 Quick Links
* [📋 Repository](https://github.com/mirvald-space/Vidzilla)
* [🐛 Report Bug](https://github.com/mirvald-space/Vidzilla/issues/new)
* [💬 Discussions](https://github.com/mirvald-space/Vidzilla/discussions)

---
*Auto-generated navigation*
EOF

# Create footer
echo -e "${BLUE}📄 Creating footer...${NC}"
cat > "$TEMP_WIKI_DIR/_Footer.md" << EOF
---
📅 **Last updated:** $(date '+%Y-%m-%d %H:%M:%S UTC')  
🤖 **Auto-synced** from [main repository](https://github.com/mirvald-space/Vidzilla/tree/main/wiki)  
📝 **Edit:** [Improve this documentation](https://github.com/mirvald-space/Vidzilla/tree/main/wiki)
EOF

# Change to wiki directory
cd "$TEMP_WIKI_DIR"

# Configure git if not already configured
if [ -z "$(git config user.name)" ]; then
    git config user.name "Wiki Sync Bot"
    git config user.email "wiki-sync@vidzilla.bot"
fi

# Check for changes
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo -e "${YELLOW}📝 Changes detected, updating wiki...${NC}"
    
    # Add all files
    git add .
    
    # Create commit message with file list
    CHANGED_FILES=$(git diff --cached --name-only | tr '\n' ', ' | sed 's/,$//')
    COMMIT_MSG="📚 Auto-sync wiki documentation

Updated files: $CHANGED_FILES

Synced from main repository at $(date '+%Y-%m-%d %H:%M:%S UTC')
"
    
    # Commit changes
    git commit -m "$COMMIT_MSG"
    
    # Push to GitHub
    echo -e "${BLUE}📤 Pushing changes to GitHub Wiki...${NC}"
    if git push origin master 2>/dev/null || git push origin main 2>/dev/null; then
        echo -e "${GREEN}✅ Wiki updated successfully!${NC}"
        echo -e "${GREEN}🌐 View at: https://github.com/mirvald-space/Vidzilla/wiki${NC}"
    else
        echo -e "${RED}❌ Failed to push changes. Check your permissions.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Wiki is already up to date!${NC}"
fi

cd ..

echo -e "${GREEN}🎉 Wiki sync completed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Wiki Statistics:${NC}"
echo "  📄 Pages: $(find "$WIKI_DIR" -name "*.md" | wc -l)"
echo "  📝 Total lines: $(cat "$WIKI_DIR"/*.md | wc -l)"
echo "  💾 Total size: $(du -sh "$WIKI_DIR" | cut -f1)"
echo ""
echo -e "${YELLOW}💡 Tip: You can also sync automatically on every push by enabling GitHub Actions${NC}"