# AUTOSAR C++14 Core Engineering Guideline

## Source and Scope

- Standard: AUTOSAR C++14, release 18-03.
- Source document: file:///C:/Users/binhh/Downloads/AUTOSAR_RS_CPP14Guidelines.pdf
- Artifact root: artifacts/cpp-standards-guideline
- Manifest: [manifest.json](manifest.json)
- Runbook: [runbook.md](runbook.md)
- Parsed source: [source-markdown.md](source-markdown.md)
- Normalized rules: [rules-normalized.json](rules-normalized.json)
- Relationship map: [rule-relationships.json](rule-relationships.json)
- Rule graph: [rule-graph.mmd](rule-graph.mmd)
- Scope: This document is a synthesized engineering guideline for design, implementation, review, and refactoring. It reduces the AUTOSAR rule corpus to a smaller set of default coding forms that are easier to apply consistently in daily C++14 work.
- Intended reader: developers, reviewers, library owners, toolchain owners, and teams migrating an existing codebase toward a safer and more uniform subset of C++14.
- How to use this guide: treat each family as a default policy. When code departs from the default, require an explicit local reason, review the interaction notes for adjacent rule families, and verify that the deviation does not merely push the defect into another part of the code.
- Non-goal: this document is not a formal compliance matrix and does not replace the source AUTOSAR text for audit evidence. It is a practical engineering guide written in original language.

## Analysis Method

1. The source PDF was parsed into markdown so the full corpus could be searched and clustered without depending on page images or manual copying.
2. The parsed corpus was normalized into 390 rule records. Each record stores a paraphrased title, family assignment, intent, preferred pattern, anti-patterns, conflict-risk notes, obligation level, automation level, and evidence location.
3. A relationship pass produced 337 rule-to-rule links. These links are not just metadata; they expose where a local cleanup is likely to reinforce or destabilize nearby code.
4. Rules were regrouped by engineering purpose rather than AUTOSAR chapter order. The goal was to identify a smaller set of canonical coding habits that satisfy multiple rules at once.
5. Canonical patterns were selected when one default implementation form absorbs several nearby obligations, for example explicit ownership in signatures, exhaustive branching over scoped enums, or one deliberate conversion boundary per expression.
6. Fix-order guidance was derived from both the relationship artifact and the conflict-risk notes in the normalized rules. This is why interface cleanup, type cleanup, ownership cleanup, and exception cleanup are ordered rather than treated as independent chores.
7. The current edition intentionally expands the earlier concise synthesis into a review and migration document. Each family now states engineering objective, default team policy, review prompts, interaction hotspots, and refactoring direction.
8. Representative AUTOSAR rule identifiers are retained for traceability. The prose, examples, and grouping below remain original and paraphrased.

## Core Rule Families

### 1. Toolchain Discipline and Verifiable Baseline

#### Engineering Objective

The toolchain is part of the product behavior, not just a build convenience. If compiler mode, warning policy, numeric model, or analysis configuration change under the code, then source-level discipline stops being a trustworthy safety argument.

#### Why This Family Comes First

Most later rule families assume that the build is already truthful. A warning-tolerant build, a permissive extension mode, or an undocumented floating-point model can make apparently compliant code behave differently across builds and render static-analysis findings inconsistent.

#### Default Team Policy

1. Build in strict ISO C++14 mode and prohibit nonstandard compiler extensions as design features.
2. Freeze the compiler, standard library, linker, and analysis-tool versions that participate in the release baseline.
3. Treat warnings as defects. If a warning is noisy, change code, tool configuration, or suppression scope explicitly rather than living with tolerated noise.
4. Document the numeric model whenever floating-point, scaled-integer, or fixed-point behavior matters for correctness.
5. Ban `long double` and other implementation-sensitive numeric choices unless the project profile explicitly justifies them.
6. Check domain, pole, and range behavior around math-library use rather than assuming the toolchain's defaults are harmless.
7. Define code-metric limits early enough that violations are prevented during ordinary development, not merely discovered at integration time.
8. Run static analysis in the same configuration family as the production build so findings correspond to the executable that will actually ship.

#### Preferred Canonical Pattern

Code should compile as if it will be built on a second conforming toolchain tomorrow. Express assumptions in code where practical, pin them in the build where necessary, and keep the diagnostic baseline stable enough that a new warning always means something changed.

#### Preferred Example Form

```cpp
#include <cstdint>

static_assert(sizeof(std::uint32_t) == 4U, "unexpected toolchain contract");

constexpr std::uint32_t kCycleMs{10U};
constexpr bool kUsesIeee754{true};
```

#### What Good Code Review Looks For

- The code does not rely on vendor-only syntax or behavior that disappears under strict standard mode.
- Numeric assumptions are declared or checked near the code that depends on them.
- Warning suppressions, if any exist, are narrowly scoped, justified, and exceptional rather than normal.
- Build and analysis settings are treated as versioned project inputs, not personal workstation choices.

#### What Strong Code Looks Like

- `constexpr`, `static_assert`, and explicit types make build-time assumptions visible.
- Floating-point and fixed-point usage is deliberate, documented, and isolated at domain boundaries.
- Analysis results are reviewed continuously, so warnings are not deferred into an unread backlog.
- Metrics serve as guardrails for maintainability, not as after-the-fact reporting.

#### Common Anti-Patterns

- Compiler extensions used as an informal language dialect.
- Warning suppressions added as routine cleanup rather than investigated as design signals.
- Different local and CI warning profiles.
- Math-library calls used without explicit error handling or domain assumptions.
- Optimization settings that relax standard compliance without corresponding project approval.

#### Interaction Hotspots

- `A0-4-1` and `A0-4-2` are tightly coupled: if floating-point behavior matters, the allowed type set and implementation model have to be fixed together.
- `A1-1-1`, `A1-1-2`, and `A1-1-3` act as anchor rules for most later families because they define what "normal C++14" even means in the project.
- `A1-4-3` reinforces warning-free builds; it is the bridge between toolchain policy and day-to-day code review.
- `M0-3-1` links runtime-failure minimization to analysis and testing, which means build discipline and verification discipline cannot be split cleanly.

#### Refactoring Guidance

1. Freeze the compiler, diagnostics, and analysis profile before touching source.
2. Remove extension dependence and warning suppressions that would invalidate later cleanups.
3. Make numeric assumptions explicit at the boundary where they matter.
4. Re-run analysis after each policy tightening step so false confidence does not survive into deeper refactors.

#### Fix-Order Trap

If you start by cleaning local casts, exceptions, or control flow before the build profile is stable, you often have to redo the same work after warnings, standard mode, or numeric assumptions change.

#### Representative Rule Clusters

- Conformance and diagnostics: `A1-1-1`, `A1-1-2`, `A1-1-3`, `A1-2-1`, `A1-4-3`
- Numeric model and arithmetic environment: `M0-4-1`, `M0-4-2`, `A0-4-1`, `A0-4-2`, `A0-4-4`
- Analysis and project baseline: `M0-3-1`, `A1-4-1`

### 2. Lexical Clarity and Symbol Hygiene

#### Engineering Objective

The token stream, literal spellings, names, and comments should be boring enough that humans and tools read the same program. Source text should not hide meaning, smuggle behavior, or force reviewers to decode naming accidents.

#### Why This Family Matters

Many defects that look semantic in code review begin as lexical ambiguity. Hidden identifiers, commented-out code, ambiguous literals, or loose comment policy make the program harder to analyze before control flow or type rules are even applied.

#### Default Team Policy

1. Use only the standard source character set and avoid alternative token forms that reduce portability or readability.
2. Delete commented-out code instead of preserving it in place.
3. Use comments to explain local design intent, assumptions, or safety reasoning, not to repeat what the code already says.
4. Keep file names aligned with the logical entity they provide.
5. Prevent identifier hiding across nested scopes, namespaces, classes, and enumerations.
6. Use unambiguous literals, uppercase suffixes where required, and named constants instead of sprinkling raw values through logic.
7. Standardize on `nullptr` as the only null-pointer constant.
8. Prefer symbolic names and typed constants over magic numbers or overloaded literal conventions.
9. Keep character and string spellings portable and explicit enough that text processing, parsing, and auditing stay predictable.

#### Preferred Canonical Pattern

Choose names, literals, and comments so that the source code does not require a second decoding layer. A reviewer should be able to tell what is a type, what is a value, what is a null pointer, and what is merely historical clutter.

#### Preferred Example Form

```cpp
enum class Mode : std::uint8_t { off, heat, cool };

constexpr std::uint8_t kRetryLimit{3U};
Mode mode{Mode::off};
```

#### What Good Code Review Looks For

