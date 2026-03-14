---
name: android-networking
description: >
  Use when implementing or reviewing networking code in Android apps using Retrofit
  and OkHttp. Covers typed API service interfaces, JSON serialization (Kotlin
  Serialization / Gson / Moshi), interceptors (auth, logging, retry), error handling,
  SSL/certificate pinning, and offline-first patterns with Flow. Applies to Android
  Studio (Gradle) and AOSP (Soong) on Android Automotive / AAOS targets.
argument-hint: <api-service-or-feature> [write|review|debug]
---

# Android Networking — Retrofit + OkHttp

Expert practices for building reliable, secure, and testable network layers in
Android applications, using **Retrofit 2** + **OkHttp 4** with **Kotlin Coroutines**.

Standards baseline: **Retrofit 2.11+** · **OkHttp 4.12+** · **Kotlin Serialization 1.6+**.

---

## When to Use This Skill

- Defining a new Retrofit API service interface.
- Setting up OkHttp client with interceptors (auth token, logging).
- Implementing retry logic, timeout configuration, or certificate pinning.
- Handling HTTP errors and mapping them to domain `Result<T>`.
- Configuring the network layer in Hilt modules.
- Troubleshooting network calls (timeouts, serialization errors, SSL issues).

---

## Prerequisites

- Kotlin Coroutines (see `android-kotlin-coroutines` skill).
- Hilt DI (see `android-architecture` skill).
- Gradle or AOSP dependency setup (see `android-build-system` skill).

---

## Project Setup

### Gradle (`libs.versions.toml`)

```toml
[versions]
retrofit = "2.11.0"
okhttp = "4.12.0"
kotlin-serialization = "1.6.3"

[libraries]
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
retrofit-kotlin-serialization = { group = "com.jakewharton.retrofit", name = "retrofit2-kotlinx-serialization-converter", version = "1.0.0" }
okhttp = { group = "com.squareup.okhttp3", name = "okhttp", version.ref = "okhttp" }
okhttp-logging = { group = "com.squareup.okhttp3", name = "logging-interceptor", version.ref = "okhttp" }

[plugins]
kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
```

```kotlin
// feature module build.gradle.kts
dependencies {
    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlin.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
}
```

### AOSP (`Android.bp`)

```soong
android_app {
    name: "MyApp",
    static_libs: [
        "retrofit",
        "okhttp",
        "okhttp-logging-interceptor",
        "kotlinx-serialization-json",
    ],
    ...
}
```

---

## API Service Interface

```kotlin
interface MediaApiService {

    @GET("v1/media")
    suspend fun getMedia(
        @Query("page") page: Int,
        @Query("size") size: Int,
        @Query("genre") genre: String? = null,
    ): MediaListResponse

    @GET("v1/media/{id}")
    suspend fun getMediaById(@Path("id") id: String): MediaDetailResponse

    @POST("v1/media/favorites")
    suspend fun addFavorite(@Body request: AddFavoriteRequest): Response<Unit>

    @DELETE("v1/media/favorites/{id}")
    suspend fun removeFavorite(@Path("id") id: String): Response<Unit>

    @Multipart
    @POST("v1/media/upload")
    suspend fun uploadMedia(
        @Part file: MultipartBody.Part,
        @Part("title") title: RequestBody,
    ): MediaDetailResponse
}
```

**Rules**
- Use `suspend` for all Retrofit methods — never `Call<T>` in new code.
- Return `Response<T>` when you need to inspect HTTP status codes; return `T` directly when a non-2xx triggers an exception.
- Use `@Query` with nullable types for optional parameters.
- Never put raw JSON strings in `@Body` — always use typed request DTOs.

---

## Data Transfer Objects (DTOs)

