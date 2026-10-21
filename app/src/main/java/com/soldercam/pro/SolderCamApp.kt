package com.soldercam.pro

import android.app.Application

class SolderCamApp : Application() {
    override fun onCreate() {
        super.onCreate()
        BugTracker.init(this)
    }
}
