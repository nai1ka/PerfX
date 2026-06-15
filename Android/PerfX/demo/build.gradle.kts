plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

kotlin {
    jvmToolchain(17)
}

val syntheticVersionCode: Int =
    (project.findProperty("syntheticVersionCode") as? String)?.toIntOrNull() ?: 1
val syntheticVersionName: String =
    (project.findProperty("syntheticVersionName") as? String) ?: "1.0"
val regressionType: String =
    (project.findProperty("regressionType") as? String) ?: "none"
val regressionIntensity: Int =
    (project.findProperty("regressionIntensity") as? String)?.toIntOrNull() ?: 0
val targetScreen: String =
    (project.findProperty("targetScreen") as? String) ?: "home"

android {
    namespace = "com.ndevelop.perfx"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.ndevelop.perfx"
        minSdk = 28
        targetSdk = 36

        versionCode = 3
        versionName = "3.0"
        buildConfigField("String", "BAKED_REGRESSION_TYPE", "\"$regressionType\"")
        buildConfigField("int",    "BAKED_REGRESSION_INTENSITY", "$regressionIntensity")
        buildConfigField("String", "TARGET_SCREEN", "\"$targetScreen\"")

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // Defaults — override per flavor or in local.properties
        buildConfigField("String", "PROJECT_ID",    "\"\"")
        buildConfigField("String", "ENDPOINT_URL",  "\"https://api.perfx.ru/\"")
    }

    flavorDimensions += "monitoring"
    productFlavors {
        create("withSdk") {
            dimension = "monitoring"
            buildConfigField("boolean", "SDK_ENABLED", "true")
            // ← paste your project UUID from the PerfX dashboard here
            buildConfigField("String", "PROJECT_ID", "\"632af5b7-43bc-4fa0-bb26-ac82e381d541\"")
        }
        create("noSdk") {
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
}