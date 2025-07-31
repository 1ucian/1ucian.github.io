# DepthOverlayApp

This is a simple SwiftUI example that demonstrates how to capture an image from the camera or select one from the photo library and overlay the associated depth map (if available).

## Building the App

The repository only includes the Swift source files. To create an Xcode project:

1. Install [XcodeGen](https://github.com/yonaskolb/XcodeGen) using `brew install xcodegen`.
2. From the `DepthOverlay` folder run `xcodegen`. This generates `DepthOverlay.xcodeproj` using `project.yml`.
3. Double‑click the new `DepthOverlay.xcodeproj` file to open it in Xcode.
4. Build the app with **Product → Build** (or press <kbd>⌘B</kbd>), then run it on a device that supports depth capture.

When you pick or capture a portrait photo, the app extracts the depth data and displays it on top of the original image with partial transparency.
