import SwiftUI
import PhotosUI

struct ContentView: View {
    @State private var showCamera = false
    @State private var showPicker = false
    @State private var pickedImage: UIImage?
    @State private var depthOverlay: UIImage?
    @State private var pickerItem: PhotosPickerItem?

    var body: some View {
        VStack {
            if let img = pickedImage {
                ZStack {
                    Image(uiImage: img)
                        .resizable()
                        .scaledToFit()
                    if let depth = depthOverlay {
                        Image(uiImage: depth)
                            .resizable()
                            .scaledToFit()
                            .opacity(0.6)
                    }
                }
            } else {
                Text("Choose or take a photo")
                    .padding()
            }
            HStack {
                Button("Camera") { showCamera = true }
                    .padding()
                Button("Photo Library") { showPicker = true }
                    .padding()
            }
        }
        .sheet(isPresented: $showCamera) {
            CameraView { img, depth in
                self.pickedImage = img
                self.depthOverlay = depth
            }
        }
        .photosPicker(isPresented: $showPicker, selection: $pickerItem, matching: .images)
        .onChange(of: pickerItem) { newItem in
            loadPhoto(from: newItem)
        }
    }

    private func loadPhoto(from item: PhotosPickerItem?) {
        guard let item else { return }
        Task {
            if let data = try? await item.loadTransferable(type: Data.self),
               let uiImage = UIImage(data: data) {
                self.pickedImage = uiImage
            }
            if let id = item.assetIdentifier {
                fetchDepth(assetID: id)
            }
        }
    }

    private func fetchDepth(assetID: String) {
        let assets = PHAsset.fetchAssets(withLocalIdentifiers: [assetID], options: nil)
        guard let asset = assets.firstObject else { return }
        let opts = PHContentEditingInputRequestOptions()
        asset.requestContentEditingInput(with: opts) { input, _ in
            guard let url = input?.fullSizeImageURL else { return }
            if let overlay = DepthRenderer.loadDepthMap(from: url) {
                DispatchQueue.main.async {
                    self.depthOverlay = overlay
                }
            }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
