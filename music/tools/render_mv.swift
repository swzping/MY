import AVFoundation
import AppKit
import CoreGraphics
import CoreText
import Foundation

let audioPath = "/Users/edy/Documents/庙堂之外_守望.m4a"
let outputPath = "/Users/edy/Documents/my_mv/exports/庙堂之外_守望_mv.mp4"
let width = 1080
let height = 1920
let fps: Int32 = 24

let audioURL = URL(fileURLWithPath: audioPath)
let outputURL = URL(fileURLWithPath: outputPath)
try? FileManager.default.removeItem(at: outputURL)
try FileManager.default.createDirectory(
    at: outputURL.deletingLastPathComponent(),
    withIntermediateDirectories: true
)

let audioAsset = AVURLAsset(url: audioURL)
let audioDuration = try await audioAsset.load(.duration)
let duration = CMTimeGetSeconds(audioDuration)
let totalFrames = Int(ceil(duration * Double(fps)))

func clamp(_ value: Double, _ low: Double = 0, _ high: Double = 1) -> Double {
    min(max(value, low), high)
}

func smoothstep(_ edge0: Double, _ edge1: Double, _ x: Double) -> Double {
    let t = clamp((x - edge0) / (edge1 - edge0))
    return t * t * (3 - 2 * t)
}

func lerp(_ a: Double, _ b: Double, _ t: Double) -> Double {
    a + (b - a) * t
}

func color(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1) -> CGColor {
    CGColor(red: r / 255, green: g / 255, blue: b / 255, alpha: a)
}

func nsColor(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1) -> NSColor {
    NSColor(calibratedRed: r / 255, green: g / 255, blue: b / 255, alpha: a)
}

func addLine(_ ctx: CGContext, x1: CGFloat, y1: CGFloat, x2: CGFloat, y2: CGFloat) {
    ctx.move(to: CGPoint(x: x1, y: y1))
    ctx.addLine(to: CGPoint(x: x2, y: y2))
}

func drawText(
    _ text: String,
    ctx: CGContext,
    x: CGFloat,
    y: CGFloat,
    size: CGFloat,
    weight: NSFont.Weight = .regular,
    alpha: CGFloat = 1,
    alignment: NSTextAlignment = .center,
    tracking: CGFloat = 0
) {
    let font = NSFont.systemFont(ofSize: size, weight: weight)
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = alignment
    let shadow = NSShadow()
    shadow.shadowColor = NSColor.black.withAlphaComponent(0.45 * alpha)
    shadow.shadowBlurRadius = 14
    shadow.shadowOffset = CGSize(width: 0, height: -2)
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: NSColor.white.withAlphaComponent(alpha),
        .paragraphStyle: paragraph,
        .kern: tracking,
        .shadow: shadow
    ]
    let rect = CGRect(x: x, y: y, width: CGFloat(width) - x * 2, height: size * 2.4)
    text.draw(in: rect, withAttributes: attributes)
}

func makeBuffer(_ adaptor: AVAssetWriterInputPixelBufferAdaptor) -> CVPixelBuffer {
    var maybeBuffer: CVPixelBuffer?
    let attrs: [String: Any] = [
        kCVPixelBufferCGImageCompatibilityKey as String: true,
        kCVPixelBufferCGBitmapContextCompatibilityKey as String: true,
        kCVPixelBufferWidthKey as String: width,
        kCVPixelBufferHeightKey as String: height,
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB
    ]
    CVPixelBufferCreate(kCFAllocatorDefault, width, height, kCVPixelFormatType_32ARGB, attrs as CFDictionary, &maybeBuffer)
    return maybeBuffer!
}

