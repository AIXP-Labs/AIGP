# AINP Protocol Whitepaper (illustrative artifact)

> AI-generated example content for the complete AINP project package. This
> document is illustrative content, not a normative specification.

## Positioning

AINP, the AI Neogenesis Protocol, standardizes a complete generation project:
the plan that defines what to create, the content artifact that is generated,
the report evidence that decides whether the generated content is done, and the
feedback record that returns content review to the plan.

## File family and format

The project package keeps the declaration in `AINP.md`, the generation plan and
evidence files in `ainp/`, and this generated content in the project content
folder. That separation lets tools validate the plan and report without
confusing them with the content they describe, while still treating plan and
content as co-equal parts of the project. Because this package is active, its
feedback file closes the reverse direction: plan guides content, content
feedback flows back to the plan.

## Examples

This package demonstrates a release-clean path: the plan declares acceptance
criteria, the report records results and disclosure gates, and the artifact hash
is recomputed from inside the package root. The project checker also confirms
that the feedback record references the same generation id as the plan and
report.

## Governance and honesty boundaries

A valid AINP package proves that `AINP.md`, the AINP plan folder, and the
project content folder are wired together consistently. It does not prove legal
compliance, source truth, rights validity, approval authenticity, downstream
content trust, or feedback truth.