- There is no commented-out logic, stale workaround block, or "disabled" code path pretending to be documentation.
- Inner scopes do not hide outer declarations in ways that change meaning silently.
- Literal spellings are deliberate and consistent, especially around unsigned values, hex constants, and character handling.
- Names communicate role and scope clearly enough that reviewers do not need context reconstruction to understand a declaration.

#### What Strong Code Looks Like

- Null handling is explicit because `nullptr` and references encode intent directly.
- Comments explain why a constraint exists, not what the next line already states.
- File names, identifiers, and enumerators line up with the abstractions they serve.
- Character, string, and numeric literals are written in forms that do not depend on tribal knowledge.

#### Common Anti-Patterns

- Octal or ambiguous numeric literals.
- `0` or `NULL` used as null pointers.
- Reused names across nested scopes that hide types, functions, or enumerators.
- Comments used as graveyards for deleted logic.
- Raw literals spread across business logic with no symbolic domain meaning.
- Nonportable character handling or mixed string encodings.

#### Interaction Hotspots

- `A5-10-1` reinforces `A4-10-1`: once `nullptr` is standardized, pointer comparison rules become easier to review and safer to enforce.
- Identifier-hiding rules interact with linkage and overload-visibility rules in the interface family; a naming cleanup can uncover latent API ambiguity.
- Character-handling rules interact with library-boundary rules such as `A21-8-1` and `A27-0-4`, especially when legacy C strings or character APIs are present.
- Comment policy interacts with control-flow cleanup because commented-out code often masks dead or infeasible branches that should be deleted instead.

#### Refactoring Guidance

1. Delete commented-out code first so review sees the real program.
2. Replace `0` and `NULL` with `nullptr` before deeper pointer or ownership work.
3. Rename hidden identifiers and normalize file names before expression cleanup so meaning stops drifting under refactor.
4. Replace magic literals with typed constants once interface types are stable.

#### Fix-Order Trap

If you leave naming, literal, and comment ambiguity in place while repairing expressions or ownership, the same readability defects tend to reappear because the code still lacks a stable surface vocabulary.

#### Representative Rule Clusters

- Source text and comments: `A2-3-1`, `A2-5-1`, `A2-5-2`, `M2-7-1`, `A2-7-1`, `A2-7-2`, `A2-7-3`, `A2-7-5`
- File and identifier hygiene: `A2-8-1`, `A2-8-2`, `M2-10-1`, `A2-10-1`, `A2-10-4`, `A2-10-5`, `A2-10-6`
- Literals and nulls: `A2-13-1`, `A2-13-4`, `A2-13-5`, `A2-13-6`, `M2-13-2`, `M2-13-3`, `M2-13-4`, `A4-10-1`, `M4-10-2`, `A5-1-1`, `A21-8-1`

### 3. Interface and Translation Unit Boundaries

#### Engineering Objective

A declaration should communicate one stable contract with the smallest necessary visibility. Headers, namespaces, linkage, and function signatures together define how code can be used, not just how it happens to compile today.

#### Why This Family Matters

Once interface boundaries drift, every later repair becomes more expensive. Ownership, exceptions, templates, and control flow all accumulate around the declared surface, so weak boundaries multiply downstream churn.

#### Default Team Policy

1. Keep headers self-contained and safe to include from multiple translation units.
2. Declare each shared type, object, or function in one clear place.
3. Minimize linkage scope and visibility so names are available only where needed.
4. Keep the global namespace nearly empty; prefer named namespaces and local scope.
5. Avoid namespace-wide `using` directives and other imports that hide the real source of names.
6. Do not use block-scope function declarations or ellipsis-based interfaces.
7. Express input, output, ownership, and nullability directly in the signature.
8. Return structured results instead of output parameters when multiple values must be conveyed.
9. Prefer references for non-null inputs and reserve pointers for optionality or explicit lifetime protocols.
10. Use smart pointers in interfaces only when the signature truly needs to express ownership transfer or sharing.
11. Keep overload sets visible and coherent from the call site.

#### Preferred Canonical Pattern

A good signature answers four questions immediately: what comes in, what goes out, who owns what after the call, and whether null is a valid state. The declaration should not outsource these answers to comments or convention.

#### Preferred Example Form

```cpp
struct ReadResult {
  bool ok;
  std::int32_t value;
};

ReadResult readSensor(const Sensor& sensor);
```

#### What Good Code Review Looks For

- Headers can be included independently without fragile include ordering.
- There is one obvious declaration site for each shared contract.
- Function signatures do not rely on output parameters, comment-based ownership, or hidden nullability.
- Call sites can see the relevant overload set without namespace tricks or surprise imports.
- Smart pointers appear in interfaces only when they encode real lifetime semantics.

#### What Strong Code Looks Like

- Header files express stable contracts and do not leak implementation mechanics.
- Linkage and namespace choices shrink the visible surface area of the program.
- Output values come back as value objects or result structs that are easy to validate and extend.
- Interface review can be done from the declaration alone because ownership and nullability are already explicit.

#### Common Anti-Patterns

- Duplicated declarations scattered across files.
- Namespace-wide `using` directives in headers or large scopes.
- Output parameters used as a default API style.
- Optional values disguised as references or informal conventions.
- Hidden overloads, block-scope declarations, or anonymous behavior at linkage boundaries.
- Smart pointers passed around by habit rather than meaning.

#### Interaction Hotspots

- `A8-4-8`, `A8-4-10`, and `A8-4-11` form a strong cluster: once output parameters disappear and nullability is explicit, smart-pointer semantics become clearer and more local.
- `A8-4-12` and `A8-4-13` reinforce the ownership family by requiring signature shapes that match `unique_ptr` and `shared_ptr` semantics.
- Linkage rules interact with lexical hygiene because hidden identifiers and hidden overloads often show up together.
- Exception policy depends on interface honesty. If callers cannot tell who owns results or whether failure is returned or thrown, failure handling becomes inconsistent immediately.

#### Refactoring Guidance

1. Make headers self-contained and remove namespace pollution.
2. Stabilize declarations and ownership semantics in signatures before touching implementation details.
3. Replace output parameters with value returns or result objects.
4. Convert pointer parameters into references or optional-pointer forms only after nullability policy is clear.
5. Re-check override sets, templates, and exceptions after signature cleanup because boundary changes propagate widely.

#### Fix-Order Trap

If you postpone interface cleanup until after local implementation refactors, you will often reintroduce the same defects at call boundaries because the public contract still encourages them.

#### Representative Rule Clusters

- Header and ODR discipline: `A3-1-1`, `M3-2-2`, `M3-2-3`, `M3-2-4`, `A3-3-1`
- Scope and namespace control: `M3-1-2`, `M3-4-1`, `M7-3-1`, `M7-3-3`, `M7-3-4`, `A7-3-1`, `M7-3-6`
- Signature semantics: `A8-4-1`, `A8-4-3`, `A8-4-4`, `A8-4-7`, `A8-4-8`, `A8-4-9`, `A8-4-10`, `A8-4-11`, `A8-4-12`, `A8-4-13`
- Standard-namespace boundary: `A17-6-1`

### 4. Deterministic Control Flow and Reachability

#### Engineering Objective

Execution paths should be easy to enumerate, hard to misunderstand, and easy for tools to prove. Control flow should expose the normal path and the abnormal path instead of burying them in nesting or subtle state.

#### Why This Family Matters

Control-flow defects are often secondary symptoms of weak contracts, ambiguous state, or hidden preprocessor branches. Even so, once they exist, they block reliable review, testing, and failure analysis.

#### Default Team Policy

1. Delete unreachable, infeasible, and unused logic rather than leaving it in place.
2. Use every non-void return value unless the interface is explicitly documented otherwise.
3. Put braces on all branches and loop bodies.
4. Close `if` and `else if` chains with an explicit `else`.
5. Keep `switch` statements well formed, exhaustive, and terminated clearly.
6. Use `default` as the final clause in multiway branching.
7. Keep loop control simple: one obvious counter, no floating-point loop counters, and no hidden mutation of the control variable.
8. Avoid `do` loops and prohibit `goto`.
9. Make boolean conditions actually boolean instead of relying on implicit truthiness.
10. Keep all exit paths from non-void functions explicit.

#### Preferred Canonical Pattern

Prefer guard clauses, explicit branching, and loops whose control state can be described in one sentence. A reviewer should not need simulation to know what paths exist.

#### Preferred Example Form

```cpp
if (!isReady) {
  reportFault();
  return;
}

switch (mode) {
  case Mode::off:
    stop();
    break;
  case Mode::heat:
    heat();
    break;
  case Mode::cool:
    cool();
    break;
  default:
    reportFault();
    break;
}
```

#### What Good Code Review Looks For

- No dead branch exists purely because older code once used it.
- Multiway branching is exhaustive and the exceptional path is obvious.
- Loop counters are visible, stable, and not modified in several places.
- Branch bodies are structured enough that hidden fallthrough, null statements, or side-effect conditions are easy to spot.
- Non-void functions never rely on implicit or accidental exits.

