# Codebase Intelligence Auditor - Implementation Tasks

## Overview

Simple, pragmatic implementation plan following core development principles: **Make it work first, then make it better.** Single file, hardcoded prompts, direct implementation.

## Implementation Tasks

- [x] **Task 1: Code Audit - What Stays, What Goes, What's In The Way**

**Priority**: Critical | **Effort**: 1 hour | **Dependencies**: None

**Objective**: Clean house before building - identify what existing code helps, what's in the way, and what can be removed.

**Context**: We have a complex codebase-gardener project but need a simple codebase auditor. Figure out what to keep and what to remove.

**🚨 MANDATORY BEFORE STARTING:**

1. **Previous Task Validation**: N/A (first task)
2. **Foundation Reading**: Read core principles, task guidelines, and gap closure framework
3. **MCP Tools Research**: Use Sequential Thinking → Context7 → Bright Data → Basic Memory (in order)
4. **Gap Analysis**: N/A (first task)

**🚨 DURING TASK:**

1. **Use Existing Components**: Enhance rather than rebuild - check what's already in `src/codebase_gardener/`
2. **Follow Established Patterns**: Use patterns from OllamaClient, FileUtilities, etc.
3. **Pragmatic POC Approach**: Working code first, optimization second
4. **Update Task Status**: Use `taskStatus` tool to mark tasks as in_progress → completed

**🚨 POST-TASK (MANDATORY):**

1. **Gap Closure Phase**: Address quick wins (<30min, low risk, improves validation)
2. **Memory File Creation**: Create comprehensive `.kiro/memory/code_audit_task1.md`
3. **Git Integration**: Commit changes with conventional format
4. **Documentation Updates**: Update task completion log and relevant docs
5. **Next Task Preparation**: Document handoff information for Task 2

**Implementation Steps**:

1. **Foundation Reading** (MANDATORY FIRST STEPS)

   - Use Sequential Thinking to analyze the existing codebase structure
   - Use Context7 to understand what components we actually need
   - Use Bright Data to find examples of simple code analysis tools

2. **Audit Existing Components**

   - **Keep**: `OllamaClient`, `FileUtilities.find_source_files()`, basic logging
   - **Maybe Keep**: Configuration loading, error handling patterns
   - **Remove/Ignore**: Complex Gradio interfaces, project switching, LoRA training, vector stores
   - **Document**: What each component does and whether we need it

3. **Identify Blockers**

   - Find any complex dependencies that would slow down simple implementation
   - Identify any architectural patterns that conflict with single-file approach
   - Document what needs to be simplified or bypassed

4. **Create Implementation Plan**
   - Map out exactly which existing code to leverage
   - Identify what new code needs to be written (should be minimal)
   - Plan the simplest possible integration approach

**Real Testing Requirements**:

1. **Existing Code Review**: Can we use `OllamaClient` and `FileUtilities` as-is?
2. **Dependency Check**: What's the minimum we need to import?
3. **Integration Test**: Can we create a simple script that uses existing components?

**🚨 TASK COMPLETION CRITERIA (MANDATORY):**

**A task is ONLY complete when:**

1. **Real Working Code**: Code works with actual gpt-oss-20b model
2. **Real Codebase**: Tested with actual codebase like this codebase-gardener project
3. **Real User Interaction**: Can be used through actual interface
4. **User Validation**: User can see and verify it works as intended
5. **Actionable Usage**: Clear explanation of how user uses the new functionality

**Task Complete When User Can**:

- See a clear list of what existing code helps vs. hurts the simple implementation
- Understand exactly what components to use and what to ignore
- Have a concrete plan for minimal integration with existing codebase

---

- [ ] **Task 2: Create Single-File Codebase Auditor**

**Priority**: High | **Effort**: 2 hours | **Dependencies**: Task 1

**Objective**: Create `codebase_auditor.py` - a single file that does everything: find files, analyze with gpt-oss-20b, store results.

**Context**: Build the simplest possible working implementation. One file, hardcoded prompts, basic functionality.

**🚨 MANDATORY BEFORE STARTING:**

1. **Previous Task Validation**: Read `.kiro/memory/code_audit_task1.md` and verify cleanup outputs work
2. **Foundation Reading**: Read core principles, task guidelines, and gap closure framework
3. **MCP Tools Research**: Use Sequential Thinking → Context7 → Bright Data → Basic Memory (in order)
4. **Gap Analysis**: Review Task 1 gaps and plan closure for current scope

**🚨 DURING TASK:**

1. **Use Existing Components**: Enhance rather than rebuild - check what's already in `src/codebase_gardener/`
2. **Follow Established Patterns**: Use patterns from OllamaClient, FileUtilities, etc.
3. **Pragmatic POC Approach**: Working code first, optimization second
4. **Update Task Status**: Use `taskStatus` tool to mark tasks as in_progress → completed