func renderFrame(_ i: Int, adaptor: AVAssetWriterInputPixelBufferAdaptor) -> CVPixelBuffer {
    let pixelBuffer = makeBuffer(adaptor)
    CVPixelBufferLockBaseAddress(pixelBuffer, [])
    defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, []) }

    let ctx = CGContext(
        data: CVPixelBufferGetBaseAddress(pixelBuffer),
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: CVPixelBufferGetBytesPerRow(pixelBuffer),
        space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
    )!

    let t = Double(i) / Double(fps)
    let p = clamp(t / duration)
    let pulse = 0.5 + 0.5 * sin(t * 2.6)
    let beat = pow(max(0, sin(t * 5.2)), 3)
    let rise = smoothstep(0.18, 0.76, p)
    let release = smoothstep(0.56, 0.9, p)

    let top = color(
        CGFloat(lerp(12, 26, rise)),
        CGFloat(lerp(18, 24, release)),
        CGFloat(lerp(31, 28, release))
    )
    let mid = color(
        CGFloat(lerp(28, 72, rise)),
        CGFloat(lerp(38, 46, release)),
        CGFloat(lerp(54, 35, release))
    )
    let bottom = color(
        CGFloat(lerp(8, 30, release)),
        CGFloat(lerp(11, 20, release)),
        CGFloat(lerp(18, 14, release))
    )

    let bg = CGGradient(
        colorsSpace: CGColorSpaceCreateDeviceRGB(),
        colors: [top, mid, bottom] as CFArray,
        locations: [0, 0.52, 1]
    )!
    ctx.drawLinearGradient(bg, start: CGPoint(x: 0, y: height), end: CGPoint(x: 0, y: 0), options: [])

    ctx.saveGState()
    ctx.setAlpha(CGFloat(0.26 + 0.18 * pulse))
    let glow = CGGradient(
        colorsSpace: CGColorSpaceCreateDeviceRGB(),
        colors: [color(233, 181, 92, 0.55), color(233, 181, 92, 0)] as CFArray,
        locations: [0, 1]
    )!
    let gx = CGFloat(width) * CGFloat(0.2 + 0.6 * smoothstep(0.25, 0.78, p))
    ctx.drawRadialGradient(
        glow,
        startCenter: CGPoint(x: gx, y: CGFloat(height) * 0.68),
        startRadius: 20,
        endCenter: CGPoint(x: gx, y: CGFloat(height) * 0.68),
        endRadius: CGFloat(width) * CGFloat(0.52 + 0.14 * beat),
        options: []
    )
    ctx.restoreGState()

    // Rain and dust traces.
    ctx.setLineWidth(1.2)
    for n in 0..<90 {
        let seed = Double((n * 110351 + 12345) % 997) / 997.0
        let x = CGFloat((seed * 1280 + t * 34 + Double(n * 17)).truncatingRemainder(dividingBy: 1180) - 50)
        let ySeed = Double((n * 7919 + 97) % 1543) / 1543.0
        let y = CGFloat((ySeed * 2050 - t * (70 + seed * 80)).truncatingRemainder(dividingBy: 2050))
        ctx.setStrokeColor(color(223, 231, 235, CGFloat(0.08 + 0.12 * seed)))
        addLine(ctx, x1: x, y1: y, x2: x + 16, y2: y - 58)
        ctx.strokePath()
    }

    // Palace wall silhouette.
    let wallY = CGFloat(440 + 44 * sin(t * 0.42))
    ctx.setFillColor(color(24, 20, 22, 0.94))
    ctx.fill(CGRect(x: 0, y: 0, width: CGFloat(width), height: wallY))
    ctx.setFillColor(color(80, 38, 35, 0.46))
    ctx.fill(CGRect(x: 0, y: wallY - 88, width: CGFloat(width), height: 88))
    for k in 0..<9 {
        let x = CGFloat(k) * 142 - CGFloat((t * 16).truncatingRemainder(dividingBy: 142))
        ctx.setFillColor(color(144, 94, 64, 0.36))
        ctx.fill(CGRect(x: x, y: wallY - 72, width: 74, height: 34))
    }

    // Temple roof outline outside the court.
    let roofBase = CGFloat(1025 - 90 * rise)
    ctx.setFillColor(color(11, 12, 17, CGFloat(0.62 + 0.22 * release)))
    let roof = CGMutablePath()
    roof.move(to: CGPoint(x: -90, y: roofBase))
    roof.addLine(to: CGPoint(x: 170, y: roofBase + 86))
    roof.addLine(to: CGPoint(x: 450, y: roofBase + 54))
    roof.addLine(to: CGPoint(x: 540, y: roofBase + 128))
    roof.addLine(to: CGPoint(x: 630, y: roofBase + 54))
    roof.addLine(to: CGPoint(x: 910, y: roofBase + 86))
    roof.addLine(to: CGPoint(x: 1170, y: roofBase))
    roof.addLine(to: CGPoint(x: 1060, y: roofBase - 42))
    roof.addLine(to: CGPoint(x: 20, y: roofBase - 42))
    roof.closeSubpath()
    ctx.addPath(roof)
    ctx.fillPath()

    // Window bars, as if seen from inside.
    ctx.setStrokeColor(color(5, 8, 12, CGFloat(0.32 + 0.18 * (1 - release))))
    ctx.setLineWidth(18)
    for x in stride(from: 94, through: 986, by: 178) {
        addLine(ctx, x1: CGFloat(x), y1: 620, x2: CGFloat(x), y2: 1660)
    }
    ctx.strokePath()
    ctx.setLineWidth(10)
    for y in stride(from: 720, through: 1540, by: 205) {
        let yf = CGFloat(Double(y) + 20 * sin(t * 0.5))
        addLine(ctx, x1: 70, y1: CGFloat(y), x2: 1010, y2: yf)
    }
    ctx.strokePath()

    // A lone watcher.
    let personX = CGFloat(lerp(438, 520, smoothstep(0.12, 0.65, p)) + 22 * sin(t * 0.36))
    let personY = CGFloat(360)
    ctx.setFillColor(color(3, 5, 8, 0.93))
    ctx.fillEllipse(in: CGRect(x: personX + 42, y: personY + 252, width: 86, height: 98))
    let body = CGMutablePath()
    body.move(to: CGPoint(x: personX + 84, y: personY + 250))
    body.addCurve(to: CGPoint(x: personX + 10, y: personY + 36), control1: CGPoint(x: personX + 34, y: personY + 210), control2: CGPoint(x: personX + 26, y: personY + 110))
    body.addLine(to: CGPoint(x: personX + 174, y: personY + 36))
    body.addCurve(to: CGPoint(x: personX + 84, y: personY + 250), control1: CGPoint(x: personX + 152, y: personY + 110), control2: CGPoint(x: personX + 140, y: personY + 210))
    body.closeSubpath()
    ctx.addPath(body)
    ctx.fillPath()
    ctx.setStrokeColor(color(224, 179, 92, CGFloat(0.28 + 0.3 * beat)))
    ctx.setLineWidth(3)
    addLine(ctx, x1: personX + 84, y1: personY + 245, x2: personX + 84, y2: personY + 72)
    ctx.strokePath()

    // Light path on the ground.
    ctx.saveGState()
    ctx.setAlpha(CGFloat(0.24 + 0.28 * release))
    let pathGrad = CGGradient(
        colorsSpace: CGColorSpaceCreateDeviceRGB(),
        colors: [color(229, 174, 91, 0), color(229, 174, 91, 0.55), color(229, 174, 91, 0)] as CFArray,
        locations: [0, 0.5, 1]
    )!
    let lightPath = CGMutablePath()
    lightPath.move(to: CGPoint(x: 476, y: 0))
    lightPath.addLine(to: CGPoint(x: 604, y: 0))
    lightPath.addLine(to: CGPoint(x: 560 + 85 * CGFloat(beat), y: 920))
    lightPath.addLine(to: CGPoint(x: 520 - 85 * CGFloat(beat), y: 920))
    lightPath.closeSubpath()
    ctx.addPath(lightPath)
    ctx.clip()
    ctx.drawLinearGradient(pathGrad, start: CGPoint(x: 540, y: 0), end: CGPoint(x: 540, y: 960), options: [])
    ctx.restoreGState()

    // Subtle film vignette.
    ctx.setStrokeColor(color(2, 3, 5, 0.42))
    ctx.setLineWidth(90)
    ctx.stroke(CGRect(x: 28, y: 28, width: width - 56, height: height - 56))

    let titleIn = smoothstep(0.02, 0.08, p) * (1 - smoothstep(0.2, 0.28, p))
    let lineIn = smoothstep(0.25, 0.34, p) * (1 - smoothstep(0.45, 0.52, p))
    let chorusIn = smoothstep(0.54, 0.61, p) * (1 - smoothstep(0.78, 0.86, p))
    let endIn = smoothstep(0.84, 0.92, p)

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(cgContext: ctx, flipped: false)
    if titleIn > 0.01 {
        drawText("庙堂之外", ctx: ctx, x: 96, y: 1440, size: 86, weight: .semibold, alpha: CGFloat(titleIn), tracking: 8)
        drawText("守望", ctx: ctx, x: 96, y: 1340, size: 50, weight: .medium, alpha: CGFloat(titleIn * 0.86), tracking: 14)
    }
    if lineIn > 0.01 {
        drawText("在高墙与风声之间", ctx: ctx, x: 86, y: 260, size: 44, weight: .regular, alpha: CGFloat(lineIn * 0.9), tracking: 2)
        drawText("把沉默站成一束光", ctx: ctx, x: 86, y: 200, size: 44, weight: .regular, alpha: CGFloat(lineIn * 0.9), tracking: 2)
    }
    if chorusIn > 0.01 {
        drawText("我仍在此处守望", ctx: ctx, x: 68, y: 1250, size: 64, weight: .semibold, alpha: CGFloat(chorusIn), tracking: 4)
        drawText("等云开，也等自己回响", ctx: ctx, x: 86, y: 1176, size: 42, weight: .regular, alpha: CGFloat(chorusIn * 0.86), tracking: 1)
    }
    if endIn > 0.01 {
        drawText("愿风越过庙堂", ctx: ctx, x: 86, y: 278, size: 44, weight: .regular, alpha: CGFloat(endIn * 0.88), tracking: 2)
        drawText("仍有人点灯", ctx: ctx, x: 86, y: 218, size: 44, weight: .regular, alpha: CGFloat(endIn * 0.88), tracking: 2)
    }
    NSGraphicsContext.restoreGraphicsState()

    return pixelBuffer
}

