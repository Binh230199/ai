# AUTOSAR C++14 Core Engineering Guideline

## Source and Scope

- Standard: AUTOSAR C++14, release 18-03.
- Source document: file:///C:/Users/binhh/Downloads/AUTOSAR_RS_CPP14Guidelines.pdf
- Artifact root: [artifacts/cpp-standards-guideline](artifacts/cpp-standards-guideline)
- Parsed source: [artifacts/cpp-standards-guideline/source-markdown.md](artifacts/cpp-standards-guideline/source-markdown.md)
- Normalized rules: [artifacts/cpp-standards-guideline/rules-normalized.json](artifacts/cpp-standards-guideline/rules-normalized.json)
- Relationship map: [artifacts/cpp-standards-guideline/rule-relationships.json](artifacts/cpp-standards-guideline/rule-relationships.json)
- Rule graph: [artifacts/cpp-standards-guideline/rule-graph.mmd](artifacts/cpp-standards-guideline/rule-graph.mmd)
- Scope: This document is an engineering synthesis for implementation, review, and refactoring. It groups AUTOSAR obligations into a smaller set of default coding forms that make compliant code easier to write and easier to review. It is deliberately paraphrased and does not restate the source document chapter by chapter.

## Analysis Method

1. The source PDF was parsed into markdown so the corpus could be inspected as structured text.
2. The corpus was normalized into 390 rule records with family, intent, preferred pattern, anti-patterns, conflict-risk notes, and evidence locations.
3. A relationship pass produced 337 practical rule links and the graph artifact used for interaction analysis.
4. Rules were regrouped by engineering intent and likely fix churn instead of AUTOSAR chapter order.
5. Canonical patterns were selected where one default implementation form satisfies multiple nearby AUTOSAR rules at once.
6. Representative AUTOSAR rule IDs are retained for traceability, while the guidance below stays original and implementation-oriented.

## Core Rule Families

### 1. Toolchain Discipline and Verifiable Baseline

- Intent: Make the build environment part of the safety argument. If conformance mode, warnings, metrics, or numeric assumptions move under the code, source-level discipline is no longer trustworthy.
- Preferred canonical pattern: Build in strict ISO C++14 mode, document the numeric model, treat warnings as defects, and keep code analyzable enough that static analysis and review agree on behavior.
- Preferred example form:

```cpp
#include <cstdint>

static_assert(sizeof(std::uint32_t) == 4U, "unexpected toolchain contract");
constexpr std::uint32_t kCycleMs{10U};
```

- Anti-patterns: compiler extensions used as design features, routine warning suppression, undocumented floating-point assumptions, metrics reviewed only after integration.
- Related rule synergies: A0-4-1, A0-4-4, A1-1-1, A1-1-2, A1-1-3, A1-4-1, A1-4-3, M0-3-1.
- Fix-order trap: Freeze compiler mode and analysis expectations first. Later repairs to types, control flow, and exceptions otherwise need to be repeated under a different warning profile.

### 2. Lexical Clarity and Symbol Hygiene

- Intent: Keep the token stream and symbol table boring enough that humans and tools read the same program.
- Preferred canonical pattern: Use the standard source character set, explicit literal spellings, scoped names, symbolic constants, and comments that explain local design intent instead of preserving dead code or external paperwork.
- Preferred example form:

```cpp
enum class Mode : std::uint8_t { off, heat, cool };

constexpr std::uint8_t kRetryLimit{3U};
Mode mode{Mode::off};
```

- Anti-patterns: commented-out code, hidden identifiers, octal literals, ambiguous suffixes, reused names across nested scopes, `0` or `NULL` as null pointers, magic literals spread through logic.
- Related rule synergies: A2-3-1, A2-7-2, A2-7-3, A2-10-1, A2-10-6, A2-13-1, A2-13-4, A2-13-5, A2-13-6, A4-10-1, M4-10-2, A5-1-1.
- Fix-order trap: Normalize names and literals after public interfaces stabilize, but before expression cleanup. Otherwise local type fixes keep reintroducing readability defects.

### 3. Interface and Translation Unit Boundaries

