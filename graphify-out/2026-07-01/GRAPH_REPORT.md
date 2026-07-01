# Graph Report - .  (2026-07-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 222 nodes · 290 edges · 18 communities (14 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `51eb626e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 16 edges
2. `RecruiterGraphState` - 12 edges
3. `cn()` - 10 edges
4. `execute_resume_rewrite_modern()` - 8 edges
5. `_run_pipeline()` - 7 edges
6. `JobRecord` - 6 edges
7. `_build_html()` - 6 edges
8. `profile_extraction()` - 6 edges
9. `resume_rewriter_node()` - 6 edges
10. `execute_resume_rewrite()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `JobRecord` --uses--> `RecruiterGraphState`  [INFERRED]
  backend/main.py → recruitement_graph.py
- `AnswersPayload` --uses--> `RecruiterGraphState`  [INFERRED]
  backend/main.py → recruitement_graph.py
- `resume_rewriter_node()` --calls--> `execute_resume_rewrite_modern()`  [EXTRACTED]
  recruitement_graph.py → backend/templates/modern.py
- `gap_analyzer_node()` --calls--> `gap_analysis()`  [EXTRACTED]
  recruitement_graph.py → analyze_gap.py
- `interviewer_node()` --calls--> `generate_targeted_interview_questions()`  [EXTRACTED]
  recruitement_graph.py → interactive_agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Generative AI Implementation Stack** — tailored_resume_aws_bedrock, tailored_resume_rag, tailored_resume_carai, tailored_resume_movie_rec [EXTRACTED 0.90]

## Communities (18 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (30): gap_analysis(), Independent execution layer for Phase 3.     Compares the candidate JSON and jo, Any, generate_targeted_interview_questions(), Analyzes the structural candidate profile and the gap analysis report,     gene, TechnicalInterviewQuestions, profile_extraction(), Independent execution layer for Phase 1 leveraging explicit JSON Mode      and (+22 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (19): INITIAL_NODES, Step, STEP_LABELS, STEPS, ChatbotPopup(), ChatbotPopupProps, Message, NODE_LABELS (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (21): cn(), Button, ButtonProps, buttonVariants, Card, CardContent, CardDescription, CardFooter (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (16): AnswersPayload, download_pdf(), JobRecord, _node_not_yet_reported(), TailorResume — FastAPI Backend Wraps the existing LangGraph recruitement_graph p, Returns True if we haven't sent a node_done for this node yet., Accept resume file + job description, kick off the LangGraph pipeline., SSE stream — yields pipeline node events as they happen. (+8 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (17): devDependencies, eslint, eslint-config-next, tailwindcss, @tailwindcss/postcss, @types/node, @types/react, @types/react-dom (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (17): dependencies, class-variance-authority, clsx, framer-motion, lucide-react, next, @radix-ui/react-dialog, @radix-ui/react-label (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.20
Nodes (13): _build_html(), _build_page_html(), _esc(), execute_resume_rewrite_modern(), _generate_resume_json(), _html_to_pdf(), Modern Resume Template — HTML + WeasyPrint renderer ============================, Call Bedrock Claude to generate resume content as a structured JSON object. (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (11): GapAnalysisReportSchema, SkillMatchSchema, TechnicalGapSchema, BaseModel, CandidateProfileSchema, EducationDetail, ExperienceSchema, extract_text_from_pdf() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.40
Nodes (6): AWS Bedrock, CarAI RAG-based Analysis System, Movie Recommendation System, Nihilent Limited, Retrieval-Augmented Generation (RAG), Uday Salathia

### Community 10 - "Community 10"
Cohesion: 0.67
Nodes (3): Next.js Agent Rules, Claude Configuration, Next.js Project

## Knowledge Gaps
- **82 isolated node(s):** `metadata`, `Step`, `INITIAL_NODES`, `STEPS`, `STEP_LABELS` (+77 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `execute_resume_rewrite_modern()` connect `Community 7` to `Community 0`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `RecruiterGraphState` connect `Community 0` to `Community 3`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `dependencies` connect `Community 6` to `Community 5`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `RecruiterGraphState` (e.g. with `AnswersPayload` and `JobRecord`) actually correct?**
  _`RecruiterGraphState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Independent execution layer for Phase 3.     Compares the candidate JSON and jo`, `TailorResume — FastAPI Backend Wraps the existing LangGraph recruitement_graph p`, `Returns True if we haven't sent a node_done for this node yet.` to the rest of the system?**
  _107 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11051693404634581 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.07741935483870968 - nodes in this community are weakly interconnected._