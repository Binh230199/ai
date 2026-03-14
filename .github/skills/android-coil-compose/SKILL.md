---
name: android-coil-compose
description: >
  Use when implementing image loading in Jetpack Compose using Coil.
  Covers AsyncImage, ImageRequest, placeholder/error states, transformations,
  memory and disk cache configuration, custom ImageLoader, and performance
  optimization. Applies to Android Studio (Gradle) and AOSP (Soong) on
  Android Automotive / AAOS targets.
argument-hint: <screen-or-component> [write|review|optimize]
---

# Coil for Jetpack Compose

Expert practices for image loading in Jetpack Compose using **Coil 2** —
the Kotlin-first, coroutine-native image loading library.

Standards baseline: **Coil 2.6+** · **Compose BOM 2024.x**.

---

## When to Use This Skill

- Displaying remote images (artwork, thumbnails, album art) in Compose screens.
- Configuring placeholder, error, and loading states for images.
- Applying image transformations (circle crop, blur, rounded corners).
- Tuning memory and disk cache for automotive media apps with large image sets.
- Creating a custom `ImageLoader` (custom headers, OkHttp client integration).
- Debugging image loading failures (cache misses, decoding errors).

---

## Setup

### Gradle (`libs.versions.toml`)

```toml
[versions]
coil = "2.6.0"

[libraries]
coil-compose = { group = "io.coil-kt", name = "coil-compose", version.ref = "coil" }
coil-video = { group = "io.coil-kt", name = "coil-video", version.ref = "coil" }
coil-gif = { group = "io.coil-kt", name = "coil-gif", version.ref = "coil" }
```

```kotlin
// feature module build.gradle.kts
dependencies {
    implementation(libs.coil.compose)
}
```

### AOSP (`Android.bp`)

```soong
android_app {
    name: "MyApp",
    static_libs: [
        "coil",
        "coil-compose",
    ],
    ...
}
```

---

## Basic Usage

### AsyncImage — simplest form

```kotlin
AsyncImage(
    model = "https://cdn.example.com/artwork/12345.jpg",
    contentDescription = stringResource(R.string.album_art_description),
    modifier = Modifier
        .size(200.dp)
        .clip(RoundedCornerShape(12.dp)),
    contentScale = ContentScale.Crop,
)
```

### With placeholder and error states

```kotlin
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data("https://cdn.example.com/artwork/12345.jpg")
        .crossfade(true)
        .build(),
    contentDescription = stringResource(R.string.album_art_description),
    placeholder = painterResource(R.drawable.ic_album_placeholder),
    error = painterResource(R.drawable.ic_album_error),
    fallback = painterResource(R.drawable.ic_album_placeholder),  // when data is null
    modifier = Modifier.size(200.dp),
    contentScale = ContentScale.Crop,
)
```

**Rules**
- Always provide `contentDescription` — required for accessibility / TalkBack.
- Always provide `placeholder` and `error` — never show an empty view while loading.
- Use `crossfade(true)` for smooth transitions; avoid it on lists with many items (performance).

---

## SubcomposeAsyncImage — Custom Loading States

Use when you need a custom composable for loading/error states (not just a drawable):

```kotlin
SubcomposeAsyncImage(
    model = artworkUrl,
    contentDescription = null,
    modifier = Modifier.fillMaxWidth().aspectRatio(1f),
) {
    when (painter.state) {
        is AsyncImagePainter.State.Loading -> {
            Box(
                modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.surfaceVariant),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator(modifier = Modifier.size(32.dp))
            }
        }
        is AsyncImagePainter.State.Error -> {
            Icon(
                imageVector = Icons.Default.BrokenImage,
                contentDescription = null,
                modifier = Modifier.size(48.dp),
                tint = MaterialTheme.colorScheme.error,
            )
        }
        else -> Image(painter = painter, contentDescription = null, contentScale = ContentScale.Crop)
    }
}
```

---

## ImageRequest — Advanced Configuration

```kotlin
val request = ImageRequest.Builder(context)
    .data(artworkUrl)
    .size(400, 400)                          // decode at target size — saves memory
    .scale(Scale.CROP)
    .transformations(
        RoundedCornersTransformation(16f),   // or: CircleCropTransformation()
    )
    .memoryCacheKey("artwork_${trackId}")    // explicit cache key
    .diskCacheKey("artwork_${trackId}")
    .crossfade(250)                          // 250 ms crossfade
    .listener(
        onError = { _, result -> Log.e("Coil", "Image load failed", result.throwable) },
    )
    .build()
```

---

## Custom ImageLoader

Configure once in `Application` or Hilt `SingletonComponent`:

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object ImageModule {

    @Provides
    @Singleton
    fun provideImageLoader(
        @ApplicationContext context: Context,
        okHttpClient: OkHttpClient,          // reuse app's OkHttp — auth, SSL
    ): ImageLoader = ImageLoader.Builder(context)
        .okHttpClient(okHttpClient)
        .memoryCache {
            MemoryCache.Builder(context)
                .maxSizePercent(0.25)        // 25% of available memory
                .build()
        }
        .diskCache {
            DiskCache.Builder()
                .directory(context.cacheDir.resolve("image_cache"))
                .maxSizeBytes(100L * 1024 * 1024)  // 100 MB
                .build()
        }
        .respectCacheHeaders(false)          // ignore server Cache-Control (local CDN)
        .crossfade(true)
        .build()
}
```

### Provide to Compose via CompositionLocal

```kotlin
// In your top-level composable / Activity
val imageLoader = hiltViewModel<ImageLoaderViewModel>().imageLoader  // or inject directly