- Intent: Every declaration should communicate one stable contract with the smallest necessary visibility and no linkage ambiguity.
- Preferred canonical pattern: Keep headers self-contained, keep names out of the global namespace unless they are truly global, return structured results instead of using output parameters, and encode input, ownership, and nullability directly in the signature.
- Preferred example form:

```cpp
struct ReadResult {
  bool ok;
  std::int32_t value;
};

ReadResult readSensor(const Sensor& sensor);
```

- Anti-patterns: block-scope function declarations, duplicated declarations across translation units, namespace-wide using directives, hidden overload sets, output parameters, nullability expressed only by convention.
- Related rule synergies: A3-1-1, M3-2-2, M3-2-3, A3-3-1, M7-3-1, M7-3-3, M7-3-4, M7-3-6, A8-4-3, A8-4-4, A8-4-8, A8-4-10.
- Fix-order trap: Stabilize signatures early. Signature churn propagates into overrides, templates, call sites, ownership semantics, and exception policy.

### 4. Deterministic Control Flow and Reachability

- Intent: Execution paths should be easy to prove and hard to misread.
- Preferred canonical pattern: Prefer straight-line code, compound statements everywhere, exhaustive branching, explicit `else` and `default` handling, early exits for failed preconditions, and loops with one obvious control variable.
- Preferred example form:

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

- Anti-patterns: dead branches, partially formed switches, loop counters modified in multiple places, `goto`, `do` loops as a default style, hidden side effects inside conditions.
- Related rule synergies: M0-1-1, M0-1-2, M0-1-3, A0-1-2, M6-4-1, M6-4-2, M6-4-3, M6-4-5, M6-4-6, A6-4-1, A6-5-1, A6-5-2, M6-5-3, A6-6-1, A8-4-2.
- Fix-order trap: Simplify control flow after interface, type, and ownership intent are visible. A dead-looking path can be compensating for a deeper contract or initialization defect.

### 5. Explicit Types, Values, and Conversion Boundaries

- Intent: Numeric intent and conversion behavior should be explicit enough that arithmetic never depends on reader guesswork.
- Preferred canonical pattern: Use fixed-width integers when size matters, scoped enums with explicit underlying types, brace initialization, one deliberate conversion at one named boundary, and named temporaries before expressions become precedence puzzles.
- Preferred example form:

```cpp
constexpr std::int32_t kScale{16};

const auto scaledCount =
    static_cast<std::int32_t>(rawCount) * kScale;
```

- Anti-patterns: mixed signed and unsigned arithmetic, implicit narrowing, float equality tests, pointer or integer reinterpretation, C-style casts, `reinterpret_cast`, hidden promotions inside long expressions.
- Related rule synergies: A3-9-1, A4-7-1, A4-10-1, M5-0-3, M5-0-4, M5-0-5, M5-0-6, M5-0-9, M5-0-20, M5-0-21, A5-2-2, A5-2-4, M6-2-2, A7-2-1, A7-2-2, A7-2-3.
- Fix-order trap: Repair interface types before local cast cleanup. Otherwise the same conversion problem reappears at every call boundary.

### 6. Ownership, Lifetime, and Initialization

- Intent: Resources should have one obvious owner, one obvious lifetime story, and no read-before-initialize state.
- Preferred canonical pattern: Prefer automatic storage, RAII wrappers, containers, and member initializers. Use smart pointers only when the interface must express transfer or shared ownership. Never expose pointers or references that outlive the objects behind them.
- Preferred example form:

```cpp
class Session {
public:
  explicit Session(std::unique_ptr<Transport> transport) noexcept
      : transport_(std::move(transport)) {}

private:
  std::unique_ptr<Transport> transport_;
};
```

- Anti-patterns: raw owning pointers, scattered `new` and `delete`, reading storage before initialization, returning addresses of shorter-lived objects, dereferencing null, deleting incomplete types, pointer arithmetic as a substitute for containers.
- Related rule synergies: A3-8-1, A5-3-2, A5-3-3, A8-4-11, A8-4-12, A8-4-13, A8-5-0, A8-5-1, A8-5-2, M7-5-1, A7-5-1, A12-0-1, A12-6-1.
- Fix-order trap: Fix ownership before exception guarantees and before class-model tuning. Lifetime changes alter destructors, move behavior, swap safety, and interface contracts.