#### What Strong Code Looks Like

- Precondition failures are handled near function entry.
- State machines use scoped enums and exhaustive `switch` blocks.
- Loops look like counted loops or range-oriented traversal rather than miniature interpreters.
- Cleanup removes truly unused parameters, locals, and helper functions instead of preserving them for fear of churn.

#### Common Anti-Patterns

- Dead code and infeasible paths kept as "future hooks".
- Partially formed `switch` statements or missing `default` behavior.
- `goto`-based cleanup or control transfer.
- `do` loops used as a general looping style.
- Conditions with non-boolean semantics or hidden side effects.
- Loop counters modified inside the body, condition, and increment fields at the same time.

#### Interaction Hotspots

- `A7-2-5` reinforces `M6-4-6`: enum-based state modeling and exhaustive `switch` handling belong together.
- `A6-5-3` reinforces the preprocessor family because macro-heavy loops hide the very control variables reviewers need to trust.
- `A0-1-2` ties interface design to control flow: ignored results often create fake linear flow while discarding real error or status information.
- Dead-code cleanup often exposes deeper type or initialization defects, so it should follow interface and ownership clarification rather than precede it blindly.

#### Refactoring Guidance

1. Remove dead declarations and dead branches only after you understand the contract they were compensating for.
2. Convert ambiguous conditions into explicit boolean expressions.
3. Normalize branching form and loop control before attempting micro-optimizations.
4. Replace implicit state with scoped enums when exhaustive branching matters.
5. Re-run tests and analysis after path cleanup because deleting unused code can expose missing initialization or missing return behavior.

#### Fix-Order Trap

If you flatten control flow before interface and ownership intent are clear, you risk deleting code that was incorrectly compensating for a deeper problem and then having to rebuild the path under a new contract.

#### Representative Rule Clusters

- Reachability and unused constructs: `M0-1-1`, `M0-1-2`, `M0-1-3`, `M0-1-10`, `A0-1-3`, `A0-1-4`, `A0-1-5`, `A0-1-6`
- Return and failure checking: `A0-1-2`, `M0-3-2`, `A8-4-2`
- Branch and loop structure: `M6-3-1`, `M6-4-1`, `M6-4-2`, `M6-4-3`, `M6-4-5`, `M6-4-6`, `A6-4-1`, `A6-5-1`, `A6-5-2`, `M6-5-3`, `A6-6-1`

### 5. Explicit Types, Values, and Conversion Boundaries

#### Engineering Objective

Type, value, and conversion intent should be explicit enough that arithmetic and expression behavior never depend on reader guesswork. The code should reveal where representation changes happen and why.

#### Why This Family Matters

C++ allows a large amount of implicit behavior in expressions. Left unmanaged, that flexibility spreads signedness bugs, narrowing conversions, precedence mistakes, and unsafe casts across otherwise clean code.

#### Default Team Policy

1. Use fixed-width integer types when size and signedness matter to the domain.
2. Prefer scoped enums with explicit underlying types for state and constrained value sets.
3. Use brace initialization by default to reduce narrowing surprises.
4. Perform one deliberate conversion at one named boundary instead of layering conversions inside large expressions.
5. Avoid implicit signedness changes, narrowing, and mixed integer-floating behavior.
6. Do not compare floating-point values for exact equality in ordinary logic.
7. Restrict bitwise logic to explicit unsigned domains.
8. Parenthesize logical expressions when readers would otherwise reconstruct precedence manually.
9. Ban C-style casts and `reinterpret_cast`.
10. Avoid pointer-integer conversions and pointer arithmetic beyond tightly bounded array-style access.
11. Keep magic values out of business logic by promoting them to typed constants.

#### Preferred Canonical Pattern

Choose the domain type first, then convert once into it, then continue the computation inside that type. If the expression needs several conversions to make sense, the boundary is in the wrong place.

#### Preferred Example Form

```cpp
constexpr std::int32_t kScale{16};

const auto scaledCount =
    static_cast<std::int32_t>(rawCount) * kScale;
```

#### What Good Code Review Looks For

- The reviewer can point to the exact line where a conversion happens and explain why it is safe.
- Signedness and width are consistent throughout arithmetic chains.
- Casts are rare, named, and local instead of sprayed across call sites.
- Floating-point usage is isolated and not compared as if it were exact integer math.
- Operators and precedence do not require mental disassembly to understand side effects.

#### What Strong Code Looks Like

- Domain types are chosen at API boundaries, not repaired after the fact in the middle of computations.
- Expressions are broken into named temporaries before they become safety puzzles.
- Boolean conditions are actually `bool`.
- Bitwise operations live in explicit low-level domains where unsigned behavior is expected.

#### Common Anti-Patterns

- Mixed signed and unsigned arithmetic.
- Implicit narrowing in assignments or return values.
- Hidden promotions inside long expressions.
- C-style casts or `reinterpret_cast` used as routine escape hatches.
- Pointer and integer conversions used to sidestep type design.
- Float equality used as control logic.

#### Interaction Hotspots

- `A3-9-1` and `A7-2-1..A7-2-3` connect domain modeling to numeric safety: explicit integer types and scoped enums make later control flow and API review simpler.
- `A18-0-2` brings library conversions into the same family: string-to-number parsing is still a conversion boundary and should be reviewed as such.
- `A21-8-1` connects character handling to conversion discipline, especially when legacy character APIs are still present.
- Many ownership and interface problems first appear as cast noise, so type cleanup should precede lifetime tuning.

#### Refactoring Guidance

1. Normalize public and frequently used boundary types first.
2. Replace implicit conversions with one named conversion at the edge of the computation.
3. Break complex expressions into typed temporaries before changing arithmetic behavior.
4. Remove unsafe cast forms only after the surrounding types and interfaces are stable.

#### Fix-Order Trap

If you attack local casts before deciding the correct interface and domain types, the same conversion bugs will reappear at every call site and storage boundary.

#### Representative Rule Clusters

- Domain types and enums: `A3-9-1`, `A7-2-1`, `A7-2-2`, `A7-2-3`, `A7-2-4`, `A7-2-5`
- Implicit and explicit conversion discipline: `A4-7-1`, `M5-0-3`, `M5-0-4`, `M5-0-5`, `M5-0-6`, `M5-0-9`, `M5-0-20`, `M5-0-21`, `A5-2-2`, `A5-2-4`
- Expression safety and precedence: `A5-0-2`, `A5-2-6`, `M5-2-10`, `M5-14-1`, `A5-16-1`, `M6-2-2`, `M5-19-1`, `M5-8-1`

### 6. Ownership, Lifetime, and Initialization

#### Engineering Objective

Every resource should have one obvious owner, one obvious lifetime story, and one obvious initialization point. Reviewers should never have to infer who frees memory, who may outlive what, or whether a value is valid before first use.

#### Why This Family Matters

Ownership mistakes cascade into leaks, use-after-free, double deletion, invalid iterator use, stale references, and untruthful exception guarantees. It is one of the highest-churn families because local repairs frequently require interface changes.

#### Default Team Policy

1. Prefer automatic storage duration for objects that do not outlive the current scope.
2. Use RAII wrappers, containers, and value types before considering manual heap management.
3. Ban `malloc`, `calloc`, `realloc`, and `free`.
4. Do not call `new` or `delete` explicitly in ordinary code.
5. Use `std::unique_ptr` for exclusive ownership and `std::shared_ptr` only when shared lifetime is genuinely required.
6. Use `std::weak_ptr` for non-owning observation of shared ownership graphs.
7. Use `std::make_unique` and `std::make_shared` to construct owned objects.
8. Initialize all memory before first read, preferably with brace or member initialization.
9. Do not access objects outside their lifetime, return pointers to shorter-lived objects, or delete incomplete types.
10. Keep delete form and allocation form matched only at the narrowest compatibility seams where raw allocation still exists.
11. Treat dynamic memory behavior as a system-level property that must be deterministic, bounded, and failure-analyzed if the project permits it at all.

#### Preferred Canonical Pattern

Make lifetime visible in the type system. Most objects should be plain values or container elements. When dynamic lifetime is unavoidable, ownership should be expressed in the declaration rather than scattered across conventions and comments.

#### Preferred Example Form

```cpp
class Session {
public:
  explicit Session(std::unique_ptr<Transport> transport) noexcept
      : transport_(std::move(transport)) {}

private:
  std::unique_ptr<Transport> transport_;
};
```

#### What Good Code Review Looks For

- The reviewer can point to the unique owner or shared-ownership boundary immediately.
- Construction and destruction happen through types, not through paired comments or cleanup folklore.
- Member and local variables are initialized before any control flow can read them.
- Raw pointers, if they remain, are obviously non-owning and short-lived.
- Dynamic allocation policy is explicit and justified rather than assumed.