```kotlin
// DTOs live in the data layer — never exposed to domain
@Serializable
data class MediaListResponse(
    @SerialName("items") val items: List<MediaItemDto>,
    @SerialName("total") val total: Int,
    @SerialName("next_page") val nextPage: Int? = null,
)

@Serializable
data class MediaItemDto(
    @SerialName("id") val id: String,
    @SerialName("title") val title: String,
    @SerialName("duration_ms") val durationMs: Long,
    @SerialName("artwork_url") val artworkUrl: String,
)

// Mapper in data layer — domain entity has no @Serializable
fun MediaItemDto.toDomain() = MediaItem(
    id = id,
    title = title,
    durationMs = durationMs,
    artworkUrl = artworkUrl,
)
```

**Rules**
- DTOs are annotated with `@Serializable`; domain entities are plain `data class`.
- Map DTO → domain in the repository or data source — never in the ViewModel.
- Use `@SerialName` for every field — don't rely on property name matching.
- Use default values (`= null`) for optional fields to survive API additions.

---

## OkHttp Client Configuration

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(buildLoggingInterceptor())
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .build()

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        val json = Json {
            ignoreUnknownKeys = true   // survive API evolution
            isLenient = false
            coerceInputValues = false
        }
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
    }

    @Provides
    @Singleton
    fun provideMediaApiService(retrofit: Retrofit): MediaApiService =
        retrofit.create(MediaApiService::class.java)

    private fun buildLoggingInterceptor() = HttpLoggingInterceptor().apply {
        level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY
                else HttpLoggingInterceptor.Level.NONE
    }
}
```

**Rules**
- `ignoreUnknownKeys = true` — never crash on new server fields.
- Logging interceptor must be `NONE` in release builds — API responses may contain PII.
- `baseUrl` from `BuildConfig` — never hardcoded.
- Add `authInterceptor` as application interceptor, not network interceptor.

---

## Authentication Interceptor

```kotlin
class AuthInterceptor @Inject constructor(
    private val tokenRepository: TokenRepository,
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenRepository.getAccessToken()  // sync — called from OkHttp thread
        val request = if (token != null) {
            chain.request().newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            chain.request()
        }
        return chain.proceed(request)
    }
}
```

### Token refresh interceptor (Authenticator)

```kotlin
class TokenAuthenticator @Inject constructor(
    private val tokenRepository: TokenRepository,
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        if (response.code != 401) return null
        val newToken = runBlocking { tokenRepository.refreshToken() } ?: return null
        return response.request.newBuilder()
            .header("Authorization", "Bearer $newToken")
            .build()
    }
}
```

```kotlin
OkHttpClient.Builder()
    .authenticator(tokenAuthenticator)
    ...
```

**Rules**
- Use `Authenticator` for 401 token refresh — do not implement retry in the interceptor.
- `runBlocking` in `Authenticator.authenticate` is acceptable — OkHttp runs this on a background thread.
- Never log `Authorization` header values.

---

## Error Handling

### Sealed result mapper

```kotlin
sealed interface NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>
    data class HttpError(val code: Int, val message: String) : NetworkResult<Nothing>
    data class NetworkError(val throwable: Throwable) : NetworkResult<Nothing>
}

suspend fun <T> safeApiCall(call: suspend () -> T): NetworkResult<T> =
    try {
        NetworkResult.Success(call())
    } catch (e: HttpException) {
        NetworkResult.HttpError(e.code(), e.message())
    } catch (e: IOException) {
        NetworkResult.NetworkError(e)
    }
```

### Usage in repository

```kotlin
override suspend fun getMediaItems(): Result<List<MediaItem>> =
    withContext(ioDispatcher) {
        when (val result = safeApiCall { apiService.getMedia(page = 1, size = 20) }) {
            is NetworkResult.Success ->
                Result.success(result.data.items.map { it.toDomain() })
            is NetworkResult.HttpError ->
                Result.failure(HttpException(result.code, result.message))
            is NetworkResult.NetworkError ->
                Result.failure(result.throwable)
        }
    }
