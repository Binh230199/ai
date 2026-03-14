---
name: android-xml-to-compose-migration
description: >
  Use when converting XML-based Android layouts and Views to idiomatic Jetpack
  Compose. Covers layout mapping (LinearLayout, ConstraintLayout, RecyclerView),
  widget migration (TextView, ImageView, Button, EditText), theme/style migration
  to Material 3, interop (AndroidView, ComposeView), incremental migration strategy,
  and common pitfalls. Applies to AAOS legacy app modernization.
argument-hint: <layout-or-screen-name> [migrate|review|plan]
---

# XML to Compose Migration

A step-by-step guide for migrating Android XML layout screens and View-based UI to
**Jetpack Compose**, covering layout equivalents, widget mapping, style migration,
and a safe incremental strategy for production AAOS apps.

Standards baseline: **Compose BOM 2024.x** · **Material Design 3**.

---

## When to Use This Skill

- Converting a specific XML layout file (`fragment_*.xml`, `activity_*.xml`, `item_*.xml`) to Compose.
- Planning an incremental Compose migration strategy for a legacy screen or module.
- Reviewing a completed migration for correctness and idiomatic patterns.
- Handling interop between existing XML Views and new Compose screens.

---

## Migration Strategy

### Recommended approach: Screen-by-screen (Strangler Fig)

Do **not** migrate the entire app at once. Use the interop layer to migrate one screen
at a time:

```
Phase 1: Add ComposeView into existing XML Activity/Fragment
Phase 2: Migrate leaf screens (simple, no nested fragments) first
Phase 3: Migrate container screens (NavHostFragment → NavHost)
Phase 4: Remove XML layouts; Activity becomes a single ComposeView host
```

### Migration readiness checklist per screen

- [ ] Identify all Views, listeners, and state sources.
- [ ] Identify which state comes from ViewModel (LiveData/StateFlow) vs View internal state.
- [ ] Map every XML View to a Compose equivalent (see tables below).
- [ ] Identify custom Views — migrate after standard views.

---

## Layout Equivalents

### Linear layouts

| XML | Compose |
|---|---|
| `LinearLayout (vertical)` | `Column` |
| `LinearLayout (horizontal)` | `Row` |
| `LinearLayout + weight` | `Column/Row` with `Modifier.weight(1f)` |
| `FrameLayout` | `Box` |
| `ConstraintLayout` | `ConstraintLayout` (compose-constraintlayout) or `Box` + nesting |
| `ScrollView` | `Column` inside `verticalScroll(rememberScrollState())` |
| `HorizontalScrollView` | `Row` inside `horizontalScroll(rememberScrollState())` |
| `RecyclerView (vertical)` | `LazyColumn` |
| `RecyclerView (horizontal)` | `LazyRow` |
| `RecyclerView (grid)` | `LazyVerticalGrid` |
| `ViewPager2` | `HorizontalPager` (Accompanist / Compose Foundation) |

### Layout attributes

| XML attribute | Compose equivalent |
|---|---|
| `android:padding="16dp"` | `Modifier.padding(16.dp)` |
| `android:layout_margin="8dp"` | `Modifier.padding(8.dp)` (on parent side) |
| `android:layout_width="match_parent"` | `Modifier.fillMaxWidth()` |
| `android:layout_height="match_parent"` | `Modifier.fillMaxHeight()` |
| `android:layout_width="wrap_content"` | default (no modifier needed) |
| `android:visibility="gone"` | `if (visible) { Composable() }` |
| `android:visibility="invisible"` | `Modifier.alpha(0f)` or `if (visible)` |
| `android:background="@color/..."` | `Modifier.background(MaterialTheme.colorScheme.surface)` |
| `android:elevation="4dp"` | `Card(elevation = CardDefaults.cardElevation(4.dp))` |
| `android:clipToOutline="true"` | `Modifier.clip(shape)` |

---

## Widget Equivalents

