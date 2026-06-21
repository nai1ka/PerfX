plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

kotlin {
    jvmToolchain(17)
}

val syntheticVersionCode: Int =
    (project.findProperty("syntheticVersionCode") as? String)?.toIntOrNull() ?: 99
val syntheticVersionName: String =
    (project.findProperty("syntheticVersionName") as? String) ?: "9.0"
val regressionType: String =
    (project.findProperty("regressionType") as? String) ?: "none"
val regressionIntensity: Int =
    (project.findProperty("regressionIntensity") as? String)?.toIntOrNull() ?: 0
val targetScreen: String =
    (project.findProperty("targetScreen") as? String) ?: "home"
// Backend the SDK reports to. Override for local evaluation, e.g.
//   -PendpointUrl=http://10.0.2.2:8080/   (emulator alias for host localhost)
val endpointUrl: String =
    (project.findProperty("endpointUrl") as? String) ?: "https://api.perfx.ru/"
// Project UUID the app reports under. Must match the --project-id passed to the
// evaluation scripts so the app and the queries agree.
val projectId: String =
    (project.findProperty("projectId") as? String) ?: "632af5b7-43bc-4fa0-bb26-ac82e381d541"

android {
    namespace = "com.ndevelop.perfx"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.ndevelop.perfx"
        minSdk = 28
        targetSdk = 36

        // Driven by -PsyntheticVersionCode / -PsyntheticVersionName so each
        // experiment build reports a distinct version. The SDK reads the version
        // from PackageManager, so this must reflect the synthetic value (default 1).
        versionCode = syntheticVersionCode
        versionName = syntheticVersionName
        buildConfigField("String", "BAKED_REGRESSION_TYPE", "\"$regressionType\"")
        buildConfigField("int",    "BAKED_REGRESSION_INTENSITY", "$regressionIntensity")
        buildConfigField("String", "TARGET_SCREEN", "\"$targetScreen\"")

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // Defaults — override per flavor or in local.properties
        buildConfigField("String", "PROJECT_ID",    "\"\"")
        buildConfigField("String", "ENDPOINT_URL",  "\"$endpointUrl\"")
    }

    flavorDimensions += "monitoring"
    productFlavors {
        create("withSdk") {
            dimension = "monitoring"
            buildConfigField("boolean", "SDK_ENABLED", "true")
            // Project UUID from the PerfX dashboard; override with -PprojectId=<uuid>.
            buildConfigField("String", "PROJECT_ID", "\"$projectId\"")
        }
        create("noSdk") {
            dimension = "monitoring"
            buildConfigField("boolean", "SDK_ENABLED", "false")
            buildConfigField("String", "PROJECT_ID", "\"\"")
        }
        // Comparison variant for the SDK overhead study: ships Firebase
        // Performance Monitoring instead of the PerfX SDK. PerfX is still on the
        // classpath (same as noSdk) but PerfX.initialize is not called.
        create("withFirebase") {
            dimension = "monitoring"
            buildConfigField("boolean", "SDK_ENABLED", "false")
            buildConfigField("String", "PROJECT_ID", "\"\"")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(project(":sdk"))
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.navigation.compose)
    implementation("com.airbnb.android:lottie-compose:6.3.0")
    testImplementation(libs.junit)

    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)

    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)

    // Firebase Performance Monitoring is linked only for the withFirebase
    // flavor, so that noSdk and withSdk builds remain unaffected.
    "withFirebaseImplementation"(platform(libs.firebase.bom))
    "withFirebaseImplementation"(libs.firebase.perf)
}

// Apply the Google Services plugin only when the user has dropped
// google-services.json into src/withFirebase/. Without this guard the noSdk
// and withSdk flavors would fail to build whenever the file is missing.
if (file("src/withFirebase/google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
}