### 7. Stable Class Invariants and Polymorphism

- Intent: Class declarations should make valid state, inheritance intent, and override behavior obvious.
- Preferred canonical pattern: Use composition for has-a, public inheritance only for real is-a, interface-like bases for polymorphism, explicit constructors, deliberate special members, private data by default, and `override` or `final` wherever virtual behavior is intentional.
- Preferred example form:

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

- Anti-patterns: inheritance used only for reuse, ambiguous multiple inheritance, hidden default arguments across overrides, accidental copy or move behavior, public data in stateful types, non-virtual destruction of polymorphic bases.
- Related rule synergies: A10-0-1, A10-0-2, A10-3-1, A10-3-2, A10-4-1, M11-0-1, A11-0-1, A11-0-2, A12-1-1, A12-4-1, A12-4-2, A12-7-1, A12-8-1, A12-8-5, M8-3-1.
- Fix-order trap: Establish invariants and special-member intent before adding `noexcept`, swap optimizations, or forwarding constructors. Those promises only make sense after the class contract is stable.

### 8. Constrained Templates and Compile-Time Code

- Intent: Generic code should fail early, locally, and read like ordinary code instead of a parallel language.
- Preferred canonical pattern: Use `constexpr` for compile-time facts, keep deduction visible, constrain template assumptions close to the template, keep specializations near the primary template, and prefer simple overloads over clever template traps.
- Preferred example form:

```cpp
template <typename T>
auto toIndex(const T& value) -> std::size_t
{
  static_assert(std::is_integral<T>::value, "integral required");
  return static_cast<std::size_t>(value);
}
```

- Anti-patterns: unconstrained templates, forwarding constructors that hijack overload resolution, explicit function-template specializations as everyday design, dependent-name ambiguity, `auto` where hidden type matters for safety review.
- Related rule synergies: A7-1-1, A7-1-2, A7-1-5, A8-2-1, A14-1-1, A14-5-1, M14-6-1, A14-7-1, A14-7-2, A14-8-2.
- Fix-order trap: Constrain templates after ordinary interfaces and class invariants stop moving. Template churn amplifies quickly across every instantiation and overload set.

### 9. Exceptions and Failure Signaling

- Intent: Failure paths should preserve invariants, stay bounded, and make recovery policy visible.
- Preferred canonical pattern: Use one failure channel per interface, throw typed exception objects when exceptions are allowed, catch where code can restore invariants or translate policy, and mark operations `noexcept` only when ownership and move semantics actually support that promise.
- Preferred example form:

```cpp
class ConfigError : public std::exception {
public:
  const char* what() const noexcept override { return "invalid config"; }
};

void swap(Buffer& other) noexcept;
```

- Anti-patterns: mixing return codes and exceptions in one interface, throwing pointers, throwing from destructors or swap, catch-all handlers that erase meaning, `noexcept` added before move and cleanup semantics are settled.
- Related rule synergies: M0-3-2, A15-0-1, A15-0-2, A15-0-3, A15-1-1, A15-1-2, A15-4-1, A15-4-2, A15-4-4, A15-5-1, M15-0-3, M15-1-1, M15-1-3, A12-8-2.
- Fix-order trap: Exception guarantees come late. They depend on ownership, destruction, move, and swap already being correct.

### 10. Preprocessor Containment and Configuration Seams

- Intent: Preprocessing should shape build seams, not hide program semantics.
- Preferred canonical pattern: Keep macros limited to include guards and narrow configuration boundaries. Use language features, constants, enums, templates, and inline or `constexpr` functions for typed behavior.
- Preferred example form:

```cpp
#ifndef PID_CONTROLLER_HPP
#define PID_CONTROLLER_HPP

class PidController;

#endif
```

- Anti-patterns: function-like macros for computation, conditional compilation embedded in business logic, undefined identifiers in `#if`, macro-heavy control flow, inclusion tricks that change semantics invisibly.
- Related rule synergies: A16-0-1, M16-0-1, M16-0-2, M16-0-5, M16-0-6, M16-0-7, M16-1-1, M16-1-2, M16-2-3, A6-5-3.
- Fix-order trap: Reduce macro surface before large static-analysis cleanup. Hidden branches distort findings for control flow, initialization, types, and ownership.