| XML Widget | Compose Equivalent |
|---|---|
| `TextView` | `Text` |
| `ImageView` | `Image` (local) / `AsyncImage` (remote via Coil) |
| `Button` | `Button { Text("...") }` |
| `ImageButton` | `IconButton { Icon(...) }` |
| `EditText` | `OutlinedTextField` / `TextField` |
| `CheckBox` | `Checkbox` |
| `Switch` | `Switch` |
| `RadioButton` | `RadioButton` |
| `SeekBar` | `Slider` |
| `ProgressBar (circular)` | `CircularProgressIndicator` |
| `ProgressBar (linear)` | `LinearProgressIndicator` |
| `Spinner` | `ExposedDropdownMenuBox` with `ExposedDropdownMenu` |
| `TabLayout + ViewPager2` | `TabRow` + `HorizontalPager` |
| `BottomNavigationView` | `NavigationBar` |
| `NavigationView` (drawer) | `ModalNavigationDrawer` |
| `Toolbar` / `AppBarLayout` | `TopAppBar` (Material 3) |
| `FloatingActionButton` | `FloatingActionButton` |
| `Snackbar` | `SnackbarHost` + `SnackbarHostState` |
| `Dialog` | `AlertDialog` |
| `Toast` | `Snackbar` (prefer) or `LaunchedEffect { Toast.makeText(...) }` |
| `CardView` | `Card` |
| `Chip` | `FilterChip` / `SuggestionChip` / `AssistChip` |
| `Divider` | `HorizontalDivider` (M3) |

---

## Style / Theme Migration

### Colors

```xml
<!-- colors.xml (old) -->
<color name="primary">#6200EE</color>
<color name="on_primary">#FFFFFF</color>
```

```kotlin
// Compose Material 3 ColorScheme
val LightColorScheme = lightColorScheme(
    primary = Color(0xFF6200EE),
    onPrimary = Color.White,
    secondary = Color(0xFF03DAC6),
    // ...
)
```

### Text styles

```xml
<!-- themes.xml (old) -->
<style name="TextAppearance.MyApp.Title">
    <item name="android:textSize">20sp</item>
    <item name="android:fontFamily">@font/roboto_medium</item>
    <item name="android:textColor">@color/on_surface</item>
</style>
```

```kotlin
// Compose Typography
val MyTypography = Typography(
    titleLarge = TextStyle(
        fontFamily = RobotoFamily,
        fontWeight = FontWeight.Medium,
        fontSize = 20.sp,
    ),
)

// Usage
Text(text = "Hello", style = MaterialTheme.typography.titleLarge)
```

### Dimensions (`dimens.xml` → Kotlin constants)

```xml
<!-- dimens.xml (old) -->
<dimen name="spacing_medium">16dp</dimen>
<dimen name="card_corner_radius">8dp</dimen>
```

```kotlin
// Compose design tokens (core:ui module)
object Dimens {
    val SpacingMedium = 16.dp
    val CardCornerRadius = 8.dp
}

// Usage
Modifier.padding(Dimens.SpacingMedium)
```

---

## Typical Screen Migration Example

### Before: XML Fragment

```xml
<!-- fragment_media_detail.xml -->
<LinearLayout vertical>
    <ImageView android:id="@+id/artwork" android:layout_width="match_parent" />
    <TextView android:id="@+id/title" style="@style/TitleText" />
    <TextView android:id="@+id/artist" />
    <Button android:id="@+id/play_button" android:text="@string/play" />
</LinearLayout>
```

```kotlin
// MediaDetailFragment.kt (old)
class MediaDetailFragment : Fragment(R.layout.fragment_media_detail) {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.artwork.load(viewModel.artworkUrl)
        binding.title.text = viewModel.title
        binding.playButton.setOnClickListener { viewModel.play() }
    }
}
```

### After: Compose Screen

```kotlin
@Composable
fun MediaDetailScreen(
    uiState: MediaDetailUiState,
    onPlayClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.fillMaxSize()) {
        AsyncImage(
            model = uiState.artworkUrl,
            contentDescription = null,
            modifier = Modifier.fillMaxWidth().aspectRatio(1f),
            contentScale = ContentScale.Crop,
        )
        Text(
            text = uiState.title,
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
        )
        Text(
            text = uiState.artist,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(horizontal = 16.dp),
        )
        Button(
            onClick = onPlayClick,
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
        ) {
            Text(stringResource(R.string.play))
        }
    }
}

// Fragment hosts the Compose screen during migration
class MediaDetailFragment : Fragment() {
    private val viewModel: MediaDetailViewModel by viewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?) =
        ComposeView(requireContext()).apply {
            setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
            setContent {
                MyAppTheme {
                    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
                    MediaDetailScreen(
                        uiState = uiState,
                        onPlayClick = viewModel::play,
                    )
                }
            }
        }
}
```

---

## Interop Patterns

### Using Compose inside XML (ComposeView)

```kotlin
// In a Fragment/Activity that still uses XML layout
binding.composeContainer.apply {  // ComposeView in layout XML
    setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
    setContent {
        MyAppTheme { NewComposableScreen() }
    }
}
```