**🚨 POST-TASK (MANDATORY):**

1. **Gap Closure Phase**: Address quick wins (<30min, low risk, improves validation)
2. **Memory File Creation**: Create comprehensive `.kiro/memory/single_file_auditor_task2.md`
3. **Git Integration**: Commit changes with conventional format
4. **Documentation Updates**: Update task completion log and relevant docs
5. **Next Task Preparation**: Document handoff information for Task 3

**Implementation Steps**:

1. **Foundation Reading** (MANDATORY FIRST STEPS)

   - Use Sequential Thinking to plan the simplest implementation
   - Use Context7 to get Ollama client documentation
   - Use Bright Data to find simple code analysis examples

2. **Create Single File Implementation**

   ```python
   # codebase_auditor.py
   class CodebaseAuditor:
       def __init__(self):
           self.ollama_client = OllamaClient()  # Use existing
           self.analysis_results = None

       def analyze_codebase(self, directory_path: str) -> str:
           """Main method - does everything"""
           # 1. Find files using existing FileUtilities
           # 2. Read file contents
           # 3. Send to gpt-oss-20b with hardcoded analysis prompt
           # 4. Store results as simple string
           # 5. Return summary

       def chat(self, question: str) -> str:
           """Answer questions about the analysis"""
           # Send question + previous analysis to gpt-oss-20b

       def export_markdown(self) -> str:
           """Generate markdown report"""
           # Format analysis results as markdown
   ```

3. **Hardcode Analysis Prompt**

   - Create comprehensive prompt that asks for architecture, tech debt, documentation gaps
   - Make it specific: ask for file names, line numbers, concrete examples
   - Keep it simple: one prompt that does everything

4. **Basic File Processing**

   - Use existing `FileUtilities.find_source_files()`
   - Read files and combine into single context for gpt-oss-20b
   - Handle large codebases by chunking if needed

5. **Simple Storage**
   - Store analysis results as plain strings
   - No complex data structures or databases
   - Keep it in memory for the session

**Real Testing Requirements**:

1. **Test with THIS Codebase**: Point it at current codebase-gardener project
2. **Test Analysis Quality**: Does gpt-oss-20b provide useful insights?
3. **Test Chat Functionality**: Can you ask questions about the analysis?
4. **Test Export**: Does markdown export work and look reasonable?

**🚨 TASK COMPLETION CRITERIA (MANDATORY):**

**A task is ONLY complete when:**

1. **Real Working Code**: Code works with actual gpt-oss-20b model
2. **Real Codebase**: Tested with actual codebase like this codebase-gardener project
3. **Real User Interaction**: Can be used through actual interface
4. **User Validation**: User can see and verify it works as intended
5. **Actionable Usage**: Clear explanation of how user uses the new functionality

**Task Complete When User Can**:

- Run `auditor = CodebaseAuditor()` and `auditor.analyze_codebase(".")`
- Get a comprehensive analysis of the current codebase
- Ask questions like "What are the main architecture issues?"
- Export a markdown report that could be shared with AI agents

---

- [ ] **Task 3: Add Simple Chat Interface**

**Priority**: Medium | **Effort**: 1 hour | **Dependencies**: Task 2

**Objective**: Create a simple command-line or basic web interface for interacting with the auditor.

**Context**: Make it easy to use without writing Python code every time. Simple interface for analysis and chat.

**🚨 MANDATORY BEFORE STARTING:**

1. **Previous Task Validation**: Read `.kiro/memory/single_file_auditor_task2.md` and verify auditor works
2. **Foundation Reading**: Read core principles, task guidelines, and gap closure framework
3. **MCP Tools Research**: Use Sequential Thinking → Context7 → Bright Data → Basic Memory (in order)
4. **Gap Analysis**: Review Task 2 gaps and plan closure for current scope

**🚨 DURING TASK:**

1. **Use Existing Components**: Enhance rather than rebuild - check what's already in `src/codebase_gardener/`
2. **Follow Established Patterns**: Use patterns from OllamaClient, FileUtilities, etc.
3. **Pragmatic POC Approach**: Working code first, optimization second
4. **Update Task Status**: Use `taskStatus` tool to mark tasks as in_progress → completed

**🚨 POST-TASK (MANDATORY):**

1. **Gap Closure Phase**: Address quick wins (<30min, low risk, improves validation)
2. **Memory File Creation**: Create comprehensive `.kiro/memory/chat_interface_task3.md`
3. **Git Integration**: Commit changes with conventional format
4. **Documentation Updates**: Update task completion log and relevant docs
5. **Next Task Preparation**: Document handoff information for Task 4