## Preferred Canonical Patterns

1. Narrow signatures with explicit ownership: Prefer `const&` or value for inputs, return a value object for outputs, and use smart pointers only when the signature must encode transfer or sharing.
2. Brace initialization with domain-specific types: Initialize every object with `{}` and use fixed-width integers, scoped enums, and small result structs where domain boundaries matter.
3. One conversion at one named boundary: Cast once, store the result in a named temporary, and continue in one chosen type.
4. Exhaustive branch form: Every `if` has braces, every multiway branch has an explicit `else` or `default`, and loops use one visible control variable.
5. RAII before policy: Model lifetime with storage duration, containers, and wrappers first. Then choose error policy, because `noexcept`, swap, move, and destructor guarantees depend on the ownership model.
6. Invariants in declarations: Constructors, special members, access control, and destructors define the class contract. Prefer `=default`, `=delete`, `explicit`, `override`, and `final` over comments or conventions.
7. Local template constraints: Put `static_assert`, visible return forms, and specialization locality close to the template so misuse fails near the source.
8. Exceptions at containment boundaries: Throw objects, not pointers; catch at subsystem boundaries; and avoid mixing recoverable and unrecoverable failure channels inside one API.
9. Macros only at seams: Use the preprocessor for inclusion and narrow configuration, never for typed behavior.
10. Clean names and typed literals: Use unambiguous identifiers, symbolic constants, standard characters, and comments that explain why the design exists.

## Rule Interaction Map

- Primary artifacts: [artifacts/cpp-standards-guideline/rule-relationships.json](artifacts/cpp-standards-guideline/rule-relationships.json) and [artifacts/cpp-standards-guideline/rule-graph.mmd](artifacts/cpp-standards-guideline/rule-graph.mmd).
- Most relationship edges are reinforcing, so the graph is best used to group repairs that should move together instead of replaying AUTOSAR chapter order.
- Signature semantics and ownership move together: A8-4-9 reinforces A8-4-8, and A8-4-12 or A8-4-13 reinforce A8-4-11 and A8-4-10. Once lifetime semantics are explicit, output parameters and informal nullability shrink together.
- Null handling and pointer comparison move together: A5-10-1 reinforces A4-10-1, so standardizing on `nullptr` removes several pointer edge cases at once.
- Enum design and branch completeness move together: A7-2-5 reinforces M6-4-6, so enum-based state machines pair naturally with exhaustive `switch` handling.
- Override safety and inheritance intent move together: M8-3-1 reinforces A10-2-1, so default arguments, override markings, and hierarchy semantics should be repaired as one object-model task.
- Macro reduction exposes real control flow: A6-5-3 reinforces A16-0-1, so shrinking preprocessor use makes loop and branch findings trustworthy.
- Copy or move semantics and exception guarantees move together: A12-8-5 reinforces A12-8-2, and A15-5-1 reinforces both A12-8-2 and A12-0-1. Ownership and self-assignment rules should be repaired before `noexcept` and swap promises.

## Fix-Order Strategy

1. Normalize toolchain settings and reduce the macro surface. Warning profiles and hidden conditional code determine how trustworthy later analysis will be.
2. Stabilize declarations, namespaces, file boundaries, and signature semantics. This defines the contract surface for every later repair.
3. Normalize types, literals, null handling, and conversion boundaries. Once data domains are explicit, later control-flow and ownership fixes stop reintroducing numeric ambiguity.
4. Eliminate ambiguous ownership and initialize every object. Lifetime must be visible before class guarantees or exception promises can be stated honestly.
5. Repair class invariants, inheritance, special members, and override behavior. This is where the object model becomes stable enough for performance and exception tuning.
6. Simplify control flow, delete dead code, and make branches exhaustive. Doing this later avoids deleting code that was compensating for an earlier contract defect.
7. Constrain templates and compile-time mechanisms. Template repairs amplify quickly, so they are safer once ordinary interfaces and classes stop moving.
8. Finalize exception policy and `noexcept` guarantees. These promises should be hardened last because they depend on ownership and class-model work already being correct.

## Review Checklist

