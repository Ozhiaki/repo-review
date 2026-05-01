# Repo Analysis Seed - Part IV
*A fourth-pass prompt for identifying extractable tools and reusable patterns*

## Why this is separate

The earlier passes analyze taste, spine, and enforcement. This pass looks for portable seeds: small parts of the repo that could live independently.

Do not look for the central abstraction. Look for compact leverage.

## Prompt

You have produced the mature repo analysis. Now identify 5-10 extractable seeds.

An extractable seed may be:

- a single file
- a function or module
- a test harness
- a CLI workflow
- a schema or config pattern
- a small domain-specific checker
- a reusable safety primitive
- a design pattern that could become a standalone article or package

For each seed, provide:

**1. Name**
A clear standalone name.

**2. Source Location**
Exact file/function/module paths.

**3. What It Does**
Plain explanation.

**4. Why It Extracts Cleanly**
Dependencies, boundaries, and what would need to be stubbed or removed.

**5. Standalone Form**
What it could become:
- CLI
- crate/library
- web tool
- Obsidian/Markdown tool
- linter
- GitHub Action
- code pattern
- article/demo

**6. First MVP**
The smallest useful version.

**7. Why It’s Interesting**
What makes it more than a utility.

**8. Extraction Difficulty**
Easy / medium / hard.

## Ranking

End with a ranked list:

1. Best immediate extraction
2. Best weird/creative extraction
3. Best commercially useful extraction
4. Best educational/demo extraction
5. Best design-pattern writeup
