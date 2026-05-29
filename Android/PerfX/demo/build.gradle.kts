plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

kotlin {
    jvmToolchain(17)
}

android {
    namespace = "com.ndevelop.perfx"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.ndevelop.perfx"
        minSdk = 28
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // Defaults — override per flavor or in local.properties
        buildConfigField("String", "PROJECT_ID",    "\"\"")
        buildConfigField("String", "ENDPOINT_URL",  "\"http://10.0.2.2:8080/\"")
    }

    flavorDimensions += "monitoring"
    productFlavors {
        create("withSdk") {
            dimension = "monitoring"
            buildConfigField("boolean", "SDK_ENABLED", "true")
            // ← paste your project UUID from the PerfX dashboard here
            buildConfigField("String", "PROJECT_ID", "\"c0fabf43-bbd4-4f9e-bdab-ee5019727b00\"")
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