let writer = try AVAssetWriter(outputURL: outputURL, fileType: .mp4)
let videoSettings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 7_500_000,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel
    ]
]
let input = AVAssetWriterInput(mediaType: .video, outputSettings: videoSettings)
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: input,
    sourcePixelBufferAttributes: [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
        kCVPixelBufferWidthKey as String: width,
        kCVPixelBufferHeightKey as String: height
    ]
)
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

let queue = DispatchQueue(label: "mv.video.writer")
let semaphore = DispatchSemaphore(value: 0)
var frame = 0
input.requestMediaDataWhenReady(on: queue) {
    while input.isReadyForMoreMediaData && frame < totalFrames {
        autoreleasepool {
            let buffer = renderFrame(frame, adaptor: adaptor)
            let time = CMTime(value: CMTimeValue(frame), timescale: fps)
            adaptor.append(buffer, withPresentationTime: time)
        }
        if frame % 120 == 0 {
            print("rendered \(frame)/\(totalFrames)")
        }
        frame += 1
    }
    if frame >= totalFrames {
        input.markAsFinished()
        writer.finishWriting {
            semaphore.signal()
        }
    }
}
semaphore.wait()

if writer.status != .completed {
    throw writer.error ?? NSError(domain: "RenderMV", code: 1)
}