**Implementation Steps**:

1. **Foundation Reading** (MANDATORY FIRST STEPS)

   - Use Sequential Thinking to choose between CLI vs web interface
   - Use Context7 to get interface framework documentation
   - Use Bright Data to find simple interface examples

2. **Choose Interface Type**

   - **Option A**: Simple CLI with input prompts
   - **Option B**: Basic Gradio interface (leverage existing patterns)
   - **Decision**: Pick the simplest that works

3. **Implement Interface**

   - Create simple interface that calls `CodebaseAuditor` methods
   - Add basic commands: analyze, chat, export
   - Keep it minimal - no fancy features

4. **Add Basic Commands**

   ```python
   # Example CLI interface
   def main():
       auditor = CodebaseAuditor()

       while True:
           command = input("> ")
           if command.startswith("analyze "):
               path = command.split(" ", 1)[1]
               result = auditor.analyze_codebase(path)
               print(result)
           elif command.startswith("chat "):
               question = command.split(" ", 1)[1]
               response = auditor.chat(question)
               print(response)
           elif command == "export":
               report = auditor.export_markdown()
               print("Report exported to codebase_analysis.md")
   ```

**Real Testing Requirements**:

1. **Test Interface**: Can you easily analyze a codebase through the interface?
2. **Test Commands**: Do analyze, chat, and export commands work?
3. **Test User Experience**: Is it intuitive to use?

**🚨 TASK COMPLETION CRITERIA (MANDATORY):**

**A task is ONLY complete when:**

1. **Real Working Code**: Code works with actual gpt-oss-20b model
2. **Real Codebase**: Tested with actual codebase like this codebase-gardener project
3. **Real User Interaction**: Can be used through actual interface
4. **User Validation**: User can see and verify it works as intended
5. **Actionable Usage**: Clear explanation of how user uses the new functionality

**Task Complete When User Can**:

- Launch the interface and analyze a codebase without writing Python code
- Chat with the system about findings through the interface
- Export reports easily through simple commands

---

- [ ] **Task 4: Test and Validate with Real Codebases**

**Priority**: High | **Effort**: 1 hour | **Dependencies**: Task 3

**Objective**: Test the auditor on real codebases and validate that the analysis is accurate and useful.

**Context**: Prove that the tool actually works by testing on known codebases and comparing results with manual review.

**🚨 MANDATORY BEFORE STARTING:**

1. **Previous Task Validation**: Read `.kiro/memory/chat_interface_task3.md` and verify interface works
2. **Foundation Reading**: Read core principles, task guidelines, and gap closure framework
3. **MCP Tools Research**: Use Sequential Thinking → Context7 → Bright Data → Basic Memory (in order)
4. **Gap Analysis**: Review Task 3 gaps and plan closure for current scope

**🚨 DURING TASK:**

1. **Use Existing Components**: Enhance rather than rebuild - check what's already in `src/codebase_gardener/`
2. **Follow Established Patterns**: Use patterns from OllamaClient, FileUtilities, etc.
3. **Pragmatic POC Approach**: Working code first, optimization second
4. **Update Task Status**: Use `taskStatus` tool to mark tasks as in_progress → completed

**🚨 POST-TASK (MANDATORY):**

1. **Gap Closure Phase**: Address quick wins (<30min, low risk, improves validation)
2. **Memory File Creation**: Create comprehensive `.kiro/memory/validation_testing_task4.md`
3. **Git Integration**: Commit changes with conventional format
4. **Documentation Updates**: Update task completion log and relevant docs
5. **Next Task Preparation**: Document handoff information for Task 5

**Implementation Steps**:

1. **Foundation Reading** (MANDATORY FIRST STEPS)

   - Use Sequential Thinking to plan validation approach
   - Use Context7 to understand validation best practices
   - Use Bright Data to find code analysis validation examples

2. **Test on THIS Codebase**

   - Run full analysis on current codebase-gardener project
   - Review findings for accuracy
   - Check if it identifies real issues we know about
   - Validate architecture understanding

3. **Test on External Codebase**

   - Test on `/Users/seancurrie/Desktop/MCP/notion_schema_tool/` or similar
   - Compare findings with manual code review
   - Check for false positives and missed issues

4. **Validate Analysis Quality**

   - Are the findings specific and actionable?
   - Does it provide file names and line numbers?
   - Are the recommendations helpful for directing AI agents?

5. **Compare with Other Tools**

   - Run same codebase through Cursor, Claude, or other analysis tools
   - Compare findings for consistency
   - Document where our tool excels or falls short

