---
name: android-car-app
description: >
  Use when developing Android apps for Android Automotive OS (AAOS), Car App Library,
  or CarService API integration. Covers driver distraction guidelines, CarAppService,
  template navigation, Car UX Restrictions (UXR), CarPropertyManager, HVAC APIs,
  and automotive-specific manifest/build configuration in Gradle and AOSP (Soong).
argument-hint: <feature-name> [car-app-library|carservice|aaos-ui|hvac]
---

# Android Car App Development

Expert practices for building Android applications targeting **Android Automotive OS
(AAOS)** IVI head units and RSE rear-seat systems, using the **Car App Library** and
**CarService APIs**. All UI must comply with automotive **Driver Distraction Guidelines**.

Standards baseline: **Car App Library 1.4+** · **Android API 33** · **AAOS Android 13+**.

---

## When to Use This Skill

- Building an app based on the **Car App Library** (navigation, POI, media, messaging templates).
- Integrating with `CarService` APIs (CarPropertyManager, HVAC, CarAudioManager).
- Handling **Car UX Restrictions (UXR)** — blocking text input, limiting list depth while driving.
- Configuring automotive manifest metadata and AOSP product integration.
- Reviewing automotive UI for driver distraction compliance.

---

## Android Automotive OS vs Android Auto

| | Android Auto | Android Automotive OS |
|---|---|---|
| Runs on | Phone (projected) | In-vehicle head unit |
| Needs phone | Yes | No |
| App entry | Car App Library or Android Auto protocol | Native Android app + Car App Library optional |
| Target | Projection experience | Standalone systemapp |
| Build | Standard APK | APK or AOSP prebuilt |

This skill focuses on **AAOS** (native in-vehicle apps), not Android Auto phone projection.

---

## Car App Library

### Suitable App Categories

- Navigation apps (MapTemplate, RoutePreviewNavigationTemplate)
- Point of Interest (POI) browsers (PlaceListMapTemplate)
- Media apps (use MediaBrowserService — Car App Library not always needed)
- Messaging (MessageTemplate)
- Generic list/grid apps (ListTemplate, GridTemplate)

### App structure

```
CarAppService
    └── Session
            └── Screen (stack managed by ScreenManager)
```

```kotlin
@AndroidEntryPoint
class MyCarAppService : CarAppService() {

    override fun createHostValidator() = HostValidator.ALLOW_ALL_HOSTS_VALIDATOR // dev only

    override fun onCreateSession(): Session = MySession()
}

class MySession : Session() {

    override fun onCreateScreen(intent: Intent): Screen =
        HomeScreen(carContext)
}
```

```xml
<!-- AndroidManifest.xml -->
<service
    android:name=".MyCarAppService"
    android:exported="true">
    <intent-filter>
        <action android:name="androidx.car.app.CarAppService" />
        <category android:name="androidx.car.app.category.POI" />
        <!-- or: navigation, parking, charging, iot, misc -->
    </intent-filter>
</service>

<meta-data
    android:name="androidx.car.app.minCarApiLevel"
    android:value="3" />
```

---

## Templates

### ListTemplate

```kotlin
class HomeScreen(carContext: CarContext) : Screen(carContext) {

    override fun onGetTemplate(): Template {
        val listBuilder = ItemList.Builder()
        menuItems.forEach { item ->
            listBuilder.addItem(
                Row.Builder()
                    .setTitle(item.title)
                    .addText(item.subtitle)
                    .setOnClickListener { screenManager.push(DetailScreen(carContext, item.id)) }
                    .build()
            )
        }

        return ListTemplate.Builder()
            .setHeaderAction(Action.APP_ICON)
            .setTitle(carContext.getString(R.string.app_name))
            .setSingleList(listBuilder.build())
            .build()
    }
}
```

### MapTemplate (Navigation apps)

```kotlin
MapTemplate.Builder()
    .setMapController(
        MapController.Builder()
            .setMapActionStrip(ActionStrip.Builder()
                .addAction(Action.PAN)
                .build())
            .build()
    )
    .setPane(
        Pane.Builder()
            .addRow(Row.Builder().setTitle("Next: Turn right").build())
            .addAction(Action.Builder().setTitle("Stop").setOnClickListener { }.build())
            .build()
    )
    .build()
```

