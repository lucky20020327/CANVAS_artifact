# CANVAS artifact

Companion artifact for **CANVAS: Exploring LLM-Assisted Model-Driven Engineering for Transactional Business Logic**.

This repository provides a sanitized design-to-code example and evaluation results with analysis scripts for RQ1–RQ4. The scripts reproduce statistics and figures from the bundled records without model calls or access to the industrial development environment. The CANVAS implementation and original industrial benchmark are not included.

## Start here

| Goal | Where to start |
|---|---|
| Reproduce the evaluation results | Follow the [experiment quick start](04_experiment_result/README.md#quick-start) |
| Find a paper table or figure | Use the [RQ-to-output guide](04_experiment_result/README.md#find-a-result) |
| Understand metrics and sample counts | Read the [analysis conventions](04_experiment_result/README.md#analysis-conventions) and the RQ-specific notes below them |
| Explore the design-to-code workflow | Follow the example walkthrough below |

## Example walkthrough

The example implements `CheckReaderCardEligibility`: it checks a reader's request, account, existing card records, and document-review status to decide whether a new library card may be issued.

1. Read [the design input](01_design.json) for the entry contract, workflow steps, rule tables, repository operations, and data dependencies.
2. Open [the generated agent workspace](02_agent_workspace/). Start with [the development task](02_agent_workspace/开发需求.md) and [the overall workflow](02_agent_workspace/整体业务流程.md), then inspect the individual steps and supporting contracts. [The handler skeleton](02_agent_workspace/checkreadercardeligibility.cpp) is the starting code.
3. Compare the skeleton with [the generated handler](03_CheckReaderCardEligibilityHandler.cpp).

The example is a fictional case constructed for illustration. Its workspace is rendered programmatically from the design using the CANVAS specification builder, with a stand-in framework guide and neutral file paths. Its identifiers, rules, and code do not correspond to a production interface. It is separate from the 15-handler evaluation benchmark. Design and workspace documents contain Chinese, matching the language used in the illustrated workflow.

## Repository contents

| Path | Contents |
|---|---|
| [01_design.json](01_design.json) | Sanitized design input |
| [02_agent_workspace/](02_agent_workspace/) | Specifications, development guidance, and handler skeleton |
| [03_CheckReaderCardEligibilityHandler.cpp](03_CheckReaderCardEligibilityHandler.cpp) | Generated example implementation |
| [04_experiment_result/](04_experiment_result/README.md) | Evaluation records, analysis and plotting scripts, and precomputed results |