#### What Strong Code Looks Like

- Most APIs consume or return values, references, containers, or smart pointers whose semantics are obvious.
- Constructors establish invariant state instead of postponing initialization into helper calls.
- Dynamic allocation is rare, localized, and supported by deterministic behavior analysis.
- Smart pointers appear because they model ownership correctly, not because they are fashionable.

#### Common Anti-Patterns

- Raw owning pointers.
- `new`/`delete` pairs distributed across multiple call sites.
- `malloc`/`free` mixed into C++ object lifetimes.
- Returning pointers or references to automatic objects.
- Reading from members before initialization.
- Deleting incomplete types or dereferencing null.
- Passing already-owned raw pointers into unrelated smart pointers.
- Dynamic allocation introduced into real-time paths without bounded behavior analysis.

#### Interaction Hotspots

- `A8-4-11`, `A8-4-12`, and `A8-4-13` connect interface design directly to ownership semantics. Once signature intent is clear, many local pointer defects disappear.
- `A12-0-1`, `A12-8-2`, and `A15-5-1` connect ownership to class invariants and truthful `noexcept` promises.
- `A18-5-1..A18-5-8` and `A20-8-1..A20-8-7` extend the family into the standard library and memory model, which means ownership policy is not confined to core language features.
- Container and iterator rules in the library family depend on lifetime discipline because invalid iterators and dangling references are ownership bugs in another costume.

#### Refactoring Guidance

1. Replace raw owners with values, containers, or RAII wrappers first.
2. Move ownership semantics into interfaces next so callers can see the new contract.
3. Normalize initialization through constructors and brace initialization.
4. Only after ownership is stable should you harden `swap`, move operations, and `noexcept` guarantees.
5. Revisit container and iterator usage after lifetime cleanup because dangling access patterns often surface only then.

#### Fix-Order Trap

If you try to finalize exception guarantees or polymorphic behavior before lifetime semantics are stable, those guarantees will usually be false or incomplete and will need to be revised again.

#### Representative Rule Clusters

- Lifetime boundaries: `A3-8-1`, `M7-5-1`, `M7-5-2`, `A7-5-1`, `A5-3-2`, `A5-3-3`
- Initialization discipline: `A8-5-0`, `A8-5-1`, `M8-5-2`, `A8-5-2`, `A8-5-3`, `A12-6-1`
- Dynamic memory and smart pointers: `A18-1-4`, `M18-2-1`, `A18-5-1`, `A18-5-2`, `A18-5-3`, `A18-5-5`, `A18-5-6`, `A18-5-7`, `A18-5-8`, `A20-8-1`, `A20-8-2`, `A20-8-3`, `A20-8-4`, `A20-8-5`, `A20-8-6`, `A20-8-7`

### 7. Stable Class Invariants and Polymorphism

#### Engineering Objective

Class declarations should make valid state, copy and move semantics, inheritance intent, and virtual behavior obvious. A class should declare its contract instead of expecting readers to infer it from scattered implementation details.

#### Why This Family Matters

Once class invariants are fuzzy, every later change becomes risky: constructors, destructors, swap, move, polymorphism, and exception guarantees all start working against each other instead of reinforcing one another.

#### Default Team Policy

1. Use composition for has-a relationships and public inheritance only for real subtype behavior.
2. Make constructors explicit when implicit conversion is not the point of the type.
3. Keep data private by default and force invariants through member functions or carefully controlled construction.
4. Define or delete special members deliberately rather than inheriting accidental behavior.
5. Mark overriding functions with `override` and terminal hierarchies or behavior with `final`.
6. Give polymorphic base classes virtual destructors.
7. Keep default arguments consistent across overrides or avoid them on virtual interfaces.
8. Keep initialization order aligned with declaration order and do not depend on hidden member ordering.
9. Ensure copy, move, and swap behavior preserve invariants rather than merely compile.
10. Avoid inheritance structures that exist only to share code.

#### Preferred Canonical Pattern

A class contract should be obvious from the declaration: what creates a valid object, whether the type can be copied or moved, how polymorphism works, and who is allowed to mutate state.

#### Preferred Example Form

```cpp
class IDevice {
public:
  virtual ~IDevice() = default;
  virtual void start() = 0;
};

class Heater final : public IDevice {
public:
  explicit Heater(Config config);
  void start() override;

private:
  Config config_;
};
```

#### What Good Code Review Looks For

- The class declaration makes invariant state and ownership visible.
- Constructors and special members are explicit enough that copy and move behavior are intentional.
- Virtual behavior is marked and safe, not accidental.
- Inheritance expresses subtype relationships, not code reuse shortcuts.
- Public data does not bypass invariant enforcement.

#### What Strong Code Looks Like

- Constructors fully establish valid state.
- Polymorphic bases are minimal and stable.
- Move and copy operations reflect real ownership and value semantics.
- Hierarchies are shallow enough that review can reason about override behavior locally.

#### Common Anti-Patterns

- Inheritance used only to borrow implementation.
- Non-virtual destruction of polymorphic bases.
- Default arguments drifting across overrides.
- Public mutable data on stateful types.
- Accidental copyability or movability.
- `noexcept` or swap promises added before class ownership and invariants are settled.

#### Interaction Hotspots

- `M8-3-1` and `A10-2-1` connect override behavior to default arguments and hierarchy safety.
- `A12-8-5` reinforces `A12-8-2`: self-assignment and move safety directly affect whether `swap` and related operations can be trusted.
- Ownership family rules define what copy and move can honestly promise.
- Exception rules rely on class invariants being strong enough that failure handling does not leave partially valid objects behind.

#### Refactoring Guidance

1. Clarify invariant state and access control before touching performance or exception annotations.
2. Delete or default special members deliberately once ownership semantics are known.
3. Flatten or replace inheritance used only for reuse.
4. Add `override` and `final` once hierarchy intent is stable.
5. Revisit move, swap, and `noexcept` only after copy and destruction semantics are trustworthy.

#### Fix-Order Trap

If you stamp `noexcept`, `final`, or forwarding constructors onto an unstable class contract, you lock in assumptions that later ownership or invariant fixes may invalidate.

#### Representative Rule Clusters

- Inheritance and virtual safety: `A10-0-1`, `A10-0-2`, `A10-2-1`, `A10-3-1`, `A10-3-2`, `M10-3-3`, `A10-4-1`, `M11-0-1`
- Data and special-member policy: `A11-0-1`, `A11-0-2`, `A12-1-1`, `A12-4-1`, `A12-4-2`, `A12-7-1`
- Copy, move, swap, and invariants: `A12-0-1`, `A12-8-1`, `A12-8-2`, `A12-8-5`, `M8-3-1`

### 8. Constrained Templates and Compile-Time Code

#### Engineering Objective

Generic and compile-time code should fail early, locally, and read like ordinary code. Template mechanisms should narrow variation, not create a second language that only a few engineers can review safely.

#### Why This Family Matters

Templates and compile-time features amplify mistakes rapidly because every ambiguous contract is instantiated in many places. The right default is not "maximum genericity"; it is the smallest generic surface that stays analyzable.

#### Default Team Policy

1. Use `constexpr` for compile-time facts and `const` for immutable runtime state.
2. Use `auto` only where the type is obvious from the right-hand side or where the language requires it for clarity.
3. Prefer `using` aliases over `typedef`.
4. Place template constraints or `static_assert` checks close to the template definition.
5. Use trailing return types when the return type depends on template parameters.
6. Keep specializations near their primary templates and avoid scattered customization.
7. Prefer simple overload sets or concrete helpers over clever forwarding traps.
8. Avoid dependent-name ambiguity, hidden deduction, and template forms that conceal important safety-relevant types.
9. Keep compile-time mechanisms aligned with the same ownership, interface, and exception rules as runtime code.

#### Preferred Canonical Pattern

Write templates as if their first job is to fail clearly when misused. If a template requires a hidden contract or extensive surrounding lore, it is already too generic for safe routine use.

#### Preferred Example Form

```cpp
template <typename T>
auto toIndex(const T& value) -> std::size_t
{
  static_assert(std::is_integral<T>::value, "integral required");
  return static_cast<std::size_t>(value);
}
```

#### What Good Code Review Looks For

- Template assumptions are explicit near the declaration.
- Deduced types are not hiding safety-relevant behavior.
- Specializations and overloads are local enough that reviewers can see the whole contract.
- `constexpr` values replace runtime magic where compile-time determination is intended.
- Compile-time code still obeys ordinary interface and ownership discipline.

#### What Strong Code Looks Like

- Most generic helpers are small, local, and obviously constrained.
- Errors appear near misuse, not as deep instantiation noise.
- Return types and deduction behavior are visible enough that readers know what the template produces.
- Compile-time constants reduce runtime ambiguity without turning interfaces into metaprogramming puzzles.