### Template limits while driving

| Template | Max list items (driving) | Max actions |
|---|---|---|
| ListTemplate | 6 | 2 |
| GridTemplate | 6 | 2 |
| MessageTemplate | — | 2 |
| NavigationTemplate | — | 4 (action strip) |

---

## Car UX Restrictions (UXR)

```kotlin
class UxRestrictionsAwareActivity : AppCompatActivity() {

    private lateinit var carUxRestrictionsManager: CarUxRestrictionsManager
    private val listener = CarUxRestrictionsManager.OnUxRestrictionsChangedListener { restrictions ->
        handleUxRestrictions(restrictions)
    }

    override fun onStart() {
        super.onStart()
        val car = Car.createCar(this)
        carUxRestrictionsManager = car.getCarManager(Car.CAR_UX_RESTRICTION_SERVICE)
                as CarUxRestrictionsManager
        carUxRestrictionsManager.registerListener(listener)
        handleUxRestrictions(carUxRestrictionsManager.currentCarUxRestrictions)
    }

    override fun onStop() {
        super.onStop()
        carUxRestrictionsManager.unregisterListener(listener)
    }

    private fun handleUxRestrictions(restrictions: CarUxRestrictions) {
        val isDriving = restrictions.isRequiresDistractionOptimization
        searchInput.isEnabled = !isDriving
        settingsButton.isVisible = !isDriving
    }
}
```

**Rules**
- Always check `isRequiresDistractionOptimization` before allowing text input or complex interactions.
- Disable / hide non-driving features — do not just block input silently.
- In Car App Library, the host enforces template limits automatically — but validate with `CarAppApiLevelToken`.

---

## CarPropertyManager — Vehicle Properties

```kotlin
@Singleton
class HvacRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val car = Car.createCar(context)
    private val propertyManager =
        car.getCarManager(Car.PROPERTY_SERVICE) as CarPropertyManager

    // Read current fan speed
    fun getFanSpeed(zone: Int): Int =
        propertyManager.getIntProperty(VehiclePropertyIds.HVAC_FAN_SPEED, zone)

    // Set driver zone temperature
    fun setDriverTemp(celsius: Float) {
        propertyManager.setFloatProperty(
            VehiclePropertyIds.HVAC_TEMPERATURE_SET,
            VehicleAreaSeat.SEAT_ROW_1_LEFT,
            celsius,
        )
    }

    // Subscribe to property changes
    fun observeDriverTemp(zone: Int): Flow<Float> = callbackFlow {
        val callback = object : CarPropertyManager.CarPropertyEventCallback {
            override fun onChangeEvent(event: CarPropertyValue<*>) {
                trySend(event.value as Float)
            }
            override fun onErrorEvent(propId: Int, zone: Int) { /* handle */ }
        }
        propertyManager.registerCallback(
            callback,
            VehiclePropertyIds.HVAC_TEMPERATURE_SET,
            CarPropertyManager.SENSOR_RATE_ONCHANGE,
        )
        awaitClose { propertyManager.unregisterCallback(callback) }
    }
}
```

**Rules**
- Always check `isPropertyAvailable()` before reading a vehicle property.
- Car API calls must be made from a background thread (IO dispatcher).
- Release `Car` instance in `onDestroy` with `car.disconnect()`.
- `android.car.permission.CONTROL_CAR_CLIMATE` required for HVAC writes — privileged app only.

---

## Permissions for Automotive Apps

| Permission | Category | Requires privileged? |
|---|---|---|
| `android.car.permission.CAR_INFO` | Read vehicle info | No |
| `android.car.permission.CONTROL_CAR_CLIMATE` | Write HVAC | Yes (system/priv) |
| `android.car.permission.CAR_SPEED` | Read vehicle speed | No |
| `android.car.permission.CAR_ENERGY_PORTS` | EV charging/fuel | No |
| `android.car.permission.CAR_EXTERIOR_LIGHTS` | Exterior lights | Yes |

