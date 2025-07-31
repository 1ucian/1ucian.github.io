import UIKit
import AVFoundation
import ImageIO

enum DepthRenderer {
    static func image(from depthData: AVDepthData) -> UIImage? {
        let converted = depthData.converting(toDepthDataType: kCVPixelFormatType_DepthFloat32)
        let map = converted.depthDataMap
        let ciImage = CIImage(cvPixelBuffer: map)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return nil }
        return UIImage(cgImage: cgImage)
    }

    static func loadDepthMap(from url: URL) -> UIImage? {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let info = CGImageSourceCopyAuxiliaryDataInfoAtIndex(source, 0, kCGImageAuxiliaryDataTypeDisparity) as? [String: Any],
              let depth = try? AVDepthData(fromDictionaryRepresentation: info) else { return nil }
        return image(from: depth)
    }
}