#### Common Anti-Patterns

- Unconstrained templates that accept far more than intended.
- Forwarding constructors that hijack overload resolution.
- `auto` used where the hidden type matters for correctness review.
- Specializations far from the primary template.
- Compile-time code used to bypass ordinary type and interface clarity.

#### Interaction Hotspots

- Template signatures inherit the same nullability, ownership, and result-shape concerns as ordinary functions.
- Class-invariant rules matter for forwarding constructors and generic wrappers because template convenience can destabilize object contracts quickly.
- Expression and conversion rules still apply: generic code is not an excuse for vague types or loose casts.
- Library-boundary rules matter when templates are built over containers, iterators, comparators, or smart pointers.

#### Refactoring Guidance

1. Stabilize ordinary interfaces before templating them.
2. Add local constraints and visible return types next.
3. Remove hidden deduction and forwarding traps.
4. Only then decide whether a generic helper should remain generic or collapse to simpler overloads.

#### Fix-Order Trap

If you template unstable interfaces too early, every later contract change multiplies through overload sets, specializations, and diagnostics, turning a local repair into a system-wide churn event.

#### Representative Rule Clusters

- Compile-time constants and deduction policy: `A7-1-1`, `A7-1-2`, `A7-1-5`, `A7-1-6`, `A8-2-1`
- Template declaration and specialization safety: `A14-1-1`, `A14-5-1`, `M14-6-1`, `A14-7-1`, `A14-7-2`, `A14-8-2`
- Local readability and declaration style: `A7-1-7`, `A7-1-8`, `A7-1-9`

### 9. Exceptions and Failure Signaling

#### Engineering Objective

Failure paths should be explicit, bounded, and compatible with the surrounding invariants. The important question is not "exceptions or return codes" in the abstract, but whether a subsystem uses one clear failure protocol per interface and preserves state correctly when things go wrong.

#### Why This Family Matters

Failure handling leaks into every other family. Weak ownership makes cleanup unreliable, weak interfaces make failure channels ambiguous, and weak class invariants make recovery unsafe.

#### Default Team Policy

1. Choose one primary failure channel per interface and keep it consistent.
2. If exceptions are enabled for a subsystem, throw objects with meaningful types and catch where code can either restore invariants or translate policy.
3. If a subsystem uses status returns instead of exceptions, do not quietly mix exceptions back in from helper code without an explicit boundary translation.
4. Never throw pointers or rely on `errno` as a normal diagnostic channel.
5. Do not ignore error information produced by an interface.
6. Keep destructors, cleanup paths, and swap operations non-throwing when the contract says they are.
7. Add `noexcept` only when ownership, move, and destruction behavior truly justify it.
8. Validate external input before parsing or converting it.
9. Check string-to-number conversion failure states and similar boundary failures explicitly.

#### Preferred Canonical Pattern

Failure policy belongs at subsystem boundaries. Within a subsystem, keep the chosen failure protocol uniform enough that reviewers do not have to guess whether a path reports by return value, exception, global state, or silent side effect.

#### Preferred Example Form

```cpp
class ConfigError : public std::exception {
public:
  const char* what() const noexcept override { return "invalid config"; }
};

void swap(Buffer& other) noexcept;
```

#### What Good Code Review Looks For

- The failure channel for an interface is visible from the declaration and surrounding subsystem policy.
- Error information is checked instead of discarded.
- Cleanup paths preserve class invariants whether control exits normally or abnormally.
- `noexcept` annotations are justified by real ownership and move semantics.
- Input parsing and conversion code validates both the data and the failure mode.

#### What Strong Code Looks Like

- Failure handling is localized to boundaries that can make policy decisions.
- Exception types are domain-relevant enough that catch sites retain meaning.
- Status-return APIs have explicit checked results rather than informal boolean folklore.
- Recovery logic does not depend on hidden global state such as `errno`.

#### Common Anti-Patterns

- Mixing return codes and exceptions in the same interface family.
- Throwing pointers or throwing from contexts that cannot preserve invariants.
- Catch-all handlers that erase fault meaning.
- `noexcept` attached early as a performance label rather than a truth statement.
- Ignored error results or unchecked conversions.
- External input trusted before validation.

#### Interaction Hotspots

- `A15-5-1` reinforces `A12-8-2` and `A12-0-1`: truthful exception guarantees depend on correct move, swap, and invariant behavior.
- `M0-3-2` links control flow to failure handling by requiring returned error information to be used.
- `A18-0-2`, `M19-3-1`, and `A27-0-1` connect library boundaries and input validation to the same family because parse and I/O faults are still failures that need a defined policy.
- Ownership cleanup usually has to happen before exception cleanup because the safety of unwinding depends on the lifetime model.

#### Refactoring Guidance

1. Decide failure policy per subsystem first.
2. Remove mixed signaling protocols from interfaces.
3. Strengthen ownership and invariants so cleanup is trustworthy.
4. Add or tighten `noexcept` annotations last.
5. Revisit parsing, conversion, and external input handling once the boundary policy is explicit.

#### Fix-Order Trap

If you stamp `noexcept` or exception-catching strategy onto code whose ownership and invariants are still unstable, the result may be formally annotated but behaviorally false.

#### Representative Rule Clusters

- Error information and status handling: `M0-3-2`, `A18-0-2`, `M19-3-1`, `A27-0-1`
- Exception object and catch policy: `A15-0-1`, `A15-0-2`, `A15-0-3`, `A15-1-1`, `A15-1-2`, `A15-4-1`, `A15-4-2`, `A15-4-4`
- Truthful non-throwing guarantees: `A15-5-1`, `M15-0-3`, `M15-1-1`, `M15-1-3`, `A18-1-6`

### 10. Preprocessor Containment and Configuration Seams

#### Engineering Objective

Preprocessing should shape build seams, not hide program semantics. The preprocessor is acceptable as a narrow configuration tool, but it is a poor substitute for typed behavior, namespace control, or ordinary control flow.

#### Why This Family Matters

Macros and conditional compilation can invalidate findings from almost every other family. If half the program is hidden behind preprocessor branches, then control-flow review, type review, and even lexical review become unreliable.

#### Default Team Policy

1. Limit macros to include guards and narrowly scoped configuration seams.
2. Prefer language features, constants, enums, templates, and inline functions over function-like macros.
3. Keep preprocessor conditions out of business logic whenever possible.
4. Do not rely on undefined identifiers or complex conditional expressions in `#if`.
5. Centralize configuration decisions so the active build surface is easy to understand.
6. Treat each conditional branch as a separate code path that still needs review, analysis, and testing.
7. Remove legacy macros that merely duplicate typed code already available in the language.

#### Preferred Canonical Pattern

If behavior must vary by build profile, expose the variation at a narrow seam and convert it into typed code as soon as possible. The rest of the program should look like ordinary C++.

#### Preferred Example Form

```cpp
#ifndef PID_CONTROLLER_HPP
#define PID_CONTROLLER_HPP

class PidController;

#endif
```

#### What Good Code Review Looks For

- Macros do not implement business logic or typed computation.
- Conditional compilation is localized and comprehensible.
- The active configuration surface is small enough that reviewers can reason about all variants.
- Include guards and configuration seams are clear rather than clever.

#### What Strong Code Looks Like

- Most behavior variation is represented by values, types, or ordinary polymorphism instead of macros.
- The build profile is visible from a small number of configuration points.
- Static analysis sees the same control flow that the reviewer sees for the selected configuration.
- Removal of legacy macros makes ordinary code simpler rather than merely different.

#### Common Anti-Patterns

- Function-like macros for computation.
- Conditional compilation interleaved through normal business logic.
- Hidden semantics behind undefined preprocessor symbols.
- Macro-heavy code that defeats search, refactoring, and type checking.
- Include patterns that depend on fragile order or side effects.

#### Interaction Hotspots

- `A6-5-3` reinforces this family because macro-heavy loop bodies and conditions hide exactly the control variables the reviewer needs to trust.
- Toolchain and baseline rules matter here because the preprocessor is part of the build profile, not an isolated text trick.
- Lexical hygiene improves once macro names, include guards, and configuration surfaces are consistent.
- Reducing macro surface often makes dead code and unreachable paths visible for the control-flow family.

#### Refactoring Guidance

1. Identify preprocessor use that changes semantics rather than just configuration.
2. Collapse that variability into typed constants, functions, or local factory seams.
3. Normalize include guards and configuration headers.
4. Re-run analysis after macro reduction because previously hidden control flow and dead code often become visible.

#### Fix-Order Trap

If you postpone macro cleanup until the end, later family repairs may be based on incomplete or misleading code paths and will need to be revisited when hidden branches become visible.