---

## AOSP — Automotive App Module

```soong
android_app {
    name: "MyAutomotiveApp",
    srcs: ["src/**/*.kt"],
    resource_dirs: ["res"],
    manifest: "AndroidManifest.xml",

    static_libs: [
        "androidx.car.app_app",             // Car App Library
        "car-ui-lib",                        // AOSP UI toolkit
        "android.car",                       // CarService stubs for compilation
        "hilt_android",
    ],
    libs: [
        "android.car",
    ],

    certificate: "platform",               // required for privileged car permissions
    privileged: true,
    product_specific: true,

    sdk_version: "current",
}
```

```xml
<!-- automotive_app_desc.xml (res/xml/) -->
<automotiveApp>
    <uses name="template" />
</automotiveApp>
```

---

## Media App in AAOS

For media playback (music, podcasts, audiobooks), use `MediaBrowserServiceCompat`
and `MediaSessionCompat` (or `androidx.media3`). AAOS Media Center discovers media
apps via `android.media.browse.MediaBrowserService` intent filter.

```xml
<service android:name=".MediaPlaybackService"
    android:exported="true">
    <intent-filter>
        <action android:name="android.media.browse.MediaBrowserService" />
    </intent-filter>
</service>
```

```kotlin
class MediaPlaybackService : MediaBrowserServiceCompat() {

    private lateinit var mediaSession: MediaSessionCompat

    override fun onCreate() {
        super.onCreate()
        mediaSession = MediaSessionCompat(this, "MediaPlayback").also { session ->
            session.setCallback(mediaSessionCallback)
            session.isActive = true
            sessionToken = session.sessionToken
        }
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

### Step 1: Request car permissions
Add `android.car.permission.*` permissions in `AndroidManifest.xml`.

### Step 2: Implement CarAppService (for Car App Library apps)
Extend `CarAppService`; override `onCreateSession()` to return your `Session`.

### Step 3: Design templates within UXR constraints
Use only template types allowed at the current `DrivingState`; check `CarUxRestrictions`.

### Step 4: Access vehicle properties
Obtain `CarPropertyManager` from `Car.createCar()` and register listeners.

### Step 5: Test on an emulator or target
Use the Android Automotive OS emulator (`car_x86_64`) or a real AAOS device.


## Troubleshooting

- **`CarNotConnectedException`** — call `Car.createCar()` only after `onStart()`; use the `ServiceLifecycle` callback overload.
- **Template rejected at runtime (UXR violation)** — check `CarUxRestrictions.isRequiresDistractionOptimization()`; only show allowed content while driving.
- **`SecurityException` accessing vehicle property** — request the specific `android.car.permission.*` in the manifest and have it granted at install time.
- **App not visible in the car launcher** — verify `android.hardware.type.automotive` feature declaration in the manifest.


## Pre-Commit Checklist

- [ ] UX Restrictions check: text input disabled while driving.
- [ ] Automotive manifest includes `automotive_app_desc.xml` meta-data.
- [ ] Car App Library: `minCarApiLevel` declared in manifest.
- [ ] Template list item count ≤ 6 while driving.
- [ ] CarPropertyManager: `isPropertyAvailable()` checked before read.
- [ ] Car API calls on IO dispatcher, not main thread.
- [ ] `Car` instance disconnected in `onDestroy`.
- [ ] AOSP: `certificate: "platform"` if using privileged car permissions.
- [ ] Media apps: `MediaBrowserService` intent filter declared.

---

## References

- [Android Automotive OS Developer Guide](https://developer.android.com/training/cars)
- [Car App Library Reference](https://developer.android.com/reference/androidx/car/app/package-summary)
- [Driver Distraction Guidelines](https://developer.android.com/training/cars/apps/ui-guidelines)
- [CarPropertyManager Reference](https://developer.android.com/reference/android/car/hardware/property/CarPropertyManager)
- [AAOS Source — packages/services/Car](https://android.googlesource.com/platform/packages/services/Car)