- Does the project build in the agreed strict C++14 configuration with no tolerated warnings?
- Are macros limited to include guards or isolated configuration seams?
- Is every header self-contained and free of namespace-wide using directives?
- Do function signatures express input, output, ownership, and nullability without output parameters or comment-based conventions?
- Are all objects initialized before first read, preferably with brace or member initialization?
- Are fixed-width integer types and scoped enums used where size and state matter?
- Is `nullptr` the only null-pointer constant?
- Are conversions isolated, named, and free of C-style or `reinterpret_cast` use?
- Are branches exhaustive, loops simple, and unreachable code deleted rather than commented out?
- Does every stateful class define invariants through constructors, data visibility, special members, and destructor strategy?
- Is inheritance used only for real subtype behavior, with `override` or `final` marking intent?
- Is ownership encoded with automatic storage, containers, RAII, or explicit smart-pointer semantics?
- Are templates locally constrained and specializations kept near their primary template?
- Is exception behavior typed, consistent, and aligned with `noexcept` promises?
- Can a reviewer trace each nontrivial design choice back to an explicit type, interface, or invariant instead of a convention?

## Rule Index

Representative identifiers only. The mapping below is for engineering traceability, not for chapter-by-chapter replacement of the standard.

| Core family | Canonical pattern | Representative AUTOSAR rule IDs |
| --- | --- | --- |
| Toolchain Discipline and Verifiable Baseline | Strict C++14 mode, warning-free build, documented numeric model | M0-3-1, A0-4-1, A0-4-4, A1-1-1, A1-1-2, A1-1-3, A1-4-1, A1-4-3 |
| Lexical Clarity and Symbol Hygiene | Standard characters, explicit literals, unambiguous names, `nullptr` | A2-3-1, A2-7-2, A2-10-1, A2-10-6, A2-13-1, A2-13-4, A4-10-1, M4-10-2, A5-1-1 |
| Interface and Translation Unit Boundaries | Self-contained headers and explicit signature semantics | A3-1-1, M3-2-2, M3-2-3, A3-3-1, M7-3-1, M7-3-4, M7-3-6, A8-4-3, A8-4-4, A8-4-8, A8-4-10 |
| Deterministic Control Flow and Reachability | Straight-line code, exhaustive branching, simple loops | M0-1-1, M0-1-2, M0-1-3, A0-1-2, M6-4-1, M6-4-5, M6-4-6, A6-4-1, A6-5-1, A6-5-2, M6-5-3, A6-6-1, A8-4-2 |
| Explicit Types, Values, and Conversion Boundaries | One named conversion boundary and fixed domain types | A3-9-1, A4-7-1, M5-0-3, M5-0-5, M5-0-21, A5-2-2, A5-2-4, M6-2-2, A7-2-1, A7-2-2, A7-2-3 |
| Ownership, Lifetime, and Initialization | RAII, initialized storage, explicit lifetime semantics | A3-8-1, A5-3-2, A5-3-3, A8-4-11, A8-4-12, A8-4-13, A8-5-0, A8-5-2, A12-0-1, A12-6-1 |
| Stable Class Invariants and Polymorphism | Composition by default, explicit special members, override-safe hierarchies | A10-0-1, A10-0-2, A10-3-1, A10-3-2, A10-4-1, M11-0-1, A11-0-1, A12-1-1, A12-4-1, A12-4-2, A12-7-1, A12-8-1, A12-8-5, M8-3-1 |
| Constrained Templates and Compile-Time Code | Local constraints, explicit deduction, specialization locality | A7-1-1, A7-1-2, A7-1-5, A8-2-1, A14-1-1, A14-5-1, M14-6-1, A14-7-1, A14-7-2, A14-8-2 |
| Exceptions and Failure Signaling | Typed exceptions, boundary catches, truthful `noexcept` | M0-3-2, A15-0-1, A15-0-2, A15-1-1, A15-1-2, A15-4-2, A15-4-4, A15-5-1, M15-1-1, A12-8-2 |
| Preprocessor Containment and Configuration Seams | Macros only at inclusion and configuration boundaries | A16-0-1, M16-0-1, M16-0-2, M16-0-5, M16-0-6, M16-0-7, M16-1-1, M16-1-2, M16-2-3, A6-5-3 |