import SwiftUI
import AVFoundation

struct CameraView: UIViewControllerRepresentable {
    var completion: (UIImage, UIImage?) -> Void

    func makeUIViewController(context: Context) -> CameraController {
        let controller = CameraController()
        controller.completion = completion
        return controller
    }

    func updateUIViewController(_ uiViewController: CameraController, context: Context) {}
}

class CameraController: UIViewController, AVCapturePhotoCaptureDelegate {
    private let session = AVCaptureSession()
    private let output = AVCapturePhotoOutput()
    var completion: ((UIImage, UIImage?) -> Void)?
    private var preview: AVCaptureVideoPreviewLayer!

    override func viewDidLoad() {
        super.viewDidLoad()
        configureSession()
        preview = AVCaptureVideoPreviewLayer(session: session)
        preview.frame = view.bounds
        preview.videoGravity = .resizeAspectFill
        view.layer.addSublayer(preview)

        let button = UIButton(type: .system)
        button.setTitle("Capture", for: .normal)
        button.backgroundColor = UIColor.systemBlue.withAlphaComponent(0.7)
        button.tintColor = .white
        button.layer.cornerRadius = 8
        button.frame = CGRect(x: 20, y: view.bounds.height - 80, width: 100, height: 44)
        button.autoresizingMask = [.flexibleTopMargin, .flexibleRightMargin]
        button.addTarget(self, action: #selector(capture), for: .touchUpInside)
        view.addSubview(button)
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        session.startRunning()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        session.stopRunning()
    }

    private func configureSession() {
        session.beginConfiguration()
        session.sessionPreset = .photo
        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: device),
              session.canAddInput(input) else { return }
        session.addInput(input)

        if session.canAddOutput(output) {
            session.addOutput(output)
            output.isDepthDataDeliveryEnabled = output.isDepthDataDeliverySupported
        }
        session.commitConfiguration()
    }

    @objc func capture() {
        let settings = AVCapturePhotoSettings()
        settings.isDepthDataDeliveryEnabled = output.isDepthDataDeliveryEnabled
        output.capturePhoto(with: settings, delegate: self)
    }

    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard error == nil, let data = photo.fileDataRepresentation(), let image = UIImage(data: data) else { return }
        var depthImage: UIImage?
        if let depth = photo.depthData {
            depthImage = DepthRenderer.image(from: depth)
        }
        completion?(image, depthImage)
        dismiss(animated: true)
    }
}
