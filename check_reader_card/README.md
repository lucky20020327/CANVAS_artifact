# CANVAS example: CheckReaderCardEligibility

A sanitized design-to-code example. Identifiers, fields, rules, and code have been rewritten and do not correspond to any production interface. This is not the 15-handler evaluation benchmark.

The materials contain Chinese because the design steps, rule text, and workspace documents are written in Chinese.

The example decides whether a reader may open a new library card: check the request, load the reader account, count card records that have not been removed, and, when the document is not a standard document, check whether review was allowed before deciding.

## Files

1. `01_design.json` — design input. It contains the entry contract, steps, rule tables, repository operations, and data dependencies.
2. `02_agent_workspace/` — agent workspace rendered from that design. The framework guide is a short stand-in, and include paths and framework wording in the coding rules were replaced.
3. `03_CheckReaderCardEligibilityHandler.cpp` — handler completed from the workspace.