### Using XML View inside Compose (AndroidView)

```kotlin
// When a View has no Compose equivalent yet (e.g., MapView, custom SurfaceView)
AndroidView(
    factory = { context ->
        MyLegacyView(context).apply {
            // one-time initialization
        }
    },
    update = { view ->
        // called on recomposition — update view with new state
        view.setValue(currentValue)
    },
    modifier = Modifier.fillMaxWidth().height(200.dp),
)
```

**Rules**
- Always set `ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed` on `ComposeView` in Fragments — prevents memory leaks.
- `AndroidView.update` is called on every recomposition — keep it fast and idempotent.
- Avoid retaining Compose state inside `AndroidView.factory` lambda — use `update` for state sync.

---

## RecyclerView → LazyColumn Migration

```kotlin
// Before: RecyclerView + Adapter + ViewHolder
class MediaAdapter(private val onClick: (MediaItem) -> Unit) :
    ListAdapter<MediaItem, MediaViewHolder>(DiffCallback) { ... }

// After: LazyColumn (no adapter, no ViewHolder, no DiffCallback)
@Composable
fun MediaList(
    items: List<MediaItem>,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(modifier = modifier) {
        items(items = items, key = { it.id }) { item ->
            MediaItemRow(
                item = item,
                onItemClick = { onItemClick(item.id) },
            )
        }
    }
}
```

**Key differences**
- No `DiffCallback` — Compose diffing is handled automatically with `key`.
- No `ViewHolder` — composables are reused by Compose runtime.
- No `notifyDataSetChanged` — just pass new list to `items()`.

---

## Common Pitfalls

| Pitfall | Solution |
|---|---|
| `ComposeView` in Fragment without strategy | Always set `ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed` |
| `collectAsState()` without lifecycle awareness | Use `collectAsStateWithLifecycle()` |
| Setting theme twice (XML + Compose) | Apply `MaterialTheme` once at top-level only |
| `match_parent` not working in Compose | Use `Modifier.fillMaxWidth()` / `fillMaxSize()` |
| View functions in `AndroidView.update` causing recomposition | Extract stable lambdas or use `remember` |
| `LiveData` observe in Compose via `observeAsState` | Migrate to `StateFlow` + `collectAsStateWithLifecycle()` |

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Identify the screen to migrate
Start with leaf screens (no nested Fragments); defer screens with complex custom views.

### Step 2: Map each XML view to a Compose equivalent
Use the Layout Equivalence and Widget Equivalence tables below.

### Step 3: Introduce ComposeView or migrate the Fragment
Use `ComposeView` for incremental migration; fully replace Fragment for complete migration.

### Step 4: Migrate the theme
Map XML styles/themes to MaterialTheme tokens; remove XML theme references from activities.

### Step 5: Verify behavior and visual spec
Run existing Espresso tests (compatible with `ComposeView`); add Compose tests for new interactions.


## Troubleshooting

- **`ComposeView` inside RecyclerView causes performance issues** — pre-allocate Compose views; use `AbstractComposeView` for better reuse.
- **Theme mismatch (XML vs Compose)** — wrap `ComposeView` with `MaterialTheme { ... }` to ensure consistent theming at the boundary.
- **Espresso test fails after migration** — `ComposeView` nodes are accessible from Espresso; check that `testTag`s are correctly set.
- **Navigation back stack broken** — XML Fragment navigation and Compose `NavHost` must not overlap; pick one navigation system per screen.


## Pre-Commit Checklist

- [ ] `ComposeView` in Fragment uses `ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed`.
- [ ] All colors/text styles from Compose screens use `MaterialTheme` tokens.
- [ ] `LazyColumn` items have `key` lambda.
- [ ] `collectAsStateWithLifecycle()` used (not `collectAsState()`).
- [ ] No duplicate theme wrapping in the composable hierarchy.
- [ ] XML layout file removed after full migration — not left as dead code.
- [ ] Strings still reference `R.string.*` — no hardcoded strings introduced during migration.

---

## References

- [Compose migration guide (official)](https://developer.android.com/jetpack/compose/migrate)
- [Interoperability APIs](https://developer.android.com/jetpack/compose/migrate/interoperability-apis/views-in-compose)
- [ComposeView in Fragment](https://developer.android.com/jetpack/compose/migrate/interoperability-apis/compose-in-views)
- [Compose layout basics](https://developer.android.com/jetpack/compose/layouts/basics)
- [Material 3 migration](https://m3.material.io/develop/android/get-started)