```

**Rules**
- Never let `HttpException` or `IOException` propagate uncaught to the ViewModel.
- Map network errors to domain-layer `Result<T>` in the repository.
- Distinguish `HttpError` (server responded) from `NetworkError` (no connectivity) — show different UI messages.

---

## SSL / Certificate Pinning

```kotlin
val certificatePinner = CertificatePinner.Builder()
    .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .add("api.example.com", "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=") // backup pin
    .build()

OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    ...
```

**Rules**
- Always pin **two** certificates (current + backup) to survive rotation.
- Pin the leaf certificate SHA-256 SPKI hash, not the full certificate.
- Disable pinning in debug builds via `BuildConfig.DEBUG` check.
- Test pin values before deploying — a wrong pin blocks all traffic.

---

## Fake for Testing

```kotlin
class FakeMediaApiService : MediaApiService {
    var mediaListResponse: MediaListResponse = MediaListResponse(emptyList(), 0)
    var shouldThrow: Boolean = false

    override suspend fun getMedia(page: Int, size: Int, genre: String?): MediaListResponse {
        if (shouldThrow) throw IOException("Simulated network error")
        return mediaListResponse
    }

    override suspend fun getMediaById(id: String): MediaDetailResponse =
        throw NotImplementedError("Not needed for this test")
}
```

**Rules**
- Prefer fakes over mocks for API service — fakes give realistic data control.
- Never make real network calls in unit or integration tests.
- Use `MockWebServer` (OkHttp) for full-stack networking integration tests.

---

## Step-by-Step Workflows

### Step 1: Add Retrofit and OkHttp dependencies
Add `retrofit2:retrofit`, `okhttp3:okhttp`, and a converter (e.g., `converter-gson`) to Gradle.

### Step 2: Define the API service interface
Annotate methods with `@GET`, `@POST`, etc.; use `suspend fun` for coroutine support.

### Step 3: Build the Retrofit instance
Create a singleton `Retrofit` backed by `OkHttpClient`; expose it via a Hilt module.

### Step 4: Handle errors consistently
Wrap calls in `try/catch`; map HTTP error codes to domain `Result<T>` / sealed class types.

### Step 5: Test with MockWebServer
Use `MockWebServer` for integration tests; mock the interface for isolated unit tests.


## Troubleshooting

- **`NetworkOnMainThreadException`** — all network calls must use `suspend` functions on `Dispatchers.IO`; never call blocking APIs on the main thread.
- **SSL handshake failure** — check that the server certificates are valid; for debug builds only, use `network_security_config.xml` to allow cleartext.
- **JSON deserialization error** — `null` field in JSON not handled; annotate DTO fields with `@SerializedName` and provide default values.
- **Retrofit `NullPointerException` on API response** — use nullable return types (`Response<T>?`) when the server may return empty bodies.


## Pre-Commit Checklist

- [ ] No hardcoded `baseUrl` — sourced from `BuildConfig`.
- [ ] `HttpLoggingInterceptor` set to `NONE` in release builds.
- [ ] `ignoreUnknownKeys = true` in `Json` configuration.
- [ ] `@SerialName` on every DTO field.
- [ ] DTOs not exposed beyond the data layer — mapped to domain entities.
- [ ] Network errors wrapped in `Result.failure(...)` before reaching ViewModel.
- [ ] Certificate pinning uses redundant (backup) pin.
- [ ] `AuthInterceptor` does not log token values.
- [ ] Unit tests use a fake or `MockWebServer`, not the real API.

---

## References

- [Retrofit documentation](https://square.github.io/retrofit/)
- [OkHttp documentation](https://square.github.io/okhttp/)
- [Kotlin Serialization](https://kotlinlang.org/docs/serialization.html)
- [OkHttp MockWebServer](https://github.com/square/okhttp/tree/master/mockwebserver)
- [Certificate Pinning Guide](https://square.github.io/okhttp/features/https/#certificate-pinning)
