---
name: android-compose-ui
description: >
  Use when writing, reviewing, or refactoring Jetpack Compose UI code for
  Android apps (IVI, HUD, RSE on Android Automotive / AAOS).
  Covers composable design, state management, Material Design 3 theming,
  performance (recomposition), side effects, navigation in Compose, animations,
  and XML interop. Applies to Android Studio (Gradle) and AOSP (Soong) builds.
argument-hint: <screen-or-component-name> [write|review|optimize]
---

# Android Compose UI

Expert practices for building high-quality, performant Jetpack Compose screens
targeting **Android Automotive OS (AAOS)** and standard Android, following the
official [Compose guidelines](https://developer.android.com/jetpack/compose/documentation)
and automotive HMI constraints.

Standards baseline: **Compose BOM 2024.x** · **Material Design 3** · **Kotlin 1.9**.

---

## When to Use This Skill

- Writing a new Compose screen, component, or theme from scratch.
- Reviewing a PR for recomposition issues, state hoisting violations, or incorrect side-effect placement.
- Migrating XML layouts to Compose.
- Optimizing Compose performance (composition, layout, draw phases).
- Designing automotive-compliant UI (touch target sizes, distraction restrictions).

---

## Composable Design Principles

### Stateless vs. Stateful Composables

**Always prefer stateless composables.** Hoist state to the nearest common owner.

```kotlin
// BAD: stateful composable — hard to test and reuse
@Composable
fun CounterButton() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) { Text("Count: $count") }
}

// GOOD: stateless composable
@Composable
fun CounterButton(
    count: Int,
    onIncrement: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Button(onClick = onIncrement, modifier = modifier) {
        Text("Count: $count")
    }
}

// State owner (ViewModel or parent composable)
@Composable
fun CounterScreen(viewModel: CounterViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    CounterButton(count = uiState.count, onIncrement = viewModel::increment)
}
```

**Rules**
- Composables that accept `onX: () -> Unit` lambdas are stateless — prefer them.
- State should live in ViewModel (`StateFlow`) or be remembered at the highest needed scope.
- Pass `Modifier` as a parameter with default `Modifier` — always last before content lambdas.

---

## State Management

### Reading ViewModel state

```kotlin
// Lifecycle-safe collection (stops in STOPPED state)
val uiState by viewModel.uiState.collectAsStateWithLifecycle()
```

### Local UI state

```kotlin
var expanded by remember { mutableStateOf(false) }           // survives recomposition
var text by rememberSaveable { mutableStateOf("") }          // survives config change
val color by remember { derivedStateOf { if (expanded) Red else Blue } }  // derived
```

### When to use each

| Holder | Survives recomposition | Survives config change | Description |
|---|---|---|---|
| `remember` | ✓ | ✗ | Ephemeral UI state (expanded, focus) |
| `rememberSaveable` | ✓ | ✓ | User input, scroll position |
| `ViewModel StateFlow` | ✓ | ✓ | Screen-level business state |

---

## Side Effects

| Effect | When to Use |
|---|---|
| `LaunchedEffect(key)` | Start coroutine tied to composable lifetime; re-launch on key change |
| `DisposableEffect(key)` | Register/unregister listeners; cleanup in `onDispose` |
| `SideEffect` | Push Compose state to non-Compose objects (analytics, etc.) |
| `rememberCoroutineScope` | Trigger coroutines from event handlers (button click, etc.) |
| `produceState` | Convert non-Compose async data into State |

```kotlin
// LaunchedEffect — scroll to top when list reloads
LaunchedEffect(uiState.items) {
    if (uiState.items.isNotEmpty()) listState.animateScrollToItem(0)
}

// DisposableEffect — register lifecycle observer
DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event ->
        if (event == Lifecycle.Event.ON_RESUME) viewModel.refresh()
    }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}

// rememberCoroutineScope — coroutine from button click
val scope = rememberCoroutineScope()
Button(onClick = { scope.launch { scrollState.animateScrollTo(0) } }) { ... }
```

---

## Material Design 3 Theming

### Theme setup

```kotlin
@Composable
fun MyAppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = MyTypography,
        shapes = MyShapes,
        content = content,
    )
}
```

### Using theme tokens — never hardcode colors

```kotlin
// BAD
Text(text = "Hello", color = Color(0xFF6200EE))

// GOOD
Text(text = "Hello", color = MaterialTheme.colorScheme.primary)

// Custom color extension (avoid raw Color() in screens)
val MyAppColors.danger: Color get() = Color(0xFFB00020)
```

---

## Performance: Avoiding Recomposition

### Stability rules

- `data class` with only immutable fields is **stable** — Compose skips recomposition if inputs unchanged.
- Mutable collections (`List`, `Map`) are **unstable** — use `@Stable` or `kotlinx.collections.immutable`.
- Lambdas captured from non-stable objects cause **extra recompositions**.

```kotlin
// BAD — unstable list causes recomposition
@Composable
fun MediaList(items: List<MediaItem>) { ... }

// GOOD — use ImmutableList
@Composable
fun MediaList(items: ImmutableList<MediaItem>) { ... }
```

### `key()` in LazyColumn

```kotlin
LazyColumn {
    items(items = mediaItems, key = { it.id }) { item ->
        MediaItemRow(item = item)
    }
}
```

### Heavy computation — remember it

```kotlin
// BAD — computed every recomposition
val sorted = items.sortedBy { it.title }

// GOOD
val sorted = remember(items) { items.sortedBy { it.title } }
```

---

## Automotive UI Constraints

| Constraint | Rule |
|---|---|
| Touch target | Minimum **76 dp × 76 dp** (Android Automotive HMI guidelines) |
| Interaction depth while driving | **Maximum 2 interactions** to complete a task |
| Text input | **Not allowed while driving** — use `Car UX Restrictions` |
| List items | Minimum **72 dp height**; limit visible items |
| Animations | Keep under **200 ms**; no looping animations in foreground |

```kotlin
@Composable
fun AutoButton(text: String, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        modifier = Modifier.defaultMinSize(minWidth = 76.dp, minHeight = 76.dp),
    ) {
        Text(text = text, style = MaterialTheme.typography.labelLarge)
    }
}
```

---

## Navigation in Compose

```kotlin
@Composable
fun AppNavHost(navController: NavHostController) {
    NavHost(navController = navController, startDestination = "home") {
        composable("home") {
            HomeScreen(onNavigateToDetail = { id ->
                navController.navigate("detail/$id")
            })
        }
        composable(
            route = "detail/{itemId}",
            arguments = listOf(navArgument("itemId") { type = NavType.StringType }),
        ) { backStackEntry ->
            DetailScreen(
                itemId = backStackEntry.arguments!!.getString("itemId")!!,
                onBack = { navController.navigateUp() },
            )
        }
    }
}
```

**Rules**
- Use `rememberNavController()` in the top-level composable.
- Pass `NavController` only to the top-level screen composable — pass lambdas downward.
- For ViewModel-triggered navigation use a `SharedFlow<NavigationEvent>` and collect in `LaunchedEffect`.

---

## Animations

```kotlin
// Animated visibility
AnimatedVisibility(visible = showPanel) {
    PanelContent()
}

// Animated value
val elevation by animateDpAsState(
    targetValue = if (isElevated) 8.dp else 0.dp,
    label = "elevation animation",
)

// Content size change
Box(modifier = Modifier.animateContentSize()) {
    if (expanded) ExpandedContent() else CollapsedContent()
}
```

---

## XML / View Interop

```kotlin
// Embed an XML View in Compose
AndroidView(
    factory = { context -> MapView(context).apply { onCreate(null) } },
    update = { mapView -> mapView.getMapAsync { it.moveCamera(...) } },
)

// Embed Compose in XML Activity/Fragment
// In layout XML:
// <androidx.compose.ui.platform.ComposeView android:id="@+id/compose_view" />

// In Fragment:
binding.composeView.setContent {
    MyAppTheme { MyScreen() }
}
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Create the Composable function
Annotate with `@Composable`; accept only `UiState` and lambdas — no ViewModel directly.

### Step 2: Manage state
Use `remember`/`mutableStateOf` for local state; hoist shared state to the ViewModel.

### Step 3: Apply theming
Use `MaterialTheme.colorScheme` and `MaterialTheme.typography`; avoid hardcoded colors.

### Step 4: Add a preview
Annotate with `@Preview` with sample data; iterate in the Design canvas before running.

### Step 5: Write Compose UI tests
Use `ComposeTestRule.setContent {}` and `onNodeWithTag()` / `performClick()` for assertions.


## Troubleshooting

- **Excessive recomposition** — use the Layout Inspector's Recomposition counts; stabilize lambdas with `remember { {}}`; annotate classes with `@Stable`.
- **State not persisting across configuration changes** — use `rememberSaveable` for UI state that must survive rotation; use ViewModel for business data.
- **Compose and XML view layout fighting** — when using `ComposeView` inside XML, set `layoutParams` explicitly; avoid `wrap_content` on both dimensions.
- **`@Preview` crashes** — preview functions cannot use `hiltViewModel()`; provide a fake ViewModel via `PreviewParameterProvider`.


## Pre-Commit Checklist

- [ ] All stateful composables hoist state to ViewModel or parent.
- [ ] `Modifier` is the last named parameter before content lambdas.
- [ ] No `Color()` literals in screen composables — only `MaterialTheme.colorScheme.*`.
- [ ] No heavy work in composition — use `remember` or `LaunchedEffect`.
- [ ] `LazyColumn` items have stable `key` lambda.
- [ ] Side effects are in the correct effect handler (not in composition body).
- [ ] Automotive touch targets ≥ 76 dp; text input blocked while driving.
- [ ] Animations complete within 200 ms.
- [ ] Screenshot/UI tests added for new screens.

---

## References

- [Jetpack Compose Documentation](https://developer.android.com/jetpack/compose)
- [Compose Performance Guide](https://developer.android.com/jetpack/compose/performance)
- [Material Design 3 for Android](https://m3.material.io/develop/android/get-started)
- [Automotive OS Design Guidelines](https://developer.android.com/training/cars/apps/ui-guidelines)
- [Compose Navigation](https://developer.android.com/jetpack/compose/navigation)
