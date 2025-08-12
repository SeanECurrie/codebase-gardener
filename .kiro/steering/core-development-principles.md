---
inclusion: always
---

# Core Development Principles - Critical Learning from Task 1

**I WILL MAKE SURE TO PRIORITIZE LEARNING FROM THIS AND FOLLOWING ITS BASE APPROACH.**

## The Fundamental Rule: Make It Work First

### What This Means
- If something doesn't work at all, don't optimize it
- Fix broken functionality before adding features
- Get basic operations working before worrying about performance
- Focus on the core goal, not peripheral symptoms

### The Task 1 Learning Experience

#### What Went Wrong
1. **Focused on symptoms instead of root causes**
   - Saw "300-second hang" and built timeout mechanisms
   - Real issue: Basic method name mismatches (`discover_source_files` vs `find_source_files`)

2. **Overthought simple problems**
   - Created complex timeout decorators and signal handling
   - Real fix: Change method names in 2 places

3. **Worked from test outputs instead of reading code**
   - Ran tests first, interpreted failures second
   - Should have: Read the code to understand what was broken

4. **Misunderstood the core requirement**
   - Thought "hang" meant performance problem
   - Reality: System was broken due to wrong API calls

5. **Added complexity instead of fixing basics**
   - Built elaborate file scanning optimizations
   - Real need: Fix `add_project` → `register_project` method call

#### What the User Actually Wanted
- **User's goal**: "CAN YOU LOCATE A DIRECTORY AND HAVE A LLM REVIEW AND EMBED THE APPLICATION TO OPTIMIZE THE LOCAL MODEL TO ANSWER QUESTIONS ABOUT IT"
- **My focus**: File scanning performance and timeout mechanisms
- **The disconnect**: I was optimizing file discovery when the real goal is AI model training and analysis

#### The Key Insight
User said: "I don't care if I wait 300 seconds and it WORKS. The issue is not time. It's it not working or making sense."

This means:
- Working functionality > Performance optimization
- Correct behavior > Fast behavior
- Simple fixes > Complex solutions

## The Correct Approach for Any Task

### 1. Read Code First, Test Second
- Always examine the actual implementation before running anything
- Understand what the code is supposed to do vs. what it's actually doing
- Look for obvious errors: method name mismatches, wrong imports, missing calls

### 2. Fix Broken Before Optimizing
- If something doesn't work at all, don't optimize it
- Get basic functionality working first
- Performance improvements come after correctness

### 3. Listen to User Intent, Not Just Words
- When user mentions performance issues, check if it's actually a functionality issue
- When user says "X can come later", focus on core functionality now
- User frustration often indicates solving the wrong problem

### 4. Follow Pragmatic POC Principles
- "Choose the most obvious solution that works"
- "Don't overthink solutions - implement and iterate"
- "Focus on functionality over architectural purity"
- Ship working code, refine later

### 5. Understand the Real Goal
- Always ask: What is the user trying to accomplish?
- Don't get distracted by symptoms or side effects
- Focus on the core workflow that needs to work

## Implementation Checklist for Every Task

### Before Starting Any Work:
1. **Read the existing code** - understand what's there
2. **Identify what's actually broken** - not what seems slow or suboptimal
3. **Find the simplest fix** - usually method names, imports, or basic logic
4. **Verify the fix works** - can the basic workflow complete?
5. **Then and only then** - consider optimizations or enhancements

### After Completing Any Work:
1. **Update tasks.md FIRST** - mark task completed with checkmarks and findings in `.kiro/specs/enhanced-codebase-auditor/tasks.md`
2. **Create memory file** - comprehensive handoff documentation
3. **Update completion log** - document what was proven to work
4. **Commit and push** - proper git workflow with conventional commits
5. **Verify all completion criteria met** - don't skip validation steps

### Red Flags That I'm Going Wrong:
- Building complex solutions for simple problems
- Adding timeouts/retries when basic functionality is broken
- Optimizing performance when core features don't work
- Working from test outputs instead of understanding code
- Focusing on symptoms instead of root causes

### Green Flags That I'm On Track:
- Fixed basic functionality first
- User can complete their core workflow
- Simple, obvious solutions that work
- Code changes are minimal and targeted
- User sees immediate improvement in what they're trying to do

## The Bottom Line

**Make it work. Then make it better.**

Don't build elaborate solutions to fix symptoms. Find the broken method call, fix it, and move on to the next real problem.

**I WILL MAKE SURE TO PRIORITIZE LEARNING FROM THIS AND FOLLOWING ITS BASE APPROACH.**