CompositionLocalProvider(LocalImageLoader provides imageLoader) {
    MyAppTheme { AppNavHost() }
}

// In any composable, pick up the shared loader
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current).data(url).build(),
    imageLoader = LocalImageLoader.current,
    contentDescription = null,
)
```

**Rules**
- Create `ImageLoader` once as a `@Singleton` — never instantiate `ImageLoader.Builder` inside a composable.
- Reuse the app's `OkHttpClient` — shares connection pool and auth interceptors.
- Set `maxSizePercent(0.25)` for memory cache — automotive devices can have constrained RAM.

---

## Performance Patterns

### Request-level size limiting

```kotlin
// Always specify target size to avoid decoding full-resolution images into memory
ImageRequest.Builder(context)
    .data(url)
    .size(thumbnailWidth, thumbnailHeight)
    .scale(Scale.FILL)
    .build()
```

### Preloading in ViewModel (prefetch next page)

```kotlin
fun prefetchArtwork(items: List<MediaItem>) {
    items.forEach { item ->
        val request = ImageRequest.Builder(context)
            .data(item.artworkUrl)
            .size(200, 200)
            .memoryCachePolicy(CachePolicy.ENABLED)
            .diskCachePolicy(CachePolicy.ENABLED)
            .build()
        imageLoader.enqueue(request)
    }
}
```

### LazyList performance

```kotlin
LazyColumn {
    items(items = mediaItems, key = { it.id }) { item ->
        // Use fixed size — avoids recomposition on image load
        AsyncImage(
            model = item.artworkUrl,
            contentDescription = null,
            modifier = Modifier.size(72.dp),   // always fixed, never wrap_content
        )
    }
}
```

**Rules**
- Always use fixed `Modifier.size()` in lazy lists — dynamic size causes recomposition storms.
- Avoid `crossfade` in LazyColumn with 50+ items — use it only on detail screens.
- Set explicit `diskCachePolicy` and `memoryCachePolicy` — defaults are enabled but make it explicit.

---

## Transformations Reference

```kotlin
.transformations(CircleCropTransformation())
.transformations(RoundedCornersTransformation(topLeft = 8f, topRight = 8f, bottomLeft = 0f, bottomRight = 0f))
.transformations(BlurTransformation(context, radius = 20f))
// Combine
.transformations(BlurTransformation(context, 10f), RoundedCornersTransformation(12f))
```

---

## Testing

```kotlin
// Fake ImageLoader in tests — avoids real network calls
val fakeImageLoader = ImageLoader.Builder(context)
    .components { add(FakeImageDecoderDecoder.Factory()) }  // or use test factory
    .build()

// In Compose tests
composeTestRule.setContent {
    CompositionLocalProvider(LocalImageLoader provides fakeImageLoader) {
        MediaCard(item = testItem)
    }
}
```

---

## Prerequisites

- Android Studio (Flamingo or newer) **or** AOSP build environment set up.
- Android SDK Platform-Tools installed (`adb` on PATH).
- Target device or emulator running Android 11+ (API 30+).
- For AOSP modules: `repo` tool, AOSP source synced, `lunch` target configured.


## Step-by-Step Workflows

### Step 1: Add the Coil dependency
Add `implementation("io.coil-kt:coil-compose:<version>")` to `build.gradle.kts`.

### Step 2: Use AsyncImage in your Composable
Call `AsyncImage(model = url, contentDescription = ...)` for basic image loading.

### Step 3: Configure ImageRequest (if needed)
Use `ImageRequest.Builder` to set placeholders, error drawables, or transformations.

### Step 4: Customize the ImageLoader (optional)
Build a singleton `ImageLoader` in your Hilt DI module with cache size and disk policies.

### Step 5: Test image loading
Use `FakeImageLoader` in unit tests; use Paparazzi/Roborazzi for screenshot tests.


## Troubleshooting

- **Image is null / blank** — check that the URL is accessible; add `OkHttpClient` with logging interceptor to debug the network request.
- **Placeholder never replaced** — the `ImageRequest` may be failing silently; add an `error()` drawable and a `listener` to log failures.
- **Memory pressure / OOM** — reduce `memoryCachePolicy` to `DISABLED` for large single-use images; set an explicit `size` constraint.
- **Custom transformation not applied** — ensure `transformations(...)` is called on `ImageRequest.Builder`, not on `AsyncImage` directly.


## Pre-Commit Checklist

- [ ] `ImageLoader` is a singleton — not created inside composable.
- [ ] `contentDescription` provided on every `AsyncImage`.
- [ ] `placeholder` and `error` drawables set on all remote images.
- [ ] Fixed `Modifier.size()` used in lazy lists.
- [ ] OkHttp client shared with app's network module.
- [ ] Memory cache sized appropriately (`maxSizePercent(0.25)` or lower on constrained devices).
- [ ] Disk cache has bounded `maxSizeBytes`.
- [ ] `crossfade` disabled in high-item-count lists.

---

## References

- [Coil documentation](https://coil-kt.github.io/coil/)
- [Coil + Compose guide](https://coil-kt.github.io/coil/compose/)
- [Coil performance tips](https://coil-kt.github.io/coil/getting_started/#requests)