let silentVideoURL = outputURL.deletingPathExtension().appendingPathExtension("silent.mp4")
try? FileManager.default.removeItem(at: silentVideoURL)
try FileManager.default.moveItem(at: outputURL, to: silentVideoURL)

let composition = AVMutableComposition()
let videoAsset = AVURLAsset(url: silentVideoURL)
let videoTrack = try await videoAsset.loadTracks(withMediaType: .video).first!
let videoDuration = try await videoAsset.load(.duration)
let compositionVideo = composition.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
try compositionVideo.insertTimeRange(CMTimeRange(start: .zero, duration: videoDuration), of: videoTrack, at: .zero)
compositionVideo.preferredTransform = try await videoTrack.load(.preferredTransform)

let audioTrack = try await audioAsset.loadTracks(withMediaType: .audio).first!
let compositionAudio = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
try compositionAudio.insertTimeRange(CMTimeRange(start: .zero, duration: audioDuration), of: audioTrack, at: .zero)

let export = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetHighestQuality)!
export.outputURL = outputURL
export.outputFileType = .mp4
export.shouldOptimizeForNetworkUse = true
await export.export()

if export.status != .completed {
    throw export.error ?? NSError(domain: "RenderMVExport", code: 2)
}

try? FileManager.default.removeItem(at: silentVideoURL)
print("done: \(outputPath)")
