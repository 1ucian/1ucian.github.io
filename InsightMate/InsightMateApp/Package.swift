// swift-tools-version: 6.1
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "InsightMateApp",
    targets: [
        .executableTarget(
            name: "InsightMateApp",
            resources: [
                .copy("Resources/py"),
                .process("Resources/Assets.xcassets")
            ]
        )
    ]
)
