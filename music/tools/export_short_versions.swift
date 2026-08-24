import AVFoundation
import Foundation

let sourcePath = "/Users/edy/Documents/my_mv/exports/庙堂之外_守望_mv.mp4"
let jobs: [(name: String, start: Double, duration: Double)] = [
    ("庙堂之外_守望_15s_hook_placeholder.mp4", 34.0, 15.0),
    ("庙堂之外_守望_30s_story_placeholder.mp4", 24.0, 30.0)
]

let sourceURL = URL(fileURLWithPath: sourcePath)
let asset = AVURLAsset(url: sourceURL)
let exportDir = URL(fileURLWithPath: "/Users/edy/Documents/my_mv/exports", isDirectory: true)

for job in jobs {
    let outURL = exportDir.appendingPathComponent(job.name)
    try? FileManager.default.removeItem(at: outURL)

    let start = CMTime(seconds: job.start, preferredTimescale: 600)
    let duration = CMTime(seconds: job.duration, preferredTimescale: 600)
    let range = CMTimeRange(start: start, duration: duration)

    guard let session = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetHighestQuality) else {
        throw NSError(domain: "ShortExport", code: 1)
    }
    session.outputURL = outURL
    session.outputFileType = .mp4
    session.timeRange = range
    session.shouldOptimizeForNetworkUse = true

    await session.export()
    if session.status != .completed {
        throw session.error ?? NSError(domain: "ShortExport", code: 2)
    }
    print("exported: \(outURL.path)")
}

