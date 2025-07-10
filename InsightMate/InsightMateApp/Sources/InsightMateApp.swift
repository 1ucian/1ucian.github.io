import SwiftUI
import AppKit

@main
struct InsightMateApp: App {
    @State private var isRunning = false
    @State private var chatWindow: NSWindow?

    var body: some Scene {
        MenuBarExtra("InsightMate", systemImage: "brain") {
            Button("Run Assistant") { runAssistant() }
            Button("Chat…") { openChat() }
            Button("Preferences…") {}
            Divider()
            Button("Quit") {
                NSApplication.shared.terminate(nil)
            }
        }
    }

    func startServerIfNeeded() {
        let check = Process()
        check.launchPath = "/usr/bin/pgrep"
        check.arguments = ["-f", "ai_server.py"]
        check.standardOutput = Pipe()
        try? check.run()
        check.waitUntilExit()
        if check.terminationStatus != 0 {
            let resourceURL = Bundle.main.resourceURL!.appendingPathComponent("py")
            let server = resourceURL.appendingPathComponent("ai_server.py").path
            let proc = Process()
            proc.launchPath = "/usr/bin/python3"
            proc.arguments = ["-u", server]
            proc.standardOutput = nil
            proc.standardError = nil
            try? proc.run()
        }
    }

    func runAssistant(prompt: String? = nil, completion: ((String) -> Void)? = nil) {
        guard !isRunning else { return }
        isRunning = true
        startServerIfNeeded()
        let resourceURL = Bundle.main.resourceURL!.appendingPathComponent("py")
        let script = resourceURL.appendingPathComponent("main.py").path
        let process = Process()
        process.launchPath = "/usr/bin/python3"
        var args = ["-u", script]
        if let p = prompt { args.append(p) }
        process.arguments = args
        process.terminationHandler = { _ in
            isRunning = false
            let outputPath = "/tmp/insight_output.txt"
            let body = (try? String(contentsOfFile: outputPath)) ?? ""
            if let completion = completion {
                completion(body)
            } else {
                notifyCompletion(body: body)
            }
        }
        try? process.run()
    }

    func notifyCompletion(body: String) {
        let notification = NSUserNotification()
        notification.title = "InsightMate"
        notification.informativeText = body
        NSUserNotificationCenter.default.deliver(notification)
    }

    func openChat() {
        if chatWindow == nil {
            let chatView = ChatView { prompt, cb in
                runAssistant(prompt: prompt, completion: cb)
            }
            chatWindow = NSWindow(
                contentRect: NSRect(x: 0, y: 0, width: 320, height: 400),
                styleMask: [.titled, .closable, .resizable],
                backing: .buffered,
                defer: false
            )
            chatWindow?.title = "InsightMate Chat"
            chatWindow?.contentView = NSHostingView(rootView: chatView)
        }
        chatWindow?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

struct ChatView: View {
    var run: (String, @escaping (String) -> Void) -> Void
    @State private var input = ""
    @State private var transcript = ""

    var body: some View {
        VStack {
            ScrollView {
                Text(transcript)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            HStack {
                TextField("Message", text: $input)
                Button("Send") {
                    let prompt = input
                    input = ""
                    run(prompt) { reply in
                        DispatchQueue.main.async {
                            transcript += "\nYou: \(prompt)\nAI: \(reply)"
                        }
                    }
                }
            }
        }
        .padding()
    }
}
