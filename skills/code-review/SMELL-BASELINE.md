# Code smell baseline

Apply only to changed code. Repository documentation overrides this baseline. Tool-enforced rules do not need review comments. Every smell is a judgement call, never a hard violation.

- **Mysterious Name**: name does not reveal purpose. Rename; if no honest name fits, inspect design.
- **Duplicated Code**: same logic shape appears in several changed places. Consolidate only when shared module increases locality and passes deletion test.
- **Feature Envy**: method reaches into another module's data more than its own. Move behavior toward data owner.
- **Data Clumps**: same fields or parameters travel together. Consider one meaningful project type.
- **Primitive Obsession**: primitive stands in for a domain concept. Use canonical project model when it reduces caller knowledge.
- **Repeated Switches**: same conditional dispatch recurs. Centralize policy or use one explicit dispatcher.
- **Shotgun Surgery**: one logical change forces scattered edits. Move ownership toward one module.
- **Divergent Change**: one module changes for unrelated reasons. Separate ownership along cohesive seams, not arbitrary file size.
- **Speculative Generality**: abstraction, parameter, or hook serves no current requirement. Delete or inline it.
- **Message Chains**: caller navigates deep implementation structure. Put behavior behind owning module's interface.
- **Middle Man**: module delegates without hiding knowledge or complexity. Apply deletion test and remove if complexity vanishes.
- **Refused Bequest**: subtype ignores most inherited behavior. Prefer composition or narrower model.

Before recommending extraction, ask whether it improves locality, depth, or ownership. Do not create shallow modules to satisfy a smell mechanically.
