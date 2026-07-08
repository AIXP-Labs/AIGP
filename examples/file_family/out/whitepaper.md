# AINP Protocol Whitepaper (illustrative artifact)

> AI-generated example content for the standalone file-family report evidence
> chain. This document is intentionally concise and is not a normative
> specification.

## Positioning

AINP, the AI Neogenesis Protocol, standardizes a complete generation project:
the plan that defines what to create, the content artifact that is generated,
the report evidence that decides whether the generated content is done, and the
feedback record that returns content review to the plan.

## File family and format

The core file is `*.generation.json`. It can be paired with a
`*.generationreport.json` evidence record, optional feedback, and a
`*.ainp.json` generation-space index. In a complete project package, those
planning and evidence files sit beside a first-class content folder. These
files are machine-checkable, but they are still untrusted input until a
consuming system applies its own trust policy.

## Examples

This file-family example demonstrates a low-risk document plan, a hash-locked
report, and a recomputable Markdown artifact. Some report evidence is
intentionally incomplete so the example can show the difference between
structure-valid and release-ready. Its feedback file shows how failed content
review feeds a requested revision back to the plan.

## Governance and honesty boundaries

A valid AINP plan proves declarations and structure, not artifact safety,
truth, originality, rights clearance, or legal compliance. A complete AINP
project also carries content, but trust still depends on report evidence and
external review. Acceptance evidence lives in the generation report and must
stay tied to the exact plan snapshot it judges. Feedback is a structured review
record, not proof that the review is complete or true.