#### Representative Rule Clusters

- Macro containment: `A16-0-1`, `M16-0-1`, `M16-0-2`, `M16-0-5`, `M16-0-6`, `M16-0-7`
- Conditional compilation hygiene: `M16-1-1`, `M16-1-2`, `M16-2-3`, `M16-3-1`, `M16-3-2`
- Control-flow interaction: `A6-5-3`

### 11. Standard Library Boundaries, Containers, and External Data

#### Engineering Objective

Use the C++ standard library in a subset that preserves ownership clarity, iterator validity, predictable comparison behavior, and safe interaction with external data. The standard library should reduce hazards, not smuggle C-style hazards back in.

#### Why This Family Matters

The concise first edition underweighted late AUTOSAR library rules. In practice, these rules matter because teams frequently reintroduce unsafe arrays, C strings, unvalidated input, invalid iterators, weak predicates, and unsafe random or I/O habits even when the core language subset looks clean.

#### Default Team Policy

1. Access C facilities through the C++ headers only.
2. Prefer C++ library types over raw C arrays and C-style strings.
3. Avoid `std::vector<bool>` and `std::auto_ptr`.
4. Treat iterator validity, reference validity, and pointer validity as part of the container contract.
5. Keep predicates pure and ensure ordering predicates satisfy strict weak ordering.
6. Validate data from independent components before parsing, storing, or acting on it.
7. Use deterministic random engines with explicit seeds or seed sources; never use `std::rand()`.
8. Do not default-initialize random engines if the seed matters to correctness.
9. Avoid C-style I/O and do not mix input and output on the same file stream without the required flush or repositioning behavior.
10. If a narrow compatibility boundary still exposes C-style strings, treat size and null termination as explicit contract data, not implicit hope.

#### Preferred Canonical Pattern

Use value-safe library types at the edge of the design and wrap unsafe legacy boundaries immediately. Containers, strings, iterators, and algorithms should make state and validity easier to reason about than raw buffers and ad hoc loops.

#### Preferred Example Form

```cpp
struct Frame {
  std::array<std::uint8_t, 8U> bytes;
};

bool hasHeader(const std::string& text)
{
  return text.size() >= 2U && text[0] == 'O' && text[1] == 'K';
}
```

#### What Good Code Review Looks For

- The code uses `std::array`, `std::vector`, `std::string`, and related library abstractions instead of raw buffers where practical.
- Iterator invalidation rules are understood and preserved across insert, erase, resize, and reallocation points.
- Predicates used by algorithms and associative containers are stable, pure, and ordered correctly.
- External input is validated before conversion or storage.
- Random behavior and file-stream behavior are explicit rather than inherited from C-style defaults.

#### What Strong Code Looks Like

- Container traversal uses library abstractions instead of manual pointer arithmetic.
- External data is validated at the boundary, then translated into typed domain data.
- Random engines are seeded deliberately and their lifetime is meaningful.
- String handling uses `std::string` or bounded container forms instead of unbounded C-style buffers.

#### Common Anti-Patterns

- Raw C arrays or C strings used as ordinary domain types.
- `std::vector<bool>` or deprecated ownership types such as `std::auto_ptr`.
- Iterators reused after container mutation without a validity review.
- Weak or stateful comparators used for sorting or associative containers.
- `std::rand()` used for pseudorandom behavior.
- C-style I/O or mixed stream directions without flush or seek discipline.
- Unvalidated external input passed directly into conversion or business logic.

#### Interaction Hotspots

- `A18-1-1` and `A27-0-4` form a strong boundary rule: once arrays and C strings disappear from ordinary code, many pointer and lifetime defects shrink with them.
- `A23-0-1` and `A23-0-2` tie container validity back to ownership and lifetime rules because invalid iterators are often dangling references by another name.
- `A25-4-1` and comparator behavior connect library use to expression and class-design families because ordering predicates must be semantically sound, not just syntactically valid.
- `A27-0-1` and `A18-0-2` connect library boundaries directly to the failure-signaling family because input validation and parse failures are policy boundaries, not just local implementation details.

#### Refactoring Guidance

1. Replace raw arrays and C strings at public boundaries first.
2. Move algorithm and container use to library abstractions with clear validity rules.
3. Review comparator and predicate correctness before trusting sort or container behavior.
4. Validate external input before conversion and persistence.
5. Replace `std::rand()` and C-style I/O only after the owning subsystem has a clear policy for determinism and error handling.

#### Fix-Order Trap

If you postpone library-boundary cleanup until the end, raw buffers, invalid iterators, and unvalidated inputs will keep reintroducing the same ownership, type, and failure-handling defects you thought were already fixed.

#### Representative Rule Clusters

- C library and raw-data boundaries: `A18-0-1`, `M18-0-3`, `M18-0-4`, `M18-0-5`, `A18-0-3`, `A27-0-4`
- Safer types and containers: `A18-1-1`, `A18-1-2`, `A18-1-3`, `A23-0-1`, `A23-0-2`
- Algorithms, random, and I/O: `A25-4-1`, `A26-5-1`, `A26-5-2`, `M27-0-1`, `A27-0-1`, `A27-0-2`, `A27-0-3`

## Preferred Canonical Patterns

### 1. Narrow Signatures with Explicit Ownership

- Default shape: use values or `const&` for inputs, return value objects for outputs, and reserve smart pointers in signatures for real transfer or sharing semantics.
- Why it works: it absorbs output-parameter, nullability, and ownership rules into one visible declaration style.
- Review cue: if the caller cannot tell whether the callee may retain, modify, or reject a resource, the signature is still too vague.
- Representative rules: `A8-4-3`, `A8-4-4`, `A8-4-8`, `A8-4-10`, `A8-4-11`, `A8-4-12`, `A8-4-13`

### 2. Brace Initialization with Domain-Specific Types

- Default shape: initialize objects with `{}`, prefer fixed-width integers and scoped enums where the domain depends on size or valid-state boundaries, and complete initialization in constructors.
- Why it works: it reduces narrowing surprises, uninitialized reads, and weak state modeling in one move.
- Review cue: if a value's width, signedness, or valid-state set is implied rather than declared, the model is still too loose.
- Representative rules: `A3-9-1`, `A7-2-1`, `A7-2-2`, `A7-2-3`, `A8-5-0`, `A8-5-2`

### 3. One Conversion at One Named Boundary

- Default shape: convert once into the domain type, store the result in a named variable, and continue the expression in that type.
- Why it works: it localizes signedness, width, and parse-risk review instead of diffusing it through long expressions.
- Review cue: if a reviewer must inspect operator precedence and promotions at the same time, the conversion boundary is too late.
- Representative rules: `A4-7-1`, `M5-0-3`, `M5-0-4`, `M5-0-5`, `M5-0-6`, `A18-0-2`, `A21-8-1`

### 4. Exhaustive Branch Form

- Default shape: braces on every branch, explicit `else` or `default`, scoped enums for state, and one visible loop control variable.
- Why it works: it compresses reachability, readability, and state-machine review into one consistent control-flow style.
- Review cue: if the set of possible states or exits is not obvious from the structure alone, the branch form is too clever.
- Representative rules: `M6-4-1`, `M6-4-2`, `M6-4-3`, `M6-4-6`, `A6-4-1`, `A6-5-2`, `A6-6-1`

### 5. RAII Before Policy

- Default shape: model lifetime with automatic storage, values, containers, and smart pointers before deciding exception guarantees or cleanup policy.
- Why it works: cleanup, swap, move, and error handling all become simpler once ownership is visible.
- Review cue: if `noexcept`, custom cleanup, or explicit deletion appears before ownership is stable, the design is probably backwards.
- Representative rules: `A3-8-1`, `A18-5-1`, `A18-5-2`, `A20-8-2`, `A20-8-3`, `A20-8-4`, `A20-8-5`, `A20-8-6`

### 6. Invariants in Declarations

- Default shape: use constructors, access control, defaulted or deleted special members, `override`, and `final` to state class behavior directly.
- Why it works: it removes guesswork from polymorphism and state management and makes invalid states harder to construct.
- Review cue: if class validity depends on call ordering outside the declaration, the invariant is still informal.
- Representative rules: `A10-0-1`, `A10-3-1`, `A10-3-2`, `A11-0-1`, `A12-1-1`, `A12-8-1`, `A12-8-5`

### 7. Local Template Constraints

- Default shape: keep compile-time assumptions beside the template using `static_assert`, visible return forms, and local specialization patterns.
- Why it works: misuse fails near the source and reviewers do not need to reconstruct hidden type contracts.
- Review cue: if a template needs surrounding lore to know what types are valid, it is under-constrained.
- Representative rules: `A7-1-2`, `A7-1-5`, `A8-2-1`, `A14-1-1`, `A14-5-1`, `A14-7-1`, `A14-8-2`

