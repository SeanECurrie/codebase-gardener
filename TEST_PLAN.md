# Test Plan - Codebase Auditor CLI

## Critical Paths
1. **File Discovery** - Core functionality to find and filter source files
2. **Analysis Generation** - Context-appropriate prompts based on project size 
3. **Chat Interaction** - Q&A with analyzed codebase

## Error Cases
- Directory doesn't exist
- No source files found
- Ollama not running/model missing
- Permission errors on file access

## Integration Check
- Full workflow: discover → analyze → chat → export

## Risk Assessment
**Highest Risk:** File discovery with edge cases (permissions, large projects)
**Medium Risk:** Analysis prompt generation for different project sizes
**Lower Risk:** Chat functionality (depends on analysis working)