6. **Fix Obvious Issues**
   - Improve prompts based on testing results
   - Fix any bugs or errors discovered
   - Enhance analysis quality based on validation

**Real Testing Requirements**:

1. **Accuracy Test**: Analysis findings match manual code review
2. **Completeness Test**: Tool identifies major issues and architecture patterns
3. **Usability Test**: Reports are useful for briefing AI agents
4. **Performance Test**: Analysis completes in reasonable time

**🚨 TASK COMPLETION CRITERIA (MANDATORY):**

**A task is ONLY complete when:**

1. **Real Working Code**: Code works with actual gpt-oss-20b model
2. **Real Codebase**: Tested with actual codebase like this codebase-gardener project
3. **Real User Interaction**: Can be used through actual interface
4. **User Validation**: User can see and verify it works as intended
5. **Actionable Usage**: Clear explanation of how user uses the new functionality

**Task Complete When User Can**:

- Get accurate, useful analysis of real codebases
- Trust the findings enough to use them for directing AI agents
- Export reports that provide genuine value for development work
- Use the tool confidently on different types of projects

---

- [ ] **Task 5: Documentation and Usage Guide**

**Priority**: Low | **Effort**: 30 minutes | **Dependencies**: Task 4

**Objective**: Create simple documentation so the tool can be used effectively.

**Context**: Basic usage instructions and examples so the tool is self-explanatory.

**🚨 MANDATORY BEFORE STARTING:**

1. **Previous Task Validation**: Read `.kiro/memory/validation_testing_task4.md` and verify testing results
2. **Foundation Reading**: Read core principles, task guidelines, and gap closure framework
3. **MCP Tools Research**: Use Sequential Thinking → Context7 → Bright Data → Basic Memory (in order)
4. **Gap Analysis**: Review Task 4 gaps and plan closure for current scope

**🚨 DURING TASK:**

1. **Use Existing Components**: Enhance rather than rebuild - check what's already in `src/codebase_gardener/`
2. **Follow Established Patterns**: Use patterns from OllamaClient, FileUtilities, etc.
3. **Pragmatic POC Approach**: Working code first, optimization second
4. **Update Task Status**: Use `taskStatus` tool to mark tasks as in_progress → completed

**🚨 POST-TASK (MANDATORY):**

1. **Gap Closure Phase**: Address quick wins (<30min, low risk, improves validation)
2. **Memory File Creation**: Create comprehensive `.kiro/memory/documentation_task5.md`
3. **Git Integration**: Commit changes with conventional format
4. **Documentation Updates**: Update task completion log and relevant docs
5. **Project Completion**: Document final project status and handoff

**Implementation Steps**:

1. **Create Simple README**

   - How to install and run the auditor
   - Basic usage examples
   - What the analysis covers
   - How to interpret results

2. **Add Usage Examples**

   - Example analysis output
   - Sample chat interactions
   - Example markdown export

3. **Document Limitations**
   - What the tool does and doesn't do
   - Known limitations and workarounds
   - When to use other tools instead

**🚨 TASK COMPLETION CRITERIA (MANDATORY):**

**A task is ONLY complete when:**

1. **Real Working Code**: Code works with actual gpt-oss-20b model
2. **Real Codebase**: Tested with actual codebase like this codebase-gardener project
3. **Real User Interaction**: Can be used through actual interface
4. **User Validation**: User can see and verify it works as intended
5. **Actionable Usage**: Clear explanation of how user uses the new functionality

**Task Complete When User Can**:

- Use the tool without additional explanation
- Understand what the analysis results mean
- Know how to get the most value from the tool

## Success Criteria

### Primary Success Indicators

1. **It Works**: Can analyze real codebases and provide useful insights
2. **It's Simple**: Single file implementation that's easy to understand and modify
3. **It's Useful**: Analysis helps with directing AI agents and understanding codebases
4. **It's Fast Enough**: Completes analysis in reasonable time (minutes, not hours)

### Validation Approach

- Test on current codebase-gardener project
- Compare results with manual code review
- Validate usefulness for AI agent briefing
- Ensure findings are specific and actionable

## Anti-Patterns to Avoid

- **Over-Engineering**: Don't add complex abstractions or enterprise patterns
- **Feature Creep**: Don't add features beyond core analysis functionality
- **Premature Optimization**: Don't optimize before it works
- **Complex Data Models**: Keep data storage simple (strings and basic structures)

## Key Principles

- **Make It Work First**: Focus on basic functionality over advanced features
- **Single File**: Keep implementation simple and contained
- **Use Existing Code**: Leverage OllamaClient and FileUtilities that already work
- **Hardcode Prompts**: Don't build complex prompt systems - use what works
- **Test on Real Code**: Validate with actual codebases, not toy examples