### 8. One Failure Protocol per Interface

- Default shape: use either typed exceptions or checked return results as the primary contract for an interface family and translate at explicit subsystem boundaries.
- Why it works: it prevents callers from guessing whether failure is returned, thrown, logged, or silently ignored.
- Review cue: if two adjacent functions in the same API family report failure differently without a boundary reason, the protocol is fragmented.
- Representative rules: `M0-3-2`, `A15-0-1`, `A15-1-1`, `A15-4-2`, `A15-5-1`, `A27-0-1`

### 9. Macros Only at Seams

- Default shape: restrict macros to include guards and narrowly defined build switches, then convert behavior into typed code immediately.
- Why it works: it keeps real semantics visible to both tools and reviewers.
- Review cue: if removing a macro would reveal ordinary logic, that logic probably should already be ordinary code.
- Representative rules: `A16-0-1`, `M16-0-1`, `M16-1-1`, `M16-2-3`

### 10. Value-Safe Library Boundaries

- Default shape: prefer `std::array`, `std::vector`, `std::string`, valid iterators, pure predicates, explicit seeds, and validated external input at boundaries.
- Why it works: it absorbs many raw-buffer, invalid-iterator, and unsafe-I/O defects into one safer library usage habit.
- Review cue: if a boundary still depends on raw arrays, C strings, or unchecked input, the library surface is still leaking low-level hazards.
- Representative rules: `A18-1-1`, `A23-0-2`, `A25-4-1`, `A26-5-2`, `A27-0-1`, `A27-0-3`, `A27-0-4`

### 11. Clean Names and Typed Literals

- Default shape: use unambiguous identifiers, symbolic constants, `nullptr`, and comments that explain why a constraint exists.
- Why it works: it removes the lexical noise that otherwise destabilizes later work in expressions, interfaces, and control flow.
- Review cue: if a reader must stop to decode whether a token is a type, constant, or pointer sentinel, the surface is not clean enough.
- Representative rules: `A2-10-1`, `A2-10-6`, `A2-13-5`, `A4-10-1`, `M4-10-2`, `A5-1-1`

## Rule Interaction Map

- Primary artifacts: [rule-relationships.json](rule-relationships.json) and [rule-graph.mmd](rule-graph.mmd)
- Relationship summary: the graph is dominated by reinforcing edges, so it is most useful for grouping repairs that should move together rather than for reproducing AUTOSAR chapter order.
- Anchor observation: `A1-1-1` and `M0-1-1` behave like anchor rules because build conformance and reachability assumptions recur across many later decisions.
- Practical reading rule: when two rules are linked and both touch ownership, signatures, or control flow, treat them as one refactor bundle unless there is a strong reason not to.

### Reinforcement Clusters That Deserve Joint Repair

- Signature semantics and ownership move together: `A8-4-9` reinforces `A8-4-8`, while `A8-4-12` and `A8-4-13` reinforce `A8-4-11` and `A8-4-10`. Once lifetime semantics are visible in the signature, output parameters, informal nullability, and smart-pointer misuse all shrink together.
- Null handling and pointer comparison move together: `A5-10-1` reinforces `A4-10-1`. Standardizing on `nullptr` removes several pointer-comparison edge cases and makes optionality review more direct.
- Enum modeling and exhaustive branching move together: `A7-2-5` reinforces `M6-4-6`. Scoped enum state models pair naturally with explicit `switch` handling and clearer default behavior.
- Override safety and hierarchy intent move together: `M8-3-1` reinforces `A10-2-1`. Override markings, default-argument policy, and real subtype behavior should be repaired as one object-model task, not three independent style chores.
- Macro reduction and control-flow clarity move together: `A6-5-3` reinforces `A16-0-1`. Preprocessor cleanup often reveals the control flow that later loop and branch rules need in order to be meaningful.
- Copy or move semantics and exception guarantees move together: `A12-8-5` reinforces `A12-8-2`, and `A15-5-1` reinforces both `A12-8-2` and `A12-0-1`. Ownership and self-assignment rules must be stable before `noexcept` and swap promises can be trusted.
- Raw buffer removal and library safety move together: `M18-0-5` points toward `A27-0-4` and `A12-0-2`. C string and unbounded buffer cleanup reinforces both ownership and interface safety.

### Hidden Conflict Zones

- Dead-code cleanup can hide a deeper contract problem. A branch that looks unreachable may be compensating for weak initialization or an ambiguous API result.
- Converting raw pointers to smart pointers without changing signatures often produces aliasing bugs rather than removing lifetime bugs. The ownership contract must move with the type.
- Adding `noexcept` early can freeze an invalid assumption about move safety or cleanup behavior.
- Replacing raw arrays with containers without checking iterator invalidation rules can change one class of lifetime bug into another.
- Macro removal can expose new warnings and previously hidden dead code. This is a good sign, but it means downstream families must be revisited under the more truthful build surface.

### Practical Repair Bundles

1. Build surface bundle: toolchain baseline, warning policy, macro containment
2. Contract bundle: headers, linkage, signatures, output values, nullability
3. Domain-model bundle: fixed-width types, scoped enums, conversion boundaries, literal cleanup
4. Lifetime bundle: RAII, initialization, smart pointers, container validity
5. Object-model bundle: invariants, inheritance, special members, truthful `noexcept`
6. Boundary-data bundle: validated input, safe parsing, library subset, deterministic random and I/O behavior

## Fix-Order Strategy

### 1. Normalize the Build Surface

- Goal: freeze compiler mode, diagnostics, analysis settings, and macro policy so the code being reviewed is the code actually being built.
- Do now: strict C++14 conformance, warning cleanup, macro containment, numeric-model decisions.
- Avoid now: deep ownership or exception tuning before the build surface is stable.
- Exit criterion: the project builds under the agreed baseline with no tolerated warning noise.

### 2. Stabilize Declarations and Visible Contracts

- Goal: make headers, namespaces, linkage, and signatures honest before implementation refactors spread churn.
- Do now: self-contained headers, overload visibility, return-object patterns, nullability and ownership semantics in signatures.
- Avoid now: rewriting internals while the public contract is still fuzzy.
- Exit criterion: a reviewer can understand most API behavior from declarations alone.

### 3. Normalize Types, Literals, and Conversion Boundaries

- Goal: fix domain modeling before control-flow or resource cleanup reintroduces numeric ambiguity.
- Do now: fixed-width integers, scoped enums, named constants, `nullptr`, explicit conversions, parse-boundary checks.
- Avoid now: micro-optimizing arithmetic or preserving clever expression compression.
- Exit criterion: data domains are explicit and conversions happen at named edges.

### 4. Make Lifetime and Initialization Explicit

- Goal: eliminate ambiguous ownership and uninitialized state before class or exception promises are hardened.
- Do now: RAII migration, automatic storage preference, smart-pointer policy, constructor and member initialization, removal of raw allocation habits.
- Avoid now: finalizing `swap`, move annotations, or subsystem exception guarantees.
- Exit criterion: each resource has a visible lifetime owner and every object has a clear initialization point.

### 5. Repair Class Invariants and Object Model Semantics

- Goal: make class behavior predictable enough that polymorphism, copying, moving, and destruction are trustworthy.
- Do now: explicit constructors, access control, special members, `override`, `final`, virtual destructors, hierarchy simplification.
- Avoid now: performance annotations that assume stable move or cleanup semantics.
- Exit criterion: class contracts are visible from declarations and invalid states are hard to construct.

### 6. Simplify Control Flow and Remove Residual Dead Paths

- Goal: make execution paths exhaustively reviewable once interfaces, types, and lifetime semantics are no longer masking them.
- Do now: delete dead code, normalize loop and branch forms, exhaustive `switch`, explicit returns, result checking.
- Avoid now: preserving strange branches "just in case" because the contract is now already explicit.
- Exit criterion: reviewers and tools can enumerate paths without reconstructing hidden behavior.

### 7. Constrain Templates and Compile-Time Mechanisms

- Goal: prevent unstable generic code from multiplying defects across many instantiations.
- Do now: local constraints, visible return forms, limited `auto`, `constexpr` promotion, specialization cleanup.
- Avoid now: templating interfaces that are still moving.
- Exit criterion: template misuse fails locally and compile-time behavior is readable.

### 8. Finalize Library Boundaries and External Data Policy

- Goal: absorb the remaining late-library AUTOSAR rules into a safe standard-library subset and explicit boundary-validation policy.
- Do now: container validity review, C-string removal, input validation, random-engine policy, stream behavior cleanup.
- Avoid now: ad hoc compatibility shims that preserve raw-buffer habits indefinitely.
- Exit criterion: external data enters through validated, typed, library-based seams.

### 9. Harden Failure Policy and Truthful `noexcept`

- Goal: align exception or status-return policy with the now-stable ownership and object model.
- Do now: unify failure channels, strengthen catch boundaries, verify non-throwing operations, remove `errno`-style leakage.
- Avoid now: broad exception annotations added as optimistic promises.
- Exit criterion: failure reporting is consistent and all `noexcept` claims are believable.

## Review Checklist

### Build and Baseline

- Does the project build in the agreed strict C++14 configuration with no tolerated warnings?
- Are compiler extensions, nonstandard modes, and warning suppressions exceptional rather than routine?
- Is the numeric model documented where floating-point or fixed-point behavior matters?
- Are math-library boundary conditions reviewed instead of assumed?
- Are metrics and static-analysis settings part of the release baseline rather than local convention?

### Source Surface and Naming

- Are comments explaining local design intent rather than preserving deleted code or external paperwork?
- Are file names aligned with the logical entities they declare or define?
- Are identifiers unambiguous and free from harmful hiding across scopes?
- Is `nullptr` the only null-pointer constant?
- Are literals symbolic, typed, and consistently spelled?

### Interfaces and Translation Units

- Is every header self-contained and safe to include in multiple translation units?
- Is there one obvious declaration site for each shared type, object, or function?
- Do signatures express input, output, ownership, and nullability directly?
- Have output parameters been avoided in favor of return objects?
- Are namespace-wide `using` directives absent from headers and broad scopes?
- Do smart-pointer parameters express actual lifetime semantics rather than habit?

### Types and Expressions

- Are fixed-width integer types and scoped enums used where domain boundaries matter?
- Are conversions isolated, named, and free of C-style or `reinterpret_cast` usage?
- Are boolean conditions actually `bool`?
- Are bitwise operations confined to explicit unsigned domains?
- Are floating-point comparisons handled without direct equality tests?
- Do long expressions use named temporaries before precedence and side effects become hard to review?

### Ownership, Initialization, and Library Boundaries

- Is every object initialized before first read?
- Do objects that stay inside a function use automatic storage duration?
- Are `malloc`, `free`, explicit `new`, and explicit `delete` absent from ordinary code?
- Are `std::unique_ptr`, `std::shared_ptr`, and `std::weak_ptr` used only with the ownership meaning they imply?
- Are arrays, strings, and buffers represented by safe library types where practical?
- Are container elements accessed only through valid iterators, references, and pointers?
- Are C-style strings and unbounded C library buffer functions removed from ordinary code?

### Class Model and Polymorphism

- Do constructors establish valid invariant state?
- Are special members defaulted, deleted, or defined deliberately?
- Is inheritance used only for true subtype behavior?
- Do polymorphic bases have virtual destructors?
- Are `override` and `final` used where intent matters?
- Are default arguments on overrides either consistent or absent?

### Templates and Compile-Time Code

- Are template assumptions visible near the template definition?
- Is `auto` used only where the hidden type is obvious or harmless?
- Are compile-time constants marked `constexpr` where appropriate?
- Are dependent return types and local constraints spelled clearly enough for review?
- Are specializations and overload sets local enough to inspect together?

### Failure Policy

- Does each interface family use one clear failure protocol?
- Is returned error information always checked?
- Are exception types meaningful and catch sites policy-aware?
- Are input-validation and parse-failure boundaries explicit?
- Do `noexcept` promises match actual ownership, move, and cleanup behavior?
- Is `errno` absent from normal error signaling?

### Final Sanity Check

- Can a reviewer trace each nontrivial design choice back to an explicit type, interface, invariant, or boundary policy instead of local convention?
- If a deviation from the default pattern exists, is the reason local, explicit, and reviewable?
- Would the same code still be understandable if compiled on a second conforming toolchain tomorrow?

## Rule Index

This index is representative rather than exhaustive. It maps each synthesized family back to a concentrated set of AUTOSAR rule identifiers that most strongly motivated the family guidance.

| Core family | Engineering focus | Representative AUTOSAR rule IDs |
| --- | --- | --- |
| Toolchain Discipline and Verifiable Baseline | Conformance mode, diagnostics, numeric model, analysis baseline | `M0-3-1`, `M0-4-1`, `M0-4-2`, `A0-4-1`, `A0-4-2`, `A0-4-4`, `A1-1-1`, `A1-1-2`, `A1-1-3`, `A1-2-1`, `A1-4-1`, `A1-4-3` |
| Lexical Clarity and Symbol Hygiene | Source text portability, comment discipline, naming, literals, null spelling | `A2-3-1`, `A2-7-2`, `A2-7-3`, `A2-8-1`, `A2-8-2`, `A2-10-1`, `A2-10-6`, `A2-13-1`, `A2-13-5`, `A2-13-6`, `A4-10-1`, `M4-10-2`, `A5-1-1`, `A21-8-1` |
| Interface and Translation Unit Boundaries | ODR safety, linkage control, namespace hygiene, explicit contract surfaces | `A3-1-1`, `M3-2-2`, `M3-2-3`, `A3-3-1`, `M7-3-1`, `M7-3-3`, `M7-3-4`, `A7-3-1`, `M7-3-6`, `A8-4-3`, `A8-4-4`, `A8-4-8`, `A8-4-10`, `A8-4-11`, `A8-4-12`, `A8-4-13`, `A17-6-1` |
| Deterministic Control Flow and Reachability | Dead-code removal, exhaustive branching, loop discipline, explicit returns | `M0-1-1`, `M0-1-2`, `M0-1-3`, `A0-1-2`, `M0-3-2`, `M6-4-1`, `M6-4-2`, `M6-4-3`, `M6-4-6`, `A6-4-1`, `A6-5-1`, `A6-5-2`, `M6-5-3`, `A6-6-1`, `A8-4-2` |
| Explicit Types, Values, and Conversion Boundaries | Domain types, enum modeling, explicit conversions, expression safety | `A3-9-1`, `A4-7-1`, `M5-0-3`, `M5-0-4`, `M5-0-5`, `M5-0-6`, `M5-0-21`, `A5-2-2`, `A5-2-4`, `M6-2-2`, `A7-2-1`, `A7-2-2`, `A7-2-3`, `A18-0-2` |
| Ownership, Lifetime, and Initialization | RAII, initialization, dynamic memory policy, smart-pointer semantics | `A3-8-1`, `A5-3-2`, `A5-3-3`, `A8-5-0`, `A8-5-2`, `A12-0-1`, `A12-6-1`, `A18-5-1`, `A18-5-2`, `A18-5-3`, `A18-5-6`, `A18-5-8`, `A20-8-1`, `A20-8-2`, `A20-8-3`, `A20-8-4`, `A20-8-5`, `A20-8-6`, `A20-8-7` |
| Stable Class Invariants and Polymorphism | Construction rules, inheritance intent, special members, override safety | `A10-0-1`, `A10-0-2`, `A10-2-1`, `A10-3-1`, `A10-3-2`, `M10-3-3`, `M11-0-1`, `A11-0-1`, `A11-0-2`, `A12-1-1`, `A12-4-1`, `A12-4-2`, `A12-7-1`, `A12-8-1`, `A12-8-2`, `A12-8-5`, `M8-3-1` |
| Constrained Templates and Compile-Time Code | `constexpr`, deduction policy, local constraints, template readability | `A7-1-1`, `A7-1-2`, `A7-1-5`, `A7-1-6`, `A8-2-1`, `A14-1-1`, `A14-5-1`, `M14-6-1`, `A14-7-1`, `A14-7-2`, `A14-8-2` |
| Exceptions and Failure Signaling | Checked error handling, typed exceptions, truthful `noexcept`, boundary catches | `M0-3-2`, `A15-0-1`, `A15-0-2`, `A15-0-3`, `A15-1-1`, `A15-1-2`, `A15-4-1`, `A15-4-2`, `A15-4-4`, `A15-5-1`, `M15-0-3`, `M15-1-1`, `M15-1-3`, `A18-1-6`, `M19-3-1`, `A27-0-1` |
| Preprocessor Containment and Configuration Seams | Macro minimization, conditional-compilation hygiene, visible build seams | `A16-0-1`, `M16-0-1`, `M16-0-2`, `M16-0-5`, `M16-0-6`, `M16-0-7`, `M16-1-1`, `M16-1-2`, `M16-2-3`, `M16-3-1`, `M16-3-2` |
| Standard Library Boundaries, Containers, and External Data | Safe library subset, container validity, raw-buffer removal, validated input | `A18-0-1`, `M18-0-3`, `M18-0-4`, `M18-0-5`, `A18-1-1`, `A18-1-2`, `A18-1-3`, `A23-0-1`, `A23-0-2`, `A25-4-1`, `A26-5-1`, `A26-5-2`, `M27-0-1`, `A27-0-1`, `A27-0-2`, `A27-0-3`, `A27-0-4` |